# Databook Table → RST (spreadsheet conversion, full guide)

Absorbed from the former `databook-table-rst` skill. Reusable workflow for converting
a spreadsheet of tabular data (instruction lists, config options, feature tables)
into a Nuclei databook `.rst` section. Table cells are written in spec-style English;
use the user-owned `spec-trans` skill for any Chinese prose needing the full
spec-translation conventions. This reference covers the **mechanical table→RST path**
and the pitfalls that appear when doing it at scale.

## When to Use

- User hands you an `.xlsx`/`.csv` of instructions, options, or features and asks for
  a databook `.rst` (tables + short intro per section).
- Splitting one workbook into per-extension/per-feature sections with an intro before
  each.

## Workflow

1. **Merge-aware cell reading.** Dense tables rely on merged cells; a value exists only
   at the top-left cell of a merged range (every other cell reads `None`). Propagate
   before reading so you don't lose values or misread empty cells:

   ```python
   import openpyxl, warnings; warnings.filterwarnings('ignore')
   wb = openpyxl.load_workbook(path, data_only=True)
   grid = {(c.row, c.column): c.value for ws in wb.worksheets for row in ws.iter_rows() for c in row}
   for ws in wb.worksheets:
       for mr in ws.merged_cells.ranges:
           v = grid.get((mr.min_row, mr.min_col))
           for r in range(mr.min_row, mr.max_row+1):
               for c in range(mr.min_col, mr.max_col+1):
                   grid[(r, c)] = v
   ```

