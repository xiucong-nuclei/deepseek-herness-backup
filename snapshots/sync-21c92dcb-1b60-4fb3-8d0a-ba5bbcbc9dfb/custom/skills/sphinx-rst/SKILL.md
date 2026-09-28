---
name: sphinx-rst
description: Sphinx/reStructuredText documentation authoring — tables, cross-references, raw directives, inline styling, build troubleshooting, LaTeX/PDF output.
metadata:
  hermes:
    tags:
    - sphinx
    - rst
    - restructuredtext
    - documentation
    - latex
    - pdf
    - cross-reference
    version: 1.0.0
    author: Hermes Agent (from session with kiucong)
    license: MIT
---

# Sphinx / RST 文档编写

面向基于 Sphinx 的技术文档（HTML + LaTeX/PDF 输出）编写与排障 reStructuredText。涵盖表格、交叉引用、`.. raw::` 指令、行内代码样式与构建修复。

## 何时使用

当用户处于以下场景：
- 编写或调试用于 Sphinx 的 `.rst` 源文件
- 排查 `make html` / `make latexpdf` 构建错误或警告
- 添加跨文件引用、表格、raw 指令或自定义样式
- 询问 Sphinx 输出的 `conf.py` 配置

## 交叉引用

### `:ref:` — 基于标签（任意位置）

在目标文件中定义标签：
```rst
.. _my-label:

Target Section Title
--------------------
```

从任意文件中引用：
```rst
详见 :ref:`my-label`
```

- `:ref:` 是 **Sphinx 标准角色**——无需任何扩展
- 反引号必须**紧贴**角色：`:ref:`my-label``（无空格）
- 标签名是全局的——同文件与跨文件语法一致
- 目标文件必须在 `toctree` 中

**避免 PDF 中出现页码：** `:ref:`label`` 在 LaTeX/PDF 输出中可能渲染为 “page X”。改用显式显示文本形式可消除页码——Sphinx 将该文本原样用作链接，不附加任何页码信息：
```rst
:ref:`display text <label>`
```
例如 `:ref:`isa_b.v <isa_b.v>`` 只渲染为可点击的 `isa_b.v`，无页码。也适合展示比原始章节标题更友好的显示文本。

**标签语法——单冒号与双冒号：**
- `.. _label:`（单冒号）——标准 RST 目标，纯 docutils 即可解析。副作用：若紧随其后出现**同文本**的标题，docutils 会警告 `Duplicate implicit target name`（标题会自动创建同名隐式目标）；Sphinx 可能警告 “duplicate label”。
- `.. _label::`（双冒号）——Sphinx 为 `:ref:` 目标提供的自定义标签形式。纯 docutils 会将其报为 `malformed hyperlink target`，但 Sphinx 接受这种写法，且不会与紧随其后的标题隐式目标冲突。

权衡：单冒号是标准写法、docutils 无警告，但有重复目标风险；双冒号是 Sphinx 专用。两者在 Sphinx 的 `:ref:` 中均可解析。

### `:ref:` 需要显式标签——而不是裸章节标题

Sphinx 的 `:ref:` 只解析显式 `.. _label:` 目标（或 `autosectionlabel` 扩展）。它**不**解析普通的章节标题隐式目标。已在 Sphinx 9 上验证：`:ref:`isa_b.v <isa_b.v>`` 引用字面标题为 `isa_b.v` 的章节会报 `WARNING: undefined label: 'isa_b.v' [ref.ref]`。如果为了消除重复目标警告而删除显式标签，`:ref:` 链接会静默失效。绝不能假设章节标题文本本身就是一个合法的 `:ref:` 标签。

### 无标签章节链接：纯 RST 短语引用 `` `text <title>`_ ``

不借助任何显式标签即可链接到章节的可靠做法，是使用标准 RST 引用，解析到标题的隐式锚点：

```rst
See `isa_b.v`_ and `custom text <isa_b.v>`_.
```

两者都能生成可用的锚点链接（HTML 中为 `href="#isa-b-v"`），无需 `.. _` 行，不渲染页码，且是纯 RST（docutils 与 Sphinx 均接受）。目标就是章节标题文本。只要想实现无需标签的文档内跳转，就使用这种形式。

### 网格表格单元格内跨物理行的行内标记

