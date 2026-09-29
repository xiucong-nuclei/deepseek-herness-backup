---
name: single-file-web-tools
description: Develop single-file web page tools (vanilla JS, no deps).
metadata:
  hermes:
    tags:
    - web
    - frontend
    - vanilla-js
    - i18n
    - single-file
    - tooling
    category: software-development
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Single-File Web Page Tools

Build and iterate standalone web tools for this user (e.g. config
generators/calculators): one zero-dependency HTML file, dark or light themed,
often bilingual. Proven on the PMA config generator
(`~/deliverables/web/pma-calc-landing/index.html`).

## User conventions (apply by default)

- **Pure ASCII in scripts/code** (no Chinese/non-ASCII in code; UI text in
  English or via i18n pairs). The user has asked 3x — non-negotiable.
- **Dark tech style** (established convention): `#0a0f1e` background,
  `#38bdf8`/`#818cf8` accents, monospace font, faint grid background — matches the
  existing landing pages under `~/deliverables/web/`.
- **BigInt for any address math ≥ 2^53** (e.g. 64-bit PA sizes). Never use Number
  for hex addresses.
- **Bilingual UI** when requested: `data-i18n` for static text + `t(key,...)`
  for dynamic strings; language toggle in the header, persisted to
  `localStorage`. Attribute/value tokens (DEVICE, CACHEABLE, hex) stay English.
- Deliver under `~/deliverables/web/<name>/` (git repo) and **commit after
  every batch of changes** so each iteration is rollback-able.
- Workflow: restate the request + list <=3 decision points WITH a recommended
  option before writing code; the user answers inline (e.g. "1A 2B 3A") or
  just says 继续 to continue iterating. They send change lists in batches —
  implement each batch, verify, commit.

## Pitfalls that actually bit

- **Input focus loss = table rebuild on every keystroke.** `oninput` calling a
  full re-render (`tbody.innerHTML=""`) destroys the focused `<input>` and the
  user can only type one char. Fix: on input, update the data model and only
  refresh non-input regions (info bar, preview, chart); rebuild the table only
  on structural changes (add/del row, attr/mode switch).
- **i18n textContent overwrite deletes children.** `el.textContent = t(...)`
  on an element containing child nodes (e.g. `<h2>REGIONS <span id=count>`)
  wipes the children → later `getElementById` returns null and crashes. Wrap
  the translatable part in its own nested `<span data-i18n>`, keep dynamic
  children outside it.
- **Duplicate CSS rules: later wins.** A fix "doesn't work" because an older
  copy of the same rule sits later in the stylesheet and overrides it (same
  specificity). Before debugging further, `grep` for the selector — delete the
  stale duplicate.
- **CSS variables for theming.** Put the whole palette in `:root` (bg/panel/
  text/accent/ok/err/warn/border) so a full theme swap (e.g. dark→light) is a
  one-block change; avoid scattering raw hex in rules.
- **Responsive scaling.** Use `vw`/`vh` + `clamp()` for fonts/spacing so the
  layout scales with the display; `grid` + `display: contents` on a wrapper
  lets grandchildren participate directly in the outer grid (handy for
  multi-column + bottom-panel layouts).

## Verification

Real-browser verification is mandatory for web deliverables — see the
`browser-verification-headless` skill (playwright chromium + CDP +
`BU_CDP_URL`) and the full local recipe in
`references/browser-verification-recipe.md` (playwright chromium path, snap-chromium
trap, BU_CDP_URL wiring, verification checklist). Key points: use the playwright
chromium binary (`~/.cache/ms-playwright/...`), NEVER snap chromium (headless never
opens the CDP port); set `os.environ["BU_CDP_URL"] = "http://127.0.0.1:9222"` as the
FIRST line of browser_exec code; capture JS errors from the start (`window.__errs`)
and assert it is empty at the end. Known extra pitfalls from later sessions:
`python3 -m http.server` (single-threaded) can silently hang → curl 000 with
the process alive → kill & restart; and when writing harness scripts, mind
Python-string quoting around embedded JS (build payloads with `json.dumps`).
Always refresh with a cache-busting `?v=N` query after editing the file, and
re-verify after every bug fix (fixes break sibling paths).

## Regression testing (in-browser test suites)

For tools with non-trivial logic (parsers, validators, generators, address/interval
math), ship a self-contained suite as `tests/<tool>_test_suite.js` NEXT TO the page
and run it in the real browser — full pattern in
`references/test-suite-pattern.md` (tiny assertion framework, driver snippet, Blob
capture, assertion traps, regression loop; proven on the PMA config generator).

- **User requirement (enforce it)**: EVERY new feature/change lands with matching
  regression cases appended to the suite, then the FULL suite re-run to ALL GREEN
  before commit. Embed the user's actual config/sample files as string literals
  (generate via `json.dumps` to avoid escaping pain) and assert exact counts/sizes —
  synthetic cases miss regressions the real files catch.
- **Log every run**: `res.logText` → `tests/logs/<tool>_test_log.txt` (header +
  per-case PASS/FAIL grouped by batch + RESULT line); commit one sample log.
- **Pitfalls**: fetch the suite with `?ts=' + Date.now()` (the test file caches
  independently of the page's `?v=` buster); mock `alert`/`confirm` at the top of
  every test script (un-mocked `alert()` blocks CDP Runtime.evaluate until timeout);
  on failure suspect the test before the product (wrong selector, wrong expected
  width, out-of-bounds fixture); if `Target.createTarget`/`Runtime.evaluate` times
  out, the browser daemon is wedged — `pkill -f remote-debugging-port=9222`,
  relaunch chromium, verify `curl http://127.0.0.1:9222/json/version`, retry.

## Session recall

For the PMA tool's feature backlog and past decisions, `session_search`
("PMA") recovers the full iteration history; the domain rules are also in
memory under "Nuclei PMA".
