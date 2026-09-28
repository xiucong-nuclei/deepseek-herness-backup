#!/usr/bin/env python3
"""
syn_diff.py - Synthesis result diff analysis

Five modes:
  -d, --diff     <csv1> <csv2>   Extract base config from syn_feature files,
                                  compute area/gate diff, write to csv2.
  -e, --extract  <csv2>          Extract base config from syn_feature files
                                  into csv2 Base Config column.
  -c, --collect  <csv1> <csv2>   Run ppa to collect synthesis results into csv1
                                  based on configs listed in csv2.
  -g, --gen      <csv2>           Generate all syn config files from csv2,
                                  write list files.
  -k, --check    <csv2> <kconfig> Check `define macros in syn_feature files
                                  against kconfig.

Environment variables required:
  PROJ_SRC_ROOT    Project source root
  PROJ_NAME        Project name

csv1 paths are resolved under:  $PROJ_SRC_ROOT/cpu_cct/syn/<csv1>
csv2 paths are resolved under:  $PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<csv2>

Examples:
  syn_diff.py -d syn_config_all.csv area_feature.csv
  syn_diff.py -e area_feature.csv
  syn_diff.py -c syn_config_all.csv area_feature.csv
  syn_diff.py -g area_feature.csv
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ============================================================
# Fixed synthesis parameters (edit as needed)
# ============================================================
PPA_FREQ = 100
PPA_TECH = "22,9t"
PPA_DC_FLAT = 1


# ============================================================
# Environment helpers
# ============================================================

def check_env():
    """Verify required environment variables exist."""
    missing = []
    for var in ('PROJ_SRC_ROOT', 'PROJ_NAME'):
        if not os.environ.get(var):
            missing.append(var)
    if missing:
        print(f"ERROR: Environment variable(s) not set: {', '.join(missing)}")
        print("Please run 'spr_cpu' to initialize environment variables")
        sys.exit(1)


def get_proj_root():
    return os.environ['PROJ_SRC_ROOT']


def get_proj_name():
    return os.environ['PROJ_NAME']


def get_syn_feature_dir():
    return str(Path(get_proj_root()) / get_proj_name() / 'configs' / 'syn_feature')


def get_csv1_path(csv1_name):
    return str(Path(get_proj_root()) / 'cpu_cct' / 'syn' / csv1_name)


def get_csv2_path(csv2_name):
    return str(Path(get_syn_feature_dir()) / csv2_name)


# ============================================================
# File utilities
# ============================================================

def detect_encoding(path: str) -> str:
    """Detect file encoding by reading BOM / first bytes."""
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


def backup_file(path: str) -> str:
    """Create rolling backup: path -> path.bak.1, path.bak.2, ..."""
    n = 1
    while True:
        bak = f"{path}.bak.{n}"
        if not Path(bak).exists():
            break
        n += 1
    shutil.copy2(path, bak)
    print(f"[BACKUP] {path} -> {bak}")
    return bak


# ============================================================
# Syn_feature file parsing
# ============================================================

def extract_include_ix(filepath: str) -> str | None:
    """Extract include_ix value from a syn_feature config file.

    Expected format: include_ix "xxx"  or  include_ix xxx
    """
    try:
        enc = detect_encoding(filepath)
    except (FileNotFoundError, PermissionError):
        return None
    try:
        with open(filepath, 'r', encoding=enc) as f:
            content = f.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return None
    m = re.search(r'include_ix\s+"([^"]+)"', content)
    if m:
        return m.group(1)
    m = re.search(r'include_ix\s+(\S+)', content)
    if m:
        return m.group(1).strip('"\'')
    return None


# ============================================================
# CSV1 synthesis results loader
# ============================================================

def load_syn_results(path: str) -> "tuple[dict, str, str]":
    """Read CSV1, return (config_mapping, tech_value, date_value)."""
    enc = detect_encoding(path)
    print(f"[CSV1] encoding={enc}")
    mapping = {}
    tech_val = date_val = ''
    with open(path, newline='', encoding=enc) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        print(f"[CSV1] columns: {fieldnames}")
        area_col = gate_col = tech_col = date_col = None
        for col in fieldnames:
            c = col.strip().lower().replace(' ', '').replace('_', '')
            if 'area' in c and area_col is None:
                area_col = col
            if ('gate' in c or 'gate_num' in c) and gate_col is None:
                gate_col = col
            if ('tech' in c or 'syn_tech' in c) and tech_col is None:
                tech_col = col
            if c == 'date' and date_col is None:
                date_col = col
        print(f"[CSV1] area_col='{area_col}' gate_col='{gate_col}' "
              f"tech_col='{tech_col}' date_col='{date_col}'")
        for row in reader:
            config = row.get('Config', '').strip()
            if not config:
                continue
            if not tech_val and tech_col:
                tech_val = row.get(tech_col, '').strip()
            if not date_val and date_col:
                date_val = row.get(date_col, '').strip()
            try:
                area = float(row.get(area_col, '').strip()) if area_col else None
            except (ValueError, AttributeError):
                area = None
            try:
                gate = float(row.get(gate_col, '').strip()) if gate_col else None
            except (ValueError, AttributeError):
                gate = None
            mapping[config] = {
                'Area': area,
                'Gate_num(k)': gate,
            }
    print(f"[CSV1] loaded {len(mapping)} records, tech='{tech_val}', date='{date_val}'")
    if mapping:
        sample = next(iter(mapping.items()))
        print(f"[CSV1] sample: {sample[0]} -> Area={sample[1]['Area']}, "
              f"Gate={sample[1]['Gate_num(k)']}")
    return mapping, tech_val, date_val


# ============================================================
# CSV2 reader helpers
# ============================================================

def read_csv2_structured(csv2_path: str) -> "tuple[list, list, list]":
    """Read csv2 and split into (meta_rows, fieldnames, data_rows).

    meta_rows are rows before the real header (TECH, UpdateTime, etc.).
    """
    enc = detect_encoding(csv2_path)
    with open(csv2_path, newline='', encoding=enc) as f:
        raw_lines = list(csv.reader(f))

    header_idx = None
    for idx, line in enumerate(raw_lines):
        if 'Type' in line and 'Feature' in line and 'Config' in line:
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError("Cannot find header row (Type/Feature/Config) in CSV2")

    meta_rows = raw_lines[:header_idx]
    fieldnames = raw_lines[header_idx]
    data_rows = raw_lines[header_idx + 1:]
    return meta_rows, fieldnames, data_rows


def write_csv2(output_path: str, meta_rows: list, fieldnames: list,
               rows: list):
    """Write csv2 preserving metadata rows."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for meta in meta_rows:
            writer.writerow(meta)
        writer.writerow(fieldnames)
        for row in rows:
            writer.writerow([row.get(col, '') for col in fieldnames])


