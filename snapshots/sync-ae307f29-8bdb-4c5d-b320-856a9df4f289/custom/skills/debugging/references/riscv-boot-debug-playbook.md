
# RISC-V CPU Boot-Time Debug

## 1. Classification — Two Distinct Cases

When iaddr (instruction address) appears stuck, **first disambiguate**:

| Observation | Classification | Root Cause Family |
|---|---|---|
| iaddr cycles through 2–4 addresses (e.g. 0x518→0x51c→0x520→0x518→...) | **Software infinite loop** | Bounds mismatch, wrap-around overflow |
| iaddr stays on **one** address cycle after cycle | **Hardware stall** | Bus no-response, LSU stall, I-Cache miss, clock/reset issue |
| iaddr = 0 / 0xFFFFFFFF / unmapped region | **Illegal address** | Bad vector, missing memory map |

## 2. Software Infinite Loop — BSS Clear Analysis

The most common boot-time infinite loop is the **BSS zero-init loop**:

```asm
la a0, _bss_start         # load BSS start address
la a1, _end               # load program end address
bgeu a0, a1, 2f           # skip if already at end
1:                        # loop body
  sw zero, 0(a0)           # *a0 = 0
  addi a0, a0, 4           # a0 += 4
  bltu a0, a1, 1b          # if a0 < a1, loop
2:
```

### Key Debug Values

In waveform, capture **register file values** at the start of this loop:

```
x10 / a0  →  _bss_start + offset
x11 / a1  →  _end
```

### Common Root Causes

| Symptom | Cause | Fix |
|---|---|---|
| a1 (`_end`) is 0xFFFFFFFF or very large | Linker script `_end` placed after unmapped/empty memory region | Check `.ld` file section ordering |
| a0 wraps from 0xFFFFFFFC → 0x00000000 | `addi` overflow: unsigned `bltu` sees 0 < large a1 → loops forever | Fix `_bss_start` alignment or add early-exit check |
| a0 > a1 at start | `_bss_start` after `_end` in linker layout | Reorder sections |

### Why `_end` (not `_bss_end`) in Startup Code

Nuclei SDK startup code uses `_end` instead of `_bss_end` because:

1. **`_end` is a GNU LD built-in symbol** — always available regardless of linker script content (along with `_etext`, `_edata`)
2. **`_bss_end` is project-specific** — if a given `.ld` file omits it, the link fails
3. **`_end` covers more than `.bss`** — includes `.sbss`, `COMMON`, padding alignment, and any post-BSS sections

```ld
// In linker script:
.bss : {
    _bss_start = .;
    *(.sbss) *(.sbss.*) *(.bss) *(.bss.*) *(COMMON)
    . = ALIGN(4);
    _bss_end = .;     // May not exist in all scripts
}
_end = .;               // Always exists, always at program boundary
```

Using `_end` makes the startup code **linker-agnostic** — it works with any `.ld` file.

## 3. Hardware Stall — Pipeline Debug

When iaddr stays on one address for >10 cycles:

### Check Clock & Reset First

| Signal | Expected | If Wrong |
|---|---|---|
| `clk` | Toggling | Clock gating / PLL issue |
| `rst_n` | High (after release) | Reset not deasserted or glitch |

### Instruction Fetch Stall

Signals to capture in waveform (valid/ready handshake):

```
ibus_arvalid  | 1 = core requesting instruction
ibus_arready  | 1 = memory/bus responding
ibus_rvalid   | 1 = data returned
ibus_rready   | 1 = core accepting
```

| Pattern | Meaning |
|---|---|
| arvalid=1, arready=0 for >10 cycles | **Bus slave not responding** — check memory map, interconnect |
| arvalid=0 | **Fetch unit stalled by backend** — go deeper |
| rvalid=0 for many cycles after arready=1 | **Memory latency** — may be normal on first access (ROM/flash), check timeout |

### Backend Stall Propagation

```
lsu_stall / load_wait    →  most common boot stall cause
fetch_pc_stall           →  frontend stalled because decode/execute is full
store_buffer_full        →  store queue clogged (data bus issue)
```

### LSU (Load/Store Unit) Stall — Most Common

A single `sw` in the BSS loop can stall if:

| Signal | What to check |
|---|---|
| `lsu_stall` | High → data bus not ready |
| `store_buffer_full` | Write buffer full → drain not happening |
| `dtlb_miss` | TLB miss on data access → page table walk |
| Data bus `awready` / `wready` | Slave not accepting writes |

