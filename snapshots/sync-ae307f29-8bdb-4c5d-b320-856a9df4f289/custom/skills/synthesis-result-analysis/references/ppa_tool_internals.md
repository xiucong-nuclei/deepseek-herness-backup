# ppa Tool Internals (report extraction side)

The `ppa` tool lives at `cpu_cct/bin/ppa` and is invoked by `syn_diff.py -c`
(collect) with:

```
../bin/ppa -syn -f "<config_list>" --freq=100 --tech=22,9t -dc_flat=1 -get_data --csv=<csv1_name>
```

It runs the synthesis flow and then extracts PPA data from report files. The
functions below were surfaced while reverse-engineering it.

## `-get_data` flag

```python
parser.add_argument('-get_data', '--get_data', action='store_true',
                    help='Only extract PPA data')
```

- **Boolean switch** (`store_true`): write `-get_data` or `--get_data` with NO
  value (never `-get_data=1` / `-get_data xxx`). Present → True, absent → False.
- Semantics: only extract PPA data from already-produced synthesis results, skip
  re-running synthesis / the full flow. Use when results already exist and you
  just want to re-aggregate data.
- `syn_diff.py -c` already appends `-get_data` unconditionally, so it is not
  needed when going through `syn_diff.py`; it matters only when calling `ppa`
  directly.

## `parse_syn_path(path_list) -> list[str]`

Normalizes a list of inputs into valid report paths. Each `path` is either a
report directory or a list file (text file whose lines are report paths).

```python
def parse_syn_path(path_list):
    rpt_path_list = []
    for path in path_list:
        if not os.path.exists(path):
            print(Fore.RED + Back.WHITE + f"Input path doesn't exists: {path}")
            continue
        if os.path.exists(os.path.join(path, "../syn.log")):
            syn_log = os.path.join(path, "../syn.log")
        else:
            syn_log = os.path.join(path, "../latest_syn.log")
        if os.path.exists(syn_log):
            rpt_path_list.append(path)   # path is a valid report dir
        else:
            with open(path) as r_file:   # path is a list file
                for line in r_file:
                    line = line.replace("\n", "")
                    rpt_path_list.append(line)
    return rpt_path_list
```

Key facts:
- **syn.log path = `os.path.join(path, "../syn.log")` = the PARENT directory of
  `path`, not inside `path`.** `os.path.join` does not normalize `..`, but
  `os.path.exists` resolves it, so it equals `dirname(path)/syn.log`.
- Priority: `syn.log` first, fall back to `latest_syn.log`.
- If neither log exists, `path` is treated as a list file and expanded line by
  line. This is the recursive/unwrap case.
- Design assumption: `syn.log` sits one level up from the report directory
  (e.g. `sub_designs/syn_n900_core_wrapper/syn.log` with reports in a
  subdirectory).

## `get_syn_info(rpt_path)` return layout

`extract_syn_data_line` indexes it as:

| index | meaning | bound to |
|-------|---------|----------|
| `[0]` | (unused here) | — |
| `[1]` | cfg / config name | `cfg` |
| `[2]` | top module name | `top` (only when caller passed empty) |
| `[3]` | freq | `freq` |
| `[4]` | tech | `tech` |

## `extract_syn_data_line(options, rpt_path, top="")`

`top` is an OPTIONAL parameter defaulting to `""`. If empty it is auto-derived:

```python
if not top:
    top = syn_info[2]   # top module name from get_syn_info
```

Report file path convention (built with `os.path.join(rpt_path, ...)`):

| variable | filename |
|----------|----------|
| `dc_area_rpt` | `{top}.mapped.area.rpt` |
| `dc_timing_rpt` | `{top}.mapped.timing.rpt` |
| `r2r_timing_rpt` | `{top}.mapped.reg2reg_timing.rpt` |
| `r2o_timing_rpt` | `{top}.mapped.reg2out_timing.rpt` |
| `dc_clk_gate_rpt` | `{top}.mapped.clock_gating.rpt` |
| `dc_run_time_rpt` | `dc_runtime_summary.rpt` (fixed, no `top`) |
| `threshold_v_rpt` | `threshold_voltage_group.rpt` (fixed, no `top`) |
| `pt_power_rpt` | `../reports/pt/report_power.report` (PT power, fixed) |

## `FATAL: must load prime-time Error 9` (pre_setm target)

Symptom in the DC/make flow:

```
make setm
FATAL: must load prime-time Error 9
make[4]: *** [pre_setm] Error 9
make[3]: *** [dc] Error 2
make[2]: *** [syn] Error 2
make[1]: *** [syn] Error 2
```

Meaning: the `pre_setm` / `setm` step invokes a PrimeTime-only command (STA /
multi-scenario / DMSA / `report_*` timing options) inside a `dc_shell` session
that has NOT loaded PrimeTime. `Error 9` is the Tcl error code. The cascading
`dc` / `syn` `Error 2` entries are just make propagating the failure upward —
not new errors.

Root-cause directions (in order of likelihood):
1. PrimeTime license feature not available / not checked out — verify with
   `lmstat -a -c $LM_LICENSE_FILE`.
2. Script uses a PT-only command in `dc_shell`.
3. The `setm` step is meant to run under `pt_shell`, not the DC make target.

To pinpoint, inspect the `pre_setm` / `setm` recipe in the Makefile and its Tcl
script, plus `.synopsys_dc.setup`.