def resolve_diff_columns(fieldnames: list) -> "tuple[str|None, ...]":
    """Find area/base_area/added_area/added_gate column names by fuzzy match."""
    area_alias = base_alias = added_area_alias = added_gate_alias = None
    for col in fieldnames:
        c = col.strip().lower().replace(' ', '').replace('_', '')
        if 'area' in c and 'base' not in c and 'added' not in c and area_alias is None:
            area_alias = col
        if 'base' in c and 'area' in c and base_alias is None:
            base_alias = col
        if 'added' in c and 'area' in c and added_area_alias is None:
            added_area_alias = col
        if 'added' in c and 'gate' in c and added_gate_alias is None:
            added_gate_alias = col
    return area_alias, base_alias, added_area_alias, added_gate_alias


# ============================================================
# Command: diff (-d)
# ============================================================

def cmd_diff(csv1_name: str, csv2_name: str):
    """-d mode: extract base config from files, compute diff, write to csv2."""
    csv1_path = get_csv1_path(csv1_name)
    csv2_path = get_csv2_path(csv2_name)
    sf_dir = get_syn_feature_dir()

    if not Path(csv1_path).exists():
        print(f"ERROR: csv1 not found: {csv1_path}")
        sys.exit(1)
    if not Path(csv2_path).exists():
        print(f"ERROR: csv2 not found: {csv2_path}")
        sys.exit(1)

    backup_file(csv2_path)
    syn, tech_val, date_val = load_syn_results(csv1_path)
    meta_rows, fieldnames, data_rows = read_csv2_structured(csv2_path)

    # Fill metadata rows with tech/date from csv1
    for line in meta_rows:
        if line and line[0].strip().upper() in ('TECH', 'SYN_TECH'):
            if tech_val:
                while len(line) < 2:
                    line.append('')
                line[1] = tech_val
        if line and line[0].strip().replace(' ', '').upper().startswith('UPDATETIME'):
            if date_val:
                while len(line) < 2:
                    line.append('')
                line[1] = date_val

    rows = [dict(zip(fieldnames, row)) for row in data_rows]
    area_col, base_col, added_a_col, added_g_col = resolve_diff_columns(fieldnames)
    print(f"[CSV2] area_col='{area_col}' base_area_col='{base_col}' "
          f"added_area_col='{added_a_col}' added_gate_col='{added_g_col}'")

    warnings = []
    mismatches = []

    for i, row in enumerate(rows, start=2):
        config_name = row.get('Config', '').strip()

        # --- Config lookup from csv1 ---
        if config_name:
            if config_name in syn:
                a = syn[config_name]['Area']
                g = syn[config_name]['Gate_num(k)']
                row['_area_val'] = a
                row['_gate_num'] = g
                if a is not None and g is not None and area_col:
                    row[area_col] = f"{a} ({g}k)"
            else:
                warnings.append(f"[WARN] Row {i}: Config '{config_name}' not found in CSV1")
                if area_col: row[area_col] = ''
                row['_area_val'] = None
                row['_gate_num'] = None
        else:
            if area_col: row[area_col] = ''
            row['_area_val'] = None
            row['_gate_num'] = None

        # --- Base Config: extract from syn_feature file ---
        file_base = extract_include_ix(str(Path(sf_dir) / config_name)) if config_name else None
        csv_base = row.get('Base Config', '').strip()
        if file_base:
            if csv_base and csv_base != file_base:
                mismatches.append(
                    f"[MISMATCH] Row {i}: Config '{config_name}' -- "
                    f"CSV2 Base Config='{csv_base}' "
                    f"but syn_feature file has include_ix='{file_base}'"
                )
            base_config_name = file_base
        else:
            base_config_name = csv_base

        # --- Base Config lookup from csv1 ---
        if base_config_name:
            if base_config_name in syn:
                a = syn[base_config_name]['Area']
                g = syn[base_config_name]['Gate_num(k)']
                row['_base_area_val'] = a
                row['_base_gate_num'] = g
                if a is not None and g is not None and base_col:
                    row[base_col] = f"{a} ({g}k)"
            else:
                warnings.append(f"[WARN] Row {i}: Base Config '{base_config_name}' not found in CSV1")
                if base_col: row[base_col] = ''
                row['_base_area_val'] = None
                row['_base_gate_num'] = None
        else:
            if base_col: row[base_col] = ''
            row['_base_area_val'] = None
            row['_base_gate_num'] = None

        # --- Compute diffs ---
        area_val = row.get('_area_val')
        base_area_val = row.get('_base_area_val')
        gate_val = row.get('_gate_num')
        base_gate_val = row.get('_base_gate_num')

        if area_val is not None and base_area_val is not None and added_a_col:
            try:
                row[added_a_col] = round(float(area_val) - float(base_area_val), 2)
            except (ValueError, TypeError):
                row[added_a_col] = ''
        elif added_a_col:
            row[added_a_col] = ''

        if gate_val is not None and base_gate_val is not None and added_g_col:
            try:
                row[added_g_col] = round(float(gate_val) - float(base_gate_val), 2)
            except (ValueError, TypeError):
                row[added_g_col] = ''
        elif added_g_col:
            row[added_g_col] = ''

    # Clean up temp columns
    for row in rows:
        for k in ('_area_val', '_base_area_val', '_gate_num', '_base_gate_num'):
            row.pop(k, None)

    out_fields = [f for f in fieldnames if not f.startswith('_')]
    write_csv2(csv2_path, meta_rows, out_fields, rows)

    print(f"[DIFF] processed {len(rows)} rows -> {csv2_path}")
    if mismatches:
        print(f"\n=== Base Config Mismatches ({len(mismatches)}) ===")
        print('\n'.join(mismatches))
    if warnings:
        print('\n'.join(warnings))
    else:
        print("All matched, no warnings.")

    # Summary
    max_cfg = max((len(row.get('Config', '').strip()) for row in rows
                   if row.get('Config', '').strip()), default=0)
    max_base = max((len(row.get('Base Config', '').strip()) for row in rows
                    if row.get('Base Config', '').strip()), default=0)
    print("\n=== Summary ===")
    for row in rows:
        cfg = row.get('Config', '').strip()
        base = row.get('Base Config', '').strip()
        if not cfg and not base:
            continue
        added_a = row.get(added_a_col, '') if added_a_col else ''
        added_g = row.get(added_g_col, '') if added_g_col else ''
        a_s = f"  Added_Area={float(added_a):+.2f}" if added_a not in (None, '') else ""
        g_s = f"  Added_Gate={float(added_g):+.2f}k" if added_g not in (None, '') else ""
        print(f"  {cfg:<{max_cfg}}  <-  {base:<{max_base}}{a_s}{g_s}")


