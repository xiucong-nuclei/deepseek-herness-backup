# Late-2026-08 iteration notes (PMA tool) — deltas after the main references

Companion to `pma-config-import-rules.md` and `test-suite-pattern.md`; captures
the newest session deltas so the main files stay stable.

## Animation duration + Chinese "增加X" semantics
Block pop animation is now `duration: 450` (was 150; user asked "增加0.3s的时间").
Rule: 中文"增加X" = INCREMENT, not "set to" — 150ms + 0.3s = 450ms. Never
silently treat an incremental request as a replacement value.

## SPLIT under the per-attr limit (applyFix)
`attrCount(attr) + blocks.length - 1 > 8` → alert + refuse the APPLY.
Worst-case split = exactly 8 blocks: base 0x59000000 size 0x60000000 (1.5GB)
splits into 16/32/64/512/512/256/128/16 MB (all aligned, full coverage).
It applies when the attr has 0-1 rows (1+7=8), but a 2nd pre-existing row of
the same attr (e.g. the default DEVICE example row) makes it 2+7=9 → refused.
"点了分割没反应" usually = this alert being ignored; check `window.alert`.

## Import page PARSE RESULT panel
Live panel under the import textarea; `oninput="renderImportResult()"`, no button.
- Stat: `Correct: 9 (CA 0 / DEV 7 / NC 2)  |  Incorrect: 0` (per-attr + totals).
- List every kept block in validation-panel style: green `[OK] DEV Region0:
  0x4000_0000 - 0x4200_0000, size 0x2000000 (32 MB)` (+ "MASK converted..."
  note when low mask converts); red `[ERR] ...: <reasons joined by "; ">`.
- Applies the SAME trim rules as import before counting (NUM-exceeding rows,
  base==0, all-ones mask) — what the panel reports is what import will load.
- Trap: do NOT use the `rangeTxt` template there — it embeds `0x` and fmtAddr
  also emits `0x`, producing `0x0x0_4000_0000`. Build with
  `fmtAddr(lo) + " - " + fmtAddr(hi) + ", " + t("sizeTxt", hexStr(size), fmtSize(size))`.
- i18n keys added: impResTitle / impResEmpty / impResStat (en+zh).

## Test suite: per-case log output
`PMATest.run()` now returns `logText` (in addition to total/pass/fail/fails):
header with timestamp + totals, then every case as `  PASS/FAIL  <name>` grouped
under `[group]` headers, footer `RESULT: ALL PASSED` or failure count. Add
`PMATest.downloadLog(res)` to save it as a txt (Blob + a.click) for manual runs.
Results carry `group` so the log can be grouped; store it in `ok()`/`eq()` pushes.
The suite file also embeds BOTH real-world config files (48-bit N600, PA=34) as
inline fixtures — loadRegionsFromConfig + assert per-attr sizes and zero [ERR]/[FIX].

## Browser session dies after days: restart pattern
`Target.createTarget` / `document.readyState` timeouts after the CDP chromium
ran ~4 days → the page is wedged even though `/json/version` answers.
Restart: `pkill -9 -f "remote-debugging-port=9222"`, then relaunch with
terminal(background=true) — NOT `nohup ... &` (Hermes blocks shell-level
background wrappers): `/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome
--headless=new --no-sandbox --disable-gpu --remote-debugging-port=9222
--user-data-dir=/home/ubuntu/.config/chromium about:blank`, then curl
`/json/version` until 200 before testing.

## Patch discipline: trust the disk, not your memory of it
A `patch` whose old_string was based on the last edit FAILED to match reality:
the user had hand-edited the file (textarea rows=13 → 25) in between. Always
`git diff` / read the current bytes first; if the diff shows a surprise
(rows="25"), preserve the user's value and only add your delta. This has
burned the session twice (rows, and a stale test assertion name).
