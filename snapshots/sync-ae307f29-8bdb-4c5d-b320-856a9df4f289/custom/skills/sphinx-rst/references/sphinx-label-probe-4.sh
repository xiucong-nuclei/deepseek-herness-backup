export LC_ALL=C
cd /home/jiaxiucong/repo/cpu_doc/n600/databook/build || exit 1
TEX=build/latex/Nuclei_600_Product_Databook.tex
echo "A) ref line 147 of Gui_Configuration.rst"
sed -n '147p' source/nuclei/Gui_Configuration.rst
echo "B0) is source/nuclei a symlink farm?"
ls -la source/nuclei | head -12
echo "B) toctree head of nuclei/index.rst"
sed -n '1,30p' source/nuclei/index.rst
echo "C) who includes Feature_SMP_6.rst"
grep -Rn --include='*.rst' 'Feature_SMP_6' source | head -5
echo "D) Revision_History mentions in .tex (line numbers)"
grep -n 'Revision_History' "$TEX" | head -10
echo "E) chapter/section markers for Revision History"
grep -c 'chapter{Revision History' "$TEX"
echo "F) python versions available"
ls /home/share/tools/python/ 2>/dev/null | head -20
