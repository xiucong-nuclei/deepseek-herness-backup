---
name: kiucong-scripts
description: Write utility scripts for kiucong's server environment — synthesis data processing, CSV tools, encoding-safe output.
metadata:
  hermes:
    triggers:
    - generate a python script
    - write a script for kiucong
    - syn_diff
    - process CSV
    - synthesis results
    platforms:
    - linux
    version: 1.0.1
    category: software-development
---

# Kiucong Script Authoring

Patterns and constraints for writing Python utility scripts deployed to kiucong's
CentOS 7 server environment.

## Constraints

1. **ASCII-only — the entire file, from the very first draft.** Applies to EVERY
   script/code delivered to kiucong, including local helper tools (e.g. `piccp`),
   not just server-side scripts. Write pure ASCII from the start; do NOT emit
   Chinese messages/comments then rewrite — the user will reject it and ask
   again. Replace:
   - `→` with `->`, `←` with `<-`, `—` (em-dash) with `-`
   - `✓` with `[OK]`, `✗` with `[ERR]`, `⚠` with `[WARN]`
   - All Chinese/Unicode in strings, comments, docstrings, and help text — use English
   - Verify before delivery: `grep -nP '[^\x00-\x7F]' <file>` must return nothing
   **Chinese prose the user wants in generated databook output** (not a script
   message): the script must still stay ASCII. Two ways: (a) put the Chinese in an
   external template file the script reads at runtime; (b) translate the prose to
   spec-style English with the `spec-trans` skill and embed it as an inline
   constant. Kiucong chose (b) — English inline, no external file dependency. Do
   NOT hardcode Chinese string literals in the `.py`; he rejects non-ASCII scripts.

2. **Code delivery: `diff -u` in chat for ≤20 lines; full file only for bigger changes.**
   When a change is ~20 lines or fewer, do NOT send a file — paste the standard
   unified diff straight into chat (`git show <commit> -- <file>` gives it): the
   `--- a/` `+++ b/` headers, `@@ -l,c +l,c @@` hunk markers, and `+`/`-` lines
   with context, so kiucong can see exactly which lines moved. Only send the full
   file when the change exceeds ~20 lines.
   **File delivery via WeCom — put the `.txt` copy in `~/delivery_tmp/`, never in
   `~/deliverables` or the home root.** When sending script files:
   - Copy to `~/delivery_tmp/<name>.txt` (a temp folder under home) before attaching
   - Tell user: "Rename back to `<name>.<ext>`"
   - `~/deliverables/` is the git repo of canonical sources — keep it free of
     `.txt` copies and `__pycache__/`. Its `.gitignore`: `__pycache__/`, `*.pyc`, `*.py.txt`
   - Do NOT litter `.txt`/`.py` copies directly in `~/` (home root)

3. **Encoding-tolerant input.** CSV files from the user's toolchain are often
   UTF-16 LE with BOM (`0xFF 0xFE`). Always detect encoding; never hardcode
   `utf-8`. Fallback chain: UTF-16 LE/BE (BOM) → UTF-8-SIG (BOM) → UTF-8 →
   GBK → latin-1.

4. **Metadata rows in CSV.** The user's CSV files often have metadata rows
   (TECH, FREQ, Update Time) before the real header row. Scan for the row
   containing `Type` + `Feature` + `Config` to locate the real header.
   Preserve metadata rows in output.

5. **Rolling backups.** Before in-place modification, create a rolling backup:
   `file.bak.1`, `file.bak.2`, ... — never overwrite an existing backup. Find
   the first unused N and copy there.

   ```python
   def backup_file(path: str) -> str:
       n = 1
       while True:
           bak = f"{path}.bak.{n}"
           if not Path(bak).exists():
               break
           n += 1
       shutil.copy2(path, bak)
       print(f"[BACKUP] {path} -> {bak}")
       return bak
   ```

6. **Encoding detection on ALL file reads.** Not just CSV files — syn_feature
   config files may also be GBK-encoded on CentOS 7. Always call
   `detect_encoding()` before opening ANY text file. Missing this on non-CSV
   files causes silent `UnicodeDecodeError` in functions like `extract_include_ix()`.

7. **Argparse before env checks.** If `check_env()` (which exits on missing
   `PROJ_SRC_ROOT`/`PROJ_NAME`) runs before `parse_args()`, then `-h`/`--help`
   is blocked — the user can't even see usage. Always structure `main()` as:

   ```python
   def main():
       parser = argparse.ArgumentParser(...)
       args = parser.parse_args()   # <-- FIRST
       check_env()                   # <-- AFTER
   ```

