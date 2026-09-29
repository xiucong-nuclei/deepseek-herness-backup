---
name: synthesis-result-analysis
description: Compute synthesis result diffs — area & gate count delta between feature configs.
metadata:
  hermes:
    tags:
    - synthesis
    - csv
    - area
    - gate-count
    - diff
    - n300
    - syn_feature
    - include_ix
    - ppa
    related_skills: []
    version: 4.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
---

# Synthesis Result Diff Analysis

For Nuclei N300/N900 synthesis result analysis. Five subcommands in one script
(`syn_diff.py`, commonly referred to as `area_diff` in the user's environment):

| Command | Args | Description |
|---------|------|-------------|
| `-d` (diff) | csv1 csv2 | Extract base config from syn_feature files, compute area/gate diff, write to csv2 |
| `-e` (extract) | csv2 | Extract `include_ix` from syn_feature files into csv2 Base Config column |
| `-c` (collect) | csv1 csv2 | Run ppa to collect synthesis results into csv1 from configs in csv2 |
| `-g` (gen) | csv2 | Generate all syn config files from csv2, write section .list files and syn_config_all.list |
| `-k` (check) | csv2 kconfig | Check `define macros in syn_feature files against kconfig |

## Documentation Output Style

When the user asks to produce documentation for this script ("写到文档里面",
"介绍下 area_diff") — especially for NuCLei databook/doc purposes:

- Use **numbered items** (1. 2. 3. 4. 5.), one per subcommand.
- **No subsection headers** (no `###`, no `**功能**` / `**处理流程**` labels).
- Each item covers (a) what the command does, (b) path dependencies, (c) key parameters and their roles — concise but not one-liner terse.
- A short ~50-character overview line at the top is acceptable as a standalone.
- The detailed reference format with tables and subsections (as in
  `references/area_diff_cn_doc.md`) is only for in-depth technical review, NOT
  for user-facing documentation output.

## Environment

Requires `PROJ_SRC_ROOT` and `PROJ_NAME` environment variables (set via `spr_cpu`).
Script exits with a message if either is missing.

Full Chinese documentation: [references/area_diff_cn_doc.md](references/area_diff_cn_doc.md)

`ppa` tool internals (report-path resolution, `-get_data` flag, report filename
conventions, `pre_setm` PrimeTime error): [references/ppa_tool_internals.md](references/ppa_tool_internals.md)

Sibling tool `syn_flow.py` (the synthesis flow driver — rtl/compile/syn modes,
its cfg mechanism, and the `-list` parameter): [references/syn_flow_driver.md](references/syn_flow_driver.md)

Path resolution:
- **csv1**: `$PROJ_SRC_ROOT/cpu_cct/syn/<csv1_name>`
- **csv2**: `$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<csv2_name>`
- **syn_feature config files**: `$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<Config>`

## How `-d` (diff) works

1. Backs up csv2 with rolling suffix: `csv2.bak.1`, `csv2.bak.2`, ... (never overwrites existing backup)
2. Loads csv1 (synthesis results) into a `{config: {Area, Gate_num(k)}}` map
3. For each row in csv2:
   - Looks up `Config` in csv1 → fills `Area` column (format: `area/gate`)
   - Reads `$SYN_FEATURE/<Config>` file, extracts `include_ix "xxx"` → this becomes the Base Config
   - If csv2 also has a `Base Config` column that differs from the file value, reports a `[MISMATCH]` warning
   - Looks up the resolved Base Config in csv1 → fills `Base Area`
   - Computes `Added Area = Area - Base Area`, `Added Gate = Gate_num - Base Gate_num`
4. Writes back to csv2 (preserving metadata rows)

## How `-e` (extract) works

1. Backs up csv2 with rolling suffix
2. For each row, reads `syn_feature/<Config>` and extracts `include_ix`
3. Writes the value into csv2's `Base Config` column (adds the column if missing)
4. Prints a line for each row whose value changed

## How `-c` (collect) works

1. Reads all `Config` values from csv2
2. Constructs `-f "syn_feature/cfg1 syn_feature/cfg2 ..."` argument list
3. Runs from `$PROJ_SRC_ROOT/cpu_cct/syn/` (not `cpu_cct/`):
   ```
   ../bin/ppa -syn -f "<config_list>" --freq=100 --tech=22,9t -dc_flat=1 -get_data --csv=<csv1_name>
   ```
4. PPA parameters (`--freq`, `--tech`, `-dc_flat`) are constants at the top of the script for easy editing

## How `-g` (gen) works

1. Reads csv2 (CSV table with Type/Feature/Config/Base Config columns) to collect all config→base_config mappings and section boundaries
2. Generates all config files from csv2 (no list file filtering):
   - Skips configs whose name contains "base" (case-insensitive) — these are baseline configs and should not be auto-generated
   - Skips configs whose Base Config is not found among all config names — reports ERROR
   - Creates each config file as `` `include_ix "Base_Config" `` (skips if file already exists)
3. Writes `syn_config_00X.list` section files (only with successfully generated configs)
4. Writes `syn_config_all.list` in syn_feature/ directory — combined list of all generated configs

## How `-k` (check) works

1. Reads kconfig file from syn_feature/ (if it exists; gracefully handles missing file)
2. Reads all config names from csv2
3. For each config, reads the syn_feature file and extracts all `` `define MACRO `` patterns
4. Checks each macro against kconfig content (whole-word match)
5. Reports ERROR for any macro not found in kconfig
6. If kconfig does not exist, reports total define count but no errors

## Key Features

- **Rolling backups**: `csv2.bak.1`, `csv2.bak.2`, ... — never overwrites an existing backup
- **Auto encoding detection**: handles UTF-8, UTF-16 LE/BE (BOM), GBK, latin-1. Applied to ALL file reads (CSV1, CSV2, syn_feature config files)
- **Metadata header skip**: CSV2 may have metadata rows (TECH, FREQ, Update Time) before the actual header; the script auto-detects the row containing `Type`/`Feature`/`Config` as the real header
- **CSV1 column auto-detection**: fuzzy-matches column names containing "area" and "gate" — not hardcoded to `Area(um2)`/`Gate_num(k)`
- **Base Config from source of truth**: `Base Config` is extracted from syn_feature config files (`include_ix "xxx"`), not from the CSV2 column. CSV2's `Base Config` column is cross-checked for mismatches.
- **ASCII-only output**: all prints use ASCII characters only (no Unicode arrows, no Chinese)

## Pitfalls

- **`csv.DictReader` skips metadata wrongly**: csv2 has metadata rows (TECH, FREQ, Update Time) before the actual header. Using `csv.DictReader` directly treats the first metadata row as header → all column lookups fail. Always use `read_csv2_structured()` which scans for the real `Type/Feature/Config` header row first.
- **Encoding on ALL file reads**: syn_feature config files may be GBK-encoded on CentOS 7. Always call `detect_encoding()` before opening ANY file — not just CSV files. Missing this causes silent `UnicodeDecodeError` → `include_ix` extraction returns None.
- **`-c` runs from `cpu_cct/syn/`, not `cpu_cct/`**: the ppa command is executed with `cwd=$PROJ_SRC_ROOT/cpu_cct/syn/`, so `../bin/ppa` and `--csv=<csv1_name>` paths are relative to that directory.
- **UTF-16 encoding**: synthesis tools often output CSV with UTF-16 LE BOM (0xFF 0xFE). The script auto-detects this, but if detection fails, check the first 2 bytes of the file.
- **Metadata rows in CSV2**: the user's CSV2 starts with `TECH`, `FREQ`, `Update Time` rows before the actual `Type,Feature,...` header. The script preserves these but parses from the real header onward.
- **Exact config name matching only**: no fuzzy/normalize. If CSV2 has `n300 syn base.v` (spaces) and CSV1 has `n300_syn_base.v` (underscores), it will NOT match.
- **Output encoding is UTF-8**: even if input was UTF-16, output is written as UTF-8.
- **syn_feature config file format**: expects `include_ix "xxx"` (with double quotes) or `include_ix xxx` (no quotes). Other formats (e.g., Tcl `set include_ix xxx`) will NOT match.
- **`-get_data` is a boolean switch, no value**: `ppa`'s `-get_data`/`--get_data` flag is `action='store_true'` (help "Only extract PPA data") — write it bare, never `-get_data=1`. It skips re-synthesis and only re-extracts PPA data from existing results. `syn_diff.py -c` already appends it unconditionally.
- **`FATAL: must load prime-time Error 9` (pre_setm)**: the `setm`/`pre_setm` step calls PrimeTime-only commands in a `dc_shell` that hasn't loaded PT. Cascading `dc`/`syn` `Error 2` lines are just make propagating the failure, not new errors. See `references/ppa_tool_internals.md` for root-cause directions.
- **syn.log lives in the PARENT dir, not the report dir**: `parse_syn_path` resolves `syn.log` as `os.path.join(path, "../syn.log")` (= `dirname(path)/syn.log`), falling back to `latest_syn.log`; if neither exists, `path` is treated as a list file and expanded line-by-line.
- **Empty `Config` cell → `IsADirectoryError`**: in `-d` (diff), if a CSV2 row has an empty `Config` cell (blank line, summary/total row, or a feature not bound to a config), `str(Path(sf_dir) / config_name)` collapses to the `syn_feature` directory itself (`Path(dir) / "" == Path(dir)`), then `detect_encoding()` does `open(dir, 'rb')` → `IsADirectoryError`. Guard every `extract_include_ix` call: `cmd_extract` already guards with `if config_name:`, but `cmd_diff` historically did NOT. Fix:
  ```python
  file_base = extract_include_ix(str(Path(sf_dir) / config_name)) if config_name else None
  ```
  With `file_base=None` the row correctly falls through to `base_config_name = csv_base`, matching how empty-config rows are already handled for the area lookup.
