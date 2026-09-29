---
name: debugging
description: '4-phase root-cause debugging; playbooks: Makefile shell & RISC-V CPU boot hangs.'
metadata:
  hermes:
    tags:
    - debugging
    - troubleshooting
    - root-cause
    - makefile
    - riscv
    - cpu
    - boot
    - verdi
    category: software-development
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Debugging (Systematic Root-Cause Method + Domain Playbooks)

Class-level debugging skill: the 4-phase root-cause method (never fix before
you understand the bug), plus the accumulated playbooks for the domains this
machine actually debugs — Makefile recipes with embedded shell, and RISC-V CPU
boot-time hangs. Absorbs the former `systematic-debugging`,
`makefile-shell-debugging`, and `riscv-cpu-boot-debug` skills.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Random fixes waste time and create new bugs; quick patches mask underlying
issues. If you haven't completed Phase 1, you cannot propose fixes.

## The Four Phases

### Phase 1 — Root Cause Investigation
1. **Read error messages carefully** — stack traces, line numbers, error codes
   often contain the exact solution. Find the error string in the codebase.
2. **Reproduce consistently** — exact steps, every time? Not reproducible →
   gather more data, don't guess.
3. **Check recent changes** — `git log --oneline -10`, `git diff`, `git log -p
   --follow <file>`.
4. **Gather evidence in multi-component systems** — BEFORE proposing fixes,
   add diagnostic instrumentation at each component boundary (log inputs,
   outputs, config/env propagation, state at each layer); run once to find
   WHERE it breaks, then investigate that component.
5. **Trace data flow** — where does the bad value originate? Keep tracing
   upstream to the source; fix at the source, not the symptom.

Completion checklist: errors read, reproduced, changes reviewed, evidence
gathered, problem isolated, root-cause hypothesis formed. **STOP** until you
understand WHY.

### Phase 2 — Pattern Analysis
Find similar WORKING code in the same codebase; read the reference
implementation completely (no skimming); list every difference between
working and broken; understand the dependencies and assumptions.

### Phase 3 — Hypothesis and Testing
Form a SINGLE specific hypothesis ("X is the root cause because Y"); test
with the SMALLEST possible change, one variable at a time; worked → Phase 4,
didn't → new hypothesis (don't stack fixes). When you don't know, say so and
research instead of pretending.

### Phase 4 — Implementation
Create a failing test/reproduction FIRST; implement ONE fix for the root
cause (no "while I'm here" improvements); verify the fix and run the full
suite for regressions.

- **Rule of Three**: 3+ failed fixes = STOP and question the architecture
  (each fix revealing new coupling elsewhere, fixes requiring massive
  refactoring, new symptoms appearing = architectural problem, not a failed
  hypothesis). Discuss with the user before attempt #4.

### Red flags — STOP and return to Phase 1
"Quick fix for now, investigate later" · "Just try changing X" · multiple
changes at once · skipping tests · "It's probably X, let me fix that" ·
proposing fixes before tracing data flow · "one more fix attempt" after 2+.

## Hermes Integration

- **Investigation tools**: `search_files` (trace calls, find error strings),
  `read_file` (line-numbered source), `terminal` (reproduce, git history),
  `web_search`/`web_extract` (research error messages).
- **Multi-component systems** → dispatch an investigation subagent so evidence is
  gathered without fix bias (adapt the delegate_task goal/context):
  ```python
  delegate_task(
      goal="Investigate why [specific test/behavior] fails",
      context="""Follow the systematic-debugging method:
      1. Read the error message carefully
      2. Reproduce the issue
      3. Trace the data flow to find root cause
      4. Report findings — do NOT fix yet
      Error: <paste>  File: <path>  Test command: <exact>""",
      toolsets=['terminal', 'file']
  )
  ```
- **TDD linkage**: Phase 4 starts with a failing test/reproduction (RED), then the
  root-cause fix (GREEN); the test stays as the regression guard.

## Domain Playbook: Makefile Shell Recipes

