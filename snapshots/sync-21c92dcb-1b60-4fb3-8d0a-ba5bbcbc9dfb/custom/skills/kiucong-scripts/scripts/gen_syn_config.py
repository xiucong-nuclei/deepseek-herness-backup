#!/usr/bin/env python3
"""
Generate syn config files from CSV.

Usage: gen_syn_config.py <csv_file>

CSV columns: Type, Feature, Config, Base Config, Gen, Compile, Syn

For each row:
  1. Create Config file (Column C), skip if exists, first line: `include_ix "Base_Config"`
  2. At each syn_config_00X.list row, write .list file with syn_feature/ prefixed Config values
"""

import csv
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <csv_file>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.is_file():
        print(f"File not found: {csv_path}")
        sys.exit(1)

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)

        current_list = None
        section_configs = []
        all_list_files = []

        for row in reader:
            if not any(row):
                continue

            row = [c.strip() for c in row]
            if not any(row):
                continue

            col_type = row[0] if len(row) > 0 else ''
            col_feature = row[1] if len(row) > 1 else ''
            col_config = row[2] if len(row) > 2 else ''
            col_base = row[3] if len(row) > 3 else ''

            if col_type in ('', 'Type', 'TECH', 'FREQ', 'Update Time'):
                continue

            if col_type.endswith('.list') and 'syn_config' in col_type:
                if current_list and section_configs:
                    write_list_file(current_list, section_configs)
                    all_list_files.append((current_list, section_configs.copy()))
                current_list = col_type
                section_configs = []
                continue

            if col_type == 'Base':
                if col_config:
                    create_config_file(col_config, col_base)
                continue

            if col_config:
                create_config_file(col_config, col_base)
                section_configs.append(col_config)

        if current_list and section_configs:
            write_list_file(current_list, section_configs)
            all_list_files.append((current_list, section_configs.copy()))

    print(f"\nDone.")
    for name, cfgs in all_list_files:
        print(f"  {name}: {len(cfgs)} config(s)")


def create_config_file(name, base_config):
    p = Path(name)
    if p.exists():
        print(f"  SKIP {name} (exists)")
        return

    line = f'`include_ix "{base_config}"' if base_config else ''
    p.write_text(line + '\n')
    print(f"  CREATE {name}")


def write_list_file(name, configs):
    p = Path(name)
    lines = '\n'.join(f'syn_feature/{c}' for c in configs) + '\n'
    p.write_text(lines)
    print(f"  LIST {name}: {len(configs)} entry(s)")


if __name__ == '__main__':
    main()
