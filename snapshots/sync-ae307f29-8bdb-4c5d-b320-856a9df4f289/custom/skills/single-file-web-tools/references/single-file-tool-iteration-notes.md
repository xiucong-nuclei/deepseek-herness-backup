# Iterating single-file tools: browser-exec testing notes (pma-calc-landing session)

Proven while iterating the PMA settings web tool on headless Ubuntu.
Complements `browser-verification-headless` (user-owned, not editable here).

## Test-script gotchas (headless browser_exec)
- **Mock dialogs FIRST.** Any flow calling `confirm()`/`alert()` (clear-all,
  apply-fix, import warnings, attr-limit) hangs the headless page; harness dies
  with `Runtime.evaluate timed out` and no useful trace. After capturing errors:
  `js("window.confirm=()=>true; window.alert=()=>true;")`.
- **Re-render invalidates DOM references.** Simulated edits that trigger a
  re-render (changing an attr select rebuilds the row table) detach previously
  fetched select/input handles — later `.value=` writes silently no-op, and the
  app data ends up scrambled (rows reordered, wrong attrs). Re-query the table
  after every edit, or bypass the DOM: drive the app's globals directly
  (`regions.push(newRegion(...)); renderGen();`) when exposed — deterministic.
- **Python-side:** plain dicts reject attribute assignment (`out.k=v` raises
  AttributeError; use `out["k"]=v`). `\n` in a Python string is consumed before
  the JS regex/string sees it — build such strings with `json.dumps`.
- Verify geometry with float precision; integer rounding can fake "overlap".

## i18n-dictionary rendering vs hand-edited static HTML
Page re-renders help panels from an i18n dict on every load
(`renderHelp()` → `panel.innerHTML = t("help" + n + "Body")`), so user edits
made directly in the static HTML are overwritten at runtime. Workflow when the
user says "我修改了 help,同步下":
1. `git diff` the file first — see exactly what changed.
2. Copy their text VERBATIM into the zh dict entries; translate a matching en
   entry (structure/order identical).
3. Mirror into the static HTML so first paint agrees.
4. Never reword or "improve" their Chinese (user: 不要轻易改动中文内容排版).
Also: users delete whole sections (e.g. help 8) — drop the dict keys too, or
renderHelp keeps showing ghosts.

## Address-map design that satisfied the user (single-file tool)
Block model: 25pt blocks (real pt, 1pt = 4/3 px), 1pt gap between consecutive
segments, unconfigured gaps shown as default blocks (same label format),
panel total 35x25pt scrolling. Overlap = nesting: lower-priority block becomes
a container sized 25pt x (1 + inner segments); children (higher priority)
stack inside, vertically centered (top remnant ~12.5pt shows container info).
Example: DEV containing CA0+CA1 (not continuous) → 4x25pt container with
CA0 / default / CA1 centered inside.
User iterated: proportional → fixed size → hybrid (>= full/8 proportional,
below fixed, container grows to fit contained fixed blocks) → nested list.
Confirm the model in words before coding (user: "你先理解我的描述").
