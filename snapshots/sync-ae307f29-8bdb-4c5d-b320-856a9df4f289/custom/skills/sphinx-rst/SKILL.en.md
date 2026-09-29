---
name: sphinx-rst
description: Sphinx/reStructuredText documentation authoring — tables, cross-references, raw directives, inline styling, build troubleshooting, LaTeX/PDF output.
metadata:
  hermes:
    tags:
    - sphinx
    - rst
    - restructuredtext
    - documentation
    - latex
    - pdf
    - cross-reference
    version: 1.0.0
    author: Hermes Agent (from session with kiucong)
    license: MIT
---

# Sphinx / RST Documentation Authoring

Authoring and troubleshooting reStructuredText for Sphinx-based technical documentation (HTML + LaTeX/PDF output). Covers tables, cross-references, `.. raw::` directives, inline code styling, and build fixes.

## When to Use

When the user is:
- Writing or debugging `.rst` source files for Sphinx
- Troubleshooting `make html` / `make latexpdf` build errors or warnings
- Adding cross-file references, tables, raw directives, or custom styling
- Asking about `conf.py` configuration for Sphinx output

## Cross-References

### `:ref:` — label-based (any location)

Define label in target file:
```rst
.. _my-label:

Target Section Title
--------------------
```

Reference from any file:
```rst
详见 :ref:`my-label`
```

- `:ref:` is a **standard Sphinx role** — no extension needed
- Backticks must **touch** the role: `:ref:`my-label`` (no space)
- Label names are global — same syntax for same-file and cross-file
- Target file must be in `toctree`

**Avoid page numbers in PDF:** `:ref:`label`` can render "page X" in LaTeX/PDF output. Use the explicit display-text form to suppress it — Sphinx uses exactly that text as the link, no page info appended:
```rst
:ref:`display text <label>`
```
e.g. `:ref:`isa_b.v <isa_b.v>`` renders just `isa_b.v`, hyperlinked, no page number. Also useful to show a friendlier label than the raw section title.

**Label syntax — single vs double colon:**
- `.. _label:` (single colon) — standard RST target; pure docutils parses it. Side effect: if a heading with the SAME text immediately follows, docutils warns `Duplicate implicit target name` (the heading auto-creates an implicit target with the same name); Sphinx may warn "duplicate label".
- `.. _label::` (double colon) — Sphinx's custom-label form for `:ref:` targets. Pure docutils calls it `malformed hyperlink target`, but Sphinx accepts it and it does not collide with the following heading's implicit target.

Trade-off: single colon is standard and docutils-clean but risks duplicate-target; double colon is Sphinx-specific. Both resolve in Sphinx's `:ref:`.

### `:ref:` needs EXPLICIT labels — not bare section titles

Sphinx's `:ref:` resolves ONLY explicit `.. _label:` targets (or the `autosectionlabel` extension). It does NOT resolve a plain section-title implicit target. Verified with Sphinx 9: `:ref:`isa_b.v <isa_b.v>`` referencing a heading literally titled `isa_b.v` fails with `WARNING: undefined label: 'isa_b.v' [ref.ref]`. If you delete explicit labels to silence duplicate-target noise, the `:ref:` links silently break. Never assume a heading's text is a valid `:ref:` label by itself.

### Label-free section link: plain RST phrase reference `` `text <title>`_ ``

The reliable way to hyperlink a section WITHOUT any explicit label is the standard RST reference, resolved to the heading's implicit anchor:

```rst
See `isa_b.v`_ and `custom text <isa_b.v>`_.
```

Both produce a working anchor link (`href="#isa-b-v"` in HTML), need no `.. _` line, render no page number, and are pure RST (accepted by docutils and Sphinx). The target is the section heading text. Use this form whenever you want label-free in-document jumps.

### Wrapping inline markup across grid-table lines

RST inline markup (backtick refs / interpreted text) CAN span physical lines inside a single grid-table cell; the newline folds to one space in the rendered text. That space is a browser soft-break point, so a long cell name wraps cleanly at the fold:

```rst
| `safety_lockstep_split_
| ioprot <safety_lockstep_split_ioprot.v>`_     (both lines inside one cell)
```

- Plain phrase refs `` `...`_ `` wrap across lines with NO warning.
- `:ref:` wrapped across lines triggers `WARNING: Inline interpreted text or phrase reference start-string without end-string.` — prefer the plain phrase-ref form for wrapped cells.
- To hold a cell at a fixed narrow width, character-wrap the display text (drop a trailing suffix like `.v` first if it buys room). The source column width = widest source line; `:widths:` controls the RENDERED proportions independently, so a source column can be wide (markup overhead) while rendering narrow.

