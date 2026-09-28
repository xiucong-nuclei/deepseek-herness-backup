# `:ref:` 的标签命名空间 ≠ LaTeX 的标签名（含 `\newlabel` 第三字段之谜）

排障场景：`WARNING: undefined label` 报找不到标签，但在 `build/latex/*.aux` 里明明能搜到同名标签；
以及表格 `.aux` 的 `\newlabel` **标题字段被"上一个章节标题"污染**。
两者是**互不相关的两个独立现象**，且后者不会引起前者（2026-09 源码核实，Sphinx master / docutils 0.23）。

## 1. `undefined label` 的真凶：两套名字天生不同

### 注册侧（read 阶段，`autosectionlabel`）

`sphinx/ext/autosectionlabel.py`（v5.3 → master 各版本一致）：

```python
labelid = node['ids'][0]
ref_name = getattr(title, 'rawsource', title.astext())
name = nodes.fully_normalize_name(docname + ':' + ref_name)   # prefix_document=True
domain.anonlabels[name] = docname, labelid
domain.labels[name] = docname, labelid, sectname
```

**键来自"标题原文"，不是节点 id。** `docutils.nodes.fully_normalize_name` 实测：

```
fully_normalize_name('nuclei/Functional_Introductions:Memory Access Request Flow')
  -> 'nuclei/functional_introductions:memory access request flow'
# 实现：' '.join(name.lower().split()) —— 小写，空格保留，不转连字符
```

### 查找侧（write 阶段，`:ref:`）

`sphinx/domains/std/__init__.py`：

```python
'ref': XRefRole(lowercase=True, innernodeclass=nodes.inline, warn_dangling=True)
```

`sphinx/roles.py` 的 `create_xref_node`：`if self.lowercase: target = target.lower()` —— **只做小写**，不折叠空格、不做 slug 转换。随后：

```python
def _resolve_ref_xref(...):
    if node['refexplicit']:
        docname, labelid = self.anonlabels.get(target, ('', ''))
    else:
        docname, labelid, sectname = self.labels.get(target, ('', '', ''))
    if not docname:
        return None        # -> warn_missing_reference -> "undefined label: %r"
```

`self.labels.get(target)` 是**原样字典查表**。因此：

| 写法 | 是否命中 |
|---|---|
| `:ref:`nuclei/Functional_Introductions:Memory Access Request Flow`` | ✅ 命中小写+空格的键（`lowercase=True` 兜住大小写） |
| `:ref:`nuclei/Functional_Introductions:memory-access-request-flow`` | ❌ 连字符 ≠ 空格 |
| `:ref:`memory-access-request-flow`` | ❌ 既无 docname 前缀也无空格 |

### `.aux` 里的标签从哪来（为什么"明明有"）

`sphinx/writers/latex.py`：

```python
def hypertarget(self, id, withdoc=True, anchor=True):
    if withdoc:
        id = self.curfilestack[-1] + ':' + id
    return (r'\phantomsection' if anchor else '') + r'\label{%s}' % self.idescape(id)

def hypertarget_to(self, node, anchor=False):
    return ''.join(self.hypertarget(i, anchor=False) for i in node['ids'])
```

即 LaTeX 标签 = `docname + ':' + node_id`，而 `node_id` 是 docutils `make_id` 生成的
**连字符 slug**。这个 `\label` 对**每个带 `ids` 的节点**都会输出，**与 std 域注册表无关**——
有没有被任何角色注册过，它都在 `.aux` 里。

> 所以"`.aux` 有它、Sphinx 却不认"不是"不同步"，而是**两套命名空间**：
> `.aux` 用**节点 id 的连字符形式**，std 域注册表用**标题原文的小写空格形式**。
> 从 `.aux` / HTML 锚点里抄标签名去写 `:ref:`，必然不命中。

**修复**：用标题原文（空格），或改加显式 `.. _label:` 后引用。清理缓存、改大小写、改 `:name:`、
换 `table`/`list-table` 都不会改变这条匹配规则。

## 2. `\newlabel` 第三字段被"上一个章节标题"污染

`.aux` 的 5 字段形式 `\newlabel{name}{{num}{page}{title}{anchor}{}}` 中：
- 第 3 字段 = `\@currentlabelname`，**只被 hyperref 的 `\nameref` 与 PDF 书签使用**；
- Sphinx 的引用生成的是 `\hyperref[<label>]{...}` / `\ref{...}`，只看第 1、2 字段与第 4 个锚点。

⇒ **第三字段错误不会造成 `Reference ... undefined`**；把它当根因是误判。

### 机制（源码链）