RST 行内标记（反引号引用 / 解释文本）**可以**跨越单个网格表格单元格内的物理行；换行符在渲染文本中折叠为一个空格。该空格是浏览器的软换行点，因此较长的单元格名称可在折行处整齐换行：

```rst
| `safety_lockstep_split_
| ioprot <safety_lockstep_split_ioprot.v>`_     (both lines inside one cell)
```

- 纯短语引用 `` `...`_ `` 跨行折行时**无任何警告**。
- `:ref:` 跨行折行会触发 `WARNING: Inline interpreted text or phrase reference start-string without end-string.`——跨行单元格优先使用纯短语引用形式。
- 若要把单元格限制在固定窄宽度，可按字符折行显示文本（若腾出空间，可先去掉 `.v` 之类的尾部后缀）。源列宽度 = 最宽的源行；`:widths:` 独立控制**渲染后**的列比例，因此源列可以很宽（含标记开销）而渲染得窄。

### 下划线 `_` 幽灵引用陷阱

RST 会把紧跟在单词之后、且后面是空白/行尾的下划线视为**超链接引用标记**（`word_` → 目标 `word`）。若目标不存在，会报 `ERROR: Unknown target name: "word".` 这类错误很容易无意触发、又很难发现，因为文本看起来就是普通的行文/名称：

- **折行后以 `_` 结尾的单元格行**——例如将 `ilm_dlm_sram_64k_addr_ecc` 按宽度 22 字符折行得到 `ilm_dlm_sram_64k_addr_`（尾部 `_`）→ 产生指向 `ilm_dlm_sram_64k_addr` 的幽灵引用。
- **空格前带 `_` 的行文/特性文本**——例如 `LOCKSTEP+IO_ PROT`（`IO_ ` 是对 `lockstep+io` 的幽灵引用）；docutils 会把目标转为小写。这在插值名称的生成式引言句子中容易踩坑。

修复方法（两者结合）：
1. 程序化折行标识符/配置名时，**只**在 `_` 分隔符处断开——紧跟下划线之后（行以 `_` 结尾），绝不在点号处或单词中间断开。尾部 `.v` 要保持完整（例如 `ilm_dlm_sram_64k_addr_` + `ecc.v`）。这是用户确认的配置名折行偏好（`dcache32k_prefetch_axi.v` 折为 `dcache32k_prefetch_` + `axi.v`）。对该尾部 `_` 应用逐行反斜杠转义（规则 2），使 RST 不会将其识别为引用——只要尾部下划线被转义，在 `_` 后断开就没问题。
2. 对行文中会触发引用的下划线做反斜杠转义：`re.sub(r'_(\s|$)', r'\\_\1', text)` 将 `IO_ PROT` 变为 `IO\_ PROT`（渲染结果相同，且不产生引用）。

通过检查构建出的 HTML / 构建日志来确认单元格干净——残留 `Unknown target name` 说明有 `_` 漏网。

### 本地 Sphinx 构建验证（无系统级 Sphinx）

当主机没有 Sphinx、又必须确认生成的 `.rst` 确实能构建时，在一次性 venv 中安装 Sphinx——切勿污染系统：

```bash
python3 -m venv /tmp/sphenv && /tmp/sphenv/bin/pip install -q sphinx
mkdir -p /tmp/sphbuild/src && cp out.rst /tmp/sphbuild/src/report.rst
cat > /tmp/sphbuild/src/index.rst <<'RST'
Index
=====

.. include:: report.rst
RST
cd /tmp/sphbuild && rm -rf _b && ../sphenv/bin/python -m sphinx -b html src _b 2>&1 \
  | grep -iE 'warning|error' | grep -viE 'toctree|not included'
```

构建干净（过滤 toctree 噪声后 0 警告/0 错误）才是真实的地面真相——单靠 docutils 无法校验 Sphinx 角色（`:ref:`、`:widths:`、`.. highlight::`），它对未知角色的报错文本还会误导人。由于指令文本本身不会字面出现在输出中，请通过 HTML 中的 `<col width=...>` / 渲染出的列比例确认 `:widths:` 生效。

### `:doc:` — 文件级引用

跳转到文件顶部，而非某个具体章节：
```rst
详见 :doc:`chapter2`
```

不带 `.rst` 后缀。目标文件无需标签。

### `autosectionlabel` — 零标签交叉引用

在 `conf.py` 中添加：
```python
extensions = ['sphinx.ext.autosectionlabel']
autosectionlabel_prefix_document = True
```

