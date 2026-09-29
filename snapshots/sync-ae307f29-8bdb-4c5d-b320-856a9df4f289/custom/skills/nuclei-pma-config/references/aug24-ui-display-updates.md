# PMA tool — Aug 24 2026 UI & display updates (browser-verified)

Companion to import-filler-rows.md and session-updates-2026-08.md (which
could not be re-written this turn due to the read-before-write dedup guard).
Commits 938ddd3, 173299f (and c2871f9). All verified in a real browser.

## Imported size shown in human form (173299f)

- `loadRegionsFromConfig` now pushes `newRegion(attr, "0x"+hexStr(base),
  "size", fmtSize(size))` — the SIZE input shows "32 MB" instead of "0x2000000".
- SAFE because PMA sizes are always powers of 2: `fmtSize` divides by
  1024^k and the result is always an integer, so `parseSize("32 MB")`
  round-trips exactly; validation stays [OK] and generated masks unchanged.
- fmtSize CAN emit decimals ("3.3 GB") for non-power-of-2 spans (default-bar
  segments) — those are display-only, never round-tripped through parseSize.

## fmtAddr: underscore every 4 hex digits from the right (938ddd3)

User requirement, applied uniformly to address bar AND validation info
(shared fmtAddr, so one change covers both):

- 32-bit:  `0x4400_0000`
- 40-bit:  `0xFF_4400_0000`
- 48-bit:  `0x0000_4400_0000`  (digits-padded)
- full:    `0xFFFF_FFFF_FFFF`

Implementation: right-anchored grouping loop (not regex), `while
(rest.length > 4)` slice(-4). Replaces the old single-underscore-at-32-bit
rule. Zero-padded `0x0000_0000_0000` groups correctly.

## Small UI adjustments (938ddd3, c2871f9)

- Address-bar block min height BLK = 33pt (was 30pt; user asked +3pt).
- Attr select width 3.8em → 5.2em — 3.8em truncated "DEV" (select arrow +
  padding ~42px > 38px box).
- Import page: CONFIG FORMAT example panel deleted (dead UI); import panel
  widened + centered: `grid-column:1/-1; max-width:64vw; justify-self:center`,
  textarea rows=10. impFmt i18n key removed.
- Region-number cell `white-space: nowrap` (was wrapping in narrow col).
- Address-bar block info now 4 fields (rb-f1 attr+num, rb-f2 base " -",
  rb-f3 end, rb-f4 size right-aligned min-width 7em) — "DEV Region0
  0x2000_0000 - 0x2FFF_FFFF 256 MB".

## Help zh/en sync discipline (user's standing rule, re-affirmed this session)

- User hand-edits the static HTML Chinese help; mirror the edit VERBATIM
  into the zh i18n dict (renderHelp overwrites static HTML at runtime, the
  dict is authoritative) and write the matching en entry.
- Do NOT touch zh strings the user did not ask to change. This session I
  rewrote an impHint sentence while deleting an unused key and had to
  revert it ("不要轻易改动中文的内容和排版").

## Session-truncation discipline (max_turns guard)

When the run is cut by "maximum number of tool-calling iterations":
- If patches/commits were NOT actually executed, do NOT claim them done.
  This session an earlier turn claimed "4 items done + committed" while the
  working tree still held only the user's one-line hand edit — the file had
  zero of the claimed changes. On the next "继续", first `git status` /
  `git diff` to reconcile reality, then actually apply + verify + commit.
- If the last browser verification result was truncated, re-run it before
  reporting.