## 4. Finding Registers in Verdi

### Register File (GPR: x0–x31)

Typical hierarchy path:

```
<top>
  └─ u_core_interface
      └─ u_exu                     ← Execution Unit
          └─ u_exu_alu
              └─ u_exu_alu_rgr     ← Register File (rgr = regfile)
```

Search in hierarchy tree: press **`/`** → `*rgr*` or `*regfile*` or `*rf*`

Inside, signals named: `regs[0..31]`, `gpr[0..31]`, or `reg_x0..reg_x31`

### CSR (Control/Status Registers)

```
u_exu
  └─ u_csr  (or csr_regs)
      ├─ mtvec
      ├─ mepc
      ├─ mcause
      └─ mstatus
```

### Fast nWave Search

In waveform viewer, directly search:
```
x10   → a0
x11   → a1
*lsu_stall*
*store_buffer*
```

## 5. Dual-Issue / Multi-Issue Trace

If the trace module has `i0_` and `i1_` signal groups:

| Prefix | Meaning |
|---|---|
| `i0_` | Slot 0 (first instruction) |
| `i1_` | Slot 1 (second instruction) |

**Dual-issue**: `i0_iaddr` and `i1_iaddr` differ by 4 (or 2 for compressed), indicating adjacent instructions fetched in the same cycle.

**To confirm**: check `i0_trace_priv == i1_trace_priv` — always same in dual-issue; may differ in SMT.

## 6. ecall Trap Cascade — mcause=9 → Continuous mcause=2

A distinct boot-time crash pattern: software intentionally calls `ecall` → **mcause=9** (S-mode ecall) → followed by continuous **mcause=2** (illegal instruction).

### Hardware Flow (Automatic, Cannot Skip)

```
ecall @ 0x80000ab2
  → mepc = 0x80000ab2         // save return address
  → mcause = 9                // ecall from S-mode
  → privilege → M-mode        // trap handler runs in M-mode
  → PC = mtvec.BASE           // jump to handler — MANDATORY
  →                           // handler fetches garbage → mcause=2 →
  →                           // mtvec again → same → infinite loop
```

ecall **always** jumps to `mtvec` — there is no mode or bit that makes it fall through.

### Root Cause

`mtvec` (or `stvec` for delegated traps) points to an **address with no valid code**:

| mtvec Value | Problem |
|---|---|
| `0x00000000` | Reset default — no handler installed |
| Points to .bss or uninitialized RAM | Junk fetched → illegal instruction |
| Points to valid address but MODE bits corrupt BASE | Wrong alignment → fetch garbage |

### Timing: ecall Before Interrupt Init

This is the most common trigger. Execution order in Nuclei SDK:

```
Reset vector
  → BSS clear           ← if ecall happens here, mtvec is still 0
  → _init()
      → ECLIC_Interrupt_Init()  ← mtvec set in this function
```

If `ecall` occurs during BSS clearing (or before `ECLIC_Interrupt_Init()`), `mtvec` is the **reset default (0)** → the trap handler address is meaningless → fetch garbage → **continuous mcause=2**.

### MTVEC Mode Bits (Nuclei CLIC Context)

```c
// Nuclei SDK typical setup:
__RV_CSR_WRITE(CSR_MTVEC, (unsigned long)exc_entry | 0x3);
```

`mtvec` format: `BASE[31:2] + MODE[1:0]`

| MODE | Name | Behavior |
|---|---|---|
| `00` | Direct | All traps → BASE directly |
| `01` | Vectored (standard) | Interrupts → BASE+4×cause; exceptions → BASE |
| `11` | CLIC vectored (Nuclei) | Uses `MTVT` for interrupt table; exceptions → BASE |

The `ori a1, a1, 3; csrrw zero, mtvec, a1` pattern sets **both** low bits (binary `11`, decimal 3), correctly configuring CLIC vectored mode for Nuclei cores.

**Key verification**: exceptions always use `mtvec.BASE` regardless of MODE. If `exc_entry = 0x80000a48`, then mtvec.BASE = `0x80000a48`, handler entry at that address.

### Debug Signals to Capture

```
mtvec    → check value + low 2 bits confirm MODE
mepc     → should equal ecall instruction address (confirms origin)
mcause   → sequence: 9 → 2 → 2 → ... (cascade confirmed)
mtval    → 0 for ecall; non-zero for cause=2 (illegal instruction encoding)
```

### Fix Path