8. **Deliverables repo drifts from the working copy.** A script may exist BOTH as a
   working copy (`/home/ubuntu/<name>.py`) and archived in `~/deliverables/` (git).
   They are NOT auto-synced — a fix applied to the working copy does NOT propagate
   to the archive. Before editing, confirm which copy is canonical; after a fix, sync
   it to BOTH. Diagnose staleness via git: a file with only the initial "Archive
   existing generated files" commit (no later commits) is a pre-fix snapshot. (Real
   case: an `if config_name else None` guard applied to `/home/ubuntu/syn_diff.py`
   was missing from `~/deliverables/tools/syn_diff.py` because the archive predated
   the fix.) The `~/deliverables` repo has `origin=git@github.com:xiucong-nuclei/
   hermes-deliverables.git` (SSH); kiucong pulls this on his local Windows/VS Code to sync.

   **AUTO-PUSH RULE (mandatory): after EVERY commit in `~/deliverables`, run
   `git push origin master` in the same turn — do not stop at `git commit`, do not
   ask, do not batch. kiucong explicitly requested this. Verify the push succeeded
   (check the `remote:` line shows the branch updated, or `git log origin/master -1`
   equals the local HEAD) before reporting done. If the push fails (e.g. local
   branch behind remote), resolve the divergence and push again before finishing.

## Interaction workflow

For multi-step feature additions (new subcommands / flags with ambiguous
semantics), restate the requirement, list the open decision points (overwrite
handling, conflict behavior, arg type), and WAIT for the user's confirmation
before generating code — kiucong runs this confirm-then-generate loop for
non-trivial changes. Small, unambiguous additions (e.g. a `pwd` keyword) can
go straight to code.

The restatement must be DETAILED, not a summary — kiucong will ask "再详细一些"
if it is too terse. Cover: the exact per-command flow, edge cases (empty input,
missing config, command-not-found), and — most importantly — flag ⚠️ every place
your interpretation deviates from the user's literal wording (e.g. "先查后提交 vs
先提交后查", whether a config name includes the `.v` extension). Err on the side
of a full spec table before writing code.

## LSF / make / subprocess workflow

kiucong's synthesis flow drives `make` from Python, and `make` internally calls
`bsub` to submit real work to LSF. Scripts should NOT `bsub` themselves — just
run `make` and poll `bjobs`.

- **subprocess inherits the shell env.** `subprocess.run([...])` (no `env=`)
  copies `os.environ` whole, so `make` sees `PROJ_SRC_ROOT`, `PROJ_NAME`, `PATH`,
  and LSF vars exactly as the shell did. Only `export`ed shell vars propagate; a
  bare `VAR=x` in `.zshrc` / `spr_cpu` does NOT reach the child.
- **make timing**: `make CFG=syn_feature/<cfg> only_compile` does ~tens of
  seconds of local preprocessing, THEN bsub's and returns. It does NOT block
  until the job finishes.
- **Throttle via bjobs (RUN+PEND), not by counting make processes.** Count
  active LSF jobs with `bjobs -r -w` + `bjobs -p -w` and sum lines starting with
  a digit (JOBID); ignore header and "No ... job" messages. Poll every 60s,
  submit the next make only when count < 6.
- **Tee (terminal + log) for a single foreground make**:
  ```python
  with open(log, 'a') as f:
      p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
      for line in p.stdout:
          print(line, end='', flush=True); f.write(line)
      p.wait()
  ```
- **Parallel makes with per-config logs (the delivered approach)**: launch up to
  `MAX_JOBS` makes in the background (Popen), each writing its own
  `<prefix>_logs/<stem>.log`, and print only a one-line `[i/N] start cfg` summary
  (parallel stdout interleaves into garbage). Wait for a slot with BOTH
  `< MAX_JOBS` alive makes AND `< MAX_JOBS` bjobs RUN+PEND.
- **Route each config through its own list file — NOT `CFG=syn_feature/<cfg>`**.
  `CFG=syn_feature/<cfg.v>` (single case) and `CFG=syn_feature/<list>` make the
  Makefile place results in DIFFERENT locations; kiucong wants the list-mode
  location, so write `<stem>.list` (content one line `syn_feature/<cfg.v>`) and
  pass `CFG=syn_feature/<stem>.list`. make reads the list at startup (include
  phase), so a per-config list file can be evicted while its make still runs —
  see `references/lsf-flow-driver.md`.

