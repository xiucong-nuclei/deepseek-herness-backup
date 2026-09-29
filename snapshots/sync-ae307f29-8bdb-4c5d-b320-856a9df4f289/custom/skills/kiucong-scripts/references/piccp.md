# piccp command reference

Location: `~/deliverables/tools/piccp/piccp` (git repo, canonical source).
Config: `piccp.conf.json` beside the script (JSON, no DB). Fields:
`source_dir`, `dest_dir`, `link_dir`, `source_name`. All paths support the
`pwd` keyword (= current working directory). Pure ASCII, `[OK]/[WARN]/[ERR]`
prefixes, interactive `[y/N]` confirms.

## Commands

| command | behavior |
|---|---|
| `set-src <path>` / `set-dst <path>` / `set-ldp <path>` / `set-name <name>` | persist config |
| `cp <new_name> [-f]` | literal single-file copy + rename; `-f` skips overwrite prompt; if the name contains `*?[` and is not found, hints to use `cps` |
| `cps [-f] [-R]` | wildcard batch copy, keeps original names (see below) |
| `mv <name>` | move, no symlink |
| `mvld <name>` | move + relative-path symlink in link_dir (defaults to source_dir) |
| `sync-v` | scan dst top-level `*.v`, overwrite with same-name file from src; skip+`[WARN]` if missing in src; one overall confirm |
| `show` | print current config |

## sync-v: NO fuzzy matching (explicitly reverted)

`sync-v` is EXACT-name only. A fuzzy-matching variant (difflib
`get_close_matches`, cutoff 0.6, backup folder + review log, mirroring
syn_diff.py's `-u`) was added once but the user immediately reverted it:
"回退，不要模糊匹配了". Do NOT re-add fuzzy matching to `sync-v` — kiucong
wants it to stay a simple same-name refresh. syn_diff.py's `-u` fuzzy logic is
specific to that tool and must NOT be generalized to piccp unless asked.

## cps specifics (added Aug 2026, commit bc84634)

- Matches `source_name` against the source dir with Python `glob` (shell
  wildcards `* ? [...]`; dotfiles only match when the pattern starts with a dot).
- Default: top-level only. `-R` recurses by prefixing `**/` unless the pattern
  already starts with `**` — `glob.glob(..., recursive=True)`.
- Lists all matches (existing dst targets marked `(overwrite)`), ONE overall
  `Proceed? [y/N]` covering overwrites too; `-f` skips it. 0 matches ->
  `[ERR] no files matched pattern: ...`, exit 1.
- Names are kept as-is (basename). With `-R`, same-name files from different
  subdirs collide — last one wins, marked `(overwrite)` in the listing.

## Division of labor

- `cp` = literal + rename (single file, legacy unchanged)
- `cps` = wildcard + keep names (batch)
- `sync-v` = reverse direction: refresh dst .v from src by name (exact only)
