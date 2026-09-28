# Makefile Dynamic Targets with $(MAKECMDGOALS)

## The Pattern

Use `$(MAKECMDGOALS)` to create Makefile targets where the **target name is a fixed verb** and the **argument is a free-form name** (e.g. a test case name).

```makefile
# Top-level: silence Make's "no rule to make target" for the dynamic argument
# Replace 'getpng' with your actual target name
ifeq ($(firstword $(MAKECMDGOALS)),getpng)
TARGET_ARG := $(word 2, $(MAKECMDGOALS))
ifneq ($(TARGET_ARG), )
$(eval $(TARGET_ARG):;:@)
endif
endif

# The actual target
getpng:
	@case_dir=$$(find $(SOME_ROOT)/path/to/cases -type d -name "$(TARGET_ARG)" 2>/dev/null | head -1); \
	if [ -n "$$case_dir" ]; then \
	    echo "Found: $$case_dir"; \
	    cp /some/source/*.png "$$case_dir/output.png"; \
	else \
	    echo "Error: '$(TARGET_ARG)' not found"; \
	    exit 1; \
	fi
```

## How It Works

```
$ make getpng my_test_case
              │          │
              │          └── word 2 → TARGET_ARG = "my_test_case"
              │
              └── firstword → triggers the ifeq block
```

1. **Parse phase**: Make evaluates `ifeq` — sees `firstword = getpng`, extracts `word 2` as `TARGET_ARG`
2. **`$(eval ...)`**: Creates an empty target rule `my_test_case:;:@` so Make doesn't error
3. **Execution**: The `getpng` target runs, shell uses `$(TARGET_ARG)` to find the case directory

## Key Requirements

| Element | Must be | Why |
|---------|---------|-----|
| `ifeq` block | **Before** any target rules (top-level) | Make evaluates conditionals during parse phase |
| `$(eval ...)` | Inside the `ifeq` block | Creates a dummy rule before Make resolves all targets |
| `%:` catch-all | **Last line** of Makefile (if used) | Only catches truly unknown targets |
| Target content | Uses `$(TARGET_ARG)` (not `$@`) | `$@` is the actual target name (`getpng`), not the argument |

## Alternative: Catch-All Pattern (less safe)

```makefile
# LAST line of Makefile — catches ALL undefined targets
%:
	@case_dir=$$(find $(SOME_ROOT)/path -type d -name "$@" 2>/dev/null | head -1); \
	if [ -n "$$case_dir" ]; then \
	    cp ... "$$case_dir/output.png"; \
	else \
	    echo "Unknown target: $@"; \
	    exit 1; \
	fi
```

**Downside**: A typo like `makr run` instead of `make run` would be silently swallowed. Prefer the `ifeq` + `$(MAKECMDGOALS)` pattern.

## Common Pitfalls

### Quote Mismatch in Recipe

```makefile
# ❌ Wrong — missing closing quote
	echo "Copying output.png to $(TARGET_ARG); \

# ✅ Correct
	echo "Copying output.png to $(TARGET_ARG)"; \
```

Make concatenates continued lines (`\` at end) into a single shell command. An unclosed quote anywhere in the chain causes `unexpected EOF while looking for matching '"'`.

### Tab vs Spaces

Makefile recipes require **Tab** (ASCII 0x09) at the start of each command line. Spaces produce `*** missing separator. Stop.`

### MAKECMDGOALS Only Contains One Word

If user types just `make getpng` with no argument:
- `$(word 2, ...)` is empty
- The `ifneq ($(TARGET_ARG), )` guard prevents the `$(eval ...)` from creating a garbage target
- The target runs but `$(TARGET_ARG)` is empty → `find -name ""` finds nothing → error

### Nested Make Calls

`$(MAKECMDGOALS)` is global. If a target internally calls `$(MAKE)`, the inner invocation inherits the parent's MAKECMDGOALS. Use `$(filter-out $@,$(MAKECMDGOALS))` to extract the argument safely when nesting.

## Real-World Use Case: Test Case Output Pipeline

```
$ make getpng cpufeat_amo_test

  1. Search $(SDK)/application/cpu_features/**/cpufeat_amo_test/
  2. Copy /external/output/*.png → found_dir/output.png
  3. (Later) Python script reads output.png → generates .rst doc with image
```

This connects simulation output → documentation in one command.

---

## Related Pattern: Verification Test Result Collection (`collect_pass`)

A second common pattern in Nuclei SDK verification: a **static target** that iterates over a case list file and collects PASS + feature lines from result logs.

### Target Structure

```makefile
collect_pass:
	@echo "Starting collect pass result..."
	@if [ ! -f "$(CASEFILE)" ] || [ ! -s "$(CASEFILE)" ]; then \
	    echo "Error: $(CASEFILE) not found or empty!"; \
	    exit 1; \
	fi
	@rm -rf $(PASSFILE);
	@i=1;
	for test in $(cat $(CASEFILE)); do \
	    echo "$$i. $$test " >> $(PASSFILE); \
	    grep "^===.*PASS" "result/$$test.log" >> $(PASSFILE) 2>/dev/null || true; \
	    grep -i "feature" "result/$$test.log" | grep "|" | sed 's/.*| *//' >> $(PASSFILE) 2>/dev/null || true; \
	    printf "\n" >> $(PASSFILE); \
	    i=$$(($$i+1)); \
	done;
```

### What It Does

| Line | Purpose |
|------|---------|
| `if [ ! -f... ]` | Guard: abort if CASEFILE missing or empty |
| `rm -rf $(PASSFILE)` | Start fresh output |
| `echo "$$i. $$test "` | Numbered case name header |
| `grep "^===.*PASS" ... \|\| true` | Collect PASS lines from result logs |
| `grep -i "feature" ... \| grep "\|" \| sed 's/.*\| *//'` | **Collect feature requirement lines**: strips `filename:line:col: error:` prefix and `line_num \|` prefix, keeping only `#error "message"` |
| `printf "\n"` | Blank line between cases |

### The Feature Grep Pipeline Explained

Result log format from `check_cpufeature.h` compilation:
```
check_cpufeature.h:20:2: error: #error "This case require L2 feature."
20 | #error "This case require L2 feature."
```

The pipeline:
```
grep -i "feature"               → keep both lines (contain "feature")
  | grep "|"                    → keep only the second line (has "|")
  | sed 's/.*| *//'             → strip "20 | " prefix → "#error ..."
  >> $(PASSFILE)
```

### Variables

| Variable | Typical Value | Description |
|----------|---------------|-------------|
| `$(CASEFILE)` | `pass_case.list` | List of test case names, one per line |
| `$(PASSFILE)` | `pass.result` | Output file with collected results |
| `result/$$test.log` | `result/cpufeat_amo_test.log` | Per-case simulation result log |
