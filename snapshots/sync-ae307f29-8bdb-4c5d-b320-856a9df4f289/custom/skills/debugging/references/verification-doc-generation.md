# Verification Doc Generation — Python + Sphinx RST Pipeline

## Overview

Nuclei SDK verification uses a Python script (`gen_cpu_mk.py`) to auto-generate Sphinx RST documentation from CPU feature test case directories. The pipeline:

```
pass_case.list (case list)
  → Python script iterates each case
    ├─ Reads README.md → "Description"
    ├─ Reads check_cpufeature.h #error lines → "Feature Require"
    ├─ Reads output.pdf (reference output image) → "Reference Output"
    └─ Writes cpu_features_test.rst
       → Sphinx → LaTeX → PDF
```

## Python Script Structure

### Path Setup

```python
sdk_path = "../nuclei-sdk"  # relative to script location
cpu_features_dir = os.path.join(sdk_path, 'application', 'cpu_features')
```

The RST file is generated in the current directory, then processed/copied to `build/source/nuclei/` by the build system.

### Section Generation (per case)

The script generates these subsections for each case:

| Section | Source | Code |
|---------|--------|------|
| Description | `README.md` (skip `#` lines) | `read_text_lines()` |
| Case Path | Directory path | `os.path.join(cpu_features_dir, case)[3:]` |
| Feature Require | `check_cpufeature.h` `#error` lines | `grep + split("'")` |
| Run command | Template | `make run_sdk TESTNAME={case_name}` |
| Wave command | Template | `make wave_sdk TESTNAME={case_name}` |
| Reference Output | `output.pdf` in case dir | `.. figure::` directive |

### Extracting Feature Requirements from check_cpufeature.h

```python
require_file = os.path.join(cpu_features_dir, case, "check_cpufeature.h")
if os.path.exists(require_file):
    with open(require_file) as r1_file:
        for line in r1_file:
            if line.startswith("#error"):
                require_list.append(line.strip().split("'")[1])
```

For a `#error` line like:
```c
#error 'CFG_HAS_AMO' 'This case require CPU AMO feature'
```
`split("'")[1]` extracts `CFG_HAS_AMO`.

### Adding Reference Output Image

```python
gen_title(w_file, "Reference Output", case_level+1)
output_pdf = os.path.join(cpu_features_dir, case, "output.pdf")
if os.path.exists(output_pdf):
    rst_fig_path = os.path.join(cpu_features_dir, case, "output.pdf")  # keep ../ prefix
    w_file.write(".. figure:: " + rst_fig_path + "\n")
    w_file.write("   :width: 100 %\n")
    w_file.write("   :align: center\n")
    w_file.write("   :alt: Reference output\n\n")
else:
    w_file.write("*No reference output*\n\n")
```

### Title Generator

The script uses nested heading levels for doc structure:

```python
def gen_title(w_file, title, level):
    w_file.write(f"{title}\n")
    symbols = {1: "=", 2: "+", 3: "-", 4: "#"}
    s = symbols.get(level, " ")
    w_file.write(s * len(title) + "\n\n")
```

## Path Resolution Pitfall

**Critical**: `.. figure::` paths are resolved by Sphinx **relative to the RST file's directory**, not the Python script's directory.

| Script runs | RST ends up at | Path prefix needed |
|---|---|---|
| `cpu_case_doc/` | `cpu_case_doc/build/source/nuclei/` | `../../../../` from RST to project root |

If the Python script generates the path as `../nuclei-sdk/...` and the RST is moved to `build/source/nuclei/`, Sphinx resolves it as `build/source/nuclei/../nuclei-sdk/...` = `build/source/nuclei-sdk/...` → **wrong**.

**Fix**: Keep the `../` prefix intact (don't `[3:]` strip it), or compute the correct number of parent-directory hops. See `references/sphinx-rst-image-path.md` for detail.

## Makefile Integration

```makefile
# Generate reference output image
getpng:
	# Dynamic target - see references/makefile-dynamic-targets.md
	cp $(PNG_PATH)/*.png "$$case_dir/output.png"
	convert "$$case_dir"/output.png -flatten "$$case_dir"/output.pdf
	rm -f "$$case_dir"/output.png

# Generate PDF documentation
pdf:
	python3 gen_cpu_mk.py ...  # generates .rst
	cd build && make latexpdf   # Sphinx → PDF
```

## Makefile collect_pass Target

The `collect_pass` target collects test results (PASS + feature requirement lines) from per-case log files — see `references/makefile-dynamic-targets.md > Related Pattern`.
