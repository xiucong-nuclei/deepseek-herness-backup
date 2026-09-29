# syn_report_to_rst.py + syn_diff.py -u (databook RST generation & config sync)

Two newer tools in the syn_feature workflow, alongside `syn_diff.py` (v3.x).
Both run on the syn server; both must be pure ASCII source (user rejects
non-ASCII, asked 3x).

## syn_report_to_rst.py — generate databook RST from csv2

Run inside `syn_feature` (no env vars needed):
```
python3 syn_report_to_rst.py <rst_name>            # default csv2 area_feature.csv
python3 syn_report_to_rst.py -f <csv2> <rst_name>
```
Reads the csv2 (metadata rows + header `Type|Feature|Config|Base Config|Area|...`)
and the `.v` config files in cwd; writes one RST file.

- Groups by csv2 col0 (`Type` = 大类). Emits a document preamble (Feature area /
  Evaluation Method / Evaluation Environment, English, hardcoded env values),
  then one section per 大类 (Base first, then ISA/Microarchitecture/LM/ICACHE/...
  in first-appearance order).
- Each section: `.. table::` grid (4 cols: Feature | Config | Base Config | diff,
  Feature col spans 2 rows) then one `.. _anchor:` subsection per config with a
  `::` literal block embedding the `.v` content; Comment column → `.. note::`.
- Anchor = strip common filename prefix (`n300_syn_`), prepend 大类 prefix if the
  stripped name lacks it (mapping in `SECTION_PREFIX`). ECLICV2 uses `eclicv2`
  (configs are `eclic2_*` → anchors `eclicv2_eclic2.v`).
- Sphinx-specific output conventions used (see `sphinx-rst` skill):
  `:width: 100%`, `:ref:`display <label>`` (no page numbers), single-colon
  `.. _label:` targets, `.. highlight:: none` at top to skip Pygments lexing of
  `.v` blocks, `µm²` emitted via `\u00b5m\u00b2` escape so the script stays ASCII.
- Numeric columns are found by FUZZY column-name match (mirrors syn_diff's
  `resolve_diff_columns`), not exact header names — header names vary between
  csv2 versions.

## syn_diff.py -u / --update — sync csv2 edits to config files

`syn_diff.py -u <csv2>` — user edits csv2 (renames Config/Base Config), then
syncs to disk `.v` files. Two passes:
1. **Config names**: exact filename match first; renamed ones fuzzy-matched
   (difflib, cutoff 0.6, best) against unclaimed `.v` files, then `os.rename`.
   New configs with no source → WARN, skipped.
2. **Base Config**: set each file's `` `include_ix "..." `` to the resolved base.
   Base refs are also fuzzy-matched (user often does NOT rename base configs, so
   the csv2 Base Config still holds old names → re-resolve to the renamed file).
   Files with no `include_ix` (the top base config) are left untouched.

Safety:
- Modified/renamed files copied to `syn_feature/update_backup_<timestamp>/`
- All fuzzy matches (renames + base refs) written to
  `syn_feature/update_review_<timestamp>.log` AND printed, for user review.
- Files written back preserving detected encoding + BOM (`\ufeff` handled).
- Full workflow: edit csv2 → `-u` sync to files → `-e` re-reads `include_ix`
  back into csv2 Base Config column (canonicalizes names).
