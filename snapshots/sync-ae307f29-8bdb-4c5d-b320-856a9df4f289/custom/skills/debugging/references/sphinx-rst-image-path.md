# Sphinx RST Image Path Pitfalls

## The Problem

A Python doc-generation script constructs paths like:

```python
cpu_features_dir = "../nuclei-sdk/application/cpu_features"
rst_fig_path = os.path.join(cpu_features_dir, case, "output.pdf")[3:]   # ← BUG
```

The `[3:]` strips `../` to make a "clean" path like `/nuclei-sdk/application/cpu_features/.../output.pdf`.

**But** this only works if the generated `.rst` file is in the **same directory** as where the Python script ran. If the RST gets moved to a deeper directory (e.g. `build/source/nuclei/`), the path is now wrong:

```
RST at:    build/source/nuclei/cpu_features_test.rst
Image ref: nuclei/nuclei-sdk/application/.../output.pdf
Resolved:  build/source/nuclei/nuclei/nuclei-sdk/...  ← WRONG!
```

Sphinx resolves `.. figure::` and `.. image::` paths **relative to the RST file's directory**.

## The Fix

**Don't strip `../`** — keep it. The relative path from the original script directory to the file is exactly what Sphinx needs, provided the RST file stays in the same relative position:

```python
# ❌ Wrong — strips "../" making the path relative to cwd, not RST location
rst_fig_path = os.path.join(cpu_features_dir, case, "output.pdf")[3:]

# ✅ Correct — keeps "../" as relative path from RST to picture
rst_fig_path = os.path.join(cpu_features_dir, case, "output.pdf")
```

## Why This Happens

The original code used `[3:]` on `case_path` too:

```python
case_path = os.path.join(cpu_features_dir, case)[3:]
```

But `case_path` was used as **display text** (a literal string in a `Case Path` section), not as a file reference. Sphinx doesn't try to open it — it's just text on the page. So the `[3:]` was harmless there.

For `.. figure::` and `.. image::`, Sphinx **actually opens the file** — the path must be correct.

## The `[3:]` Origin

`cpu_features_dir = "../nuclei-sdk/application/cpu_features"` → the first 3 characters are `../`. The `[3:]` was intended to strip these for cleaner display. This was safe for display-only paths but broken for file references.

## Diagnosis

When pdflatex runs, check the Sphinx log for:

```
WARNING: image file not readable: <some path>
```

The error message shows exactly what path Sphinx resolved. Compare it against the RST file's actual directory to confirm the mismatch.
