# PMA tool — Aug 27 2026: click feedback + END/SIZE auto-convert (browser-verified)

Commits 660d98a→0146a84 (click feedback redo), 28b93c7 (mode auto-convert).

## "点击反馈" = momentary scale pop, NOT color highlight (user correction)

User asked for click feedback on address-bar blocks; the first attempt added
:active dimming + an `.active` accent ring (selected state). User rejected:
"你理解错了... 能够让用户感觉到点击了一下，比如放大一下这种特效。而不是变色和高亮。"

Lesson: for this user, "点击反馈" means a TACTILE press moment (scale pop),
never persistent highlight/color state. Implemented:

```js
function popAnim(el) {
  if (typeof el.animate !== "function") return;
  el.animate(
    [{ transform: "scale(1)" }, { transform: "scale(1.07)" }, { transform: "scale(1)" }],
    { duration: 150, easing: "ease-out" }
  );
}
```

- Fired on click for cfg blocks (then `setActiveRow(idx)` to sync the table
  row highlight — the pre-existing linkage) and default blocks (then
  `setActiveRow(-1)` clears table selection).
- Verified via `getAnimations()` + `effect.getKeyframes()` → scale(1)→1.07→1.
- No `.active` class, no brightness filter. cursor: pointer kept.

## END/SIZE mode switch auto-converts a valid value (28b93c7)

`selMode.onchange` (was `r.mode = selMode.value; renderGen();`):

```js
const from = r.mode, to = selMode.value;
if (from !== to) {
  const base = parseHex(r.base);
  if (base !== null) {
    if (from === "end") {
      const end = parseHex(r.val);
      if (end !== null && end > base) r.val = fmtSize(end - base);   // human
    } else {
      const size = parseSize(r.val);
      if (size !== null && size > 0n) r.val = "0x" + hexStr(base + size); // hex
    }
  }
  r.mode = to;
}
renderGen();
```

- end → size fills human (`fmtSize`), size → end fills hex — consistent with
  the SIZE input's human convention and END input's hex convention.
- Round-trip is exact: 0x20000000 end / 0x10000000 base → "256 MB" → back to
  "0x20000000".
- Invalid source value or missing base → value untouched (kept as-is).

## Stale SKILL.md sections (superseded — read this file + references first)

- Core Rule 2 says "ALWAYS use 1s-trailing"; tool actually OUTPUTS 1s-leading
  high masks (`'hFFFFFF000000`), import accepts both and converts low→high.
- "Check Mode (tool spec)" — check mode was removed; it is an IMPORT page now
  (paste / from-file, both CONFIG_= and `define formats, PA SIZE extracted
  first, filler rows trimmed — see import-filler-rows.md).
- "Address-bar visualization: horizontal rectangle" — it is a VERTICAL bar
  (0x0 at bottom, space end at top), recursive priority slicing, min 33pt.
- "End XOR Size (mutually exclusive)" — switching now auto-converts instead.
