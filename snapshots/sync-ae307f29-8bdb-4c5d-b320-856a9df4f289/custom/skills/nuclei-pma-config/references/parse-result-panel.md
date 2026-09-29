# PARSE RESULT panel (import page) — spec as of 2026-08-24

Import page has a second panel under the paste box: PARSE RESULT / 解析结果.
Live-parses the textarea (`oninput`), no button needed.

## Display rules (user-confirmed, evolved over 3 rounds)

1. **Show EVERY parsed REGION row pair** (BASE or MASK line present = a row).
   Never silently trim. Filler rows get an `unused` line instead of vanishing.
2. Three states, three styles:
   - `[OK]` green — valid block: `DEV 区域0: 0x4000_0000 - 0x4200_0000, size
     0x2000000 (32 MB)` (+ `MASK converted...` note when low mask rewritten).
   - `[ERR]` red — with the base address shown: `DEV 区域1 (0x4200_1000):
     BASE not aligned to size.`
   - `[UNUSED]` grey dashed — filler: zero base, or all-ones mask, or no BASE
     line with an absent/all-ones mask: `DEV 区域7 (0x0): unused filler`.
3. Counts line: `Correct: {n} (CA {a} / DEV {b} / NC {c}) | Incorrect: {m} |
   Unused: {k}` (i18n: impResStat, 6 args).
4. **REGION_NUM consistency check** per attribute (used = non-filler rows):
   - used > NUM  -> red `[ERR] Parsed 8 DEV region(s) but REGION_NUM=7.`
   - used < NUM  -> yellow `[WARN] Only 1 NC region(s) parsed but REGION_NUM=2.`
5. **Missing vs invalid distinguished** in checkRegion (i18n keys):
   - `errBaseMissing` 缺少 BASE 行 / `errBaseBad` 基地址十六进制值无效
   - `errMaskMissing` 缺少 MASK 行 / `errMaskBad` MASK 十六进制值无效
   - `errMaskNeither` mask 既不是 1 后置也不是 1 前置 (non-contiguous ones)

## Filler classification (must match what import actually trims)

```
isFiller(r):
  b = parseHex(r.base), m = parseHex(r.mask)
  if b === 0n            -> true            # zero base = unused slot
  if b === null          -> m === null || allMask(m)
  return m !== null && allMask(m)           # all-ones mask = disabled
```
allMask uses bits = max(paSize, value bit length), same formula as the
mask-bitwidth fix (see references/mask-bitwidth-and-test-suite.md).

## Real-file expectations (regression anchors)

- PA=34 sample (DEVICE_NUM 7 with REGION7 filler, CACHEABLE_NUM 0 with 8 zero
  bases, NC_NUM 2 with 6 fillers): Correct 9 (DEV 7 / NC 2), Incorrect 0,
  Unused 15, 24 lines total.
- Real 48-bit N600 file: 15 rows all OK.

## Notes

- OK rows use `fmtAddr(lo) + " - " + fmtAddr(hi) + ", " + sizeTxt(...)` — do
  NOT use rangeTxt template (it carries a `0x` prefix that doubles with
  fmtAddr's own `0x` -> "0x0x0_4000_0000").
- textarea rows=25 was user-adjusted manually — preserve user-touched
  attributes; only add the `oninput` binding.
