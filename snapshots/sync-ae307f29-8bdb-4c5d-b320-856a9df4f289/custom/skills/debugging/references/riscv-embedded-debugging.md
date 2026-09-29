# RISC-V Embedded Debugging Patterns

## Zcmt (Jump Table) Debugging — Nuclei / RISC-V

### Common Crash Pattern

The test code writes to `JVT` CSR (`__RV_CSR_WRITE(CSR_JVT, jptbl)`) and then hangs or crashes when `cm.jt` or `cm.jalt` instructions execute.

### Root Cause Possibilities

#### 1. Compiler-Generated Zcmt Instructions Conflicting with User JVT

The compiler may auto-generate `cm.jt`/`cm.jalt` for function calls (e.g., `printf` → `cm.jalt 33`). When the test code overwrites JVT with its own table, the compiler's jump table becomes invalid, so the next compiler-generated `cm.jalt` reads address 0 from the new table and jumps to zero.

**Diagnostic:**
```bash
# Check if compiler uses Zcmt
riscv*-elf-objdump -d test.elf | grep -E "cm\.jt|cm\.jalt"
```

**Fix A — Disable compiler Zcmt generation (+ risk of flag not recognized):**
```makefile
CFLAGS += -mno-zcmt
```
If toolchain doesn't recognize `-mno-zcmt` (e.g., `riscv64-unknown-elf-gcc` vs `riscv-nuclei-elf-gcc`), strip `_zcmt` from the `-march` string instead:

```makefile
override ARCH_EXT := $(subst _zcmt,,$(ARCH_EXT))
```

**Fix B — Remove zcmt from march explicitly:**
```makefile
# Change
-march=rv64gc_zca_zcb_zcmp_zcmt
# To
-march=rv64gc_zca_zcb_zcmp
```

#### 2. JVT Points to Data Memory (DLM) Instead of Instruction Memory (ILM)

`cm.jt` reads the jump table entry via the **instruction fetch path (IFU)**, NOT the data load path (LSU). On many Nuclei cores, the IFU can only access ILM/ITCM (`0x80000000+`), not DLM/DTCM (`0x90000000+`).

**Symptom:** JVT set to a DLM address (e.g., `0x90000640`), table contents appear correct in data memory dump, but `cm.jt` reads garbage (Table → DLM → wrong raw bits read by IFU → invalid address → crash).

**Diagnostic:**
```bash
# Find where jptbl is linked
riscv*-elf-objdump -t test.elf | grep jptbl
# Expected: 0x80000xxx (ILM)  ← correct
# Found:    0x90000xxx (DLM)  ← problem
```

**Fix — Place jump table in .text section:**
```c
// Forces jptbl into instruction memory
unsigned long jptbl[256] __attribute__((section(".text"))) = {0};
```

#### 3. Zcmt Shares the Zcd (`C.FSDSP`) Encoding Slot — and How to Read a Table-Jump Trap

`cm.jt`/`cm.jalt` occupy the 16-bit `C.FSDSP` slot (quadrant 2, funct3=101, bits[12:10]=000,
index in bits[9:2]). The Zcmt chapter opens with "The Zcmt extension conflicts with the Zcd
extension" and notes it is "not compatible with RVA profiles". A core that also has D must pick
one interpretation; Nuclei exposes that choice as `mmisc_ctl[7] ZCMT_ZCMP_EN`
(Nuclei_RISC-V_ISA_Spec.pdf §8.5.10): 0 = Zcd encoding (`0xa082` = `c.fsdsp f0, 8(sp)`),
1 = ZCMP/ZCMT encoding (`0xa082` = `cm.jalt 32`). With Zc and no D the bit is read-only 1; with
Zc and D it resets to 0, and software must write 1 (after turning the FPU off) to get ZCMP/ZCMT.

Consequence: one binary means two things. In Zcd mode with `mstatus.FS=0` the slot traps as
illegal instruction at the call site; in Zcd mode with the FPU on it silently stores the FP
register to the stack slot instead of calling.

Index layout: 0-31 = `cm.jt`, 32-255 = `cm.jalt`, so the first *call* slot is index 32.
`table_address = jvt.base + (index<<2 | index<<3)` (RV32 | RV64); base must be 64-byte aligned;
the entry read is itself an instruction fetch (execute permission required, read is irrelevant).

Read a table-jump trap by the cause/mtval pair **at the table jump's own PC** — per zcmt.adoc
"the table entry ... is considered an extension of the instruction itself", and a fault on
either fetch sets xEPC to the table jump's PC:

| mtval | Meaning |
|---|---|
| the encoding (e.g. `0xa082`) | the core rejected the instruction: ZCMT encoding not selected (Zcd mode + FS=0), or `jvt.mode != 0` — any mode but 000000 makes cm.jt/cm.jalt reserved -> illegal instruction |
| a table address | the entry fetch failed: JVT and table are not a matched pair (table outside fetchable memory, JVT never initialized, JVT overwritten by a test's own table, entry-size or alignment mismatch) |

Fix: make image and hardware agree — set `mmisc_ctl[7]=1` before running Zcmt code, or rebuild
without `_zcmt`; and keep JVT pointing at the linker's table. To observe JVT without using a
table jump, store it to memory from asm — the `printf` that prints JVT is itself a `cm.jalt`.

Vendor reference: `nuclei-sdk/application/cpu_features/zc/cpufeat_zc_jumptable`
(Nuclei_CPU_Case_Description.pdf §9.20.1; reference output starts `Jump table located in 0xa8000600`).

#### 4. Toolchain Differences

| Toolchain | Notes |
|---|---|
| `riscv-nuclei-elf-gcc` | Nuclei's own GCC — may support different -m flags |
| `riscv64-unknown-elf-gcc` | Standard RISC-V GCC — usually newer, may lack Nuclei-specific flags |

Always check flag support first:
```bash
riscv*-elf-gcc --help=target | grep zcmt
```

### Post-Test Segfault (Not a Test Failure)

Simulation passes (`TEST_PASS`) but then crashes with:
```
*Verdi* ERROR: Disk quota exceeded
Segmentation fault during cbEndOfSimulation VPI callback
```

This is **not a test bug** — it's a Verdi/VCS waveform dump failure due to:
- Disk quota exceeded on the simulation server
- VCS calls `system()` during end-of-simulation cleanup, which fails when disk is full

**Fix:** Clean disk space or increase quota. The test itself is correct.

### General Workflow for RISC-V Embedded Crash Debugging

1. **Verify the test itself passes** — look for `TEST_PASS` before any tool crash
2. **Check linker placement** — `objdump -t` to see where key variables and functions are
3. **Know your memory map** — ILM/ITCM vs DLM/DTCM address ranges for your core
4. **Check instruction fetch vs data load paths** — some CPU features (JVT, vector table, etc.) read via specific bus paths
5. **Check compiler flags** — `--help=target` for supported flags, `objdump -d` for actual generated instructions
6. **Isolate toolchain crashes from test failures** — Verdi/VCS segfaults after `TEST_PASS` are environment issues, not code bugs
