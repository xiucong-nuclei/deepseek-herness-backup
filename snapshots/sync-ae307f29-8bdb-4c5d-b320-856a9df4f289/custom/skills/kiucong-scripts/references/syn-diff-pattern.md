# syn_diff.py Pattern

Six-command synthesis result analysis tool for Nuclei N300/N900.

## Environment

Requires `PROJ_SRC_ROOT` and `PROJ_NAME` env vars (set by `spr_cpu`).
Script exits with message if missing.

Path resolution:
- **csv1**: `$PROJ_SRC_ROOT/cpu_cct/syn/<csv1_name>`
- **csv2**: `$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<csv2_name>`
- **syn_feature configs**: `$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<Config>`

## Six Commands

| Command | Args | What it does |
|---------|------|-------------|
| `-d` / `--diff` | csv1 csv2 | Extract base config from files, compute Area/Gate diff, write csv2 |
| `-e` / `--extract` | csv2 | Extract `include_ix` from config files into csv2 Base Config column |
| `-c` / `--collect` | csv1 csv2 | Run ppa from cpu_cct/syn/ to collect synthesis results into csv1 |
| `-g` / `--gen` | csv2 | Generate ALL config files from csv2, write section .list files + combined syn_config_all.list |
| `-k` / `--check` | csv2 kconfig | Check `define macros in config files against kconfig |
| `-u` / `--update` | csv2 | Sync csv2 Config/Base Config edits to syn_feature files (rename + include_ix) — see section 9 |

## Full Pipeline

```
-g (gen configs) -> -c (collect ppa) -> -e (extract base) -> -d (diff)
```

## Key Techniques

### 1. Metadata row skip (csv2)

CSV2 has metadata rows before the real header:

```
TECH,,,...
FREQ,100MHZ,,,...
Update Time,,,...
Type,Feature,Config,Base Config,Area,Base Area,Added Area,Added Gate
Base,Base(n300),n300_syn_base.v,,,,
...
```

**Read with `csv.reader` always** — never use `csv.DictReader` directly on
files with metadata rows, as it will treat the first metadata row as header
and all subsequent column lookups will fail.

```python
raw_lines = list(csv.reader(f))
header_idx = None
for idx, line in enumerate(raw_lines):
    if 'Type' in line and 'Feature' in line and 'Config' in line:
        header_idx = idx
        break
meta_rows = raw_lines[:header_idx]
fieldnames = raw_lines[header_idx]
data_rows = raw_lines[header_idx + 1:]
rows = [dict(zip(fieldnames, row)) for row in data_rows]
```

### 2. CSV1 lookup with fuzzy column detection

Column names vary across tool versions. Fuzzy-match on lowercase column name:

```python
for col in fieldnames:
    c = col.strip().lower().replace(' ', '').replace('_', '')
    if 'area' in c and area_col is None:
        area_col = col
    if ('gate' in c or 'gate_num' in c) and gate_col is None:
        gate_col = col
```

### 3. Base Config from syn_feature files (source of truth)

Instead of reading "Base Config" from csv2 column, extract it from the config file:

```python
def extract_include_ix(filepath: str) -> str | None:
    # MUST use detect_encoding() -- files may be GBK
    try:
        enc = detect_encoding(filepath)
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return None
    try:
        with open(filepath, 'r', encoding=enc) as f:
            content = f.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, IsADirectoryError):
        return None
    m = re.search(r'include_ix\s+"([^"]+)"', content)
    if m:
        return m.group(1)
    m = re.search(r'include_ix\s+(\S+)', content)
    if m:
        return m.group(1).strip('"\'')
    return None
```

**Empty-Config guard (recurring bug).** When a csv2 row has an empty `Config`
cell, `Path(sf_dir) / ''` resolves to the sf_dir DIRECTORY, and `open(dir, 'rb')`
inside `detect_encoding` raises `IsADirectoryError` (not a subclass of
`PermissionError`, so a bare `except (FileNotFoundError, PermissionError)` misses it).
Two-part fix: (1) guard the call site
`extract_include_ix(str(Path(sf_dir) / config_name)) if config_name else None`;
(2) catch `IsADirectoryError` inside `extract_include_ix`. Note `cmd_extract` already
had the `if config_name:` guard — `cmd_diff` was the one missing it. Verify with a
csv2 that has an empty-Config row and assert `exit == 0`.

Then cross-check with csv2's "Base Config" column for mismatches (someone changed
include_ix but forgot to update the table).

### 4. Rolling backups

Never overwrite existing backups. Find first unused N:

```python
def backup_file(path: str) -> str:
    n = 1
    while True:
        bak = f"{path}.bak.{n}"
        if not Path(bak).exists():
            break
        n += 1
    shutil.copy2(path, bak)
    print(f"[BACKUP] {path} -> {bak}")
    return bak
