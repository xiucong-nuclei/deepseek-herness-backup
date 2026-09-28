
# Makefile Shell Recipe Debugging

When a Makefile target uses `\` continuation to embed multi-line shell scripts, errors can be opaque. This skill covers systematic debugging and common pitfalls.

## Triggers

User reports any of these in a Makefile recipe:
- `syntax error near unexpected token`
- `unexpected end of file`
- `[: missing ']'`
- `line N: ...` errors from `/bin/sh`
- ANSI colors not rendering (literal `\033` text output)
- Pipeline `if` conditions not working as expected
- `for` loop never executes but `[ -n "$VAR" ]` confirms variable is non-empty
- `echo` prints PID number instead of expected variable value

## Workflow

### Step 1: Run `make -n`

```bash
make -n <target>
```

`-n` dry-runs and prints the ACTUAL shell commands Make would execute, including all `\`-continued lines concatenated. **Always start here** — the error's `line N` refers to lines in this generated script, not the Makefile.

### Step 2: Check `$` vs `$$`

In a Makefile recipe, `$` is the Make variable expansion prefix. Shell variables need `$$`:

| Makefile writes | Shell receives | Correct? |
| :-- | :-- | :-- |
| `$i` | Make expands `$(i)` → `` (empty) | ❌ |
| `$$i` | `$i` | ✅ |
| `$matched` | Make expands `$(m)atched` → `atched` | ❌ |
| `$$matched` | `$matched` | ✅ |
| `$((i+1))` | Make mangles it | ❌ |
| `$$((i+1))` | `$((i+1))` | ✅ |
| `$0` (in awk) | Make auto-var (target name) | ❌ |
| `$$0` (in awk) | `$0` | ✅ |

### Step 3: Pipeline exit codes in `if` conditions and `tee`

The exit status of a pipeline `A | B | C` is `C`'s exit status (unless `set -o pipefail`). This is the most common hidden bug.

**Bug pattern:**
```makefile
if grep "error" file.log | sed 's/.*//' > tmp; then ...
```
`sed` always succeeds (exit 0), so `if` is **always true** regardless of whether `grep` matched.

**Fix: separate and use `[ -s ]`:**
```makefile
grep "error" file.log | sed 's/.*//' > tmp; \
if [ -s tmp ]; then ...  # only if tmp is non-empty
```

**tee eats exit codes:** `| tee file` makes the pipeline exit `0` (tee always succeeds). To preserve the original command's exit code, use `PIPESTATUS` (bash) or `$pipestatus` (zsh):

```makefile
$(MAKE) -C ./vsim/ run_sdk TESTNAME=$$test 2>&1 | tee result/$$test.log; \
exit $${PIPESTATUS[0]}
```
Make variable `${PIPESTATUS[0]}` would be caught by Make's own `${}` syntax, so escape it once: `$${PIPESTATUS[0]}` → shell receives `${PIPESTATUS[0]}` (bash special array of pipeline exit codes).

### Step 4: ANSI color codes — use `awk`, not `sed`

`sed` does NOT expand `\033` to the ESC character on all systems (CentOS 7 sed is particularly unreliable). Use `awk` which handles `\033` natively.

**Wrong (produces literal `\033[31m` text):**
```makefile
grep PASS file.log | sed 's/^/\033[32m/' >> output
```

**Right:**
```makefile
grep PASS file.log | awk '{printf "\033[32m%s\033[0m\n", $$0}' >> output
```

### Step 5: Missing `\` continuation

A line in a multi-line recipe block without trailing `\` splits the shell script into two separate invocations. The second half runs in a new shell without the preceding context (e.g., outside a `for` loop).

**Bug pattern:**
```makefile
for test in $$(cat list); do \
    echo "$$test" >> out;   # ← NO \ — breaks the for loop!
    matched=0; \
```

**Fix:** every line inside the block (except the last) must end with `; \`:
```makefile
for test in $$(cat list); do \
    echo "$$test" >> out; \
    matched=0; \
```

### Step 6: `find` returns empty — check for trailing whitespace

When `find -name "$$var"` returns nothing (variable empty), the most common cause is trailing whitespace or `\r` in the file being iterated. This is especially common with `$(cat $$(CASEFILE))` loops.

**Fix: strip whitespace from the input:**
```makefile
for case in $$(cat $$(CASEFILE) | tr -d ' \r'); do \
    case_dir=$$(find $$(NUCLEI_SDK_DIR)/app -type d -name "$$case" 2>/dev/null | head -1); \
```

Alternatively use `xargs`:
```makefile
case=$$(echo $$case | xargs); \
```

**Debugging:** temporarily add `@echo "DEBUG: case=[$$case]"` to see the actual value including invisible trailing chars.

### Step 7: bsub job dependency naming — avoid matching yourself

When using `bsub -w "ended($(CPU_NAME)*)"` to wait for all jobs matching a prefix, do NOT name the waiting job with the same prefix — it will match itself and deadlock.

**Wrong (collect job matches its own dependency pattern):**
```makefile
bsub -q regression -J "$(CPU_NAME)ended" -w "ended($(CPU_NAME)*)" ...
# $(CPU_NAME)ended matches $(CPU_NAME)* → waits for itself, never starts
```

**Right (use a distinct prefix):**
```makefile
bsub -q regression -J "$(CPU_NAME)_collect" -w "ended($(CPU_NAME)*)" ...
# $(CPU_NAME)_collect does NOT match $(CPU_NAME)*
```

### Step 8: `[: missing ']'` — look for missing `&&`

When you see `then [ "$x" = "0" ] cmd`, the `[` and `cmd` need `&&` between them:

```makefile
# Wrong
then [ "$$errorf" = "0" ] awk '...' >> out; \

# Right
then [ "$$errorf" = "0" ] && awk '...' >> out; \
```

### Step 9: `$(...)` command substitution vs `${...}` variable expansion

In shell (and Makefile recipes), `$(...)` and `${...}` are fundamentally different:

| Syntax | Meaning | Shell example |
|--------|---------|---------------|
| `$var` / `${var}` | **Variable expansion** — substitute the value of `var` | `cat "$CASEFILE"` |
| `$(cmd)` | **Command substitution** — execute `cmd`, substitute its output | `for f in $(cat list.txt)` |

**Bug pattern — uses `$(var)` where `${var}` was intended:**

```bash
# Wrong: $(CASEFILE) tries to run a command named "CASEFILE"
for test in $(cat $(CASEFILE)); do
echo $(cat $(CASEFILE))
```

```bash
# Right: "$CASEFILE" or "${CASEFILE}" for variable expansion
for test in $(cat "$CASEFILE"); do
echo $(cat "$CASEFILE")
```

The loop produces zero iterations because `$(CASEFILE)` runs a non-existent command (empty output), so `cat` gets no filename argument and reads from stdin. Meanwhile `[ -n "$CASEFILE" ]` still passes — the variable IS non-empty. This mismatch (check passes, loop doesn't run) is the diagnostic signal.

**Variant: `$$var` when you want the variable, not the PID:**

```bash
# Wrong: $$ expands to shell PID, $test is the variable
echo "Submitting $$test ..."

# Right:
echo "Submitting $test ..."
```

## Common Error → Fix Table

| Error | Cause | Fix |
| :-- | :-- | :-- |
| `unexpected end of file` | Missing `\` on some continuation line | Add `\` to all lines in block except last |
| `syntax error near ';'` | `>> ;` — redirect target variable is empty | Check `$(PASSFILE)` etc. are defined |
| `[: missing ']'` | `[ ... ] cmd` missing `&&` | Add `&&` between `]` and next command |
| ANSI colors show as literal text | `sed` doesn't expand `\033` | Use `awk` instead of `sed` |
| `if grep \| sed` always true | Pipeline exit = last command (sed always 0) | Separate pipeline from `if`, use `[ -s file ]` |
| Shell vars empty in recipe | `$var` expanded by Make | Use `$$var` |
| `find -name "$$case"` returns nothing | Trailing `\r` or space in case names from file | Pipe through `tr -d ' \r'` |
| `tee` swallows command exit code | Pipeline exit = last command (tee always 0) | Append `; exit $${PIPESTATUS[0]}` |
| bsub wait job never starts | Job name matches its own `-w` dependency pattern | Use distinct prefix for collect job |
| `awk: $0` becomes Make target name | `$0` is Make auto-var | Use `$$0` in awk |
| `for` loop never iterates but `[ -n "$VAR" ]` passes | `$(VAR)` used as command substitution instead of `$VAR` | Use `$VAR` or `"$VAR"` for variable expansion |
| `$$test` prints PID instead of loop variable | `$$` is shell PID, `$test` is the variable | Use `$test` or `${test}` |

## Reference

See `ansiesc-vim-install.md` for offline installation of the AnsiEsc.vim plugin on CentOS 7 (required to render ANSI colors in vim).
