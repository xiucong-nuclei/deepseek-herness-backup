---
name: nuclei-pma-config
description: PMA config gen/check for Nuclei CPUs (Kconfig + web tool).
metadata:
  hermes:
    tags:
    - Nuclei
    - PMA
    - RISC-V
    - Kconfig
    - WebTool
    category: software-development
    related_skills:
    - riscv-cpu-boot-debug
    version: 1.0.0
    author: Hermes Agent + kiucong
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Nuclei PMA Configuration

PMA (Physical Memory Attribute) regions define address-space attributes
(Device / Cacheable / Non-Cacheable) for Nuclei CPUs (N300/N600/N900 family).
Settings live in Kconfig-style .config lines. Manual config is error-prone
(alignment, mask format), so the user maintains a web tool for generation +
validation.

## When to Use

- Generate or validate PMA region settings for a Nuclei SoC
- Work on the PMA config web tool (~/deliverables/web/pma-calc-landing/index.html)
- Write databook/spec sections about PMA region semantics

## Core Rules (user-confirmed)

1. Region match: `(Addr & ~Mask) == (Base & ~Mask)`. Mask bit=1 -> don't care.
   Mask=0 -> matches Base only (single address).
2. Mask = ~(Size - 1), policy is **1s-leading**: high bits 1, low bits 0
   (e.g. `'hF0000000`) — this is the output form used consistently by the web
   tool and its help text. Import parsing accepts both forms (1s-leading and
   1s-trailing `mask = Size - 1`); output always converts to 1s-leading.
   Validity check: `all = (1n<<PA) - 1n; mask===0n || maskIsOnesTrailing(all ^ mask)`.
3. Size must be a power of 2 and >= 4K. Base must be 4K-aligned AND aligned to
   size (`base % size === 0`).
4. Max 8 regions per attribute type (DEVICE / CACHEABLE / NC).
5. `PMA_CSR_NUM` = total region count (sample: DEVICE 1 + CACHEABLE 1 + NC 0
   -> 2). User said "don't worry about it": generate by count, never validate.
6. Typical values: default 0x4000_0000 / 0x03FF_FFFF -> 64MB; sample config
   uses DEVICE 0x1000_0000 +0x0FFF_FFFF (256MB) and CACHEABLE 0x2000_0000.

## Kconfig Variable Format

```
#
# PMA
#

#
# Base & Mask must be aligned to 4k
#

#
# Device Region
#
CONFIG_N600_CFG_DEVICE_REGION_NUM=1
CONFIG_N600_CFG_DEVICE_REGION0_BASE="`N600_CFG_PA_SIZE'h10000000"
CONFIG_N600_CFG_DEVICE_REGION0_MASK="`N600_CFG_PA_SIZE'h0FFFFFFF"

#
# Cacheable Region
#
CONFIG_N600_CFG_CACHEABLE_REGION_NUM=1
CONFIG_N600_CFG_CACHEABLE_REGION0_BASE="`N600_CFG_PA_SIZE'h20000000"
CONFIG_N600_CFG_CACHEABLE_REGION0_MASK="`N600_CFG_PA_SIZE'h0FFFFFFF"

#
# Non-Cacheable Region
#
CONFIG_N600_CFG_NC_REGION_NUM=0
CONFIG_N600_CFG_PMA_CSR_NUM=2
# end of PMA
```

- Attributes: DEVICE, CACHEABLE, NC; each has `_REGION_NUM` plus
  `_REGION<n>_BASE` / `_REGION<n>_MASK` rows.
- Values are Verilog-style `` `MACRO'hHEX `` — hex digit count = PA_SIZE/4
  (8 digits for 32-bit, 16 for 64-bit).
- Section comments to reproduce: `# PMA`, `# Base & Mask must be aligned to
  4k`, `# Device Region`, `# Cacheable Region`, `# Non-Cacheable Region`,
  `# end of PMA`.

## Generate Mode (tool spec)

Inputs: PA Size (32/64, validate), Prefix (default N600), and per region:
attribute + Base + End XOR Size (mutually exclusive — filling one locks the
other). Outputs:

1. Config snippet exactly in the Kconfig format above.
2. Address-bar visualization: horizontal rectangle, regions positioned by
   base, width by size, min-width ~1.2% so small regions stay visible.
3. Info box: when alignment fails offer two fix schemes via toggle buttons:
   - **Scheme A WRAP (default shown)**: enclose [lo, hi) in one
     power-of-2-aligned block.
   - **Scheme B SPLIT**: binary-decompose into aligned power-of-2 blocks;
     if blocks > 8 show red warning (do NOT auto-switch — user decision).

## Fix Algorithms (use BigInt — 64-bit PA unsafe for JS Number > 2^53)

```
wrapRange(lo, hi):
  sz = hiPow2Ceil(hi - lo)          # smallest power of 2 >= span
  b  = lo & ~(sz - 1n)
  while (b + sz < hi): sz <<= 1n; b = lo & ~(sz - 1n)
  return {base: b, size: sz}

splitRange(lo, hi):
  cur = lo; parts = []
  while cur < hi:
    p = hiPow2Le(hi - cur)          # largest power of 2 <= remaining
    while (cur % p != 0n): p >>= 1n # shrink until block is aligned
    parts.push({base: cur, size: p}); cur += p
  return parts
```

Start both from `lo4k = lo & ~0xFFFn` (round down to 4K). Drop blocks with
size < 4096 or exceeding the PA address space; report instead.

Hex parsing must accept `0x...`, bare hex, and `` `MACRO'h... `` (regex
`/[0-9a-fA-F_]+$/` on trimmed input), with optional underscores.

## Check Mode (tool spec)

- Input: pasted config text. **No PA Size input** (user decision) — infer per
  value. **No CSR_NUM validation** (user decision).
- Parse with regexes:
  - `^CONFIG_([A-Za-z0-9_]+)_CFG_(DEVICE|CACHEABLE|NC)_REGION_NUM=(\d+)`
  - `^CONFIG_..._REGION(\d+)_(BASE|MASK)=` (group rows by attr+idx)
  - `^CONFIG_..._CFG_PMA_CSR_NUM=(\d+)`
  - Prefix = first CONFIG_ line's group.
- Validate: NUM vs actual row count; base 4K; mask 1s-leading (or convertible
  1s-trailing); size >= 4K;
  base % size == 0; overlap (same-attr = ERR, cross-attr = WARN).
- Output = **fixed file**: original lines preserved verbatim except bad
  BASE/MASK values replaced (Scheme A wrap — single block, row count
  unchanged), NUM lines corrected, missing NUM lines appended. Preview +
  download button (Blob + `a[download]`, revokeObjectURL after).

## Pitfalls

- UI text must be pure ASCII English (user's standing rule: no non-ASCII in
  code; status tags `[OK]` / `[ERR]` / `[FIX]` / `[WARN]`).
- Single-file static HTML, zero deps, dark tech style (#0a0f1e bg, #38bdf8 /
  #818cf8 accents) matching the existing landing page.
- Serving for browser verification: `python3 -m http.server <port>` with
  workdir = project dir — the server serves its CWD, wrong dir -> 404.
- `PMA_CSR_NUM` and check-mode PA Size are deliberately out of scope; do not
  re-litigate with the user.

## Status

Tool v1 at ~/deliverables/web/pma-calc-landing/index.html (replaced the
"PMA计算工具(待上线)" landing stub). Browser verification was interrupted
mid-session; verify both modes in a real browser + git commit before
declaring the tool done. Full session spec: references/web-tool-spec.md.
