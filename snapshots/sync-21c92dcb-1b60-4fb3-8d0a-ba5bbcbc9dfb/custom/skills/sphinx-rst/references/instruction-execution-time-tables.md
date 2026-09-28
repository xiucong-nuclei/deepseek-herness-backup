# Nuclei Instruction-Execution-Time Tables (xlsx → RST, RV32/RV64 split)

Class-level recipe for generating the Nuclei instruction execution time chapter from the
vendor `*_指令执行时间.xlsx` workbook. Used for N300, then N600/N900 (same architecture,
so one N900-generated chapter feeds the N600 databook). Complements
`xlsx-to-rst-conversion.md` (generic merge-aware recipe) — this file is the
instruction-execution-time-specific semantic layer.

## Output shape: RV32/RV64 4-column split (user-approved)

Each extension gets ONE table, not two. Header distinguishes the XLENs explicitly —
the 4 data columns are `RV32 Execute Latency | RV32 Execute Throughput | RV64 Execute
Latency | RV64 Execute Throughput` (NOT bare `Execute Latency` repeated — indistinguishable).

```
Instruction | RV32 Execute Latency | RV32 Execute Throughput | RV64 Execute Latency | RV64 Execute Throughput
```

- Section per extension, named `RV64{letter} Extension` (`RV64I`, `RV64A`, `RV64M`, `RV64B`,
  `RV64K`, `RV64P`, `RV64F`, `RV64D`, `RV64_ZFH`) plus `RVC Extension` (compressed, no XLEN split).
- Section lead-in intro sentence before each table (自然引出表, not a summary of values).
- **Every table gets a caption name** (user requirement): `.. list-table:: <Extension> ... Execution Time`.
  e.g. `.. list-table:: RV64I Base Integer Instruction Execution Time`, `RV64A Atomic`,
  `RVC Compressed`, `RV64M Multiply/Divide`, `RV64B Bit-Manipulation`, `RV64K Scalar
  Cryptography`, `RV64P DSP ... (RV32/RV64 Instruction Set)`, `RV64F Single-Precision`,
  `RV64D Double-Precision`, `RV64_ZFH Half-Precision`.
- `.. note::` defines the sentinel phrasings: ``---`` = data-dependent/unspecified,
  ``Stalls the pipeline`` = instruction blocks the pipeline until complete.

## Uniform special-value mapping — do NOT read raw cells anywhere

The `阻塞执行 → Stalls the pipeline` / `不可预期 → Unpredictable` / `\ → ---` mapping MUST be
applied on **every sheet**, including the numeric ones. Real bug: the first generator read
base/A/M/B cells with bare `str()` (not the mapping), so `阻塞执行`/`不可预期` from base
(`FENCE.I ECALL EBREAK URET SRET MRET WFI`) leaked verbatim into the RST and failed the
no-Chinese check. Route all raw cells through one `map_val()` (or equivalent) and verify
zero CJK before delivery: `grep -cP '[\x{4e00}-\x{9fff}]' out.rst` must return 0.

## Special-value mappings (cell text → RST phrasing)

| Raw cell | RST output |
|---|---|
| `\` (backslash) | ``---`` (instruction absent in that XLEN) |
| `阻塞执行` | `Stalls the pipeline` |
| `不可预期` | `Unpredictable` |
| latency cell == throughput cell (e.g. DIV 18/18, FDIV.S 20/20) | latency = the number; throughput = `Same as latency (state-machine implementation)` |
| ZFH `FDIV.H`/`FSQRT.H` | latency `5~7` / `5~11`; throughput = the full state-machine note: `Same as latency (state-machine implementation). The pipeline ie->ie2->le1->le2->le3 iterates at ie2; div iterates up to 3 times, sqrt up to 7 times.` (the xlsx note cell carries this verbatim) |
| `5~7` / `2~4` style ranges | keep or map to `X to Y` per the generic recipe |

## Per-extension data handling (the pitfalls)

**RV64-only instructions → `---` in the RV32 columns.** The workbook often fills RV32 cells
with the RV64 value anyway, so you MUST override by knowledge, not by reading the sheet:
- RV64I: `LWU LD SD` + `*W` (ADDIW SLLIW SRLIW SRAIW ADDW SUBW SLLW SRLW SRAW) → RV32 `---`
- RV64A: `LR.D SC.D AMO*.D` → RV32 `---`
- RV64M: `MULW DIVW DIVUW REMW REMUW` → RV32 `---` (note DIVW lat 18 RV32 / 34 RV64 per sheet, but RV32 is really absent)
- RV64B: `*U.W` (ADD.UW SH1ADD.UW SH2ADD.UW SH3ADD.UW SLLI.UW) + `*W` (CLZW CTZW CPOPW ROLW RORW RORIW) → RV32 `---`
- K: `ZIP UNZIP AES32*` are RV32-only; `AES64*` are RV64-only.

**K extension — YES/NO support matrix, not latency cells.** Sheet columns are
`RV32 | RV64 | 执行延时 | 执行吞吐率` with `YES`/`NO`. Convert: YES → the latency/thruput
value, NO → `---`. Duplicate instruction rows with contradictory YES/NO (RORI, REV8,
AES64KS1I, AES64KS2 appear twice) must be **merged by union of support** — technically these
exist in both XLEN (per B extension / RISC-V Zk/Zbkb), so prefer the row that says YES/YES.

**P extension — RV32 and RV64 are DIFFERENT instruction sets → split into TWO tables.**
The sheet is a side-by-side two-column layout (`RV32 instr | RV64 instr`) with disjoint
mnemonics (e.g. `ADD16` is RV32, `ADD32` is RV64). User correction: do NOT merge into one
4-column table with `---` placeholders — emit **two separate 3-column tables**, one per
instruction set (`RV64P DSP Instruction Execution Time (RV32 Instruction Set)` and
`(RV64 Instruction Set)`), each `Instruction | Execute Latency | Execute Throughput`.
This keeps the table clean when the two sets share no mnemonics. (First draft merged them
into one 4-col table; user rejected and asked for the split.)

**F / D / ZFH — shared left-column instructions apply to BOTH XLENs.** The sheet is
`RV32 instr | RV32 lat/thr | RV64 instr | lat/thr`: the left column holds the base/shared
instructions (FLW, FMADD.S, FADD.S …) that exist in both RV32 and RV64 with the SAME latency,
while only the right column is RV64-only additions (FCVT.L.S, FCVT.LU.S …). So left-column
rows → RV32 = RV64 = same value (NOT RV32-only). Right-column rows → RV32 `---`, RV64 = value.
Getting this wrong silently marks every base FP instruction as RV32-only.

**C extension — no XLEN split.** Single 3-column table (Instruction | Latency | Throughput).
Dedupe repeated `C.FSWSP`.

## Special-flag rows

- `WFI` → `Unpredictable` (both XLEN, both columns).
- `FENCE.I ECALL EBREAK URET SRET MRET` → `Stalls the pipeline`.
- `C.EBREAK`: latency = `Stalls the pipeline`, throughput = 1 (sheet keeps thruput at 1).

## Recommended flow

Generate programmatically with openpyxl (hundreds of P rows = not hand-typed). Parse each
sheet, apply the per-extension RV64-only/merge rules above, emit `.. list-table::` blocks.
Then validate with docutils `publish_doctree` (catches malformed tables) and `git commit`
into `~/deliverables` before delivery. Output file convention:
`n600_instruction_execution_time.rst` (this VM; the databook on the syn server consumes it).
