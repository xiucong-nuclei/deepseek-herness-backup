# syn_report_to_rst.py — databook RST from syn_diff csv2

Generates a databook RST doc from the syn_diff.py csv2 table + the syn_feature
`.v` config files. Lives at `~/deliverables/tools/syn_report_to_rst.py`.

## Usage / inputs

Run INSIDE the syn_feature dir (that is the whole point — no PROJ_* env vars):

    syn_report_to_rst.py <rst_name>              # default csv2 = area_feature.csv
    syn_report_to_rst.py -f <csv2> <rst_name>    # override csv2
    # rst is written to cwd; .v files are read relative to cwd

Inputs: csv2 (default `area_feature.csv`) + every `Config` `.v` file that the
csv2 references, both relative to cwd.

## csv2 schema (the user's real file: Nuclei_CPU_Options_Matrix-300 FA.csv)

- Metadata rows BEFORE the real header: `TECH,<val>`, `FREQ,<val>`,
  `Update Time,<val>`, and a `Minimum NAND ...` row.
- Header row = the row containing `Type`,`Feature`,`Config` (locate by scanning,
  same as syn_diff.py's read_csv2_structured).
- Columns: `Type,Feature,Config,Base Config,Area(um2)/Gate(K),Base Area(um2)/Gate(K),Added Area(um2),Added Gate(K),Comment`
- Footer rows AFTER the data: `Config Dir,<dir>`, `Version,<v>`,
  `Base Config,<description>` — values are in the SECOND column (Feature col),
  NOT the third. Distinguish footer from config rows by: a row whose Config
  (col 3) is non-empty is a config row; else if Type is one of those three keys
  it is footer info; else ignore blank rows.
- `Type` (col 0) is the 大类 (feature group) = the rst section title. Group by it,
  preserving first-appearance order, but emit a `Base` section FIRST.
- `Area`/`Base Area` are combined strings `"23735.75 (62.79k)"` → format to
  `"23735.75 / 62.79(k)"`. `Added Area`/`Added Gate` are separate plain numbers
  (can be negative) → diff cell `"-4179.8 / -11.06(k)"`.

## Design decisions (current state, confirmed with user)

- One section per 大类; **Base section generated first**, hosting the COMMON
  content (Tech/Freq/Minimum/Version/Base-Config description). Base table = 2
  cols (Config | area/gate). Feature table = 4 cols (Feature | Config | Base
  Config | diff).
- **NO links, NO labels.** Config names render as PLAIN WRAPPED TEXT (keeps the
  `.v` suffix — user: "不要去 .v 加上 .v"). There is no `:ref:`, no `.. _label:`,
  no `` `text <target>`_ `` in the table. Sphinx's `:ref:` only resolves explicit
  labels (never bare section-title implicit targets), which is why the earlier
  label-based attempts failed; the final choice was to drop links entirely.
- **Anchor naming**: strip the common filename prefix across all Config names
  (e.g. `n300_syn_` → `isa_b.v`). **Two-chapter series (600/900) KEEP the
  chapter token**: the common prefix (`syn_600_rv32_`) is stripped only up to
  `rv32_`/`rv64_`, so anchors read `rv32_base.v` / `rv64_base.v` instead of two
  identical `base.v` (user requirement). Then if the stripped name does NOT
  already start with its group's prefix (checked PAST the chapter token),
  PREPEND `<prefix>_` (with underscore). Map:
  ISA=isa, Microarchitecture=micro, Memory Protection=pmp, LM=ilm/dlm (both
  acceptable, no prepend), ICACHE=icache, DCACHE=dcache, PERIPHERAL=peripheral,
  ECLICV2=eclicv2 (prepend to `eclic2_*` → `eclicv2_eclic2.v`), NICE=nice,
  SAFETY=safety, ETRACE=etrace, DEBUG=debug. Resulting anchors:
  `micro_dual_issue.v`, `pmp_stack_check.v`, `peripheral_ppi_1m.v`,
  `peripheral_fio_4k.v`, `eclicv2_eclic2.v`.
- **Title adornment (kiucong databook convention):** section title underline `+`,
  config subsection heading underline `#`. Emit `adornment * len(title)` so the
  underline always matches the title length.
- Config subsections: heading (the anchor, e.g. `safety_lockstep_ioprot.v`) with
  `#` underline, an intro line ending `::`, blank line, then the `.v` content
  indented 3 spaces (read with detect_encoding, rstrip trailing newline).
- **include_ix rewrite:** when embedding each config's `.v` content, rewrite any
  `` `include_ix "<file>" `` value to that file's RST anchor so it matches the
  section names in the doc (e.g. `n300_syn_base.v` → `base.v`;
  `syn_600_rv32_base.v` → `rv32_base.v`). Uses the same
  anchor_map; unknown values are left unchanged. (`rewrite_include_ix`.)
- **Blank-line strip:** embedded config content drops empty lines.
- Comment col (non-empty) → `.. note:: <comment>` inside that config's subsection.
- If a base config is not in the csv2 (data error, e.g. SAFETY used
  `n300_syn_lockstep.v`), print `[WARN]` and render that base cell as the raw
  text (no link anyway, so it is just the string).

## Table width + wrapping (current)

- Feature tables: `.. table::` + `:widths: 34 22 22 22` (4 cols: 34 22 22 22).
- Base table: `:widths: 22 78` (2 cols). `:widths:` values are space-separated
  integers; they control the RENDERED proportions (the directive text does not
  appear literally in HTML — it becomes `<col width>`).
- **Wrapping (`_wrap_text`)**: config/base names wrap at the column width,
  breaking ONLY right after an `_` (underscore boundary), never at a dot or
  mid-token, and keeping a trailing `.v` together. Example:
  `dcache32k_prefetch_axi.v` → `dcache32k_prefetch_` + `axi.v`; a 26-char
  `ilm_dlm_sram_64k_addr_ecc.v` → `ilm_dlm_sram_64k_addr_` + `ecc.v`.
- **`_esc_ref`**: every wrapped line and interpolated feature prose is passed
  through `re.sub(r'_(\s|$)', r'\\_\1', s)` to backslash-escape any underscore
  followed by whitespace/end-of-line. Without this, a line/word ending in `_`
  (e.g. the wrapped `...addr_` or the feature text `LOCKSTEP+IO_ PROT`) becomes
  an RST hyperlink reference and the build fails with `Unknown target name`.
  `\_` renders identically to `_` but is not a reference.

## Grid table renderer (rst grid table, vertical spans + multi-line cells)

`render_grid_table(rows, spans)`. `rows` are logical rows; each cell is either a
str (single line) or a list of str (pre-wrapped lines). `spans` = set of
`(row, col)` meaning that cell spans INTO `row+1` (Feature column). The renderer:
- Normalizes cells to lists; computes per-column width = max line length.
- Per logical row, physical height `H[r]` = max over NON-spanning cells of their
  line count (min 1); spanning cells are padded to `H[r]+H[r+1]` (top-aligned).
- Flattens to physical lines; per-column continuation-border sets decide `|`
  (cell continues) vs `+` (cell boundary) at each internal divider. A wrapped
  multi-line cell shows NO horizontal divider through its own lines (all `|`),
  while the Feature rowspan keeps col0 `|` across its config+area rows.
- Emits `border(set())` top/bottom, content rows `| ' ' + ljust(w) + ' ' |`.

## Python pitfalls hit (real bugs)

1. **Local shadows module function** → `UnboundLocalError`:
   `common_prefix = common_prefix([...])` inside `main()` makes `common_prefix`
   a local, so the RHS call resolves to the not-yet-assigned local. Rename the
   local (`cp = common_prefix([...])`).
2. **Prepend prefix without underscore** → `microdual_issue` instead of
   `micro_dual_issue`. Use `prefixes[0] + '_' + base`.

## Validation — use a real Sphinx venv (docutils is misleading)

This rst targets Sphinx (the databook build). Pure docutils reports FLOODS of
false errors for Sphinx-only constructs AND — critically — does NOT catch the
things that actually break a Sphinx build (`:ref:` undefined labels, `_`
phantom references). The reliable check is a real Sphinx build in a throwaway
venv (host has no system Sphinx):

    python3 -m venv /tmp/sphenv && /tmp/sphenv/bin/pip install -q sphinx
    # index.rst = `.. include:: report.rst`; build with:
    #   ../sphenv/bin/python -m sphinx -b html src _b 2>&1 \
    #     | grep -iE 'warning|error' | grep -viE 'toctree|not included'
    # clean = 0 non-toctree warnings/errors.

Sphinx facts learned here:
- `:ref:` resolves ONLY explicit `.. _label:` targets (or autosectionlabel) —
  never a bare section-title implicit target. `:ref:`name <name.v>`` against a
  heading literally titled `name.v` fails with `undefined label: 'name.v'`.
- Plain phrase refs `` `text <title>`_ `` DO resolve to a heading's implicit
  anchor with no label, and fold a newline inside the backticks to a space.
- Any word ending in `_` before whitespace/end-of-line is a phantom hyperlink
  reference (see `_esc_ref` above). Wrapped cells ending in `_` trigger this.
- `.. highlight:: none` at the top suppresses Pygments' failed Verilog lexing.

## syn_diff.py -update mode (IMPLEMENTED, commit + pushed)

`-u/--update <csv2>` syncs csv2 edits BACK to the .v files (reverse of -e/-g):
- **Pass 1 — sync Config names (rename files):** exact-match existing .v files
  first (claim, no-op); for csv2 Config names with no exact disk match, fuzzy-match
  (difflib.get_close_matches, ~0.6 cutoff, best score) against UNCLAIMED .v files
  and `os.rename`. New config with no disk source → `[WARN]` skip.
- **Pass 2 — sync Base Config (include_ix):** the csv2 Base Config value is often
  the OLD base name; fuzzy-match it against current config names to resolve the
  renamed base, then set that file's `` `include_ix `` to the resolved name.
  **Files with no include_ix line (e.g. top base config) are left untouched.**
- **Backups:** copy every modified .v into `update_backup_<ts>/` (a folder, not
  `.bak.N`). **Review log:** every fuzzy match goes to `update_review_<ts>.log`
  AND stdout. Uses PROJ_SRC_ROOT/PROJ_NAME env scheme. Tested end-to-end.

## Preamble: inline spec-trans English, NOT an external template

Written DIRECTLY into the script as the `PREAMBLE` constant (no external file).
`.. Feature area` is COMMENTED OUT (databook provides the title at the include
site); intro says "some features"; TECH/FREQ/Minimum NAND env values are hardcoded.
Square microns written as `\u00b5m\u00b2` escape so the script stays ASCII.

## Series support: 300 / 600 (and 900 later)

`--series` distinguishes CPU series (default 300; choices 300/600, other values
error out - 900 gets added by extending `SERIES_CHAPTERS`):

    syn_report_to_rst.py --series 300 [csv2] <rst_name>          # 1 csv2, no chapters (default csv2 = area_feature.csv)
    syn_report_to_rst.py --series 600 <rv32.csv> <rv64.csv> <rst_name>  # 2 csv2 -> two chapters

- 300: same single-document layout as before, but `-f` was REMOVED (4.1);
  positionals only. Evaluation Method/Environment headings changed from `#`
  to `+` (same level as Base/ISA sections) so config subsections (`#`) nest
  correctly under their sections (fixes the old h1-everywhere hierarchy).
- 600: each csv2 becomes a chapter: "RV32 Feature Area" / "RV64 Feature Area",
  chapter underline `*` (h1), sections `+` (h2), configs `#` (h3). Preamble is
  emitted per chapter (minus the commented `.. Feature area` line), and each
  chapter carries its own Base section + footer (Version/Config Dir/Base Config).
- .v lookup for 600: `rv32/<config>` and `rv64/<config>` relative to cwd -
  NO cwd fallback (user runs in the folder containing rv32//rv64/).
  For 300: plain `<cwd>/<config>` (unchanged).
- Per-csv anchor maps: common prefix stripped UP TO the chapter token for
  600/900 (anchors keep `rv32_`/`rv64_`, so no duplicate `base.v` across
  chapters; 300 strips the full `n300_syn_`); include_ix rewrites are
  independent per chapter.
- Comment column: the 600 csv2 files have an UNNAMED 9th column; the user fixes
  the csv (adds a `Comment` header) before running - the script does not fall
  back (7.2).
- Edge cases: 600 with !=2 csv2 -> error; 300 with >1 csv2 -> error;
  empty/unparseable csv2 -> [ERR] + exit 1; missing .v -> [WARN] + placeholder.