When a Makefile target uses `\` continuation to embed multi-line shell
scripts, errors are opaque. Triggers: `syntax error near unexpected token`,
`unexpected end of file`, `[: missing ']'`, `/bin/sh` line errors, literal
`\033` ANSI text, pipeline `if` never true, `for` loop never runs while
`[ -n "$VAR" ]` passes.

Top error → fix table (full detail in `references/makefile-recipe-debugging.md`):

| Error | Cause | Fix |
|---|---|---|
| `unexpected end of file` | Missing `\` on a continuation line | `\` on every line except the last |
| `[: missing ']'` | `[ ... ] cmd` without separator | `] && cmd` |
| ANSI shows literal `\033` | `sed` doesn't expand `\033` (CentOS 7) | use `awk '{printf "\033[32m%s\033[0m\n", $$0}'` |
| `if grep \| sed` always true | pipeline exit = LAST command | separate, then `if [ -s tmp ]` |
| Shell vars empty in recipe | `$var` eaten by Make | `$$var` (`$$0` in awk too) |
| `tee` swallows exit code | pipeline exit = tee's 0 | append `; exit $${PIPESTATUS[0]}` |
| `for` never iterates, check passes | `$(VAR)` = command substitution, not variable | use `"$VAR"` |
| `$$test` prints a PID | `$$` = shell PID | `$test` |
| `find -name "$$case"` empty | trailing `\r`/space from file | `tr -d ' \r'` / `xargs` |
| bsub wait job never starts | job name matches its own `-w` pattern | distinct prefix for the collect job |

Start every diagnosis with `make -n <target>` — it prints the ACTUAL
concatenated shell script Make runs, and `line N` errors refer to lines in
that script, not the Makefile.

## Domain Playbook: RISC-V CPU Boot-Time Debugging

When a CPU core is stuck at boot (iaddr frozen, PC not moving — especially
during BSS init or early startup). Full playbook (waveform signals, Verdi
navigation, ecall trap cascade, ECC injection, PMA basics):
`references/riscv-boot-debug-playbook.md`.

**First disambiguate**:

| Observation | Classification | Root cause family |
|---|---|---|
| iaddr cycles 2-4 addresses (0x518→0x51c→...) | Software infinite loop | bounds mismatch, wrap overflow |
| iaddr on ONE address cycle after cycle | Hardware stall | bus no-response, LSU stall, I-Cache miss, clock/reset |
| iaddr = 0 / 0xFFFFFFFF / unmapped | Illegal address | bad vector, missing memory map |

- **Software loop** → BSS zero-init loop: capture `a0` (`_bss_start`) and `a1`
  (`_end`) in the register file. `a1` = 0xFFFFFFFF → linker script `_end`
  after unmapped memory; `a0` wraps 0xFFFFFFFC→0 → `addi` overflow with
  unsigned `bltu`; `a0 > a1` at start → section ordering. Nuclei SDK uses
  `_end` (GNU LD built-in, always exists) not `_bss_end` — linker-agnostic.
- **Hardware stall** → check `clk` toggling and `rst_n` first, then the fetch
  handshake: `ibus_arvalid=1, arready=0` for >10 cycles = bus slave not
  responding; `arvalid=0` = fetch unit stalled by backend. Backend stall
  propagation: `lsu_stall`/`load_wait` (most common — a single `sw` in the
  BSS loop can stall), `fetch_pc_stall`, `store_buffer_full`; check `dtlb_miss`
  and data-bus `awready`/`wready`.
- **Trap cascade** (ecall → mcause=9 → continuous mcause=2): ecall ALWAYS
  jumps to `mtvec` (no mode makes it fall through). If `mtvec` is 0 (ecall
  before `ECLIC_Interrupt_Init()`) or points at .bss/garbage, the handler
  fetches junk → mcause=2 → mtvec again → infinite loop. Check `mtvec`
  value + MODE bits (CLIC vectored = low bits `11`), `mepc`, `mtval`.
- **Verdi**: register file under `u_exu → u_exu_alu → u_exu_alu_rgr`
  (search `*rgr*`); CSR under `u_exu → u_csr`; `mtval` = instruction encoding
  for mcause=2 (0 → fetch from uninitialized memory), virtual address for
  5/7, 0 for ecall. `.fsdb` "empty file"/"Wrong file type" = sim crashed
  before dump (disk quota) or `$fsdbDumpvars` missing.
- **ECC injection** (MECC_CODE is an XOR mask: `0x01` flips ECC bit 0 →
  single-bit error): read `MECC_CODE` BEFORE any `csrc` (csrc clears the
  latch); CSR_MCACHE_CTL/MECC_CODE are M-mode only — in S/U-mode writes
  silently fail (check `cpu_mode` / `mstatus.MPP`); use fresh trampoline
  addresses or page-separated code so the cache actually misses.

## Reference Files

| File | Content |
|---|---|
| `references/riscv-embedded-debugging.md` | RISC-V/Nuclei embedded pitfalls (Zcmt jump tables, JVT CSR, toolchain flags) |
| `references/riscv-boot-debug-playbook.md` | Full RISC-V boot-hang playbook (iaddr classification, BSS loop, trap cascade, ECC, PMA, Verdi) |
| `references/makefile-recipe-debugging.md` | Full Makefile shell-recipe debugging guide + error→fix table |
| `references/n300-bss-loop-case-study.md` | N300 BSS loop freeze case study |
| `references/trap-cascade-n900-case-study.md` | N900 ecall trap cascade case study |
| `references/hws-dwarf-compatibility.md` | hws/hwsww DWARF 5 → DWARF 4 compatibility fix |
| `references/makefile-dynamic-targets.md` | Makefile dynamic targets via `$(MAKECMDGOALS)` (getpng/run/show) |
| `references/verification-doc-generation.md` | Python + Sphinx RST doc generation from test case dirs |
| `references/amo-type-portability.md` | AMO intrinsic `long *` RV32/RV64 portability trap |
| `references/sphinx-rst-image-path.md` | RST image path handling |
| `references/misaligned-bus-error-debug.md` | Misaligned bus error debug |
| `references/ansiesc-vim-install.md` | Offline AnsiEsc.vim install (CentOS 7) for ANSI rendering in vim |
