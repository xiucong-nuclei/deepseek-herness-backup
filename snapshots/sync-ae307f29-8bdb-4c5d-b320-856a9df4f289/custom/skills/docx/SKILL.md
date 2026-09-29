---
name: docx
description: Create, read, edit, template, and review Word .docx files.
metadata:
  hermes:
    tags:
    - word
    - docx
    - documents
    - office
    - templates
    - revisions
    - comments
    category: productivity
    related_skills:
    - pdf
    - xlsx
    - powerpoint
    version: 1.1.0
    author: Nous Research
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Docx 技能

通过小型 CLI 用 python-docx 创建、读取、编辑和模板化 Microsoft Word `.docx` 文件。支持文本、样式、列表、表格、图片、页眉/页脚、`{{token}}` 模板化、修订（列出/接受/拒绝）、批注（列出/添加/删除）、目录和页码域，以及包健康检查。它本身不渲染文档（PDF 需要 LibreOffice——见"转换为 PDF"），也不编辑旧版 `.doc`。

## 适用场景

- 用户要求生成 Word 文档（报告、信函、合同）。
- 需要提取 `.docx` 的文本、大纲、样式或内嵌图片。
- 必须修改现有 `.docx`：替换文本、编辑表格单元格、插入/删除段落、应用样式、合并碎片化的 run。
- 有带 `{{placeholders}}` 的 `.docx` 模板需要用数据填充。
- 文档带有需要审阅、接受或拒绝的修订。
- 需要读取审阅者的批注，或添加/删除批注。
- `.docx` 打不开或行为异常，需要做损坏排查。
- 文档需要目录或 "Page X of Y" 页脚。
- 不适用于：`.doc`（旧版）、`.odt` 或所见即所得（WYSIWYG）排版工作。

## 前置条件

- Python 3.10+ 并安装 `python-docx`：`pip install python-docx`（导入名是 `docx`；lxml 随其一并安装）。
- 批注 `add` 在 python-docx >= 1.2 上使用原生 API，在旧版本上使用 XML 回退——两者都是自动的。
- 图片块：图片文件必须存在于本地（PNG/JPEG）。

## 运行方式

所有辅助脚本都位于本文件旁的 `scripts/` 目录。用 `terminal` 工具运行它们；每个脚本都支持 `--help` 并向 stdout 输出 JSON。

```bash
python scripts/docx_create.py spec.json out.docx
python scripts/docx_read.py out.docx --text
python scripts/docx_edit.py replace out.docx --find old --replace new
python scripts/docx_template.py tpl.docx values.json filled.docx
python scripts/docx_revisions.py list out.docx
python scripts/docx_comments.py list out.docx
python scripts/docx_validate.py out.docx
```

## 快速参考

| 任务 | 命令 |
| --- | --- |
| 从 JSON spec 创建 | `docx_create.py spec.json out.docx` |
| 全文（正文+表格+页眉/页脚） | `docx_read.py f.docx --text` |
| 标题大纲 + 表格形状 | `docx_read.py f.docx --structure` |
| 实际使用的样式 | `docx_read.py f.docx --styles` |
| 提取内嵌图片 | `docx_read.py f.docx --images outdir/` |
| 检测修订/批注 | `docx_read.py f.docx --revisions` |
| 查找/替换（保留格式） | `docx_edit.py replace f.docx --find A --replace B -o out.docx` |
| 设置表格单元格 | `docx_edit.py set-cell f.docx --table 0 --row 1 --col 2 --text X` |
| 在索引 N 之前插入段落 | `docx_edit.py insert f.docx --index N --text X --style Normal` |
| 删除段落 N | `docx_edit.py delete f.docx --index N` |
| 为段落 N 应用样式 | `docx_edit.py style f.docx --index N --style "Heading 1"` |
| 合并格式相同的相邻 run | `docx_edit.py normalize f.docx -o out.docx` |
| 在段落 N 前插入 TOC 域 | `docx_edit.py toc f.docx --index N -o out.docx` |
| "Page X of Y" 页脚域 | `docx_edit.py page-numbers f.docx` |
| 填充 `{{tokens}}` | `docx_template.py tpl.docx values.json out.docx --strict` |
| 列出修订（id/作者/日期/文本） | `docx_revisions.py list f.docx` |
| 接受 / 拒绝全部修订 | `docx_revisions.py accept-all f.docx -o out.docx`（或 `reject-all`） |
| 接受 / 拒绝单条修订 | `docx_revisions.py accept f.docx --id 3 -o out.docx` |
| 列出批注（含锚定文本） | `docx_comments.py list f.docx` |
| 添加锚定到文本的批注 | `docx_comments.py add f.docx --target "phrase" --text "note" --author You` |
| 按 id 删除批注 | `docx_comments.py delete f.docx --id 0` |
| 检查包健康状况 | `docx_validate.py f.docx`（出错时退出码 1） |

## 操作流程