1. 赋值点只有两类：章节命令、`\@caption`。
   - `hyperref.dtx:11353-11364`：
     ```latex
     \long\def\@caption#1[#2]#3{%
       \expandafter\ifx\csname if@capstart...\endcsname \csname iftrue\endcsname
         \global\let\@currentHref\hc@currentHref     % 只有锚点是 global
       \else \hyper@makecurrent{\@captype}\fi
       \@ifundefined{NR@gettitle}{%
         \def\@currentlabelname{#2}%                  % 局部 def
       }{\NR@gettitle{#2}}%
     ```
   - `nameref.dtx:429-432`（默认随 hyperref 加载）：
     ```latex
     \def\NR@gettitle#1{\GetTitleString{#1}\let\@currentlabelname\GetTitleStringResult}
     ```
     同样是**局部** `\let`，没有 `\global`。
2. Sphinx 的表格是**非浮动**表格，标题走：
   `\sphinxcapstartof{table}` + `\sphinxcaption{...}`，而
   `sphinx/texinputs/sphinxlatextables.sty:224` 的 `\spx@caption` 把 `\caption` 包在
   `\noindent\hb@xt@\linewidth{\hss\vtop{...\caption[{#1}]{...}...}\hss}` 里——**一个 TeX 分组**。
3. 模板把 `\label` 排在 `\sphinxcaption{...}` 之后（`sphinx/templates/latex/tabular.tex.jinja`、
   `longtable.tex.jinja`）：
   ```
   \sphinxcapstartof{table}
   \sphinxthecaptionisattop
   \sphinxcaption{<caption>}\label{\detokenize{...}}
   \sphinxaftertopcaption
   ```
   ⇒ `\label` 求值时**分组已经结束**。
4. 结果：锚点（第 4 字段，被 `\global\let` 恢复）与编号正确，
   而 `\@currentlabelname` 的局部赋值随分组消失 → 退回**上一个章节命令留下的标题**。
5. 无标题表格走模板另一分支 `\phantomsection\label{...}`，根本没有 caption，
   名字自然是同一个残留值 → 同一种污染（这就是"自动生成 idXX 标签也被污染"的原因）。

### 结论与处置

- 这是 **hyperref `\capstart` 路径只 global 化锚点、未 global 化名字**造成的状态泄漏，
  Sphinx 因使用非浮动标题而触发。**不是 `list-table` 的 bug**：
  `.. table::` 网格表、`:class: longtable` 共用同一套 `\sphinxcaption` 与模板，
  换指令写法**无效**。
- 真要修正第三字段：`\usepackage{etoolbox}` + 把 `\NR@gettitle` 的 `\let` 改成 `\global\let`；
  或直接忽略（Sphinx 不读它）。

## 3. `Label 'doc::doc' multiply defined`

`\label{\detokenize{<docname>::doc}}` 在排版结果里出现两次 ⇒ **同一 docname 的内容被排进 PDF 两遍**。
常见来源：该 `.rst` 既被 `.. include::` 又被 toctree 收录；glob toctree 与显式条目重叠；
同一文件在 `latex_documents` 或 toctree 中列了两次。这条**是**真会破坏引用的（重定义后指向错误目标），
优先级高于第 2 节。

定位：
```bash
grep -rn "Revision_History" --include=*.rst .
grep -rn "^\.\. include::" --include=*.rst . | awk '{print $2}' | sort | uniq -c | sort -rn | head
```

## 快速自检命令

现成脚本：`sphinx-label-probe.sh`（本目录，纯 ASCII）。在工程根或其上级执行
`bash sphinx-label-probe.sh`：自动定位 `conf.py` / `environment.pickle` / latex 构建目录、
探测能 `import sphinx` 的解释器、dump 标签注册表、统计 include 重复与 `Revision_History` 出现处。

> **约束**：目标机器无中文 locale，终端结果靠截图 OCR 读回 —— 交给用户执行的脚本，
> 其注释、`echo` 输出、错误提示**一律英文**；中文只留在本知识与文档里。

```bash
# 1) read 阶段到底注册了什么（决定性证据，比 -vvv 精确）
python -c "import pickle;e=pickle.load(open('build/doctrees/environment.pickle','rb'));\
d=e.domains['std'];L=getattr(d,'data',{}).get('labels') or d.labels;\
print(len(L));print('\n'.join(k for k in L if 'emory' in k or 'ntroduction' in k))"

# 2) 表格标签在 .tex 中的现场（验证第 2 节机制）
grep -n -B4 -A2 "<name 或 caption slug>" build/latex/*.tex

# 3) LaTeX 侧
grep -nE "multiply defined|Reference .* undefined" build/latex/*.log
```

