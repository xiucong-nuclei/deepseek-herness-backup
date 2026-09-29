# Feature Design: Complexity Ceiling & Minimal Variant Pivot

How kiucong reacts to over-engineered feature proposals, and the pivot that
gets the feature shipped anyway. Real case: piccp batch-copy, 2026-08.

## The pattern

kiucong proposes a capability (e.g. "support regex in source filename so I
can batch-copy files"). A full-featured design (regex engine, rename
semantics, per-file confirm, recursive option, edge cases — 5 numbered
decision points) gets rejected:

> "算了，不想搞了，太复杂了" (forget it, too complex)

He still wants the capability — he just does not want the machinery.

## The pivot

Offer the MINIMAL viable variant immediately. In the piccp case:

- Rejected: regex-based matching with 5 open decision points.
- Accepted: new `cps` subcommand using shell-style glob (`*`, `?`, `[...]`),
  top-level matching only, two flags only:
  - `-f` / `--force` — skip the overall y/N confirmation
  - `-R` / `--recursive` — match into subdirectories
- All other semantics fixed by convention, not configurable:
  - keep original filenames (no rename arg)
  - list matches + one overall `Proceed? [y/N]` (same style as `sync-v`)
  - existing targets marked `(overwrite)` inside the same confirmation
  - 0 matches → `[ERR] no files matched`

## Rules of thumb

1. When a design gets "too complex", simplify MATCHING first (glob over
   regex), then drop flags, then fix behaviors by convention.
2. Keep open decision points to ≤2-3 when proposing the minimal design —
   the 5-question spec is what caused the bail.
3. Reuse existing subcommand conventions (`sync-v` confirm style, `[OK]`/
   `[WARN]`/`[ERR]` prefixes, ASCII-only) so the new command needs zero
   new decisions.
4. Test in a temp dir and commit after acceptance, same as any other script
   (see main SKILL.md delivery rules).

## Deliverable state

`cps` shipped in `~/deliverables/tools/piccp/piccp` (commit `bc84634`),
verified: top-level glob, `-f`, `-R`, no-match error, `cp` wildcard hint.