然后按精确的标题文本引用章节：
```rst
详见 :ref:`CFG_CORE_PFX 选项`
```

章节标题在文件间必须唯一（或使用 `prefix_document`）。

### 用替换变量同步 list-table 内容

当 list-table 行中包含也出现在正文中的文档名或引用字符串（例如 “Referenced Documents” 表格中的每一条目在文档其他位置都有引用）时，两处重复书写会带来维护负担。问题就是表格与正文的编辑失同步。

**解决方案：** 在共享的 `.. include::` 文件中定义 `rst_epilog` 风格的替换变量（`.. |VAR| replace:: text`），表格单元格与正文文本同时使用。无需修改 `conf.py`。

**第 1 步——** 创建 `common/doc_refs.rst`：

```rst
.. |ARMv8| replace:: ARMv8-A Architecture Reference Manual
.. |RISCV_PRIV| replace:: RISC-V Privileged Specification
.. |AXI4| replace:: AMBA AXI4-Stream Protocol Specification
```

**第 2 步——** 在每个引用这些变量的 `.rst` 文件顶部添加一行：

```rst
.. include:: ../common/doc_refs.rst
```

**第 3 步——** 随处使用 `|VAR|`：

表格：
```rst
.. list-table:: Referenced Documents
   :name: ref-docs
   :header-rows: 1

   * - Document Name
     - Version
   * - |ARMv8|
     - DDI 0487J.a
   * - |RISCV_PRIV|
     - 20211203
```

正文：
```rst
The design follows |ARMv8| exception model and |RISCV_PRIV| privileged architecture.
```

修改 `common/doc_refs.rst` 中的文档名 → 所有 `.. include::` 它的 `.rst` 文件自动更新。`.. list-table::` 与 `.. table::` 均适用。

**常见陷阱：**
- `|VAR|` 渲染为**纯文本**，而非超链接。此方法解决的是内容同步，不是可点击的交叉引用。
- 若还需要可点击链接，请将 `|VAR|` 与其他位置的 `.. _label:` 定义搭配使用。
- 在每个文件中，`.. include::` 行必须出现在首次使用 `|VAR|` 之前。

## 表格

### `.. list-table::` 指令——项目符号列表式表格

```rst
.. list-table:: Table Title Here
   :name: short-unique-id
   :widths: 30 35 35
   :header-rows: 1
   :class: longtable

   * - Column 1
     - Column 2
     - Column 3
   * - Value 1
     - Value 2
     - Value 3
```

**多行单元格：** 同一缩进级别的每个 `-` 都成为独立的一列。**不要**用 `|`（line block）承载多行单元格内容——会产生多余的垂直间距。改为在单行内使用逗号分隔的值：

```rst
# ❌ BAD: | line blocks add blank lines
   * - param
     - desc
     - | value1
       | value2
       | value3

# ✅ GOOD: comma-separated
   * - param
     - desc
     - value1, value2, value3
```

另一种做法是把每个值放在单元格下各自缩进的 `-` 上，但这仅在该单元格是最后一列时有效（Sphinx 会将尾部的 `-` 项合并进最后一个单元格）。

**RST 构建错误：** `uniform two-level bullet list expected, but row 2 does not contain the same number of items as row 1 (8 vs 3)`——意思是某数据行的 `-` 项比表头行多。每个 `-` 就是一列。检查单个单元格内的多行值是否被拆到了多个 `-` 项目上。

### `.. tabularcolumns::` — 逐列对齐（仅 LaTeX/PDF）

放在表格指令**之前**。使用 LaTeX 列描述符：

```rst
.. tabularcolumns:: |c|m{0.30\\linewidth}|c|

.. list-table::
   ...

   * - Centered
     - Vertically centered + wraps
     - Centered
```

| Descriptor | 水平 | 垂直 |
|-----------|-----------|----------|
| `l` | 左 | 居中 |
| `c` | 居中 | 居中 |
| `r` | 右 | 居中 |
| `p{width}` | 左 + 换行 | 顶部 |
| `m{width}` | 左 + 换行 | **居中** |
| `b{width}` | 左 + 换行 | 底部 |

`m{}` 需要 `array` 宏包（Sphinx LaTeX builder 默认会加载）。仅影响 PDF 输出；HTML 忽略 `tabularcolumns`。

