---
name: in-page-regression-suite
description: Use when building a regression test suite inside a web tool.
metadata:
  hermes:
    tags:
    - testing
    - regression
    - browser
    - web-tool
    - verification
    category: software-development
    version: 1.0.0
    author: Hermes Agent
    license: MIT
---

# In-Page Regression Suite (web tools)

For a single-file / vanilla web tool that must stay correct across many edits,
embed a reusable test suite and run it in the real browser (via browser_exec)
instead of ad-hoc one-off probes. Proven on a PMA config generator (199 cases,
6 batches, all green). Pair with the `browser-verification-headless` skill for
the CDP/browser plumbing.

## When to Use

- Iterating on a single-file web tool (index.html + inline JS) where regressions
  are easy to introduce and a human re-test isn't enough.
- The user wants high coverage + multiple boundary cases covered repeatably.
- You need a fast way to prove a change didn't break a sibling path.

## Structure

1. **Independent test file** served next to the page (e.g. `tests/foo_test_suite.js`).
   No deps, pure ASCII (user requirement on Chinese machines). It defines:
   - a tiny assertion framework: `ok(name,cond,detail)`, `eq`, `eqn`, and
     `T(name, fn)` that catches thrown exceptions into a FAIL;
   - per-batch functions (`suite.unit`, `suite.parse`, `suite.analyze`,
     `suite.render`, `suite.import`, `suite.edge`, ...) registered on a `suite`
     object;
   - a runner `window.PMATest.run(batch?)` returning
     `{total, pass, fail, fails:[{name,detail}], groups, logText}`.
2. **Unit tests call page functions directly** — they live in the page's global
   scope (`parseHex`, `fmtAddr`, `analyzeRegion`, `wrapRange`, ...).
3. **UI/integration tests set up state then assert DOM**: assign the page's
   state array (`regions = [...]`), call its render (`renderGen()`), then
   `querySelector` and compare `textContent`. For framework-less listeners, set
   `.value` then dispatch `new Event('input')` / `('change')` so the handler runs.
4. **Fixture real files**: embed actual user config files as inline strings and
   assert exact per-attribute counts/sizes — synthetic cases miss real regressions.

## Running it (browser_exec)

Cache-bust BOTH the page and the fetched test file — the HTML `?v=N` does NOT
bust a separately-fetched JS file:

```python
out = js("""(async () => {
  const r = await fetch('/tests/foo_test_suite.js?ts=' + Date.now());
  (0, eval)(await r.text());
  return PMATest.run(0);
})()""")
```

Always start integration tests with `window.alert=()=>{}; window.confirm=()=>true;`
or a stray `alert` in a code path blocks the harness (`Runtime.evaluate` hangs).

## Per-case log

Have `run()` also produce `logText`: header (timestamp, total/pass/fail,
batches) + one `  PASS|FAIL <name>` line per case grouped by batch, ending with
`RESULT: ALL PASSED` or `RESULT: N FAILURE(S)`. Write it to a file and commit a
sample so the user can see exactly what ran; offer `downloadLog()` for manual
browser use (Blob + a.click, `.txt`).

## Discipline

- **Every new feature / bug fix gets regression cases before commit** — this is
  an explicit user requirement for this class of work ("每次添加新的测试方案，
  就添加到回归测试环境中"). New batches/cases go into the existing suite file,
  then `PMATest.run(0)` must be all green before you commit.
- **A failing assertion is often a test-data bug, not a product bug.** Verify
  intended semantics first. Observed gotchas:
  - `parseSize("abc")` is a *valid* bare hex value (`0xABC`); `"3.3 GB"` tails as
    hex `B` (parseHex grabs the trailing hex run).
  - `END = base + 4095` is a *valid inclusive* END (yields size 4096).
  - Adding a 9th region of a full attribute *rotates* to the next attribute
    instead of being blocked.
  - A 48-bit max-address test must use a 4K-aligned base inside the space
    (`0xFFFFFFFFE000`), not `0xFFFFFFFFF000` (that +0x1000 overflows).
  Only after confirming it's a real defect should you change the product.
- **Re-run the whole suite after every change**; a fix to one path commonly
  breaks a sibling.
- Extract pure helpers (e.g. a file-extraction function) into named functions so
  they can be unit-tested directly.

## Pitfalls

- After patching a long test/source file, re-read/`search_files` it to confirm the edit
  actually landed on disk before trusting the next browser run (patch tool can
  silently no-op on big files).
- A per-attribute limit can silently reject a SPLIT/apply that generates exactly
  `MAX_PER_ATTR` blocks when that attribute already has ≥1 region — surface this
  in the fix UI rather than a bare alert.
