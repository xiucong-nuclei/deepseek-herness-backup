---
name: cpu-benchmarking
description: CPU benchmark selection & interpretation (Dhrystone, Whetstone, CoreMark) — version/compiler-flag score inflation, DMIPS/MWIPS conversion, honest reporting.
metadata:
  hermes:
    triggers:
    - dhrystone
    - whetstone
    - coremark
    - DMIPS
    - MWIPS
    - benchmark version
    - DMIPS/MHz
    platforms:
    - linux
    version: 1.0.0
    category: software-development
---

# CPU Benchmarking

Benchmark selection and result interpretation for Nuclei RISC-V core validation
(N300/N900) and embedded CPU benchmarking generally.

## First rule: report version + compiler flags

DMIPS/MWIPS numbers are meaningless without the benchmark VERSION and the
compiler flags. Two runs of the same benchmark differ 10-30% purely from
`-O2` vs `-O3`, `-fno-inline`, and the libc string functions used (Dhrystone
is strcmp/strcpy-heavy, so linking newlib vs hand-written string functions
moves the score by double-digit percent).

## Version inflation (compiler dead-code elimination)

Modern optimizing compilers eliminate the benchmark body when results are
unused. "Honest" versions add `volatile` / anti-DCE guards and score LOWER;
the classic originals score HIGHER (inflated).

| Benchmark | Inflated (higher) | Honest (lower, realistic) |
|-----------|-------------------|---------------------------|
| Dhrystone | 2.1 (original, no volatile) | 2.2 (volatile + anti-DCE) |
| Whetstone | Netlib 1.2 (classic C) | Roy Longbottom (volatile) |

- Dhrystone 2.2 `dry.c` header states it prevents optimizers "removing
  significant statements" (co-developed with Rick Richardson).
- Roy Longbottom's Whetstone docs have a dedicated "Compiler Optimisation"
  section for the same reason.

## Conversions

- 1 DMIPS = 1757 Dhrystones/sec (VAX 11/780 reference machine).
- Whetstone uses MWIPS (millions of weighted instructions/sec); Longbottom's
  version also reports per-loop MFLOPS (loops N1-N8).

## Selection guidance

- Internal regression / honest comparison → use the honest version
  (Dhrystone 2.2 / Longbottom Whetstone).
- Aligning with vendor/historical published numbers → use whatever version they
  quoted (usually 2.1 / Netlib 1.2) and state it in the report header.
