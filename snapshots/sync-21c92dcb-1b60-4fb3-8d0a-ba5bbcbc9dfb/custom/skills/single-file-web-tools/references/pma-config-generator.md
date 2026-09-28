# Nuclei PMA Config Generator Web Tool

Project: `/home/ubuntu/deliverables/web/pma-calc-landing/index.html` (single-file HTML, Generate + Check modes). Started 2026-08-19 from a landing page ("待上线") per requirements in `~/input/PMA 生成网页工具.md`.

## Purpose
Solve Nuclei PMA config complexity: Generate mode (input regions -> Kconfig config snippet) and Check mode (paste .config -> validate -> produce FIXED file -> download).

## Config file format (Kconfig style, exact)
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
# ... Cacheable Region / Non-Cacheable Region sections identical shape ...
CONFIG_N600_CFG_NC_REGION_NUM=0
CONFIG_N600_CFG_PMA_CSR_NUM=2
# end of PMA
```
- Prefix (N600) user-configurable; values reference Verilog macro as `` `PREFIX_CFG_PA_SIZE'h<hex> ``.
- NUM=0 sections have no BASE/MASK rows.

## PMA semantics (confirmed with user)
- Region match: `(Addr & ~Mask) == (Base & ~Mask)`. Mask=0 -> single-address match (must equal Base).
- Mask = Size - 1, ALWAYS 1s-trailing (低位连续 1, e.g. 0x0FFFFFFF). Never 1s-leading. 1s-trailing chosen for easy 64-bit SoC integration.
- Alignment: Base must be 4K aligned; Size must be power of 2 and >= 4K; Base must be aligned to Size.
- Max 8 regions per attribute type (DEVICE / CACHEABLE / NC).
- PMA_CSR_NUM: user said "先不管" -> generate as total region count, do NOT validate in check mode.
- Check mode needs NO PA Size input (user decision). Mask hex-digit width is inferred from value.

## Fix schemes for unaligned input
- Scheme A (WRAP, default): `sz = hiPow2Ceil(hi-lo)`, `b = lo & ~(sz-1)`, double sz until `b+sz >= hi`. Single block.
- Scheme B (SPLIT): greedy binary decomposition — `p = hiPow2Le(remaining)`, shrink `p` until `cur % p == 0`, emit block, advance. Filter blocks < 4K and beyond PA space.
- Both start from `lo4k = lo & ~0xFFFn`.
- SPLIT with >8 blocks: red warning, do NOT auto-switch (user decision).

## Check mode design (user decisions this session)
- Parse `CONFIG_...` lines with regex; keep non-PMA lines byte-identical in the fixed output.
- Validate: NUM vs actual row count, Base 4K, mask 1s-trailing (`mask & (mask+1) == 0`), size >= 4K, base % size == 0, overlap (same-attr = ERR, cross-attr = WARN).
- Output = FIXED full file: replace bad BASE/MASK values (wrap scheme), fix NUM lines, append missing NUM lines + download button (Blob + a[download], filename input, default "config").
- Hex parsing must accept: `0x` prefix, `` `PREFIX_CFG_PA_SIZE'hXXXX `` (regex tail hex), underscores, case-insensitive.

## UI notes
- Address bar: span = `hiPow2Ceil(maxEnd)` with min 0x10000000; block width min 1.2% so small regions stay visible; linear positioning; per-region WRAP/SPLIT toggle buttons live in the validation info box.
- BigInt for all address math (64-bit PA support); parse/format via hex strings.

## Status (as of session end)
- HTTP server: OK (200) on 127.0.0.1:8640 (background proc).
- Chromium installed + headless CDP alive on 127.0.0.1:9222, BUT browser-harness (browser_exec) connection UNRESOLVED ("chrome-not-running") -> browser-level verification pending; do not claim verified.
- git commit in ~/deliverables pending.