其它手段：`missing-reference`/`warn-missing-reference` 事件里打印 `repr(node['reftarget'])`
（查隐藏字符）与 `difflib.get_close_matches` 最近邻键——定位"名字形式不匹配"最省力。
`warning` 里的行号可用 `python3 -c "print(repr(open(f).read().split(chr(10))[N-1]))"` 反查源行。

## Confirmed case: nuclei databook `undefined label` (2026-xx)

Evidence chain (all from the real project, Sphinx build tree under `n600/databook/build`):

- `source/nuclei/*.rst` are **symlinks** into the repo root `n600/databook/*.rst` (plus a
  `Makefile` symlink). Hence the docname prefix `nuclei/` comes from the symlink path, while
  the real files live flat in the repo root. `grep -r` does NOT follow those symlinks, so
  plain recursive greps silently return nothing; use `grep -R` or `find -L`.
- Ref site: `source/nuclei/Gui_Configuration.rst:147`
  `:ref:`nuclei/Functional_Introductions:memory-access-request-flow`` (cat -A confirms no
  trailing space / no high byte). No `.. _memory-access-request-flow:` exists anywhere.
- The section title lives in `databook_share/Feature_SMP_6.rst:47`, outside the source tree,
  pulled in by `include` from `nuclei/Functional_Introductions.rst` -> the autosectionlabel
  key is `nuclei/functional_introductions:memory access request flow` (lowercase, SPACES).
- `:ref:` -> `XRefRole(lowercase=True)` -> `target.lower()` -> `labels.get(...)` -> hyphenated
  form can never match. Fix = write the ref with the title text, not the HTML/LaTeX anchor slug.

### Local reproduction of the `::doc` question (sphinx 9.0.4, /tmp/lab)

Baseline 4-file project: 4 `\label{<docname>::doc}` labels, **no** `\appendix`, no duplicate.
The natural label line shape is `\label{<doc>::<title-slug>}\label{<doc>::doc}`.

Variants tried to force a duplicate `::doc` -- all failed (Sphinx dedupes):
- same doc in two different toctrees (master + sub-index)
- `:glob:` with `*` plus an explicit entry
- same doc listed twice in one toctree -> `WARNING: duplicated entry found in toctree [toc.duplicate_entry]`
- `a.rst` and `./a.rst` in one toctree -> same warning
- `include` of a doc that is also a toctree child
- symlinked source files

Conclusion: `visit_document` (latex.py, sole `hypertarget(':doc')` site in 4.5.0 and master)
fires once per document node, so a duplicated `::doc` means two document nodes for one
docname. Since a duplicate toctree path is caught and deduped, the trigger is something else
and must be read off the generated `.tex`: both occurrences of `nuclei/Revision_History::doc`
sit on the SAME line 113 while `\chapter{Revision History` occurs exactly once -> content is
laid out once, the label is emitted twice. Check with:

    awk 'NR==113' TEX | grep -o 'detokenize{[^}]*}' | sed 's/detokenize{//'

### Lessons

- Long probe output read through screenshots is unreliable: keep every probe's output under
  ~10 short lines, and prefer `awk '$1>1'` style filters over `head -25` dumps.
- Python-unpickle probes: `environment.pickle` written under Python 3.8+ uses protocol 5 and
  raises `ValueError: unsupported pickle protocol: 5` on any 3.7 interpreter. A PATH `python3`
  that cannot load it is proof that the build used a different interpreter.

## Second trap: `:ref:` resolves but renders as BLACK PLAIN TEXT

Symptom: `.. _X:` is defined, `:ref:`X`` in another document renders as black,
non-clickable text showing the literal name `X`; no `undefined label` warning appears.

Mechanism, source-verified in Sphinx 4.5.0 (`sphinx/domains/std.py`):

* `process_doc` (lines 729-768) puts **every** explicit label into `anonlabels`
  (name -> docname, labelid). That is why the anchor exists in HTML and why
  `\label{<docname>:<anchor>}` exists in the LaTeX `.aux`.
* The label is **also** copied into `labels` (name -> docname, labelid, **sectname**)
  only when the node carrying it is: a `section` (sectname = its title), a `rubric`,
  an enumerable node **with a caption** (table/figure; `continue` if no caption),
  or a toctree with a `caption`. Otherwise: anonymous-only.
* `_resolve_ref_xref` (lines 818-834): `:ref:`X`` without an explicit title reads
  `labels` and returns None on a miss; `:ref:`Text <X>`` (`refexplicit=True`) reads
  `anonlabels` and uses `Text`, so it works regardless of placement.