```rst
.. table:: Table Title Here
   :name: short-unique-id
   :class: longtable
   :width: 100%
   :widths: 28 18 18 18 18

   +-----+-----+-----+-----+-----+
   | Col1 | Col2 | Col3 | Col4 | Col5 |
   +-----+-----+-----+-----+-----+
   | val  | val  | val  | val  | val  |
   +-----+-----+-----+-----+-----+
```

完整示例见 `references/complex-grid-table-example.rst`（含多行单元格、Yes/No/TBD 取值和脚注的多列行为矩阵）。

**程序化**生成网格表格（含纵向合并/rowspan 单元格）、ASCII 安全输出（用 unicode 转义表示 `µm²`）以及正确的标题下划线长度，见 `references/grid-table-rowspan-programmatic.md`。

**常见陷阱：**
- `:widths:` 的值使用**空格**而非逗号：`28 18 18 18 18` ✅ / `28, 18, 18, 18, 18` ❌
- 表格网格必须在指令下**缩进**（3 个空格）——否则 Sphinx 不会将其识别为指令内容
- `:name:` 必须是**简短唯一的标识符**（例如 `mem-if-support`），不能与标题重复
- **不要**把标题作为单独一行文本放在 `.. table::` 与表格网格之间——会破坏指令
- `.. table:: Title` 与标题必须放在**同一行**
- 上述任一项出错，表格都不会显示标题（Sphinx 会静默丢弃畸形指令）
- **脚注必须放在 `.. table::` 指令之外。** 在指令内容块内部（网格表格之后、但仍在缩进块内）定义 `.. [N]` 脚注会触发：`WARNING: Error parsing content block for the "table" directive: exactly one table expected.` 将脚注定义移到指令之后，缩进级别与 `.. table::` 相同

### 宽度控制

| Option | 作用 |
|--------|-------------|
| `:width: 100%` | 表格总宽度（需要 `%` 单位） |
| `:widths: 28 18 18 18 18` | 列比例（无单位，相对整数） |

全宽表格：同时使用 `:width: 100%` 与 `:widths:`。

### 用 `numfig` 自动编号

在 `conf.py` 中：
```python
numfig = True
```

然后给表格添加 `:name:`：
```rst
.. table:: Table Title
   :name: table-id
```

渲染为 “Table 1.2: Table Title”，编号可点击。

### 电子表格 → RST：保留原始列结构

将 `.xlsx`/CSV 表格转换为 RST 表格时，输出**必须镜像源表格的列结构**，包括任何分组/合并列——绝不能压扁成更少的列。源表格为 `指令类型 | 指令名称 | 执行延时 | 执行吞吐率`（4 列）就必须保持 4 列；丢掉分组列（`指令类型`/`Instruction Type`）产出的结果会被用户以 “格式和原始 excel 中对不上” 为由打回。

- 分组列保留为**第一列**，表头做翻译（例如 `指令类型` → `Instruction Type`），扩展/类型名称也翻译（`P扩展（DSP)指令` → `P (DSP)`、`自定义DSP指令` → `P (DSP) Custom`）。
- RST 的 `.. list-table::` **没有合并单元格**。在视觉上模拟源表的合并单元格分组：把类型值放在**该组的第一行，后续行留空**（不要每行重复）。空白用 `''` 表示，这样不会渲染成用于真实缺失数据的 `—` 占位符。
- 组内规范化：统一大小写/命名（例如半精度助记符统一为 `H_*`）、删除重复的指令行、修正明显的笔误（`H_SUB` → `H_FSUB`）。在摘要中标注这些改动，供用户确认。
- 用程序（openpyxl）生成而非手敲数百行：**识别合并单元格的读取器**会把每个合并区域左上角的值传播到该区域的所有单元格（openpyxl 只在左上角返回值）。对分组列做前向填充。交付前再用 `[\u4e00-\u9fff]` 正则扫描输出，**确认零残留 CJK**。完整做法：`references/xlsx-to-rst-conversion.md`。
- **指令执行时间章节**（N300/N600/N900 `*_指令执行时间.xlsx` → RST）的语义层在 `references/instruction-execution-time-tables.md`：用户认可的 RV32/RV64 4 列拆分（`RV32 Execute Latency | RV32 Execute Throughput | RV64 ...`），每个表都要有 caption 名称；特殊值措辞映射（``---`` / `Stalls the pipeline` / `Unpredictable` / `Same as latency (state-machine implementation)`）；以及各扩展的陷阱——RV64 专用指令在 RV32 列必须强制为 `---`；K 是 YES/NO 矩阵，需要按支持集并集做行合并；P 的 RV32 与 RV64 助记符不相交，因此 P **拆分**为两张独立的 3 列表格（每个指令集一张）；F/D/ZFH 左列共享指令同时适用于两种 XLEN；C 不做 XLEN 拆分（3 列表格）；特殊值映射必须在每个 sheet 上统一应用（裸 `str()` 会漏出 `阻塞执行` → 无法通过零 CJK 检查）。

