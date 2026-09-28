# Misaligned Exception & Bus Error Debug (Nuclei)

## 1. Store/AMO Address Misaligned (mcause=7)

### What It Means (Real Case)

The processor detected a store or atomic memory operation to a non-aligned address:
- `sw` / `sh` / `sb` / `amoswap` / `amoadd` etc. to an address that violates alignment
- `sw` requires 4-byte alignment; `sh` requires 2-byte alignment
- AMO always requires **natural alignment** (4B for word, 8B for double-word)

### Bus Error Masquerading as Misaligned

**Critical pattern on Nuclei cores**: A `sw` to a valid 4-byte aligned address that triggers a **bus error** (slave not responding, decode miss, timeout) may be reported as **Store/AMO address misaligned (mcause=7)** rather than Store access fault (mcause=9).

This happens because the bus error is detected AFTER the alignment check passes. The core's exception priority logic may map the bus error to a misaligned encoding depending on the implementation.

### How to Disambiguate

| Signal / CSR | Real Misaligned | Bus Error Masquerade |
|---|---|---|
| Target address | Address % width != 0 | Address is aligned (e.g. 0x40000050 for `sw`) |
| `mdcause` / `dcause` | Alignment-specific code | May show bus error subtype |
| `mtval` | Faulting address | Faulting address (same) |
| Bus signals (waveform) | N/A | Slave error / no response on data bus |

### Debug Flow

```
1. Identify the instruction (sw/sh/amoswap etc.) from mepc or trace
2. Calculate actual target address (base + offset) from disassembly
3. Check alignment: target_addr % access_width == 0?
   ├─ NO  → Real misaligned — fix code
   └─ YES → Bus error masquerade — go to step 4
4. Check mdcause / dcause for subtype
5. Check if target address space supports this access type
6. Check bus/ICB signals in waveform
```

## 2. Exception Table — mcause + mdcause Mapping

### RISC-V Standard mcause Values

| mcause | Exception Type | Synchronous? |
|---|---|---|
| 0 | Instruction address misaligned | Sync |
| 1 | Instruction access fault | Sync |
| 2 | Illegal instruction | Sync |
| 3 | Breakpoint | Sync |
| 4 | Load address misaligned | Sync |
| 5 | Load access fault | Sync |
| 6 | Store/AMO address misaligned | Sync |
| 7 | Store/AMO access fault | Sync |
| 8 | User env call (ecall from U-mode) | Sync |
| 9 | Supervisor env call (ecall from S-mode) | Sync |
| 11 | Machine env call (ecall from M-mode) | Sync |
| 12–23 | Standard page faults (Sv39/Sv48) | Sync |

### Nuclei Core Bus Error → mcause=6 (Not mcause=7!)

On Nuclei cores, a **core bus error** (due to memory read/write failing on the bus) maps to **mcause=6**, with `mdcause` providing the subtype:

| mdcause | Subtype |
|---|---|
| 2 | Bus error caused by core memory read |
| 2 | Bus error caused by core memory write |

Both read and write bus errors map to `mdcause=2`.

### Exception #6 vs #7 Clarification

| mcause | Name | Correct Value for Bus Error |
|---|---|---|
| **6** | **Store/AMO address misaligned** | Used by Nuclei for bus errors on read AND write (mdcause=2) |
| 7 | Store/AMO access fault | Standard RISC-V — not typically used for Nuclei bus errors |

So if you see mcause=6 (Store/AMO address misaligned) on a Nuclei core, check mdcause:
- `mdcause=2` → It's actually a **bus error**
- `mdcause=other` → Real alignment issue

## 3. PPI Address Space Alignment Considerations

PPI (Private Peripheral Interconnect) region: typically `0x4000_0000` range.

### Common Pitfall: sw to PPI with Incorrect Offset

Given:
```
lui a3, 0x40000          → a3 = 0x4000_0000 (low 12 bits cleared)
sw a5, 80(a3)            → address = 0x4000_0000 + 80 = 0x4000_0050
sw a5, 84(a3)            → address = 0x4000_0000 + 84 = 0x4000_0054
sw a5, 88(a3)            → address = 0x4000_0000 + 88 = 0x4000_0058
```