```

### 5. Encoding detection on ALL file reads

Not just CSV files -- syn_feature config files may be GBK-encoded on CentOS 7.
Always call `detect_encoding()` before opening ANY text file. Missing this on
non-CSV files causes silent `UnicodeDecodeError`.

```python
def detect_encoding(path: str) -> str:
    with open(path, 'rb') as f:
        head = f.read(4)
    if head.startswith(b'\xff\xfe'):
        return 'utf-16-le'
    if head.startswith(b'\xfe\xff'):
        return 'utf-16-be'
    if head.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    for enc in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(path, encoding=enc) as f:
                f.read(1024)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'latin-1'
```

### 6. PPA collect command (`-c`)

Reads Config values from csv2, constructs `-f "syn_feature/cfg1 syn_feature/cfg2 ..."`,
runs from `$PROJ_SRC_ROOT/cpu_cct/syn/`:

```
../bin/ppa -syn -f "<config_list>" --freq=100 --tech=22,9t -dc_flat=1 -get_data --csv=<csv1_name>
```

PPA parameters are constants at the top of the script for easy editing.

### 7. Gen command (`-g`) — v3.2.0

Reads csv2 and generates ALL config files (no filter list needed):

```bash
syn_diff.py -g area_feature.csv
```

Behavior:
1. Two-pass read of csv2: first collect all (config, base_config) pairs and section groupings
2. For each config:
   - **Base config validation**: if base_config is set but not found among all configs, report ERROR and skip
   - Otherwise, create config file with `` `include_ix "Base_Config" `` (skip if file already exists)
3. Write section `.list` files (`syn_config_001.list`, etc.) with `syn_feature/`-prefixed entries (only generated configs)
4. Write combined `syn_config_all.list` into `syn_feature/` directory with all generated configs sorted

Key change from v3.1.0: no longer requires a `.list` filter file — generates everything from csv2.
Key change from v3.3.0: removed the base-name skip — `-g` now generates base files too (the `skipped_base` counter was deleted).
Config files that already exist on disk are never overwritten.

### 8. ASCII-only output

Use `<-` not `←`, `->` not `→`. No Chinese characters anywhere.

### 9. Update command (-u) — sync csv2 edits to files

kiucong edits `area_feature.csv` (renames Config, changes Base Config), then
`syn_diff.py -u area_feature.csv` applies those edits to the `.v` files on disk.

**Pass 1 — sync Config names (rename files).** Exact filename match = unchanged
(claim it). For a csv2 Config with no exact on-disk match (a rename), fuzzy-match
against the unclaimed `.v` files with
`difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)` (pick best score;
claim as you go, in csv2 order). Rename via `os.rename`. No source found →
`[WARN]` and skip — kiucong said do NOT auto-create files (that's `-g`'s job).

**Pass 2 — sync Base Config (include_ix).** kiucong does NOT rename the Base
Config column when renaming configs, so the csv2 base reference is the OLD name.
Fuzzy-match it against current config names to re-resolve to the renamed base
file, then set the file's `` `include_ix "..." `` to that resolved name. Files
with no `include_ix` line (the top base config) are skipped untouched. An empty
Base Config column never occurs (kiucong confirmed) — handled defensively by skip.

**Backup & review (kiucong's choices for -u):**
- Backups go in a per-run **backup folder** `update_backup_<ts>/` (copy the file
  before any change), NOT `.bak.N` beside the file — that preference is specific
  to `-u`; other modes still use rolling `.bak.N`.
- Every fuzzy match (rename + base re-resolution) and every warning is written to
  a **review log** `update_review_<ts>.log` and printed, so kiucong can review.

**Full editing workflow:** edit csv2 → `-u` (sync to files) → `-e` (read the now-
resolved `include_ix` back into csv2's Base Config column). `-e` already exists.

When rewriting `.v` content, preserve encoding/BOM: read with `detect_encoding()`
(section 5), strip a leading `\ufeff` before regex, and re-prepend it on write
with the same detected encoding.
