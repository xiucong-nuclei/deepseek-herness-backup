# syn_flow.py — synthesis flow driver (-rtl / -compile / -syn)

Standalone script, split out of `syn_diff.py` because "太多参数不易用". Drives the
synthesis flow by running `make` from `$PROJ_SRC_ROOT/cpu_cct`. Mirrors syn_diff.py's
`check_env` / `get_proj_root` / `get_proj_name` / `get_syn_feature_dir` helpers.

## Modes

| Mode | make command |
|------|--------------|
| `-rtl` | `make CFG=syn_feature DUMP_FILE=1` (single foreground run, tee) |
| `-compile` | `make CFG=syn_feature/<stem>.list only_compile` (per config, bjobs-throttled) |
| `-syn` | `make CFG=syn_feature/<stem>.list TECH=22 TRACK=9t only_syn` (per config, throttled) |

Each `-compile`/`-syn` config is routed through its OWN list file `<stem>.list`
(no `.v`), whose content is one line `syn_feature/<cfg.v>`. See "List-file routing".

## Decisions confirmed with kiucong

1. Not in cpu_cct → **error out** with a `cd $PROJ_SRC_ROOT/cpu_cct` hint (NOT auto-`os.chdir`).
2. cpu_cct check by **absolute path**: `(Path(get_proj_root()) / 'cpu_cct').resolve()` == `Path.cwd().resolve()`.
3. Config list = `glob('*.v')` sorted; name **includes `.v`** (used inside list content, not in the list filename).
4. Script never `bsub`s — `make` does it internally; script only polls `bjobs`.
5. Throttle counts **RUN + PEND** (`bjobs -r -w` + `bjobs -p -w`).
6. `MAX_JOBS = 8` (bumped from 6); poll every **30 s (compile) / 60 s (syn)**.
7. `TRACK=9t` (NOT `TRACE`).

## List-file routing (the key insight)

`make CFG=syn_feature/<cfg.v>` (single case) and `make CFG=syn_feature/<list>`
(list) make the Makefile place RESULTS IN DIFFERENT LOCATIONS. kiucong wants the
list-mode location, so even a single config must go through a list file.

- List file name: `<stem>.list` (e.g. `syn_600_rv32_base.list` — NO `.v`).
- List content: one line `syn_feature/<cfg.v>` (e.g. `syn_feature/syn_600_rv32_base.v`).
- make command: `CFG=syn_feature/<stem>.list`.

**make reads the list at STARTUP** (include/parse phase), so after launch the list
file is no longer needed. This is what makes per-config list files safe under
concurrency: a list file can be deleted while its make is still running.

## Per-config list + MAX_JOBS-slot FIFO (parallel-safe, no shared-file race)

6 makes run concurrently but must NOT share one list file (a second write would
clobber it before the first make reads it). Instead: each config writes its own
`<stem>.list`, and a FIFO queue (bounded to `MAX_JOBS`) tracks them.

```python
list_queue = []  # FIFO, <= MAX_JOBS
for cfg in configs:
    # wait for a free slot (alive makes < MAX_JOBS AND bjobs RUN+PEND < MAX_JOBS)
    ...
    # evict the OLDEST list file before enqueuing a new one
    if len(list_queue) >= MAX_JOBS:
        Path(list_queue.pop(0)).unlink()
    # write this config's list, enqueue, launch make
    list_path = write_cfg_list_file(cfg)   # writes "syn_feature/<cfg.v>" into <stem>.list
    list_queue.append(list_path)
    p = subprocess.Popen(['make', f'CFG=syn_feature/{stem}.list', *extra, target], ...)
...
# finally: delete every list file still in list_queue
```

Evict-OLDEST (not evict-completed) is safe precisely because make reads its list at
startup; by the time the parent launches config 7, config 1's make already consumed
its own list file.

## Throttle loop (parallel — the delivered approach)

`-compile`/`-syn` launch up to `MAX_JOBS` makes in the background (Popen), each
writing its own log file (`<prefix>_logs/<stem>.log`), printing only a one-line
`[i/N] start cfg` summary to the terminal (parallel stdout would interleave). The
parent waits for a free slot with BOTH conditions — `< MAX_JOBS` alive makes AND
`< MAX_JOBS` bjobs RUN+PEND — because bjobs alone has a lag window: make spends
~tens of seconds in local preprocessing before it bsub's.

```python
MAX_JOBS = 8
POLL_SEC_COMPILE = 30
POLL_SEC_SYN = 60

def count_active_jobs() -> int:
    total = 0
    for flag in ('-r', '-p'):
        try:
            r = subprocess.run(['bjobs', flag, '-w'], capture_output=True, text=True, timeout=30)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return 0
        if r.returncode != 0:
            continue
        for line in r.stdout.splitlines():
            if line.strip()[:1].isdigit():   # JOBID rows only
                total += 1
    return total
```

## Logs

Per-config logs under cpu_cct: `<prefix>_logs/<stem>.log` (`compile_logs/`,
`syn_logs/`). `-rtl` uses a single tee'd `make_rtl.log` (truncated each run).