## `.. raw::` 指令

### 语法

内容**必须缩进**（3 个空格）到指令之下：

```rst
.. raw:: latex

   \renewcommand{\texttt}[1]{{\ttfamily\bfseries #1}}

.. raw:: html

   <style>
   code.docutils.literal { background: #f3f3f3; padding: 1px 3px; border-radius: 2px; }
   </style>
```

⚠️ **指令与内容之间允许空行**，但内容必须保持一致的缩进。缺少缩进 = Sphinx 警告：`Content block expected for the "raw" directive; none found.`

### 行内代码（`` ``xxx`` ``）样式

RST `` ``xxx`` `` → Sphinx → LaTeX `\texttt{xxx}` 或 HTML `<code>`

- **HTML**：在文件顶部用 `.. raw:: html` 注入 CSS
- **PDF/LaTeX**：在文件顶部的 `.. raw:: latex` 中用 `\renewcommand{\texttt}`
- 替代方案：用 `conf.py` 的 `latex_elements['preamble']` 或 `html_css_files` 做全局修改

## 构建排障

### `undefined label` / `.aux` 里明明有标签却不认 / `\newlabel` 标题被污染

`autosectionlabel` 注册的标签键是**标题原文的小写空格形式**（`fully_normalize_name(docname + ':' + 标题)`），
`:ref:` 只做 `lower()` 后**原样查表**；而 `.aux` 里的标签是 LaTeX writer 输出的 **`docname:节点id`（连字符）**，
与注册表无关。从 `.aux` / HTML 锚点抄标签名写 `:ref:` 必然 `undefined label`——必须用标题原文。
表格 `\newlabel` 第三字段（`\@currentlabelname`）被上一章节标题污染，是 hyperref `\capstart`
只 global 化锚点所致，**与引用解析无关**，换 `table`/`list-table` 也无效。
完整源码链、判定命令与规避规则见 `references/ref-label-namespaces-and-latex.md`，
现成自检脚本为 `references/sphinx-label-probe.sh`（注释与输出一律英文——目标机器无中文 locale，结果靠截图读回）。

### WaveDrom 嵌入

WaveDrom 语法、严格 JSON 要求、信号名对齐以及间隙/省略模式，见 `references/wavedrom.md`。

### `make latexpdf` 挂起

原因：`pdflatex` 遇到错误后进入**交互模式**，等待用户输入。

**快速修复：**
```bash
make latexpdf LATEXOPTS="-interaction=nonstopmode"
```

**永久修复**——在项目根目录（`Makefile` 旁）创建 `latexmkrc`：
```perl
$pdflatex = "pdflatex -interaction=nonstopmode %O %S";
```

这样 LaTeX 会越过错误继续运行，让你一次性看到所有警告。

### 表格宽度错误

```
WARNING: Error in "table" directive
not a positive measure of one of the following units: ...
```

原因：`:width:` 或 `:widths:` 语法有误。

修复：
- `:widths:` → 空格分隔的整数：`28 18 18`（无逗号、无单位）
- `:width:` → 需要单位：`100%`（不是裸的 `100`）

### `Could not lex literal_block ... Highlighting skipped`

原因：Sphinx/Pygments 尝试对 `::` 字面块做语法高亮，但无法确定词法分析器——例如没有语言提示的 Verilog/`.v` 配置内容（默认为 `python3`，猜测会失败或选错）。

修复：在文件顶部添加 `.. highlight:: none`。它会把文档其余部分的默认高亮语言设为 `none`，Pygments 因此跳过这些块：
```rst
.. highlight:: none
```
`.. highlight::` 是 Sphinx 专属指令——纯 docutils 会报 `Unknown directive type "highlight"`，但 Sphinx 支持它。替代方案：在 `conf.py` 中设置 `highlight_language = 'none'`（全局生效），或者若确实想高亮，把该块包进 `.. code-block:: verilog`（或真正的词法分析器）。

