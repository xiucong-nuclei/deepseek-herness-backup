# Programmatic RST: grid tables with vertical cell spans + ASCII-safe generation

Patterns from generating a databook RST file (feature-area tables) from a
synthesis CSV via a Python script. Reusable whenever RST must be emitted from
code (CSV → databook tables, config listings, etc.).

## Grid table with a vertically-merged cell (rowspan)

The databook feature table has the `Feature` column spanning 2 physical rows
per record (row 1 = `:ref:` link, row 2 = area value), while the other columns
split into two stacked single-row cells. This is a rowspan=2 grid table.

Rendering rules that keep docutils/Sphinx happy:
- Each logical record = 2 grid content rows. A spanning cell's text goes on the
  first row; the second row has an empty string in that column.
- Column width = max length of any cell line in that column (Python `len()`).
- Content row format: `'|' + '|'.join(' ' + text.ljust(w) + ' ' for w) + '|'`.
  Border width for column of width `w` is `w+2` dashes.
- On a **divider line that a spanning cell crosses**, that column's block is
  SPACES (not dashes) and its left boundary is `|` (not `+`). Internal boundary
  between two adjacent spanning columns is `|`; otherwise `+`. Only the
  spanning column is blanked on that divider; others stay dashed with `+`.

Mini algorithm:
```
def border(widths, spanned):        # spanned = set of cols crossing this divider
    b = [('|' if 0 in spanned else '+')]
    for c in range(1, len(widths)):
        b.append('|' if ((c-1) in spanned and c in spanned) else '+')
    b.append('|' if (len(widths)-1) in spanned else '+')
    out = b[0]
    for c in range(len(widths)):
        out += (' ' if c in spanned else '-') * (widths[c]+2) + b[c+1]
    return out
```

## Title underline length must equal title length

Emit `adornment * len(title)` (e.g. `'#' * len('isa_b.v')`). A short underline
is a docutils error; an over-long one is tolerated but sloppy. See the
adornment-hierarchy pitfall in the main SKILL.md — keep same-depth headings on
the SAME adornment.

## Keep generated-content scripts pure ASCII

Hard requirement on this user's scripts (they reject non-ASCII, asked 3x). Two
ways to emit non-ASCII into the OUTPUT while the `.py` source stays ASCII:

1. **Unicode escapes**: `µm²` (micro + superscript two) → `'\u00b5m\u00b2'` in
   the source. The file is pure ASCII (backslash-u...), Python decodes it to
   the real character at runtime. Verify with `grep -nP '[^\x00-\x7F]' file.py`
   → must return nothing.
2. **Chinese/other prose in an external template**: if the generated content
   itself must be Chinese (a draft that gets spec-trans'd later), keep it in a
   separate `.rst`/`.txt` template the script reads (detect encoding), NOT in
   the `.py`. Once the prose is finalized to English, inline it back as an
   ASCII constant and drop the template.

Unicode characters like `µ` (U+00B5) and `²` (U+00B2) are single-width, so
swapping `um2` → `µm²` does not break grid-table column alignment.

## Related

- Grid-table indentation/`.. table::` pitfalls: see main SKILL.md Tables section.
- Excel → RST conversion: `references/xlsx-to-rst-conversion.md`.
