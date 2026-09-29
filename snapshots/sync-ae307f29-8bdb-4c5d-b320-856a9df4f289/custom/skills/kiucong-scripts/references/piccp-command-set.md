# piccp Command Set (as of 2026-08)

piccp = persistent-config file mover for the synthesis flow. Config stored in
`piccp.conf.json` next to the script. Pure ASCII, prompts `[OK]/[WARN]/[ERR]`,
confirm-then-act (no side effects until `y`). Canonical source:
`~/deliverables/tools/piccp/piccp` (git repo, commit `bc84634`).

## Commands

| Command | Behavior |
|---|---|
| `set-src <path\|pwd>` / `set-dst` / `set-ldp` / `set-name <name>` | Store config (`pwd` = current dir) |
| `cp <new_name> [-f]` | Literal single-file copy + rename; source name comes from `set-name`. `-f` skips overwrite prompt. |
| `cps [-f] [-R]` | Shell-glob batch copy, keeps original names. Default top-level only; `-R` recurses (pattern auto-prefixed with `**/` unless it already starts with `**`). |
| `mv <name>` / `mvld <name>` | Move to dst (mvld also creates relative-path symlink in link_dir; link_dir defaults to src) |
| `sync-v` | Overwrite dst top-level `.v` with same-name src files; src-missing files skipped with `[WARN]` |
| `show` | Print current config |

## cps semantics (user-reviewed design)

- `set-name` holds a glob pattern (shell wildcards `* ? [...]`); 0 matches
  → `[ERR] no files matched pattern: ...` exit 1
- Prints match list with `(overwrite)` marks on targets that already exist,
  then ONE overall `Proceed? [y/N]`; `-f` skips all prompts including overwrites
- No `<new_name>` — batch keeps original filenames; rename use case stays with `cp`
- `-R`: same-name files from different subdirs overwrite each other (later wins),
  visible as `(overwrite)` in the list — accepted behavior, surfaced at confirm time
- `cp` with wildcard chars in `set-name` fails with a hint: `use 'cps' for wildcard pattern matching`

## Design history note

cps was born from "cp 源文件名支持正则吗?" → full-regex design was rejected
("太复杂了") → shell-glob version accepted in one round. Regex metachars vs
literal names were a real ambiguity; glob sidestepped it entirely.
