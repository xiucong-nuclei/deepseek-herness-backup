# Case Study: N300 BSS Clear Loop Freeze (Nuclei N300)

## Symptoms

During boot, iaddr stuck. Trace shows addresses cycling:

```
0xa0000518 → 0xa000051c → 0xa0000520 → 0xa0000518 → ...
```

Corresponding disassembly:

| Address | Instruction | Meaning |
|---|---|---|
| a0000518 | `sw zero, 0(a0)` | Store 0 to *a0 |
| a000051c | `c.addi a0, 4` | a0 += 4 |
| a0000520 | `bltu a0, a1, ...` | if a0 < a1 loop back |

This is the **BSS clear loop** in `_init_common` startup code.

## Root Cause

**Software infinite loop** — not a hardware stall. The `_end` symbol pointed to an address significantly larger than the actual memory footprint, causing the loop to iterate for astronomically long.

## Debug Steps Taken

1. **Classification**: iaddr cycling (not stuck on one address) → Software loop, not hardware
2. **Code identification**:
   - Address range 0xa0000518–0xa0000520 identified as BSS clear
   - Code pattern: `la a0, _bss_start` → `la a1, _end` → `sw`/`addi`/`bltu`
3. **`_end` investigation**:
   - User searched source code for `_end` — not found in `.c`/`.S`
   - Explained: `_end` is a **GNU LD built-in symbol** defined in the linker script (`.ld`)
   - The startup code uses `_end` (not `_bss_end`) because it's guaranteed to exist
4. **Register file access**:
   - Hierarchy: `n300_exu` → `u_exu_alu` → `u_exu_alu_rgr`
   - `rgr` = Register File containing x0–x31 (a0 = x10, a1 = x11)

## Key Verdi Navigation

```
n300_exu
  └─ u_exu_alu
      ├─ u_exu_alu_bjp          ← branch prediction
      ├─ u_exu_alu_bmu          ← branch mispredict
      ├─ u_exu_alu_csrti        ← control signals
      ├─ u_exu_alu_dpath        ← data path
      ├─ u_exu_alu_dsp          ← DSP
      ├─ u_exu_alu_lsagu        ← load/store address gen
      ├─ u_exu_alu_rgr          ← ⬅️ Register File (a0/a1 here)
      ├─ u_exu_alu_wbck_arbit   ← writeback arbiter
      ├─ u_exu_div
      ├─ u_exu_fpu
      ├─ u_exu_mul_1cyc
      └─ u_exu_nice
```

## Dual-Issue Trace Confirmation

The core trace module shows `i0_` and `i1_` signal groups — confirmed **dual-issue** (2-wide superscalar):
- `i0_iaddr` and `i1_iaddr` differ by 4 (adjacent 32-bit instructions)
- `i0_trace_priv == i1_trace_priv` (same privilege level)