```c
// Option A: Ensure mtvec is set before any ecall
void early_trap_init(void) {
    __RV_CSR_WRITE(CSR_MTVEC, (unsigned long)early_trap_handler | 0x3);
}

// Option B: For baremetal, avoid entering S-mode entirely
// (stay in M-mode, don't execute ecall intended for SBI/OpenSBI)

// Option C: Check that exc_entry points to valid code region
// Linker map (.map file) shows final resolved addresses
```

## 7. CSR Analysis for Trap Debugging

### mtval (Machine Trap Value)

Records different data depending on `mcause`:

| mcause | mtval Content |
|---|---|
| 2 (Illegal instruction) | **Instruction encoding** that caused the fault |
| 5 (Load access fault) / 7 (Store access fault) | **Virtual address** that was accessed |
| 1 (Instruction access fault) | **Instruction address** that failed |
| 3 (Breakpoint) | Breakpoint instruction address |
| 9/11 (ecall) | **0** (undefined for ecall) |

If mtval=0 for mcause=2, the instruction encoding itself was 0x00000000 (fetch from uninitialized memory → confirmed bad mtvec target).

### mepc (Machine Exception PC)

- For ecall: mepc = address of the `ecall` instruction itself
- For mcause=2: mepc = address of the illegal instruction
- On `mret`: execution resumes at mepc

## 8. Verdi .fsdb Troubleshooting

### "Please open file first"

Verdi warning when trying to add signals to waveform without loading a database:

```bash
# Correct startup order:
verdi -ssf tb_top.fsdb &          # Option A: load fsdb at startup

# Option B: start empty, then File → Open Database → select .fsdb
verdi &
```

### Empty / Wrong File Type .fsdb

```
1> File(tb_top.fsdb) is an empty file.
2> Wrong file type: tb_top.fsdb
```

Root causes:
- Simulation crashed before waveform dump started (disk quota, segmentation fault)
- Verdi error during dump: `Disk quota exceeded → Give up dump vars`
- `$fsdbDumpvars` not called in testbench

Check:
```bash
ls -lh tb_top.fsdb    # 0 bytes = empty; MB/GB = healthy
```

Fix: clean old waveforms, free disk space, re-run simulation.

## 9. ECC Error Injection & Verification

### 9.1 MECC_CODE Injection Mechanism (RISC-V CSR)

The `MECC_CODE` CSR is an **XOR mask register** — hardware XORs the value written here against the computed ECC on every cache line fill, deliberately creating a mismatch:

```
Memory → hardware computes ECC → XOR with MECC_CODE → compare with stored ECC
                                       ↑
                                write 0x01 here → flips bit 0 of ECC
```

Write pattern → error type:
| MECC_CODE | Effect |
|---|---|
| `0x01` | Flip ECC bit 0 → **single-bit error (correctable)** |
| `0x03` | Flip ECC bits 0+1 → may exceed correction capacity |
| `0x00` | Normal operation, no injection |

### 9.2 Standard Injection Sequence

```c
// Step 1: Enable ECC features
__RV_CSR_SET(CSR_MCACHE_CTL, 0x10d);
// bit 0: IC_EN          → I-Cache on
// bit 2: IC_ECC_EN      → ECC checking on
// bit 3: IC_ECC_EXCP_EN → ECC error → exception
// bit 8: IC_DRAM_ECC_CHK_EN → DRAM ECC check

// Step 2: Set injection mask
ecc_code_xor = 0x01;
__RV_CSR_WRITE(CSR_MECC_CODE, ecc_code_xor);

// Step 3: Invalidate I-Cache (force refetch)
MinvalICache();

// Step 4: Enable injection mode bit
__RV_CSR_SET(CSR_MCACHE_CTL, 0x10);   // bit 4: injection enable

// Step 5: Trigger instruction fetch → ECC error hits
cache_func();   // any function call causes I-fetch

// Step 6: Read ECC status
result = __RV_CSR_READ(CSR_MECC_CODE);
if (result & (1 << 24)) {
    // bit[24] = 1 → single-bit error detected
}
```

### 9.3 Common Pitfalls

| Pitfall | Symptom | Root Cause | Fix |
|---|---|---|---|
| **`csrc` cleared error before read** | `MECC_CODE.bit[24]` = 0 despite successful injection | `csrc mcache_ctl` after `jalr` clears error latch | Read `MECC_CODE` **before** `csrc`, or remove `csrc` | 
| **Privilege mode mismatch** ⚠️ | CSR writes appear to do nothing; MECC_CODE stays 0 | CSR_MCACHE_CTL / CSR_MECC_CODE are **M-mode only**; running in S-mode or U-mode causes silent write failure | Check `cpu_mode` register (0x3=M, 0x1=S, 0x0=U); use `ecall` to delegate injection to M-mode trap handler, or run entire test before switching to S-mode |

