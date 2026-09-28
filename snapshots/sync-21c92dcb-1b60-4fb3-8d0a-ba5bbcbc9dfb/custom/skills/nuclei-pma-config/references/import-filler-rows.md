# Import filler-row trimming (Aug 24 2026, browser-verified)

Real N600 config files pad unused PMA regions with filler rows. Importing
them naively produces garbage regions. Fix verified in real browser with the
user's full 48-bit N600 config; commit `743919c`.

## Filler-row semantics (from the real file)

- `define <PFX>_CFG_<ATTR>_REGION_NUM n` (or `CONFIG_..._REGION_NUM=n`)
  declares the effective region count for that attribute: rows 0..n-1 are
  real, rows >= n are filler and MUST be ignored.
- Filler rows look like: `REGIONn_BASE = ...'h00000000` (base 0) and/or
  `REGIONn_MASK = ...'hffffffff` (all-ones mask). The file may define
  REGION4..7 BASE/MASK even when NUM=4.
- **all-ones mask = disabled/unconfigured sentinel.** Sized naively,
  `mask+1` = 2^32 → a bogus 4 GB block at 0x0. This was the "导入不正确"
  bug: 15 real regions + 9 garbage ones (4 GB blocks + empty base-0 rows).
- `mask === all` must be judged at the effective bit width:
  `bits = max(maskBitsFromRaw(raw), paSize)`, `all = 2^bits - 1`.
  A 48-bit `'hFFFFFFFFFFFF` is all-ones; a 32-bit `'hFFFFFFFF` at PA_SIZE 48
  is NOT (it is a legit 4 GB region if base != 0).

## Trim rules (loadRegionsFromConfig, shared by both input formats)

1. `num = parsed.numLines[attr].value`; if `num !== null && idx >= num` → skip.
2. `mask === all` (at bits width) → skip (disabled).
3. `base === null || base === 0n` → skip (filler).

Order matters: check num first, then mask===all, then base===0 — a filler row
hits all three; a legit base!=0 low-32-bit-mask row survives rules 2-3.

## PA SIZE first (user requirement)

Extract PA SIZE before resolving BASE/MASK: regexes
`^`define\s+([A-Za-z0-9_]+)_CFG_PA_SIZE\s+(\d+)` (define style) and
`^CONFIG_([A-Za-z0-9_]+)_CFG_PA_SIZE=(\d+)` (config style). Write it into the
pasize input, then resolve masks with `bits = max(maskBitsFromRaw, paSize)`.
Low masks auto-convert to high on import.

## Both formats share the parser

- define style: `` `define N600_CFG_NC_REGION0_BASE `N600_CFG_PA_SIZE'h44000000 ``
- config style: `CONFIG_N600_CFG_NC_REGION0_BASE="`N600_CFG_PA_SIZE'h44000000"`
- Values parse via trailing-hex regex (`/[0-9a-fA-F_]+$/` after stripping
  quotes); underscores stripped. `parseHex` handles both.

## Real-file verification recipe

1. `write_file` the user's config to `/tmp/pma_real_cfg.txt`.
2. browser_exec: `open()` the file, `json.dumps` the text into the textarea,
   call `loadRegionsFromConfig`, then assert:
   - pasize input = 48
   - row groups: NC 4 (0x44000000/0x46000000/0xf0000000/0xf8000000),
     DEVICE 6 (0x10000000/0x11000000/0x30000000/0x38000000/0x40000000/
     0x42000000), CACHEABLE 5 (0x16000000/0x48000000/0x80000000/0xa0000000/
     0xc0000000) — sizes: 32M/32M/128M/128M (NC), 16M×2/128M×2/32M×2 (DEV),
     16M/64M/512M/512M/512M (CA); all `[OK]`.
   - no 0x0 rows, no 4 GB blocks; generated code groups REGION_NUM per attr
     and emits 12-hex-digit 48-bit values with high masks.

## File quirks not to mistake for PMA rows

- `` `define CFG_CORE_PFX n900_ `` — core-prefix macro; unrelated to the
  `N600_` prefix extracted from PA_SIZE/NUM macro names.
- `` `define N600_CFG_ILM_BASE_ADDR `N600_CFG_PA_SIZE'h8000_0000 `` — not a
  REGION row (regex requires `_REGION(\d+)_(BASE|MASK)`), ignored.
- `` `let N600_IDCODE_TMP1 = "00280d2f" `` — `let not `define, ignored.