# ============================================================
# Command: extract (-e)
# ============================================================

def cmd_extract(csv2_name: str):
    """-e mode: extract base config from syn_feature files, write to csv2."""
    csv2_path = get_csv2_path(csv2_name)
    sf_dir = get_syn_feature_dir()

    if not Path(csv2_path).exists():
        print(f"ERROR: csv2 not found: {csv2_path}")
        sys.exit(1)

    backup_file(csv2_path)
    meta_rows, fieldnames, data_rows = read_csv2_structured(csv2_path)

    # Ensure Base Config column exists
    base_col = None
    for col in fieldnames:
        if 'base' in col.strip().lower():
            base_col = col
            break
    if not base_col:
        base_col = 'Base Config'
        fieldnames.append(base_col)

    rows = [dict(zip(fieldnames, row)) for row in data_rows]
    updated = 0
    for row in rows:
        config_name = row.get('Config', '').strip()
        if config_name:
            sf_path = str(Path(sf_dir) / config_name)
            file_base = extract_include_ix(sf_path)
            if file_base:
                old_base = row.get(base_col, '').strip()
                if old_base != file_base:
                    updated += 1
                    print(f"  [{config_name}] Base Config: '{old_base}' -> '{file_base}'")
                row[base_col] = file_base
            else:
                print(f"  [WARN] [{config_name}] include_ix not found in {sf_path}")

    write_csv2(csv2_path, meta_rows, fieldnames, rows)
    print(f"[EXTRACT] Updated {updated} rows -> {csv2_path}")