### Underscore `_` phantom-reference gotcha

RST treats an underscore immediately following a word AND followed by whitespace/end-of-line as a **hyperlink reference marker** (`word_` → target `word`). If the target doesn't exist, you get `ERROR: Unknown target name: "word".` These are easy to trigger accidentally and hard to spot because the text looks like ordinary prose/names:

- **A wrapped cell line that ends with `_`** — e.g. char-wrapping `ilm_dlm_sram_64k_addr_ecc` at width 22 yields `ilm_dlm_sram_64k_addr_` (trailing `_`) → phantom reference to `ilm_dlm_sram_64k_addr`.
- **Prose/feature text with `_` before a space** — e.g. `LOCKSTEP+IO_ PROT` (the `IO_ ` is a phantom ref to `lockstep+io`); docutils lowercases the target. This bites in generated intro sentences that interpolate names.

Fixes (combine both):
1. When programmatically wrapping identifier/config names, break ONLY at `_` separators — right after the underscore (line ends with `_`), never at a dot or mid-token. Keep a trailing `.v` together (e.g. `ilm_dlm_sram_64k_addr_` + `ecc.v`). This is the user's confirmed wrapping preference for config names (`dcache32k_prefetch_axi.v` wraps as `dcache32k_prefetch_` + `axi.v`). Apply the per-line backslash-escape (rule 2) to that trailing `_` so RST does not read it as a reference — breaking after `_` is fine as long as the trailing underscore is escaped.
2. Backslash-escape reference-triggering underscores in prose: `re.sub(r'_(\s|$)', r'\\_\1', text)` turns `IO_ PROT` into `IO\_ PROT` (renders identically, no reference).

Verify a cell is clean by checking the built HTML / build log — a leftover `Unknown target name` means a `_` slipped through.

### Local Sphinx build verification (no system Sphinx)

When the host has no Sphinx and you must confirm a generated `.rst` really builds, install Sphinx in a throwaway venv — do NOT pollute the system:

```bash
python3 -m venv /tmp/sphenv && /tmp/sphenv/bin/pip install -q sphinx
mkdir -p /tmp/sphbuild/src && cp out.rst /tmp/sphbuild/src/report.rst
cat > /tmp/sphbuild/src/index.rst <<'RST'
Index
=====

.. include:: report.rst
RST
cd /tmp/sphbuild && rm -rf _b && ../sphenv/bin/python -m sphinx -b html src _b 2>&1 \
  | grep -iE 'warning|error' | grep -viE 'toctree|not included'
```

A clean build (0 warnings/errors after filtering toctree noise) is real ground truth — docutils alone can't validate Sphinx roles (`:ref:`, `:widths:`, `.. highlight::`), and its error text for unknown roles is misleading. Confirm `:widths:` took effect via `<col width=...>` / rendered column proportions in the HTML, since the directive text itself doesn't appear literally in output.

### `:doc:` — file-level reference

Jumps to file top, not a specific section:
```rst
详见 :doc:`chapter2`
```

No `.rst` suffix. No label needed in target file.

### `autosectionlabel` — zero-label cross-references

Add to `conf.py`:
```python
extensions = ['sphinx.ext.autosectionlabel']
autosectionlabel_prefix_document = True
```

Then reference sections by their exact heading text:
```rst
详见 :ref:`CFG_CORE_PFX 选项`
```

Section titles must be unique across files (or use `prefix_document`).

### Sync List-Table Content with Substitution Variables

When list-table rows contain document names or reference strings that also appear in prose (e.g., a "Referenced Documents" table where each entry is cited elsewhere in the document), writing them twice creates a maintenance burden. Edit-table-and-prose-desync is the problem.

**Solution:** `rst_epilog`-style substitution variables (`.. |VAR| replace:: text`) in a shared `.. include::` file, used in both table cells and body text. No `conf.py` changes needed.

**Step 1 —** Create `common/doc_refs.rst`:

```rst
.. |ARMv8| replace:: ARMv8-A Architecture Reference Manual
.. |RISCV_PRIV| replace:: RISC-V Privileged Specification
.. |AXI4| replace:: AMBA AXI4-Stream Protocol Specification
```

**Step 2 —** In every `.rst` file that references these, add one line at the top:

```rst
.. include:: ../common/doc_refs.rst
```

**Step 3 —** Use `|VAR|` everywhere:

Table:
```rst
.. list-table:: Referenced Documents
   :name: ref-docs
   :header-rows: 1

   * - Document Name
     - Version
   * - |ARMv8|
     - DDI 0487J.a
   * - |RISCV_PRIV|
     - 20211203
```

