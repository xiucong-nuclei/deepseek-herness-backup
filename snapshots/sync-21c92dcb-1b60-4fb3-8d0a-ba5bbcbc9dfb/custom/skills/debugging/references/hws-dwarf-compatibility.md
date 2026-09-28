# hws/hwsww Simulation Tool — DWARF Compatibility

## Symptom

`hws_debug_convert` or `hwsww_debug_convert` crashes during ELF processing:

```
In next(): Unhandled FORM 'DW_FORM_line_strp'
DwarfDebugInfoAttribute::next(): Assertion '0' failed.
Aborted (core dumped)
hws convert failed, please check the error information
```

## Root Cause

The tool's DWARF parser is too old to handle **DWARF 5** output. `DW_FORM_line_strp` is a DWARF 5-specific form for source line number strings, introduced in GCC 12+ / newer RISC-V toolchains.

## Diagnosis

```bash
# Check ELF's DWARF version
readelf -h <elf_file> | grep DWARF

# Check if DW_FORM_line_strp is present
readelf --debug-dump=info <elf_file> | grep DW_FORM_line_strp

# Check GCC version
riscv64-unknown-elf-gcc --version
```

## Fix Approaches

### Approach A: Compile with DWARF 4 (preferred)

```makefile
CFLAGS += -gdwarf-4 -gstrict-dwarf
```

`-gstrict-dwarf` is **critical** — without it, GCC 12+ emits DWARF 5 constructs even under `-gdwarf-4`.

### Approach B: Strip debug info entirely

When only symbol addresses (not source-level line info) are needed:

```bash
riscv64-unknown-elf-objcopy --strip-debug \
    program.elf \
    program.nodbg.elf

# Then use program.nodbg.elf with hws
hws -e program.nodbg.elf ...
```

Or one-step compile:

```makefile
CFLAGS += -g0    # no debug info at all
```

### Approach C: Strip line info only (keep symbols)

```bash
riscv64-unknown-elf-objcopy \
    --strip-section=.debug_line \
    --strip-section=.debug_line_str \
    program.elf \
    program.noline.elf
```

### Approach D: Upgrade hws/hwsww toolchain

Contact the tools team for a binary that supports DWARF 5.

## Verification

```bash
# Confirm no more DW_FORM_line_strp
readelf --debug-dump=info <new_elf> | grep DW_FORM_line_strp
# Should return nothing

# Re-run hws
hws -e <new_elf> -t tb_top.rvtrace --clock=1ps --fsdb=tb_top.fsdb
# Should complete without assertion failure
```

## Related Warnings

```
*NOVAS WARN* The FSDB file already exists.
Overwriting the FSDB file may crash the programs that are using this file.
```

This is a **non-fatal warning** — just means a previous run's waveform exists. Ignore or `rm -f tb_top.fsdb` before re-running.
