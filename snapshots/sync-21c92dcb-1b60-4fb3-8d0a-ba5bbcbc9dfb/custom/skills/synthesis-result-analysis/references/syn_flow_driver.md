# syn_flow.py — Synthesis Flow Driver

Sibling tool to `syn_diff.py`. Lives at `~/deliverables/tools/syn_flow.py` (git
repo, commit-after-change per user convention). Drives the Makefile over the
syn_feature configs in three modes. Requires `PROJ_SRC_ROOT` + `PROJ_NAME`
(via `spr_cpu`), run from `$PROJ_SRC_ROOT/cpu_cct`.

## Modes (argparse mutually-exclusive, one required)

| Flag | make invocation | Log | Poll |
|------|-----------------|-----|------|
| `-rtl`     | `make CFG=syn_feature DUMP_FILE=1` (whole dir, single make) | make_rtl.log | — |
| `-compile` | per-config `make CFG=syn_feature/<stem>.list only_compile` | compile_logs/<stem>.log | 30s |
| `-syn`     | per-config `make CFG=syn_feature/<stem>.list TECH=22 TRACK=9t only_syn` | syn_logs/<stem>.log | 60s |

## cfg mechanism (IMPORTANT — no CLI cfg param on compile/syn)

- `-compile` and `-syn` do NOT accept a per-config CLI arg. They auto-enumerate
  **all** `*.v` in `syn_feature/` (`load_config_list()`), sorted, and run each.
- Per config it writes a `<stem>.list` file (content: `syn_feature/<cfg>`) then
  runs `make CFG=syn_feature/<stem>.list <extra> <target>`. List files cleaned
  up at end.
- Throttle: submit next config only when `(active makes) < MAX_JOBS(6)` AND
  `(bjobs RUN+PEND of current user) < MAX_JOBS`. `bjobs` uses `-r -w` and `-p -w`
  (RUN and PEND). Missing/timeout bjobs ⇒ treat as 0, don't hard-fail.
- `syn_feature` dir = `$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature`
  (`get_syn_feature_dir()`).

## `-list <path>` parameter (added 2026-08, applies to all three modes)

Optional, shared across `-rtl`/`-compile`/`-syn`. When absent → behavior is
exactly as above (back-compatible). When present:

- Path resolved **relative to syn_feature dir** unless absolute
  (`Path(list_arg)`; if not absolute → `Path(sf_dir)/<arg>`). Missing file ⇒
  exit 1 with `ERROR: list file not found`.
- Read lines; skip blank and `#` comments; take `Path(line).name` as the cfg
  name; each must exist under `sf_dir` or exit 1 (`ERROR: cfg not found`).
- Returns configs in **list order** (not sorted). Callers pass them into
  `_run_config_make(target, extra, log_prefix, poll_sec, configs)`.
- `_run_config_make` gained `configs` param (default `None` → falls back to
  `load_config_list()`). Type annotation `'list | None' = None` to satisfy
  Pyright.
- `-rtl -list ...`: runs per-config via `_run_config_make('', ['DUMP_FILE=1'],
  'rtl', POLL_SEC_RTL=30, configs)` — throttled, logs to `rtl_logs/<stem>.log`.
  Only when NO `-list` does rtl keep the single whole-dir make.
- `-compile`/`-syn -list ...`: replaces the enumeration source with the parsed
  list; `_run_config_make` elsewhere unchanged.

## Gotchas

- The empty `target` for rtl builds `make CFG=... DUMP_FILE=1` with no target —
  `_run_config_make` already handles `target=''` fine.
- Workflow pitfall: do NOT assume compile/syn have a per-config CLI arg when
  restating a change request — read the code first. The cfg is a make-internal
  `CFG=` mechanism driven by directory enumeration, not a CLI selector. Verify
  actual current behavior before proposing edits.