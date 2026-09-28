# gen_syn_config.py — CSV-Driven Config File Generator

Generates Nuclei synthesis configuration files from a CSV manifest.

## CSV Format

Expected columns:
- **A (Type):** Section delimiter (`syn_config_00X.list`) or feature category (`ISA`, `LM`, `ICACHE`, etc.)
- **B (Feature):** Feature identifier (e.g., `ISA_ZBA_ZBB_ZBS`)
- **C (Config):** Output filename (e.g., `n300_syn_isa_zba_zbb_zbs.v`)
- **D (Base Config):** Parent config file for `include_ix` directive

Metadata rows (Type = `TECH`, `FREQ`, `Update Time`, `Type`) are skipped.

## Output

For each data row:
1. Creates `<Config>` file with `` `include_ix "<Base Config>"` `` as first line
2. Skips file creation if it already exists

For each `syn_config_00X.list` delimiter row:
1. Writes `<list_name>` file containing all Config values from that section
2. Each line: `syn_feature/<config_filename>`

Example output of `syn_config_000.list`:
```
syn_feature/n300_syn_isa_zba_zbb_zbs.v
syn_feature/n300_syn_isa_b.v
syn_feature/n300_syn_isa_b_k.v
...
```

## Chain Dependencies

Base Config values form a dependency chain (e.g., `n300_syn_isa_b_k.v` → `n300_syn_isa_b.v` → `n300_syn_base.v`). The script does NOT resolve this chain — it writes the Base Config reference as-is. The build tool handles traversal.
