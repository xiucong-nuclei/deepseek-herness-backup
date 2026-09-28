export LC_ALL=C
cd /home/jiaxiucong/repo/cpu_doc/n600/databook/build || exit 1
echo "### pwd: $(pwd)"
echo "### conf.py lines 160-200 (latex_documents / latex_appendices)"
sed -n '160,200p' source/conf.py
echo "### where the section title lives"
grep -rn --include='*.rst' "Memory Access Request Flow" . 2>/dev/null | head -10
echo "### exact :ref: line, cat -A (shows trailing/odd chars)"
for f in $(grep -rl --include='*.rst' 'memory-access-request-flow' . 2>/dev/null | head -3); do
  n=$(grep -n 'memory-access-request-flow' "$f" | head -1 | cut -d: -f1)
  echo "--- $f:$n"
  sed -n "${n}p" "$f" | cat -A
done
echo "### toctree context around Revision_History"
for f in $(grep -rl --include='*.rst' 'Revision_History' . 2>/dev/null | head -3); do
  echo "--- $f"
  grep -n -B12 -A2 'Revision_History' "$f" | head -30
done
echo "### duplicate labels in generated .tex (count>1 = duplicate)"
grep -o '\\label{\\detokenize{[^}]*}}' build/latex/*.tex | sed 's/.*detokenize{//; s/}}$//' | sort | uniq -c | sort -rn | head -25
echo "### duplicate newlabel in .aux"
grep -o '\\newlabel{[^}]*}' build/latex/*.aux | sort | uniq -c | sort -rn | head -15
echo "### can python3 unpickle the doctree cache (traceback NOT hidden)"
python3 -c "import pickle;e=pickle.load(open('build/doctrees/environment.pickle','rb'));print('OK', type(e))"
