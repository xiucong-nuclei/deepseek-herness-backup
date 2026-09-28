#!/usr/bin/env bash
# Sphinx label / cross-reference forensics.
# Locates the project, the build environment, the interpreter able to read
# environment.pickle, the registered label names, and duplicate entry points.
#
# Usage: run from the project root (the directory holding conf.py) or any parent:
#     bash sphinx-label-probe.sh
#
# NOTE: all output is intentionally plain ASCII English: the target machine has
# no CJK locale, and results are read back from terminal screenshots.

export LC_ALL=C   # deterministic collation, no locale warnings on bare servers
shopt -s nullglob

echo "### cwd: $(pwd)"

echo "### conf.py candidates"
find . -maxdepth 5 -name conf.py 2>/dev/null | head -5

echo "### environment.pickle"
find . -maxdepth 6 -name environment.pickle 2>/dev/null | head -5

echo "### aux files"
find . -maxdepth 6 -name '*.aux' 2>/dev/null | head -6

echo "### build dirs"
find . -maxdepth 4 -type d \( -name latex -o -name build -o -name _build -o -name doctrees \) 2>/dev/null | head -10

echo "### sphinx-build"
if command -v sphinx-build >/dev/null 2>&1; then
    command -v sphinx-build
    sphinx-build --version 2>&1 | head -2
else
    echo "  (sphinx-build not on PATH)"
fi

echo "### interpreters that can import sphinx"
for p in python python2 python3 .venv/bin/python venv/bin/python env/bin/python env/bin/python3; do
    command -v "$p" >/dev/null 2>&1 || continue
    v=$("$p" -c 'import sphinx;print(sphinx.__version__)' 2>/dev/null)
    [ -n "${v:-}" ] && echo "  HIT $p -> sphinx $v"
done

echo "### Makefile BUILDDIR / SPHINXBUILD"
for f in $(find . -maxdepth 4 -name Makefile 2>/dev/null | head -3); do
    echo "--- $f"
    grep -nE "BUILDDIR|SPHINXBUILD" "$f" | head -6
done

echo "### conf.py settings of interest"
for f in $(find . -maxdepth 5 -name conf.py 2>/dev/null | head -3); do
    echo "--- $f"
    grep -nE "autosectionlabel|exclude_patterns|master_doc|root_doc|latex_documents|numfig|source_suffix" "$f"
done

echo "### ref / label sites of interest"
grep -rn --include='*.rst' -E "memory-access-request-flow|Functional_Introductions" . 2>/dev/null | head -20

echo "### include target counts (desc)"
grep -rhoE '^\.\. include:: *[^ ]+' --include='*.rst' . 2>/dev/null \
    | sed 's/.*include:: *//' | sort | uniq -c | sort -rn | head -10

echo "### Revision_History occurrences"
grep -rn --include='*.rst' "Revision_History" . 2>/dev/null | head -20

echo "### label registry dump (from doctree cache)"
for f in $(find . -maxdepth 6 -name environment.pickle 2>/dev/null | head -2); do
    for p in python python2 python3 .venv/bin/python venv/bin/python env/bin/python env/bin/python3; do
        command -v "$p" >/dev/null 2>&1 || continue
        out=$("$p" - "$f" <<'PY' 2>/dev/null
import pickle, sys
e = pickle.load(open(sys.argv[1], 'rb'))
try:    d = e.domains['std']
except Exception: d = e.domaindata['std']
try:    L = d.data['labels']
except Exception:
    try:    L = d.labels
    except Exception: L = d['labels']
print('labels total:', len(L))
for k in sorted(L):
    if 'emory' in k or 'ntroduction' in k or 'cfg-cc' in k:
        print('  ', repr(k), '->', L[k][0], L[k][1])
PY
)
        if [ -n "$out" ]; then
            echo "  [$p] $f"
            echo "$out"
            break 2
        fi
    done
done