* `warn_missing_reference` (lines 1097-1106) chooses the message: target not in
  `anonlabels` -> `undefined label: %s`; target in `anonlabels` but no link text ->
  **`Failed to create a cross reference. A title or caption not found: %s`**
  (warning type `ref.ref`). Grepping only for `undefined label` misses it.

Measured with sphinx 9.0.4 + `-b latex`/`-b html`:

| label placed directly above | anchor emitted | entry in `labels` | result of `:ref:`X`` |
|---|---|---|---|
| a section title | yes | yes (title) | link, text = section title |
| a titled `list-table` | yes | yes (caption) | link, text = table caption |
| an **untitled** table | yes | **no** | black text "X" + warning |
| a paragraph | yes | **no** | black text "X" + warning |
| (any placement) | yes | yes | `:ref:`Text <X>`` always links |

In the LaTeX `.tex` a failed `:ref:` emits no `\hyperref` at all, just
`\DUrole{xref}{\DUrole{std}{\DUrole{std-ref}{X}}}` -> black, non-clickable in the PDF.

Fixes: move the label directly above the section title (preferred), give the table a
`:title:`/caption, or write `:ref:`X <X>`` (explicit link text).

Fastest way to tell the two failure modes apart without rebuilding: read the cached
environment and compare the two dicts --
`d.data['anonlabels'][k]` present while `d.data['labels'].get(k)` is None means
"anchor exists, no link text".

## ROOT CAUSE: silent black text from NoUri (Sphinx 4.1.2, nuclei databook)

Confirmed on the nuclei databook (build host whdoc02, `/usr/bin/python3` = Python 3.9.2,
Sphinx 4.1.2; SPHINXBUILD comes from `build/Makefile:29  SPHINXBUILD ?= /usr/local/bin/sphinx-build`).
Note: `build/doctrees/environment.pickle` can only be unpickled by that interpreter
(protocol 5); the py3.7.3 on PATH cannot read it.

Symptom: `:ref:`X`` renders as plain black text, no hyperlink, and **no warning at all**,
even after the label exists and is fully registered (both `anonlabels` and `labels`,
with link text). 17 refs broken vs 181 working in one book.

Three code lines explain it:

    # sphinx/domains/std.py:798-810   build_reference_node
    newnode['refuri'] = builder.get_relative_uri(fromdocname, docname)   # to = TARGET doc
    # sphinx/builders/latex/__init__.py:139-147
    def get_target_uri(self, docname, typ=None):
        if docname not in self.docnames:   # docnames = docs really inlined into the PDF
            raise NoUri(docname, typ)
    # sphinx/transforms/post_transforms/__init__.py:102-103   ReferencesResolver.run
    except NoUri:
        newnode = None        # skips warn_missing_reference -> unresolved AND silent

So: resolution SUCCEEDS in the domain, then the LaTeX builder rejects the target
docname, and the exception is swallowed. `\DUrole{xref,std,std-ref}{...}` in the .tex
is the fingerprint (the pending_xref's inner inline keeps the `xref` class);
a resolved ref looks like `\hyperref[...]{\sphinxcrossref{\DUrole{std}{\DUrole{std-ref}{...}}}}`
(note: no `xref` class inside).

Trigger in this repo: shared fragments are mirrored into the source tree
(`source/nuclei/databook_share/*.rst`), so Sphinx reads each fragment as a standalone
document. Its explicit label registration happens AFTER the includer's and wins for the
plain (unprefixed) name, so the winning entry points at a docname that is not in any
toctree -> not in `builders.latex.docnames` -> NoUri. The 31
"document isn't included in any toctree" warnings are the same orphan docs.

Fix: keep fragments out of the document registry:

    exclude_patterns.append('nuclei/databook_share/**')   # source/conf.py

`.. include::` still works (it reads from the filesystem, not the doc registry).
After the fix the label registers only under the includer docname
(`nuclei/Functional_Introductions`), which IS in the book, so refs resolve.

Diagnostics that settled it (all pure ASCII, run from `build/`):
- `/usr/bin/python3 - build/doctrees/environment.pickle` then
  `e.domaindata['std']['labels']` / `['anonlabels']` (a plain dict here, NOT `.labels`),
  and `e.get_doctree(docname)`: a cached doctree may still contain pending_xref nodes,
  and printing `node.get('refwarn')` shows whether a warning was expected.
- `grep -o 'DUrole{xref[^}]*}' build/latex/*.tex | wc -l` vs `grep -c sphinxcrossref ...`
  splits the book into unresolved vs resolved refs in one shot.
- two failure modes must not be confused: `undefined label` (name form mismatch:
  hyphen/id form vs title form) vs silent NoUri (name form correct, target doc outside
  the LaTeX book).
