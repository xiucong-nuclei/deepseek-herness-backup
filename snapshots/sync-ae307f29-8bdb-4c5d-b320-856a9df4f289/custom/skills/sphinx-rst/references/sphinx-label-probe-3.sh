export LC_ALL=C
cd /home/jiaxiucong/repo/cpu_doc/n600/databook/build || exit 1
TEX=build/latex/Nuclei_600_Product_Databook.tex

echo "### source layout (grep -r does NOT follow symlinks)"
readlink -f source; readlink -f source/conf.py
ls -la source | head -25
echo "### conf.py: appendices / toctree_only / prolog"
grep -n "appendices\|toctree_only\|rst_prolog\|inc_content" source/conf.py | head -10

echo "### source files reachable WITH symlinks followed"
find -L . -maxdepth 5 \( -name '*.rst' -o -name '*.md' \) 2>/dev/null | head -25

echo "### title / ref / Revision_History (grep -R follows symlinks; rst + md)"
grep -Rn --include='*.rst' --include='*.md' -E "Memory Access Request Flow|memory-access-request-flow|Revision_History" . 2>/dev/null | head -25

echo "### raw bytes of every line mentioning Functional_Introductions"
for x in $(grep -Rl --include='*.rst' --include='*.md' 'Functional_Introductions' . 2>/dev/null | head -6); do
  echo "--- $x"
  grep -n 'Functional_Introductions' "$x" | head -5 | cat -A
done

echo "### all ::doc labels in .tex, file order"
grep -o '\\label{\\detokenize{[^}]*::doc}}' "$TEX" | head -60
echo "### appendix markers in .tex"
grep -c '\\appendix' "$TEX"
echo "### context of the duplicated ::doc"
grep -n -B6 -A2 'Revision_History::doc' "$TEX" | head -40

echo "### python candidates able to load the doctree cache (protocol 5 needs py3.8+)"
for p in $(command -v python3) /usr/bin/python3 /usr/local/bin/python3 /home/share/tools/python/*/bin/python3; do
  [ -x "$p" ] || continue
  info=$("$p" -c 'import sys,sphinx;print(sys.version.split()[0], "sphinx", sphinx.__version__)' 2>/dev/null)
  [ -n "$info" ] || continue
  echo "  candidate: $p -> $info"
  "$p" - <<'PY' 2>&1 | head -20
import pickle
try:
    e = pickle.load(open('build/doctrees/environment.pickle', 'rb'))
except Exception as ex:
    print('    load failed:', repr(ex))
else:
    try:    d = e.domains['std']
    except Exception: d = e.domaindata['std']
    try:    L = d.data['labels']
    except Exception:
        try:    L = d.labels
        except Exception: L = d['labels']
    print('    sphinx version in cache:', getattr(e, 'version', '?'))
    print('    labels total:', len(L))
    for k in sorted(L):
        if 'emory' in k or 'ntroduction' in k or 'cfg-cc' in k:
            print('    ', repr(k), '->', L[k][0], L[k][1])
PY
done
