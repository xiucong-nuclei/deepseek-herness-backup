# xlsx → RST Conversion Recipe (merge-aware, translated)

Reliable flow for turning a spreadsheet (e.g. an instruction-execution-time table) into a
spec-style RST doc with per-extension sections and intros. Produced while converting an
N300 instruction-latency workbook; verified zero residual CJK before delivery.

## 1. Merge-aware cell reader

openpyxl stores a merged cell's value only at the top-left; other cells in the range read
as `None`. Build a grid dict and propagate the top-left value to every cell in each merged
range:

```python
import openpyxl, warnings
warnings.filterwarnings('ignore')
wb = openpyxl.load_workbook(SRC, data_only=True)

def sheet_reader(ws):
    grid = {}
    for row in ws.iter_rows():
        for c in row:
            grid[(c.row, c.column)] = c.value
    for mr in ws.merged_cells.ranges:
        tlrow, tlcol = mr.min_row, mr.min_col
        val = grid.get((tlrow, tlcol))
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                grid[(r, c)] = val
    return grid
```

The grouping column (e.g. `指令类型`) is typically one big vertical merge per extension
group; this reader naturally forward-fills it per group. Branch rows whose latency AND
throughput live in one `C:D` merged range also resolve correctly (both columns get the same
text) — which you'd otherwise misread as empty throughput.

## 2. Translation

Keep a `TRANS` dict keyed by **normalized** cell text (`' '.join(value.split())` collapses
newlines/multiple spaces). Two distinct branch-description variants with/without a space
(`为2 预测错误` vs `为2预测错误`) need **separate keys** — normalize alone won't merge them.
Fall back to a range regex `^(\d+)[~-](\d+)$` → `"X to Y"` for latency cells like `2~4`,
`16-19`, `32-35`. Literal extension/instruction names stay as-is; instruction mnemonics get
wrapped in RST backticks (`` ``LUI`` ``).

## 3. Normalization edits to apply (flag each to the user)

- Unify case/naming within a group (e.g. all half-precision mnemonics uppercase `H_*`).
- Delete duplicate instruction rows (e.g. repeated `C.FSWSP`).
- Fix obvious typos (e.g. `H_SUB` → `H_FSUB`; a `ZK` label that is really `H_FDIV`).

## 4. Rendering the grouping column (merged-cell mirror)

`.. list-table::` has no merged cells, so mirror the source merge: type value on the first
row of each group, `''` on continuation rows. `None` → `—` only for genuinely-missing data.

```python
itype = TYPE_BY_TITLE.get(sec['title'], '')
for r_i, row in enumerate(sec['rows']):
    cells = [itype if r_i == 0 else ''] + [c if c is not None else '—' for c in row]
```

## 5. Verification (mandatory before delivery)

Scan the output for residual CJK so no untranslated cell ships:

```python
import re
t = open(OUT, encoding='utf-8').read()
assert not re.findall(r'[\u4e00-\u9fff]', t)   # 0 => clean
```

Also grep for the edited rows (`grep -c '``C.FSWSP``'` should be 1, `H_SUB` absent).
