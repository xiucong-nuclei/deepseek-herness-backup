export LC_ALL=C
cd /home/jiaxiucong/repo/cpu_doc/n600/databook || exit 1
TEX=$(ls build/build/latex/*.tex build/latex/*.tex 2>/dev/null | head -1)
ENV=$(ls build/build/doctrees/environment.pickle build/doctrees/environment.pickle 2>/dev/null | head -1)
echo "P) tex=$TEX env=$ENV"
echo "1) label definition site, with placement context"
grep -Rn -B3 -A2 --include='*.rst' --include='*.md' '_Memory Access Request Flow' . 2>/dev/null | head -10
echo "2) ref site, raw bytes"
grep -Rn --include='*.rst' --include='*.md' 'ref:.*Memory Access Request Flow' . 2>/dev/null | cat -A | head -4
echo "3) which node carries the anchor in HTML"
grep -rno '<[a-z]*[^>]*id="memory-access-request-flow"' build/build/html 2>/dev/null | head -3
echo "4) labels vs anonlabels"
for p in /home/share/tools/python/python3.9.0/bin/python3 /home/share/tools/python/python3.10.0/bin/python3; do
  [ -x "$p" ] || continue
  "$p" - "$ENV" <<'PY' 2>&1 | head -8
import pickle, sys
e = pickle.load(open(sys.argv[1], 'rb'))
d = e.domains['std']
L = getattr(d, 'data', {}).get('labels') or d.labels
A = getattr(d, 'data', {}).get('anonlabels') or d.anonlabels
for k in sorted(A):
    if 'memory access request flow' in k:
        print('anonlabels:', repr(k), '->', A[k])
        print('labels    :', repr(k), '->', L.get(k, 'ABSENT -> no link text'))
PY
done
echo "5) how the ref was emitted in the .tex (needs a fresh latex build)"
grep -o '.\{0,45\}Memory Access Request Flow.\{0,25\}' "$TEX" 2>/dev/null | head -3