`lui` sets a3 = `0x4000_0000` correctly. Offsets 80/84/88 are all 4-byte aligned. **The address is not the problem.**

If bus error occurs here, check:
1. Does the PPI slave map offset 0x50/0x54/0x58?
2. Is the slave returning `rready`/`rvalid` correctly in the waveform?
3. Any address translation (PMB/MMU) changing the physical address?

## 4. ICB Response Selector — port_id & err Signal Analysis

### ICB Protocol Signals

| Signal | Width | Meaning |
|---|---|---|
| `o_icb_rsp_port_id[j]` | N-bit | Split channel j's **port ID bitmap** — which port this response belongs to |
| `o_icb_rsp_err[j]` | N-bit | Split channel j's **error bitmap** — which ports have errors |
| `sel_i_icb_rsp_err` | 1-bit | Final OR'd error (1 = at least one selected port has error) |

### Selection Logic

```verilog
sel_i_icb_rsp_err = 1'b0;
for(j = 0; j < SPLT_NUM; j = j+1) begin
    sel_i_icb_rsp_err = sel_i_icb_rsp_err || ( o_icb_rsp_port_id[j] & o_icb_rsp_err[j] );
end
```

- `o_icb_rsp_port_id[j]` is a **bitmap**: bit k = 1 means "this response targets port k"
- `o_icb_rsp_err[j]` is also a **bitmap**: bit k = 1 means "port k has an error"
- Their AND gives: "which ports are selected AND have errors"
- OR across all j: "any split channel has a selected port with error"

### SPLT_NUM Mismatch — Most Common Bug

When SPLT_NUM is smaller than the actual port ID range being used:

| SPLT_NUM | Loop covers | port_id value | err value | Result |
|---|---|---|---|---|
| 1 | j=0 only | port_id[0]=2 (binary 10) | err[0]=3 (binary 11) | port_id[0] & err[0] = 2 & 3 = **2 (non-zero, error detected)** |
| 1 | j=0 only | port_id[0]=0 | err[0]=3 | port_id[0] & err[0] = 0 → **no error detected — mistake!** |

**Example from real debug**:
- `o_icb_rsp_port_id[1] & o_icb_rsp_err[1]` = 1 (bit 1 of both signals is 1)
- But `SPLT_NUM=1` means the loop stops at j=0 → **port 1's error is never examined**

### Fix

Either:
- Increase `SPLT_NUM` to cover all possible port IDs
- Or ensure `port_id` bitmap only sets bits within `[0, SPLT_NUM)` range

## 5. Waveform Signals to Capture

For bus error / misaligned exception debug:

```verilog
// Exception info
*mcause*           // exception cause code
*mdcause*           // NUCLEI-specific: bus error subtype
*dcause*            // D-mode cause
*mtval*             // trap value (address or instruction)
*mepc*              // exception PC

// Data bus (ICB)
*icb_rsp_port_id*   // port ID bitmap
*icb_rsp_err*       // error bitmap
*icb_rsp_rdata*     // read data
*icb_cmd_valid*     // command valid
*icb_cmd_ready*     // command ready
*icb_rsp_valid*     // response valid
*icb_rsp_ready*     // response ready

// Core signals
*lsu_stall*         // load/store unit stall
*store_buffer_full* // store buffer full
*data_wait*         // waiting for data bus
```

## 6. Quick Decision Flow

```
misaligned exception (mcause=6/7)?
├─ Check address alignment
│   ├─ NOT aligned → REAL MISALIGNED → fix code/address calc
│   └─ Aligned → BUS ERROR MASQUERADE
│       ├─ Check mdcause
│       │   └─ mdcause=2 → Bus error confirmed
│       ├─ Check PPI/ICB signals in waveform
│       │   ├─ Slave not responding? → Memory map issue
│       │   ├─ rsp_err=1? → ICB error → check port_id vs SPLT_NUM
│       │   └─ Port bitmap outside SPLT_NUM range → SPLT_NUM mismatch
│       └─ If bus signals clean → Core implementation bug
```