## Batch file tools (paste-friendly stdin, CSV-driven generation)

From the absorbed `batch-file-tools` skill: creating many files from pasted
newline-separated names (use an `input()`-loop, never `sys.stdin.read()` — the shell
executes pasted newlines as Enter) and CSV-driven config generation. Scripts:
`scripts/touchs` (batch touch from pasted names), `scripts/gen_syn_config.py`
(Verilog config + `.list` manifests from CSV; docs in `references/gen-syn-config.md`).
Full guide: `references/batch-file-tools.md`.

## Python pitfalls

- **Local shadows module function.** `x = x([...])` inside `main()` makes `x` a
  local, so the RHS call raises `UnboundLocalError`. Rename the local
  (`cp = common_prefix([...])`).
- **Prepending a name-prefix** needs the trailing underscore — `'micro' + 'dual_issue.v'`
  → `microdual_issue.v`. Use `prefix + '_' + base`.
- **docutils is not a validator for Sphinx-targeted databook rst.** It reports
  false "Unknown interpreted text role ref" / "malformed hyperlink target" /
  "Unknown target name" for `:ref:` and `.. _xxx.v::` double-colon labels. Only
  grid-table parse errors from docutils are real; final check needs Sphinx.
- **csv2 numeric column names vary** across tool versions — never look up
  area/gate (or Feature/Base Config/Comment) by EXACT header name; it returns ''
  and the table cells come out empty. Fuzzy-match: lowercase, strip
  spaces/underscores, then match area / base area / added area / added gate,
  mirroring syn_diff.py's `resolve_diff_columns`.
- **Emitting non-ASCII in OUTPUT while keeping the script ASCII.** If the
  generated rst/doc must carry a proper symbol (e.g. `µm²` for square microns,
  not the ASCII `um2`), DON'T paste the Unicode char into the `.py` — that breaks
  the ASCII grep. Write it as a Python unicode escape: `'\u00b5m\u00b2'`
  (`µ`=U+00B5, `²`=U+00B2). The source bytes stay ASCII (grep-clean) and the
  emitted rst is correct. Each special char is single-width, so grid-table column
  alignment is unchanged vs the ASCII form.
- **RST title adornment levels.** Same-level subsections must share the same
  adornment char. Introducing a new level for a sub-header (e.g. `-` for
  `评估方法`) pushes the existing config subsection headings (`=`) to a deeper
  level → docutils "Inconsistent title style: skip from level 1 to 3". Fix: use
  the same char as the siblings at that level (use `=` for the preamble
  sub-headers, matching the config headings). Choose adornments so the whole
  document's nesting is consistent before generating.
  **kiucong's databook convention:** section titles underline with `+`, sub-section
  headings with `#` — he explicitly asked to switch config/`Evaluation*` headings
  from `=` to `#` ("符合我的 databook 的章节格式"). Use `+` (sections) / `#`
  (sub-sections) for this databook, not `=`.

## References

- `references/syn-diff-pattern.md` — full syn_diff.py pattern: metadata skip, CSV lookup, diff compute, summary output, and the `-u/--update` sync-to-files mode (rename + include_ix, fuzzy match, backup folder, review log).
- `references/syn-report-to-rst.md` — syn_report_to_rst.py: databook RST generation from csv2 (csv2 schema, 大类 grouping, anchor naming, plain-text wrapped config cells with NO links, `:widths:` control, underscore-boundary wrapping, `_esc_ref`, include_ix rewrite, Sphinx venv validation).
- `references/piccp.md` — piccp command set. **`sync-v` is EXACT-name only — the user explicitly reverted fuzzy matching ("回退，不要模糊匹配了"); do NOT re-add difflib fuzzy to piccp.**
- `references/lsf-flow-driver.md` — syn_flow.py flow driver (-rtl/-compile/-syn): make+bsub+bjobs throttle, cpu_cct check, tee.

## Encoding Detection Snippet

```python
def detect_encoding(path: str) -> str:
    with open(path, 'rb') as f:
        head = f.read(4)
    if head.startswith(b'\xff\xfe'):
        return 'utf-16-le'
    if head.startswith(b'\xfe\xff'):
        return 'utf-16-be'
    if head.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    for enc in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(path, encoding=enc) as f:
                f.read(1024)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'latin-1'
```