# ============================================================
# Command: collect (-c)
# ============================================================

def cmd_collect(csv1_name: str, csv2_name: str):
    """-c mode: collect synthesis results into csv1 using ppa."""
    csv1_path = get_csv1_path(csv1_name)
    csv2_path = get_csv2_path(csv2_name)

    if not Path(csv2_path).exists():
        print(f"ERROR: csv2 not found: {csv2_path}")
        sys.exit(1)

    # Read config names from csv2 (skip metadata rows)
    _meta, fieldnames, data_rows = read_csv2_structured(csv2_path)
    configs = []
    for row_data in data_rows:
        row = dict(zip(fieldnames, row_data))
        cfg = row.get('Config', '').strip()
        if cfg:
            configs.append(f"syn_feature/{cfg}")

    if not configs:
        print("ERROR: No Config entries found in csv2")
        sys.exit(1)

    config_list = ' '.join(configs)
    cpu_cct_dir = str(Path(get_proj_root()) / 'cpu_cct' / 'syn')

    # Ensure output directory exists
    Path(csv1_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = (
        f"../bin/ppa -syn "
        f"-f \"{config_list}\" "
        f"--freq={PPA_FREQ} "
        f"--tech={PPA_TECH} "
        f"-dc_flat={PPA_DC_FLAT} "
        f"-get_data "
        f"--csv={csv1_name}"
    )
    print(f"[COLLECT] cd {cpu_cct_dir}")
    print(f"[COLLECT] {cmd}")

    result = subprocess.run(cmd, shell=True, cwd=cpu_cct_dir)
    if result.returncode != 0:
        print(f"ERROR: ppa failed with exit code {result.returncode}")
        sys.exit(1)
    print(f"[COLLECT] Done -> {csv1_path}")


# ============================================================
# Command: gen (-g)
# ============================================================

def cmd_gen(csv2_name: str):
    """-g mode: generate all syn config files from csv2 and write list files.

    csv2: CSV table (Type/Feature/Config/Base Config) in syn_feature.

    Generates config files for all entries in csv2, writes section .list files
    (syn_config_00X.list), and writes syn_config_all.list in syn_feature/
    with all generated configs.
    """
    csv2_path = get_csv2_path(csv2_name)
    sf_dir = get_syn_feature_dir()

    if not Path(csv2_path).is_file():
        print(f"ERROR: csv2 not found: {csv2_path}")
        sys.exit(1)

    # --- Read csv2: collect all configs and section groupings ---
    enc = detect_encoding(csv2_path)
    all_configs = {}         # config_name -> base_config
    section_order = []       # ordered section .list names
    section_configs = {}     # section_name -> [config_names]

    with open(csv2_path, newline='', encoding=enc) as f:
        reader = csv.reader(f)
        current_section = None
        for row in reader:
            if not any(row):
                continue
            row = [c.strip() for c in row]
            col_type = row[0] if len(row) > 0 else ''
            col_config = row[2] if len(row) > 2 else ''
            col_base = row[3] if len(row) > 3 else ''

            if col_type in ('', 'Type', 'TECH', 'FREQ', 'Update Time'):
                continue
            if col_type.endswith('.list') and 'syn_config' in col_type:
                current_section = col_type
                if current_section not in section_order:
                    section_order.append(current_section)
                continue
            if col_config:
                all_configs[col_config] = col_base
                if current_section:
                    section_configs.setdefault(current_section, []).append(col_config)

    all_names = set(all_configs.keys())
    print(f"[GEN] {len(all_configs)} config(s) total from {csv2_name}")

    # --- Generate config files ---
    generated = set()
    skipped_base = 0
    errors = 0

    for config_name, base_config in all_configs.items():
        if 'base' in config_name.lower():
            print(f"  SKIP {config_name} (base file)")
            skipped_base += 1
            continue
        if base_config and base_config not in all_names:
            print(f"  ERROR {config_name}: Base Config '{base_config}' not found")
            errors += 1
            continue
        create_config_file(config_name, base_config)
        generated.add(config_name)

    # --- Write section .list files (only generated configs) ---
    for sec_name in section_order:
        cfgs = section_configs.get(sec_name, [])
        valid = [c for c in cfgs if c in generated]
        if valid:
            write_list_file(sec_name, valid)

    # --- Write combined list file to syn_feature/ ---
    combined_list = str(Path(sf_dir) / 'syn_config_all.list')
    with open(combined_list, 'w') as f:
        for c in sorted(generated):
            f.write(f'syn_feature/{c}\n')

    print(f"\n[GEN] Done: {len(generated)} generated, {skipped_base} skipped, {errors} errors")
    print(f"  Combined list: {combined_list}")


# ============================================================
# Command: check (-k)
# ============================================================

def cmd_check(csv2_name: str, kconfig_name: str):
    """-k mode: check define macros in syn_feature files against kconfig.

    Reads each config file from csv2, extracts `define macros, and verifies
    they exist in kconfig (if kconfig file exists).

    csv2:    CSV table (Type/Feature/Config/Base Config) in syn_feature.
    kconfig: Kconfig file in syn_feature (may not exist).
    """
    csv2_path = get_csv2_path(csv2_name)
    sf_dir = get_syn_feature_dir()
    kconfig_path = str(Path(sf_dir) / kconfig_name)

    if not Path(csv2_path).is_file():
        print(f"ERROR: csv2 not found: {csv2_path}")
        sys.exit(1)

    # --- Read kconfig if exists ---
    kconfig_content = ''
    if Path(kconfig_path).is_file():
        with open(kconfig_path, 'r') as f:
            kconfig_content = f.read()
        print(f"[CHECK] kconfig loaded: {kconfig_path}")
    else:
        print(f"[CHECK] kconfig not found, skipping check: {kconfig_path}")

    # --- Read csv2 to get all config names ---
    enc = detect_encoding(csv2_path)
    configs = []
    with open(csv2_path, newline='', encoding=enc) as f:
        reader = csv.reader(f)
        for row in reader:
            if not any(row):
                continue
            row = [c.strip() for c in row]
            col_type = row[0] if len(row) > 0 else ''
            col_config = row[2] if len(row) > 2 else ''
            if col_type in ('', 'Type', 'TECH', 'FREQ', 'Update Time'):
                continue
            if col_type.endswith('.list') and 'syn_config' in col_type:
                continue
            if col_config:
                configs.append(col_config)

    print(f"[CHECK] {len(configs)} config(s) from {csv2_name}")

    # --- Check each config ---
    errors = 0
    total_defines = 0

    for config_name in configs:
        sf_path = str(Path(sf_dir) / config_name)
        if not Path(sf_path).is_file():
            print(f"  SKIP {config_name} (file not found)")
            continue

        enc = detect_encoding(sf_path)
        with open(sf_path, 'r', encoding=enc) as f:
            content = f.read()

        defines = re.findall(r'`define\s+(\S+)', content)
        if not defines:
            continue

        total_defines += len(defines)
        for macro in defines:
            if kconfig_content and not re.search(r'\b' + re.escape(macro) + r'\b', kconfig_content):
                print(f"  ERROR {config_name}: `define {macro}` not found in kconfig")
                errors += 1

    if not kconfig_content:
        print(f"\n[CHECK] {total_defines} define(s) found, kconfig not available — no checks performed")
    elif errors == 0:
        print(f"\n[CHECK] All {total_defines} define(s) OK")
    else:
        print(f"\n[CHECK] {errors}/{total_defines} error(s)")


def create_config_file(name, base_config):
    p = Path(name)
    if p.exists():
        print(f"  SKIP {name} (exists)")
        return
    line = f'`include_ix \"{base_config}\"' if base_config else ''
    p.write_text(line + '\n')
    print(f"  CREATE {name}")


def write_list_file(name, configs):
    p = Path(name)
    lines = '\n'.join(f'syn_feature/{c}' for c in configs) + '\n'
    p.write_text(lines)
    print(f"  LIST {name}: {len(configs)} entry(s)")


# ============================================================
# Main entry point
# ============================================================

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(
        description='Synthesis result diff analysis tool'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--diff', nargs=2,
                       metavar=('CSV1', 'CSV2'),
                       help='Compute area/gate diff and write to csv2')
    group.add_argument('-e', '--extract', metavar='CSV2',
                       help='Extract base config from syn_feature files into csv2')
    group.add_argument('-c', '--collect', nargs=2,
                       metavar=('CSV1', 'CSV2'),
                       help='Run ppa to collect synthesis results into csv1')
    group.add_argument('-g', '--gen', metavar='CSV2',
                       help='Generate syn config files from csv2 and write list files')
    group.add_argument('-k', '--check', nargs=2,
                       metavar=('CSV2', 'KCONFIG'),
                       help='Check define macros in syn_feature files against kconfig')

    args = parser.parse_args()

    check_env()

    try:
        if args.diff:
            cmd_diff(args.diff[0], args.diff[1])
        elif args.extract:
            cmd_extract(args.extract)
        elif args.collect:
            cmd_collect(args.collect[0], args.collect[1])
        elif args.gen:
            cmd_gen(args.gen)
        elif args.check:
            cmd_check(args.check[0], args.check[1])
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
