# PMA tool — session updates (Aug 2026, browser-verified)

Supplement to web-tool-spec.md. All items below are user-confirmed during the
Aug 19 2026 session and verified in a real browser. The SKILL.md body could
not be patched from a background curator turn (read-before-write guard bug —
see note at bottom); reconcile this file into SKILL.md next foreground edit.

## Input semantics (changed this session)

1. PA SIZE is now a NUMBER INPUT (32..48), NOT a 32/64 radio. Validate integer
   in range; invalid → red border + `[ERR] PA SIZE must be an integer in 32..48`.
   Hex digits in generated values = PA_SIZE/4 (48 → 12 digits).
2. SIZE field accepts hex OR decimal-with-unit: `32KB`/`32k`/`1m`/`256KB`/
   `2G` (K/M/G, case-insensitive, optional B). Parse via `parseSize()`:
   `^([0-9]+)\s*([kKmMgG])([bB]?)$` → n × 1024^unit, else fall back to
   `parseHex()`. END stays hex-only.
3. END dual semantics (user-confirmed, "和之前一样" + inclusive tolerated):
   - Primary: exclusive `[BASE, END)`, size = END − BASE. Shown as
     `0x10000000 - 0x20000000`.
   - If `END − BASE` is invalid but `END − BASE + 1` is valid (power of 2,
     ≥4K, base-aligned), accept as inclusive `[BASE, END]` and emit a [WARN]
     line: "END looks like an inclusive end ([BASE,END]): size = END-BASE+1
     = 0x…. Use END = 0x… for [BASE,END) semantics." Never error on it.
   - Detection: `okA = pow2(end-base)&&…`, `okB = pow2(end-base+1n)&&…`;
     prefer okA, else okB+warning, else normal validation errors.
   - Default sample values: DEVICE 0x10000000 END 0x20000000 (exclusive),
     CACHEABLE 0x20000000 SIZE 256MB.
4. `parseHex()` must strip surrounding quotes first:
   `s.trim().replace(/^["']+|["']+$/g,"")` — check-mode values arrive quoted
   (`"`N600_CFG_PA_SIZE'h10000000"`) and the trailing quote breaks the
   `/[0-9a-fA-F_]+$/` anchor (bug found & fixed this session).

## Layout / theme (user-driven redesign)

- Theme: WHITE/BLUE (replaced dark). bg #f2f6fc, panels #ffffff, panel2
  #e9f0fa, accent #1d6fd8, text #132b4c, border #d4e2f4; pre.code bg #f8fbff
  text #0b2a55. Do NOT revert to dark.
- Responsive: sizes in vw/vh/clamp ("页面做成随显示器大小,元素等比放大").
- Layout: 3-column grid — LEFT config (scroll) | MIDDLE config output
  (scroll, narrower) | RIGHT ADDRESS MAP (15vw) — plus BOTTOM validation
  panel (max-height ~26vh, scroll).
- ADDRESS MAP: VERTICAL thin rectangle spanning page height (not horizontal).
  top = base/span, height = size/span, min-height ~1.6%, blocks flush
  (left/right 0), each block shows START and END addresses as two lines
  (exclusive end = hi), axis 0x0 top / span bottom. DEVICE #2563eb (BLUE —
  user banned red in the map), CACHEABLE #16a34a, NC #d97706.
- Bottom VALIDATION panel shows per-region [OK]/[ERR]/[FIX] + overlap rows;
  [WARN] rows (yellow) for inclusive-END case. Fix buttons WRAP/SPLIT live in
  the bottom panel too.

## Front-end pitfalls (apply to any single-file tool)

- FOCUS BUG (this session): rebuilding the region table inside an `oninput`
  handler destroys the input element → user can type only ONE character.
  Fix: `oninput` updates state + lightweight `updateOutputs()` (bar/info/
  code) only; only structural changes (add/del row, attr/mode switch) call
  full `renderGen()`.
- Browser caches the old HTML after edits → verify with `?v=N` cache-buster.

## Status

Tool fully browser-verified (generate + check + fix + download), git commits
through `8617410` (Aug 19 2026). Service: http 8640 in
~/deliverables/web/pma-calc-landing; CDP chrome on 9222.

## Note on this file

Background curator guard refused SKILL.md patches ("content has not been
loaded in this review turn") even after skill_view returned full content —
appears to be a guard × dedup interaction. Keep updating references/ from
background turns; fold into SKILL.md from a foreground session.