Prose:
```rst
The design follows |ARMv8| exception model and |RISCV_PRIV| privileged architecture.
```

Change the document name in `common/doc_refs.rst` → all `.rst` files that `.. include::` it update automatically. Works with both `.. list-table::` and `.. table::`.

**Pitfalls:**
- `|VAR|` renders as **plain text**, not a hyperlink. This approach is about content sync, not clickable cross-references.
- If you also need clickable links, pair `|VAR|` with `.. _label:` definitions elsewhere.
- The `.. include::` line must appear before first use of `|VAR|` in each file.

## Tables

### `.. list-table::` directive — bullet-list tables

```rst
.. list-table:: Table Title Here
   :name: short-unique-id
   :widths: 30 35 35
   :header-rows: 1
   :class: longtable

   * - Column 1
     - Column 2
     - Column 3
   * - Value 1
     - Value 2
     - Value 3
```

**Multiline cells:** Each `-` at the same indentation level becomes a separate column. Do NOT use `|` (line block) for multiline cell content — it causes extra vertical spacing. Use comma-separated values on a single line instead:

```rst
# ❌ BAD: | line blocks add blank lines
   * - param
     - desc
     - | value1
       | value2
       | value3

# ✅ GOOD: comma-separated
   * - param
     - desc
     - value1, value2, value3
```

Alternatively, keep each value on its own `-` indented under the cell, but this only works if the cell is the last column (Sphinx merges trailing `-` items into the last cell).

**RST build error:** `uniform two-level bullet list expected, but row 2 does not contain the same number of items as row 1 (8 vs 3)` — this means a data row has more `-` items than the header row. Each `-` is a column. Check that multiline values in a single cell are not split across separate `-` bullets.

### `.. tabularcolumns::` — per-column alignment (LaTeX/PDF only)

Placed **before** a table directive. Uses LaTeX column descriptors:

```rst
.. tabularcolumns:: |c|m{0.30\\linewidth}|c|

.. list-table::
   ...

   * - Centered
     - Vertically centered + wraps
     - Centered
```

| Descriptor | Horizontal | Vertical |
|-----------|-----------|----------|
| `l` | Left | Middle |
| `c` | Center | Middle |
| `r` | Right | Middle |
| `p{width}` | Left + wrap | Top |
| `m{width}` | Left + wrap | **Middle** |
| `b{width}` | Left + wrap | Bottom |

`m{}` requires the `array` package (Sphinx LaTeX builder loads it by default). Only affects PDF output; HTML ignores `tabularcolumns`.

```rst
.. table:: Table Title Here
   :name: short-unique-id
   :class: longtable
   :width: 100%
   :widths: 28 18 18 18 18

   +-----+-----+-----+-----+-----+
   | Col1 | Col2 | Col3 | Col4 | Col5 |
   +-----+-----+-----+-----+-----+
   | val  | val  | val  | val  | val  |
   +-----+-----+-----+-----+-----+
```

For full-scale examples, see `references/complex-grid-table-example.rst` (multi-column behavior matrix with multi-line cells, Yes/No/TBD values, and footnotes).

For generating grid tables **programmatically** (with a vertically-merged/rowspan cell), ASCII-safe output (`µm²` via unicode escapes), and correct title-underline lengths, see `references/grid-table-rowspan-programmatic.md`.

**Pitfalls:**
- `:widths:` values use **spaces**, not commas: `28 18 18 18 18` ✅ / `28, 18, 18, 18, 18` ❌
- Table grid must be **indented** (3 spaces) under the directive — otherwise Sphinx doesn't recognize it as directive content
- `:name:` must be a **short unique identifier** (e.g. `mem-if-support`), not a duplicate of the title
- DO NOT put the title as a separate text line between `.. table::` and the table grid — it breaks the directive
- `.. table:: Title` and title go on the **same line**
- Table won't show title if any of the above is wrong (Sphinx silently drops malformed directives)
- **Footnotes must go OUTSIDE the `.. table::` directive.** Defining a `.. [N]` footnote inside the directive's content block (after the grid table but within the indented block) triggers: `WARNING: Error parsing content block for the "table" directive: exactly one table expected.` Move footnote definitions to after the directive, at the same indent level as `.. table::`

### Width control

| Option | What it does |
|--------|-------------|
| `:width: 100%` | Overall table width (needs `%` unit) |
| `:widths: 28 18 18 18 18` | Column proportions (no units, relative integers) |

For full-width tables: use both `:width: 100%` and `:widths:`.

### Auto-numbering with `numfig`

In `conf.py`:
```python
numfig = True
```