**How to check cpu_mode in debugger / waveform:**
```c
// Read mstatus.MPP bits (12:11) — works from any mode
uint64_t mpp = (_RV_CSR_READ(CSR_MSTATUS) >> 11) & 0x3;
// mpp=3 → M-mode, mpp=1 → S-mode, mpp=0 → U-mode

// Or search for *cpu_mode* signal in Verdi hierarchy
```

| Pitfall | Symptom | Root Cause | Fix |
|---|---|---|---|
| **Cache pre-fill — trampoline already resident** | ECC error never triggers; cache_func hits cache (HIT) not miss | `cache_func` address was fetched by a previous test (same trampoline) or by instruction prefetch before MECC_CODE was written | Strategies: (a) Use a **different trampoline address** each test run (round-robin 3–4 trampolines); (b) **Page-separate**: place inject code and cache_func on different 4KB pages (prefetchers rarely cross pages); (c) **Cold jump**: after MinvalICache, jump to a far address (e.g. ROM ret) then to cache_func — guarantees cold miss; (d) **`aligned(64)`**: align cache_func to 64B (cache line size) so exactly one line fetch is needed | 
| **MinvalICache incomplete** | Tag still valid, line not refetched | Invalidation didn't cover all ways/sets | Check `MInvalICache()` implementation — it writes `CCM_IC_INVAL_ALL` to `CSR_CCM_MCOMMAND`, **only clears valid bits** (tag+data preserved). Some implementations may miss prefetch buffers | 
| **Exception handler swallowed error** | Test code after `cache_func` not reached | `IC_ECC_EXCP_EN` on → ECC exception fires → handler consumes event | Check `mcause` in waveform or disable exception (bit 3 = 0) for polling mode |
| **Wrong cache targeted** | ECC not detected | MECC_CODE configured for D-Cache or L2, but test exercises only I-Cache | Confirm `CSR_MCACHE_CTL` targets the correct cache |

### 9.4 Waveform Debug Signals

In Verdi / nWave, capture:

```verilog
// Cache miss/hit
*icache_miss* / *icache_hit*

// ECC detection signals
*ecc_err* / *ecc_single* / *ecc_double*
*single_bit_error* / *double_bit_error*

// ECC error address
*ecc_addr* / *ecc_fail_addr*

// MECC register access (CSR bus)
*mcache_ctl*  // watch for bit[4] toggle
*mecc_code*   // watch for the XOR value written
```

### 9.5 Verifying Injection Succeeded

```bash
# Option A: Check MECC_CODE after test (before any csrc!)
readelf doesn't help — use bare-metal printf or VCD signal dump.

# Option B: In waveform, confirm sequence:
#   mcahce_ctl = 0x10d
#   mecc_code = 0x01 (write)
#   icache_miss = 1
#   ecc_single = 1 (pulse)
#   mecc_code bit[24] = 1 (read-back)

# Option C: If test prints bit[24] status, expected output:
#   "The icache have single-bit eccrr, mecc_code bit 24 is 1."
#   Unexpected: "ERROR:The icache have no single-bit eccrr, ..."
```

### 9.6 Single vs Double Bit Error

| Error Type | MECC_CODE value | Expected MECC_CODE.bit[X] | Exception |
|---|---|---|---|
| Single-bit (correctable) | `0x01` | bit[24]=1 | Configurable via IC_ECC_EXCP_EN |
| Double-bit (uncorrectable) | `0x03` or more bits | Different bit pattern | Usually always triggers exception |

The exact bit position reporting (e.g. bit[24]) is **implementation-defined** per chip — check the core's CSR specification.

### 9.7 Automating Output Capture (Makefile getpng Workflow)

After running an ECC test, capture the output waveform image for documentation:

```makefile
# In project Makefile — see makefile-dynamic-targets.md for details
$ make getpng cpufeat_ecc_xor_tram_icache
```

This searches the cases directory, copies a reference PNG, and later the RST doc generator script can auto-include it under a "Reference Output" section.

## Related Reference Files

