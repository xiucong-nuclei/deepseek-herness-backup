# PMA tool — mask bit-width fix + high-coverage test suite (Aug 24 2026)

## Mask bit-width inference (CRITICAL — bug found this session)

`maskBitsFromRaw()` derived bit width from the RAW HEX STRING length
(`len * 4`, min 32). That is WRONG for PA sizes that are not multiples of 4:
a 34-bit high mask like `3fe000000` is 9 hex chars (=36 "bits" by string
length) but the VALUE only needs 34 bits (`0x3FE000000 < 2^34`). With the
wrong 36-bit `all`, `size = (all ^ mask) + 1` became a non-power-of-2 →
false [ERR] on import, and every downstream WRAP/SPLIT fix was garbage.

Correct rule (both `checkRegion(row, paSize)` and `loadRegionsFromConfig`):

```js
const bits = Math.max(paSize || 32, mask > 0n ? mask.toString(2).length : 1);
```

i.e. value bit length (`BigInt.toString(2).length`), NOT hex-string length.
This also makes low→high mask conversion correct: 32MB at PA=34 converts to
high mask `0x3FE000000` (34-bit all ^ (size-1)) — exactly the form the user's
real PA=34 file already uses. `checkRegion` now takes `paSize` (call sites
pass `getPaSize()`).

Real-file regression: PA_SIZE=34, DEVICE_REGION1_MASK=`3fe000000` (32MB),
REGION2_MASK=`3fc000000` (64MB) must import as [OK]. High masks at 48-bit
(`fffff8000000` → 128MB) unchanged.

## Test suite pattern (reusable for single-file web tools)

Location: `~/deliverables/web/pma-calc-landing/tests/pma_test_suite.js`
(served by the same http.server, same origin). 156 assertions, all green.

Architecture:
- Self-contained IIFE: tiny assert framework (`ok/eq/eqn` + `T(name, fn)`
  try/catch) collecting `{name, pass, detail}`; grouped suites
  `suite.unit/parse/analyze/render/import/edge`; runner
  `PMATest.run(batchName|0)` returns `{total, pass, fail, fails[]}`.
- Inject into the loaded page from browser_exec:
  `fetch('/tests/pma_test_suite.js') → text → (0,eval)(src) → PMATest.run(0)`.
  The page's globals (parseHex, analyzeRegion, regions, renderGen, …) are
  directly callable — no module exports needed.
- Coverage: pure functions (parseHex/parseSize/fmtSize/fmtAddr/wrapRange/
  splitRange), parseConfig (Kconfig `=` AND verilog `` `define `` formats),
  checkRegion across PA 32/34/48 + low/high/all-ones masks, analyzeRegion
  error matrix (align/pow2/small/4k/overflow/endlt/base/size), UI render
  (group headers, MODE auto-convert, address-bar priority split, pop
  animation, generated code regexes, lang toggle, CSV via Blob patch),
  import integration (real 48-bit & 34-bit files, filler trimming, garbage
  input), edge cases (PA 31/49 invalid, 33pt block height when scrolling,
  empty regions, 4K END boundary, 48-bit max address).

## Test-authoring pitfalls (all hit this session — avoid)

1. Query selector traps: `input:last-of-type` inside a row matches BOTH
   inputs (each is last in its own td) → selector returned BASE not the
   END/SIZE value. Use `row.querySelectorAll('input[type=text]')[1]`.
2. `parseSize("4096")` is hex 0x4096, NOT decimal 4096 — write `"0x1000"`.
3. `parseSize("abc")` = 0xABC (bare hex by design); `"3.3 GB"` = 0xB (trailing
   "B" is a hex digit). Only empty/null are null. Document, don't "fix".
4. END semantics: `end = base + 4095` is a VALID inclusive END (okB path,
   size 4096) — not an error.
5. Addresses above the PA space (e.g. 52-bit base at PA=48) are correctly
   filtered as overflow — use in-range values (`0xFFFFFFFFFFF000` for 48-bit).
6. exportCsv() downloads (Blob + a.click), returns undefined — capture via
   Blob monkey-patch, or check the CSV string before download.
7. addRegion() at 8/attr does NOT block — it ROTATES to the next free attr
   (DEVICE→NC→CACHEABLE). The 9th row is NC, not rejected.
8. Always `window.alert = () => {}; window.confirm = () => true;` first —
   any APPLY/attrLimit path blocks the harness (Runtime.evaluate timeout).
9. Batch runs must reset global state (regions, activeIdx, pasize, lang)
   between cases — tests run in one page session.

## Run recipe

```bash
cd ~/deliverables/web/pma-calc-landing && python3 -m http.server 8640 --bind 127.0.0.1
# browser_exec: BU_CDP_URL=http://127.0.0.1:9222, goto http://127.0.0.1:8640/index.html?v=N
# then fetch+eval tests/pma_test_suite.js, PMATest.run(0) → expect 156/156
```