Then add `:name:` to tables:
```rst
.. table:: Table Title
   :name: table-id
```

Rendered as "Table 1.2: Table Title" with clickable number.

### Spreadsheet → RST: preserve the original column structure

When converting a `.xlsx`/CSV table into an RST table, the output **must mirror the source table's column structure**, including any grouping/merged column — never flatten to fewer columns. A source table of `指令类型 | 指令名称 | 执行延时 | 执行吞吐率` (4 cols) must stay 4 cols; dropping the grouping column (`指令类型`/`Instruction Type`) produces output the user rejects as "格式和原始 excel 中对不上".

- Keep a grouping column as the **first column**, header translated (e.g. `指令类型` → `Instruction Type`), extension/type names translated (`P扩展（DSP)指令` → `P (DSP)`, `自定义DSP指令` → `P (DSP) Custom`).
- RST `.. list-table::` has **no merged cells**. Mirror the source's merged-cell grouping visually: put the type value on the **first row of the group, blank on continuation rows** (not repeated per row). Use `''` for the blank, so it doesn't render as the `—` placeholder used for genuinely-missing data.
- Normalize within a group: unify case/naming (e.g. half-precision mnemonics all `H_*`), delete duplicate instruction rows, fix obvious typos (`H_SUB` → `H_FSUB`). Flag these edits in the summary so the user can confirm.
- Generate programmatically (openpyxl) rather than hand-typing hundreds of rows: a **merge-aware cell reader** that propagates each merged range's top-left value to every cell in the range (openpyxl returns the value only at the top-left). Forward-fill the grouping column. Then **verify zero residual CJK** by scanning the output with a `[\u4e00-\u9fff]` regex before delivery. Full recipe: `references/xlsx-to-rst-conversion.md`.
- For the **instruction-execution-time chapter specifically** (N300/N600/N900 `*_指令执行时间.xlsx` → RST), the semantic layer lives in `references/instruction-execution-time-tables.md`: the user-approved RV32/RV64 4-column split (`RV32 Execute Latency | RV32 Execute Throughput | RV64 ...`) with a caption name on EVERY table, the special-value phrasing map (``---`` / `Stalls the pipeline` / `Unpredictable` / `Same as latency (state-machine implementation)`), and the per-extension traps — RV64-only instructions must be forced to `---` in the RV32 columns, K is a YES/NO matrix needing row-merge by union of support, P's RV32 and RV64 mnemonics are disjoint so P is SPLIT into two separate 3-column tables (one per instruction set), F/D/ZFH left-column shared instructions apply to BOTH XLENs, C has no XLEN split (3-column table), and the special-value mapping must be applied uniformly on every sheet (bare `str()` leaks `阻塞执行` → fails the zero-CJK check).

## `.. raw::` Directives

### Syntax

Content **must be indented** (3 spaces) under the directive:

```rst
.. raw:: latex

   \renewcommand{\texttt}[1]{{\ttfamily\bfseries #1}}

.. raw:: html

   <style>
   code.docutils.literal { background: #f3f3f3; padding: 1px 3px; border-radius: 2px; }
   </style>
```

⚠️ **Blank line between directive and content is OK**, but content must be consistently indented. Missing indentation = Sphinx warning: `Content block expected for the "raw" directive; none found.`

### Inline code (`` ``xxx`` ``) styling

RST `` ``xxx`` `` → Sphinx → LaTeX `\texttt{xxx}` or HTML `<code>`

- **HTML**: inject CSS via `.. raw:: html` at file top
- **PDF/LaTeX**: `\renewcommand{\texttt}` in `.. raw:: latex` at file top
- Alternative: use `conf.py` `latex_elements['preamble']` or `html_css_files` for global changes

## Build Troubleshooting

### WaveDrom embedding

See `references/wavedrom.md` for WaveDrom syntax, strict JSON requirements, signal name alignment, and gap/omission patterns.

### `make latexpdf` hangs

Cause: `pdflatex` encounters an error and enters **interactive mode**, waiting for user input.

**Quick fix:**
```bash
make latexpdf LATEXOPTS="-interaction=nonstopmode"
```

**Permanent fix** — create `latexmkrc` in project root (next to `Makefile`):
```perl
$pdflatex = "pdflatex -interaction=nonstopmode %O %S";
```

This keeps LaTeX running past errors so you can see all warnings at once.

### Table width error

```
WARNING: Error in "table" directive
not a positive measure of one of the following units: ...
```

Cause: `:width:` or `:widths:` has wrong syntax.

Fix:
- `:widths:` → space-separated integers: `28 18 18` (no commas, no units)
- `:width:` → needs unit: `100%` (not bare `100`)