2. **Forward-fill the group/type column** (e.g. 指令类型 = RV32I/RV32M/RVC). In these
   sheets it is one big merged block, so step 1 already fills it. Group rows by type
   and emit one section per type. Skip a type block when a dedicated sheet covers the
   same extension (dedupe, don't double-list).

3. **Translate latency/throughput cells** with an exact-match dict. Numeric cells pass
   through; ranges `N~M` / `N-M` → `N to M`; `1/2/3cycle可配置` → `1, 2, or 3 cycles
   (configurable)`; `由于是状态机实现，吞吐率与执行延迟一样` → `Same as latency
   (state-machine implementation)`; `阻塞执行` → `Stalls the pipeline`; `不可预期` →
   `Unpredictable`. Mnemonics are already English — wrap in backticks (monospace).

4. **Render `.. list-table::`** header `Instruction | Execute Latency | Execute
   Throughput`, one `* - ``MNEM`` / - value / - value` row per instruction. Prepend a
   short spec intro per section. Add a leading section note defining latency/throughput
   and the `—` meaning.

## Section intros: LEAD IN, do NOT summarize (hard user requirement)

User correction (verbatim): *"这段内容不是对表格的总结，而是能够自然的引出这个表格"*
(the intro must naturally introduce the table, not summarize it). Do NOT restate the
table's numeric content in the intro — no "loads take 2 cycles", no "FDIV.S is 16-19".
That duplicates the table. Pattern — one sentence naming what the extension provides,
then a pointer at the table:

> The RV32M extension adds integer multiply and divide instructions. The following
> table lists the execute latency and throughput of each RV32M instruction.

Structural/column information IS acceptable (it is not a data restatement): e.g. an
RV32F table's `Functional Unit` column meaning (`FSIM`/`FMIS`) earns one sentence.
Keep it to 1-2 sentences. Concrete reusable lead-ins for the standard extension sets
live in `lead-in-intros.md` (in this skill's references).

## Defining latency & throughput in the intro (user-crafted definition)

User found the generic "throughput = instructions issued per cycle" phrasing unclear
and hand-built the precise definition used in the doc. Capture it:

- **Execute latency** = number of cycles from instruction issue to the result being
  available; it describes how long a single instruction takes.
- **Execute throughput** = the RESULT RATE when the SAME instruction runs back to
  back in the pipeline. Throughput 1 → the pipeline produces a result every cycle.
  Throughput 2 → the pipeline inserts a bubble and produces a result every two
  cycles. Higher values follow the same rule. It is independent of latency (a
  pipelined unit can have latency >1 yet throughput 1).
- **When throughput equals execute latency** → the unit is NOT pipelined (state
  machine such as divide/square-root); it returns one result per latency period.

Structure the doc intro as 3-4 short paragraphs: latency → throughput → the
equals-latency exception → a "values marked as configurable depend on the
corresponding option" note.

## Pitfalls (hit in real use)

- **Whitespace variants break exact-match dicts.** Identical Chinese can differ only
  by a space (`为2 预测错误` vs `为2预测错误`). `' '.join(s.split())` does NOT merge
  them, so the lookup silently misses and raw Chinese leaks into the RST. Fix: keep
  every variant as its own key, AND verify output by scanning for residual CJK:
  ```python
  import re; assert not re.findall(r'[\u4e00-\u9fff]+', output)
  ```
- **Empty throughput cells are data-dependent, not a typo.** Branch rows often leave
  throughput blank (depends on prediction). Do NOT invent `1`. Render `—` and add a
  `.. note::` that `—` means data-dependent / unspecified. Only branch rows whose
  latency cell is merged `C:D` carry the prediction description in BOTH columns.
- **Mislabeled row, correct by context.** A dedicated extension sheet may carry a
  garbled row label (half-precision sheet labels the divide row `ZK` when the
  following `H_FSQRT` + state-machine note make clear it is `H_FDIV`). Correct it and
  flag the change to the user; do not silently choose.
- **Two sheets cover one extension.** e.g. a combined `RV32IMAC` sheet lists ZFH at
  the bottom (lowercase `h_*`) AND a dedicated `半精度浮点指令` sheet lists the same
  set (uppercase `H_*`). Use the dedicated sheet; drop the embedded block.
- **RST table forms — the user distinguishes them.** RST has three: the
  `.. list-table::` directive, the literal **grid table** (`+===+` bordered), and the
  simple table (`====`). When the user says "table 格式" they mean the literal grid
  table, NOT the list-table directive. Ask which they want, or state the choice,
  before generating. Docutils validates all three (`publish_doctree`).
- **RST cannot do TRUE merged cells** (grid AND list-table — the RST spec forbids cell
  spanning). A merged grouping column is only representable by putting the value on
  the group's first row and leaving continuation cells blank. Grid tables with long
  cell text (branch/div descriptions) get extremely wide — offer to shorten or
  footnote them.
- **Grouping/type column is redundant once split per-extension.** If each section is
  one extension (the section title already names it), the `指令类型`/grouping column
  adds nothing — drop it. User: "因为我们是完全按照扩展写的表格，所以可以不写第一列".
  Keep the column only when a single table mirrors a whole sheet that has internal
  type groups.

## Nuclei conventions confirmed

- **Half-precision (RV32_ZFH) mnemonics use UPPERCASE** `H_*` (`H_FDIV`, `H_FSQRT`,
  `H_FSGNJ`, `H_FMADD`, `H_FCVT_WH`), NOT lowercase `h_*` — user: "统一用大写"
  (standardize on uppercase). Normalize all ZFH names to uppercase in databook output.
- Config names stay verbatim in backticks: `CFG_2CYC_MUL`, `CFG_HAS_ADV_DIV`,
  `N300_XCYC_FPU`, `N300_HAS_VPU`.
- **Section titles: uniform `{Ext} Extension`.** When the doc is one section per
  extension, title them `RV32F Extension`, `P Extension`, `Zc Extension`, etc. —
  user chose this over descriptive parentheticals like `RV32F (Single-Precision
  Floating-Point)`. Use RISC-V extension case (uppercase `Zc`/`Zcmp`/`Zcmt`).
- Branch description spec phrasing: `1 if correctly predicted not-taken; 1 if
  correctly predicted taken to an aligned address, 2 if misaligned; a misprediction
  stalls the pipeline`.

## Relation to spec-trans

`spec-trans` (user-owned, not curator-editable) governs Chinese→spec-English prose and
its extensive Nuclei terminology table. Use it for paragraphs and free-text cells.
This reference handles the table-extraction and cell-translation path around it.