### toctree 警告

```
WARNING: toctree contains reference to nonexisting document 'nuclei/changelog'
```

从父文件的 `toctree` 指令中移除该引用。

### 文档不在 toctree 中

```
WARNING: document isn't included in any toctree
```

把该文件加入某个 `toctree` 指令；如果是有意为之（例如仅 `.. include::`），可忽略。

## 用 `rst_epilog` 做全局文本替换

在 `conf.py` 中使用 `rst_epilog` 定义全局同步的文本别名——**改一处，所有引用随之更新**。

```python
# conf.py
rst_epilog = """
.. |ARMv8| replace:: ARMv8-A Architecture Reference Manual
.. |RISCV_PRIV| replace:: RISC-V Privileged Specification
.. |AXI4| replace:: AMBA AXI4-Stream Protocol Specification
"""
```

可在任意 `.rst` 文件中使用（表格单元格、正文、admonition）：

```rst
* - |ARMv8|
  - DDI 0487J.a

该设计符合 |ARMv8| 中定义的异常模型。
```

**关键特性：**
- 替换渲染为**纯文本**，**不是**超链接——无法跨文件跳转
- `|...|` 与相邻文本或标点之间不留空格：`|ARMv8|，` / `|ARMv8|。`
- 表格用法：`|NAME|` 可用于 `.. table::`（网格表格）和 `.. list-table::` 的单元格
- 最适合：文档名出现在多个文件且必须保持一致性的引用文档表格

**与 `:ref:` 对比：**
| 模式 | 源文件变更时自动更新 | 可点击链接 |
|---------|---------------------------|----------------|
| `:ref:`label`` | 是（显示目标标题） | 是 |
| 通过 `rst_epilog` 的 `|NAME|` | 是（文本同步） | 否 |
| 单元格中的 `` _`text` `` | 否（手动复制） | 仅同文件 |

当同时需要自动同步**和**可点击链接时，把列表项转换为带 `:ref:` 的章节（见上文“交叉引用”）。

## SMP 特性领域知识

Nuclei SMP 特性章节领域笔记（N600）：`references/scu-domain-notes.md`（SCU 一致性点角色、shadow-data-tag 实现、Icache-snoop-Dcache 机制 + `CC_CTRL.I_SNOOP_D_EN` 门控）与 `references/clm-iocp-domain-notes.md`（CLM 复位信号/寄存器、IOCP 行缓冲 / 写流式 / 预取 / 传输 / 用法）。整个 SMP 章节的正文风格规则：`references/smp-chapter-style-conventions.md`。

## 常见陷阱

- **`:ref:` 间距**：`:ref:`label`` 反引号要紧贴——`:ref:` 与开头反引号之间不留空格
- **表格网格缩进**：必须在 `.. table::` 指令下缩进
- **`.. table::` 标题**：标题与指令同一行，内容中不要重复标题行
- **`:widths:` 的逗号**：用空格，不用逗号
- **`.. raw::` 内容**：必须缩进，空行之后也要缩进
- **latexmk 挂起**：始终使用 `-interaction=nonstopmode` 或 `latexmkrc`
- **尽量不动 `conf.py`**：当用户说明其项目配置复杂时，改为在 `.rst` 文件中使用 `.. raw::`
- **`.. note::` 分页拆分**：当 `.. note::` admonition 在 PDF 输出中被跨页拆分时，在其前面插入 `\needspace{}`：
  ```rst
  .. raw:: latex

     \needspace{4\baselineskip}

  .. note::

     Content that must stay together.
  ```
  `\needspace{}` 检查剩余页面空间；取值应大于备注高度 + 间距。
- **标题修饰符层级**：docutils/Sphinx 按修饰符字符（首次出现的顺序）决定标题的**层级**。如果在两个既有层级之间给某个子章节引入**新的**修饰符，它会“抢占”一个层级，把更深层标题逼成跳级 → `Inconsistent title style: skip from level 1 to 3`（例如在 `+` 章节与 `=` 配置标题之间插入 `-` 子章节，会把 `=` 标题推到 level-1 父级之下的第 3 级）。所有同深度标题必须使用**相同**修饰符。在某个 Nuclei databook 约定中：章节用 `+`，子章节/配置标题用 `#`。程序化生成 RST 时，输出 `adornment * len(title)`，保证下划线长度始终匹配。