### `Could not lex literal_block ... Highlighting skipped`

Cause: Sphinx/Pygments tries to syntax-highlight a `::` literal block but cannot determine a lexer — e.g. Verilog/`.v` config content with no language hint (default is `python3`, and guessing fails or picks wrong).

Fix: add `.. highlight:: none` at the top of the file. It sets the default highlight language to `none` for the rest of the document, so Pygments skips those blocks:
```rst
.. highlight:: none
```
`.. highlight::` is Sphinx-specific — pure docutils reports `Unknown directive type "highlight"`, but Sphinx supports it. Alternatives: set `highlight_language = 'none'` in `conf.py` (global), or wrap the block in `.. code-block:: verilog` (or the real lexer) if you actually want it highlighted.

### toctree warning

```
WARNING: toctree contains reference to nonexisting document 'nuclei/changelog'
```

Remove the reference from the `toctree` directive in the parent file.

### document not in toctree

```
WARNING: document isn't included in any toctree
```

Add the file to a `toctree` directive, or if intentional (e.g. `.. include::` only), ignore.

## Global Text Replacements with `rst_epilog`

Use `rst_epilog` in `conf.py` to define text aliases that sync everywhere — **change once, all references update**.

```python
# conf.py
rst_epilog = """
.. |ARMv8| replace:: ARMv8-A Architecture Reference Manual
.. |RISCV_PRIV| replace:: RISC-V Privileged Specification
.. |AXI4| replace:: AMBA AXI4-Stream Protocol Specification
"""
```

Use in any `.rst` file (table cells, body text, admonitions):

```rst
* - |ARMv8|
  - DDI 0487J.a

该设计符合 |ARMv8| 中定义的异常模型。
```

**Key characteristics:**
- Substitutions render as **plain text**, NOT hyperlinks — no cross-file jump
- No space between `|...|` and adjacent text or punctuation: `|ARMv8|，` / `|ARMv8|。`
- Table usage: `|NAME|` works in `.. table::` (grid table) and `.. list-table::` cells
- Best for: reference document tables where the document name appears in many files and must stay consistent

**Contrast with `:ref:`:**
| Pattern | Updates when source changes | Clickable link |
|---------|---------------------------|----------------|
| `:ref:`label`` | Yes (shows target title) | Yes |
| `|NAME|` via `rst_epilog` | Yes (text synced) | No |
| `` _`text` `` in cell | No (manual copy) | Same-file only |

When you need BOTH auto-sync AND clickable links, convert list items to sections with `:ref:` (see Cross-References above).

## SMP feature domain knowledge

Nuclei SMP feature chapter domain notes (N600): `references/scu-domain-notes.md` (SCU
coherency point role, shadow-data-tag implementation, Icache-snoop-Dcache mechanism +
`CC_CTRL.I_SNOOP_D_EN` gate) and `references/clm-iocp-domain-notes.md` (CLM reset
signals/registers, IOCP line buffer / write-streaming / prefetch / transfer / usage).
Prose-style rules for the whole SMP chapter: `references/smp-chapter-style-conventions.md`.

## Pitfalls

- **`:ref:` spacing**: `:ref:`label`` with backticks touching — no space between `:ref:` and opening backtick
- **Table grid indentation**: must be indented under `.. table::` directive
- **`.. table::` title**: title on same line as directive, no duplicate title line in content
- **`:widths:` commas**: use spaces, not commas
- **`.. raw::` content**: must be indented, even after a blank line
- **latexmk hang**: always use `-interaction=nonstopmode` or a `latexmkrc`
- **Prefer not touching `conf.py`** when the user says their project has complex config — use `.. raw::` in `.rst` files instead
- **`.. note::` page-break splitting**: When a `.. note::` admonition is split across pages in PDF output, insert `\needspace{}` before it:
  ```rst
  .. raw:: latex

     \needspace{4\baselineskip}

  .. note::

     Content that must stay together.
  ```
  `\needspace{}` checks remaining page space; value should exceed note height + spacing.
- **Title adornment hierarchy**: docutils/Sphinx assign a title's LEVEL by its adornment character (first-seen order). If you introduce a NEW adornment for a subsection between two existing levels, it "steals" a level and forces deeper headings into a skip → `Inconsistent title style: skip from level 1 to 3` (e.g. a `-` subsection between `+` sections and `=` config-headings pushes `=` headings to level 3 under a level-1 parent). Keep every heading at the same depth using the SAME adornment. In one Nuclei databook convention: sections `+`, subsections/config-headings `#`. When generating RST programmatically, emit `adornment * len(title)` so underline length always matches.
