# High-coverage in-browser test suite pattern

Reusable pattern for pushing a single-file web tool (vanilla JS, zero deps) to
high test coverage with no test framework. Proven on the PMA config tool:
156 cases, 6 groups, all green in headless Chromium.

## Shape

One standalone JS file served by the same http.server, loaded into the page
after the app script so every global (parseHex, renderGen, regions, ...) is
directly callable. It defines its own tiny assertion framework and returns a
result object; the driver prints it.

```js
/* tests/suite.js — load after index.html */
(function () {
  const results = [];
  function ok(name, cond, detail) { results.push({ name, pass: !!cond, detail: detail || "" }); }
  function eq(name, a, e) { const A = String(a), E = String(e); ok(name, A === E, "expected=" + E + " actual=" + A); }
  function eqn(name, a, e) { eq(name, a.toString(), e.toString()); }   // BigInt-safe
  const T = (name, fn) => { try { fn(); } catch (err) { ok(name, false, "THREW: " + err.message); } };
  const suite = { /* unit, parse, analyze, render, import, edge batches */ };
  window.PMATest = { run(batch) { /* batch ? [batch] : all keys; collect fails; return {total,pass,fail,fails} */ } };
})();
```

Driver (browser_exec):

```python
out = js("""(async () => {
  window.alert = () => {}; window.confirm = () => true;          # mock FIRST
  const r = await fetch('/tests/suite.js?ts=' + Date.now());      # ts REQUIRED, see cache trap
  const src = await r.text();
  (0, eval)(src);                                                 # indirect eval = global scope
  return PMATest.run(0);
})()""")
```

Run all: `PMATest.run(0)`; one group: `PMATest.run('unit')`. Keep pure
function tests (parse/analyze/wrap/split) separate from DOM tests so a broken
DOM never blocks logic coverage.

## Capturing downloads (Blob trap)

`exportCsv()`-style functions build a Blob and `a.click()` — they return
nothing. Capture the payload:

```js
let captured = "";
const OrigBlob = window.Blob;
window.Blob = function (parts, opts) { captured = parts.join(""); return new OrigBlob(parts, opts); };
window.Blob.prototype = OrigBlob.prototype;
exportCsv();
window.Blob = OrigBlob;
```

## Test-assertion traps (all hit in practice)

- **`:last-of-type` in a table row matches the first input too** — every `<td>`
  with one input satisfies `input:last-of-type`; `querySelector` returns the
  first (often the BASE column). Use
  `tr.querySelectorAll("input[type=text]")[1]` to target the value column.
- **First `.rblock` may be the default block, not your config block.** Blocks
  are stacked by descending hi address; the top-most is the default remainder
  segment. `find(b => !b.classList.contains('default'))` before asserting.
- **Bare hex semantics:** `parseSize("abc")` === 0xABC and the trailing "B" of
  `"3.3 GB"` parses as hex 0xB — by design of the tail-hex extractor. Assert
  the documented behavior, don't "fix" it.
- **PA-space boundary math:** for paSize=N, a size-S region at base B is valid
  iff B + S <= 2^N - 1. For N=48 the largest valid 4K page is
  B = 0xFFFFFFFFE000 (NOT 0xFFFFFFFFF000 → that overflows at 2^48, and NOT
  0xFFFFFFFFFFE000 → that is 14 hex digits / 56 bits, over the space). Count
  hex digits before writing max-address fixtures.
- **Inclusive END semantics:** END = base + size − 1 is a legal inclusive
  range (yields size) and must be accepted with a warn, not rejected.
- **8-block attribute limit rotates to the next attribute** (DEVICE→NC→
  CACHEABLE) rather than blocking the add — assert the rotation.
- **BigInt comparisons:** assert via `.toString()` (eqn), never `==` between
  BigInt and Number.

## Regression-verification loop

1. Patch the app.
2. Reload with `?v=N` AND fetch the suite with `?ts=Date.now()` — both caches
   bite; a fetch without ts silently serves the OLD suite and makes you
   "fix" a test that was already fixed.
3. Full run must stay green; if a new failure appears, decide: app bug or
   stale assertion (the traps above are the usual suspects).

## Domain note: Verilog/Kconfig mask width (PMA-style parsers)

`maskBitsFromRaw(hexString)` using string length × 4 OVERESTIMATES bit width
when paSize < 36: `3fe000000` is 9 hex chars (=36) but its value needs only
34 bits (it is the high-mask form of a 32 MB block in a 34-bit PA space).
Wrong bits → wrong `all = 2^bits - 1` → wrong size → false parse errors.
Correct: `bits = Math.max(paSize || 32, mask > 0n ? mask.toString(2).length : 1)`
(value bit length, not string length). The same bug bites anywhere a
hex-literal width is inferred from digit count instead of the value.
