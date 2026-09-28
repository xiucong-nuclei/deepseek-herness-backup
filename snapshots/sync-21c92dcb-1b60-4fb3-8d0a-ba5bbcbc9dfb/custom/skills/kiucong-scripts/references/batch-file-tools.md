# Batch File Tools (paste-friendly stdin, CSV-driven generation)

Absorbed from the former `batch-file-tools` skill. Patterns and reference scripts
for batch file operations driven by tabular or newline-separated text input
(CSV columns, spreadsheet paste, etc.).

## When to Use

- User needs to create many files from a list of names (pasted from CSV/Excel)
- User needs to generate config/module files driven by a CSV manifest
- User pastes multi-line content into terminal and shell auto-executes on newlines

## Paste-Friendly Stdin Pattern

**Problem:** When the user pastes newline-separated content into the terminal after
running a script, the shell interprets `\n` as Enter and executes partial commands
before the script's `sys.stdin.read()` ever gets the data.

**Solution:** Use `input()` in a `while` loop. Each pasted line is consumed by Python
as a line separator — the shell never sees them. Terminate with an empty line (just
press Enter).

```python
lines = []
while True:
    try:
        line = input()
    except (EOFError, KeyboardInterrupt):
        break
    if not line.strip():
        break
    lines.append(line.strip())
```

This beats `sys.stdin.read()` (requires Ctrl+D, which clashes with copy) and heredoc
(requires user to type `<< 'EOF'`).

## Reference Scripts (moved into this skill)

- `scripts/touchs` — Batch `touch` files from pasted newline-separated names. Usage:
  run `touchs`, paste, empty line to finish.
- `scripts/gen_syn_config.py` — Generate Verilog config files and `.list` manifests
  from a CSV. See `references/gen-syn-config.md`.
- `references/gen-syn-config.md` — Detailed docs for the CSV-driven config generator
  (format, output, chain dependencies).

## Pitfalls

- **Clipboard reading needs X11** — `xclip`/`xsel` require `DISPLAY`. On
  headless/SSH servers, fall back to the paste-friendly stdin pattern.
- **`Ctrl+C` in terminal = SIGINT** — when the system copy shortcut is also `Ctrl+C`,
  use `Ctrl+Shift+C` for terminal copy, or avoid stdin designs that need Ctrl+D (EOF)
  to terminate.