1. **创建。** 用 `write_file` 编写 JSON spec，然后运行 `scripts/docx_create.py`。spec 支持：`page`（尺寸 + 以 mm 为单位的页边距）、`header`/`footer` 字符串、`footer_page_numbers`（添加 "Page X of Y" 域页脚）、`styles`（自定义段落样式，含字体、字号、粗体/斜体、十六进制 `color`），以及 `blocks`——`heading`（级别 1-9）、`paragraph`（`text` 或 `runs` 列表，每个 run 可设置 `bold`/`italic`/`underline`）、`bullet_list`、`numbered_list`、`table`（`header` 行渲染为粗体、`rows`、可选的内置表格 `style`，如 `Table Grid`）、`image`（`path`、可选 `width_mm`）、`toc`（目录域）和 `page_break`。完整 spec 格式见 `scripts/docx_create.py` 顶部的文档。
2. **读取。** 使用 `scripts/docx_read.py`，恰好指定一个模式标志。`--text` 以 JSON 返回正文段落、所有表格单元格文本以及页眉/页脚文本。`--structure` 返回标题大纲以及段落/表格/节计数。`--images DIR` 将 `word/media/` 下的所有文件复制出包。
3. **编辑。** 使用 `scripts/docx_edit.py`。`replace` 遍历正文、表格（含嵌套）、页眉和页脚，并保留 run 格式；加 `--body-only` 可跳过页眉/页脚。传 `-o out.docx` 保留原件；省略则就地编辑。`insert`/`delete`/`style`/`toc` 的段落索引对应 `--structure`/`--text` 的正文顺序。对经过大量 Word 编辑的文档先运行 `normalize`——它会合并格式完全相同的相邻 run，使后续查找/替换可靠匹配。
4. **审阅修订。** `docx_revisions.py list` 报告正文、表格、页眉或页脚中所有的 `w:ins` 和 `w:del`（id、作者、日期、受影响的文本）。`accept-all` / `reject-all` 批量解决；`accept`/`reject --id N` 处理单条修订。接受会保留插入并删除被删文本；拒绝则相反。
5. **批注。** `docx_comments.py list` 返回每条批注的 id、作者、日期、正文文本以及它所锚定的文档文本。`add --target "some phrase"` 将新批注锚定到该短语首次出现的位置（必要时拆分 run；格式保留）。`delete --id N` 删除批注及其标记，不触碰文档文本。
6. **模板。** 在文档中放入 `{{name}}` 风格的 token。运行 `scripts/docx_template.py` 并传入 JSON 值对象。使用 `--strict` 在存在未填充 token 时报错；无论是否使用严格模式，JSON 输出都会列出 `filled` 计数和 `unfilled_tokens`。
7. **验证**（始终）：用 `--text` 或 `--structure` 重新读取输出，并对任何经过修订/批注处理的作品运行 `docx_validate.py`。

## 转换为 PDF

无需脚本。安装了 LibreOffice 时，可无头转换：

```bash
soffice --headless --convert-to pdf --outdir outdir/ file.docx
```

先检查是否可用（`command -v soffice || command -v libreoffice`）。如果两者都不存在，告诉用户此环境无法进行 PDF 转换，而不要临时凑合——python-docx 无法渲染 PDF，版面保真需要真正的渲染器。

## 常见陷阱

- **Token 被拆分到多个 run。** Word 常把文本拆成多个 run。替换助手会合并匹配到的 run（替换文本继承第一个 run 的格式）；先运行 `docx_edit.py normalize` 可减少碎片化，让后续所有编辑更可靠。
- **修订覆盖范围。** `docx_revisions.py` 处理 run 级插入和删除（占绝大多数）。段落标记和表格行修订、格式更改记录以及移动操作会被 `--revisions` 检测到，但不会自动解决——见 `references/revisions-and-comments.md`，把这些交给 Word。
- **批注线程。** 回复和"已解决"状态存放在 `commentsExtended.xml` 中，本技能忽略该文件；它添加的批注是普通的顶层批注。
- **域结果由 Word 计算。** `toc`、`page-numbers` 以及 spec 选项 `toc`/`footer_page_numbers` 写入的是*域代码*。Word/LibreOffice 在打开文件时填充实际条目和编号（Word 可能提示更新域）；python-docx 从不计算它们，所以在此之前显示的是占位文本。
- **校验是健康检查，不是 schema 校验。** `docx_validate.py` 检查 zip、必需部件、关系目标、图片魔数和引用的样式。它不是 XSD 校验——文件可能通过检查，却仍包含 Word 不喜欢的 XML。
- **样式名必须存在。** 应用文档中未定义的样式会抛出 `KeyError`。`Heading 1`、`List Bullet`、`List Number`、`Table Grid` 等内置样式存在于默认模板中；自定义样式必须先在建 spec 中声明。
- **编号列表延续编号。** `List Number` 依赖 Word 的默认编号；同一文档中的多个列表可能延续编号而不是重新开始。提醒需要精确多列表编号的用户。
- **单元格写入会替换格式。** `set-cell` 使用 `cell.text = ...`，会把该单元格的 run 重置为普通格式。
- **编码。** 所有 JSON spec/值文件都显式按 UTF-8 读取；自己写胶水代码时绝不要依赖区域设置的默认值。
- **不要解压后直接 sed XML。** 通过脚本（或 python-docx）编辑；在 `document.xml` 中做裸文本替换极易损坏文件。`patch`/`write_file` 只用于 JSON 输入，绝不要用于 `.docx` 文件本身。

## 验证

- 创建/编辑/模板化之后，运行 `docx_read.py out.docx --text`，确认预期字符串出现（且旧字符串消失）。
- 接受/拒绝之后，`docx_revisions.py list` 应返回 `[]`（或只剩你有意留下的 id）；批注处理后，`docx_comments.py list` 应反映改动，且 `--text` 输出必须保持不变。
- 包健康时 `docx_validate.py out.docx` 以 0 退出并输出 `"ok": true`——任何修订/批注/域操作后都要运行它。
- 模板用 `--strict` 运行，或检查 `unfilled_tokens == []`。
- 结构检查：`--structure` 应显示预期的标题大纲和表格形状；`--styles` 确认自定义样式已应用。