| File | Content |
|---|---|
| `n300-bss-loop-case-study.md` | N300 BSS loop freeze case study |
| `trap-cascade-n900-case-study.md` | N900 ecall trap cascade case study |
| `hws-dwarf-compatibility.md` | hws/hwsww tool DWARF 5 → DWARF 4 compatibility fix |
| `makefile-dynamic-targets.md` | Makefile dynamic targets via `$(MAKECMDGOALS)` pattern (used by getpng, run, show targets) |
| `verification-doc-generation.md` | Python script + Sphinx RST doc generation from test case directories |
| `amo-type-portability.md` | AMO intrinsic `long *` portability trap — RV32 vs RV64 type mismatch, fix with `int32_t *`/`int64_t *` |

## 10. PMA (Physical Memory Attributes) Basics

PMA defines per-region memory attributes (cacheable, atomic, executable, etc.). In RISC-V, PMA entries can be either **hardware-fixed** (hardwired per address range) or **software-programmable** (via CSR registers like `PMA_CFG0`, `PMA_CFG1`).

### When Debugging a PMA Issue

```verilog
// Signals to capture:
*pma_cfg*       // Which regions are configured
*pma_match*     // Whether current address hits a PMA entry
*atomic_amo*    // Atomic operation gated by PMA
*icache_en*     // I-Cache enable gated by PMA per region
```

### Common PMA-Caused Boot Stalls

| Symptom | Likely Cause |
|---|---|
| First atomic instruction hangs | Memory region's PMA has A (Atomic) = 0 |
| Code runs but takes 100x longer | C (Cacheable) = 0, every fetch uncached |
| Instruction fetch bus error | I (Instruction) = 0 for that address range |
| Store to MMIO silently dropped | W (Write) = 0 for that range |

### Software PMA (Nuclei CCM)

Typical CSR fields per PMA entry:
```
PMA_CFGx:
  bit 0:  M (Cacheable)
  bit 1:  A (Atomic support)
  bit 2:  I (Instruction fetch ok)
  bit 3:  W (Write ok)
  bits [5:4]: R (Read permissions)
```

## 11. MinvalICache / MInvalICache — What It Actually Does

The `MInvalICache()` function (Nuclei CCM interface):

```c
_STATIC_INLINE void MInvalICache(void) {
    RV_CSR_WRITE(CSR_CCM_MCOMMAND, CCM_IC_INVAL_ALL);  // Send inval command
    FlushPipeCCM();   // Flush pipeline to ensure command executes
    __RWMB();         // Memory barrier for ordering
}
```

- **What it clears**: Only I-Cache **valid bits** (line valid → 0)
- **What it keeps**: Tag and data arrays are **not erased** — ECC values in data RAM persist
- **Why `FlushPipeCCM()`**: Drains any instructions already in the pipeline that were fetched before invalidation
- **Why `__RWMB()`**: Ensures the CCM command is committed before subsequent loads/stores execute
- **Must be called in M-Mode** — CSR_CCM_MCOMMAND is an M-mode-only CSR

## 12. AMO Intrinsic Type Portability (RV32 ↔ RV64)

When writing or porting AMO test code between RV32 (N300) and RV64 (N900):

**Never use `long *` or `unsigned long *` for AMO pointer types.** On RV32 `long` = 32-bit (works by accident), on RV64 `long` = 64-bit (breaks with `-Wincompatible-pointer-types`).

Use `int32_t *` / `uint32_t *` for `_W` functions and `int64_t *` / `uint64_t *` for `_D` functions. See `amo-type-portability.md` for full fix patterns.

## 13. Quick Decision Flowchart

```
iaddr stuck?
  ├─ cycling through 2–4 addresses? → SOFTWARE LOOP
  │   Check a0/a1 in register file
  │   ├─ a1 = 0xFFFFFFFF?  → Linker script _end issue
  │   ├─ a0 wraps around?  → addi overflow
  │   └─ a0 > a1 at start? → Section ordering
  │
  ├─ stuck on 1 address? → HARDWARE STALL
  │   Check clk, rst_n
  │   ├─ clk/rst bad → Clock/reset problem
  │   └─ clk/rst OK → Pipeline stall
  │       ├─ ibus_arready=0? → Bus not responding
  │       ├─ lsu_stall=1? → Data bus/store issue
  │       └─ fetch_pc_stall=1? → Backend full
  │
  └─ ecall then continuous mcause=2 → TRAP CASCADE
      Check mtvec value
      ├─ mtvec = 0? → ecall before interrupt init
      ├─ mtvec low bits != 3? → MODE wrong for CLIC
      └─ mtvec.BASE → invalid address? → Bad exc_entry
```
