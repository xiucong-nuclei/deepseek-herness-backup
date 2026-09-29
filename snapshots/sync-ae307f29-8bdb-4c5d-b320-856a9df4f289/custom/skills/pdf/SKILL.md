---
name: pdf
description: Create, read, merge, fill, and secure PDF files.
metadata:
  hermes:
    tags:
    - pdf
    - documents
    - forms
    - reportlab
    - pypdf
    - pdfplumber
    category: productivity
    related_skills:
    - docx
    - xlsx
    - powerpoint
    - ocr-and-documents
    version: 1.0.0
    author: Nous Research
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# PDF Skill

使用 pypdf、reportlab 与 pdfplumber：从结构化 spec 创建 PDF，构建并填写 AcroForm 表单（含布局 lint 与可视化叠加检查），提取文本/表格/元数据，合并/拆分/旋转/加水印/盖章页面，导出页面图像，管理元数据与附件，以及加密/解密。扫描版（纯图像）PDF 没有文本层：OCR 明确不在本 skill 范围内——当页面为纯图像时，停下并改用 `ocr-and-documents` skill，不要假装能提取文本。

## 使用场景

- 将报告、发票或多页文档生成为 PDF。
- 从 JSON spec 构建可填写的 AcroForm（文本/复选框/单选/下拉），先对布局做 lint 检查。
- 从 PDF 中提取文本、表格（JSON/CSV）、元数据或表单字段值。
- 合并、拆分、旋转、提取页面子集、加水印、按坐标盖章文本/图像、加书签或压缩 PDF。
- 导出页面为 PNG 供可视化检查或交给 OCR；设置/清除文档元数据；添加/提取文件附件。
- 填写或扁平化 AcroForm 表单；用密码加密或解密。
- 不适用于扫描版/纯图像 PDF（使用 `ocr-and-documents`），也不适用于像素级精确的 HTML 转 PDF（使用无头浏览器）。

## 前置条件

- Python 3.10+，带 `pypdf`、`reportlab`、`pdfplumber`：
  `python -m pip install pypdf reportlab pdfplumber`
- 可选：用于页面栅格化（`pdf_page_image.py`、叠加渲染）：`python -m pip install pypdfium2`，或将 poppler 的 `pdftoppm` 加入 PATH。脚本按 pypdfium2 → pdftoppm 顺序回退，两者都不存在时报告 `{"rendered": false, "missing": [...]}`（exit 0）。
- 每个辅助脚本惰性检查导入，缺少依赖时打印安装提示。

## 运行方式

所有辅助脚本位于 `scripts/` 中，均为 argparse CLI——用 `terminal` 工具运行；每个都支持 `--help`。它们严格以 UTF-8 读写 JSON，把 JSON 结果打印到 stdout，失败时以非零码退出。

```bash
python scripts/pdf_create.py spec.json -o out.pdf         # build PDF from JSON spec
python scripts/pdf_make_form.py formspec.json -o form.pdf # build fillable AcroForm from JSON spec
python scripts/pdf_form_layout.py formspec.json           # lint form layout BEFORE building
python scripts/pdf_form_layout.py formspec.json --render-overlay boxes.png [--pdf form.pdf]
python scripts/pdf_read.py doc.pdf --text                 # per-page text (JSON)
python scripts/pdf_read.py doc.pdf --tables --csv-dir t/  # tables to JSON + CSV files
python scripts/pdf_read.py doc.pdf --meta                 # metadata, page sizes, encrypted/scanned flags
python scripts/pdf_read.py form.pdf --fields              # form fields: name, type, value
python scripts/pdf_merge.py a.pdf b.pdf -o merged.pdf [--bookmarks]
python scripts/pdf_split.py doc.pdf --pages 1-3,7 -o part.pdf [--rotate 90]
python scripts/pdf_fill_form.py form.pdf --fields-json values.json -o filled.pdf [--flatten]
python scripts/pdf_secure.py doc.pdf --encrypt -o enc.pdf --user-password your-password
python scripts/pdf_secure.py enc.pdf --decrypt -o dec.pdf --password your-password
python scripts/pdf_watermark.py doc.pdf --stamp mark.pdf -o stamped.pdf [--under]
python scripts/pdf_stamp.py doc.pdf -o out.pdf --text "DRAFT" --x 150 --y 400 \
    --font-size 60 --rotation 45 --opacity 0.3 --color "#cc0000" [--pages 1-3]
python scripts/pdf_stamp.py doc.pdf -o out.pdf --image sig.png --x 400 --y 60 --width 120
python scripts/pdf_page_image.py doc.pdf --pages 1-3 --dpi 150 --out-dir imgs/
python scripts/pdf_meta.py doc.pdf --set-meta --title "T" --author "A" -o out.pdf
python scripts/pdf_meta.py doc.pdf --attach data.csv -o out.pdf
python scripts/pdf_meta.py doc.pdf --list-attachments | --extract-attachments dir/
```

## 快速参考

| 任务 | 工具 | 命令 / API |
|---|---|---|
| 创建文档（标题、表格、图像） | reportlab platypus | `pdf_create.py spec.json -o out.pdf` |
| 构建可填写表单 | reportlab acroForm | `pdf_make_form.py formspec.json -o form.pdf` |
| 表单布局 lint / 叠加图像 | 纯 python + PIL | `pdf_form_layout.py formspec.json [--render-overlay o.png]` |
| 逐页文本 | pdfplumber | `pdf_read.py f.pdf --text` |
| 表格 → JSON/CSV | pdfplumber | `pdf_read.py f.pdf --tables` |
| 元数据 / 尺寸 / 加密 / 扫描 | pypdf + pdfplumber | `pdf_read.py f.pdf --meta` |
| 合并（+ 大纲） | pypdf | `pdf_merge.py a.pdf b.pdf -o m.pdf` |
| 拆分 / 提取 / 旋转 | pypdf | `pdf_split.py f.pdf --pages 2-5 --rotate 90` |
| 列出 / 填写 / 扁平化表单 | pypdf | `pdf_read.py --fields`, `pdf_fill_form.py` |
| 加密 / 解密（AES-256） | pypdf | `pdf_secure.py --encrypt/--decrypt` |
| 加水印 / 盖章 PDF 页面 | pypdf | `pdf_watermark.py f.pdf --stamp w.pdf` |
| 按坐标盖章文本/图像 | reportlab + pypdf | `pdf_stamp.py f.pdf --text "Sign here" --x 400 --y 60` |
| 页面 → PNG（检查 / 交给 OCR） | pypdfium2 或 pdftoppm | `pdf_page_image.py f.pdf --pages 1-3 --out-dir imgs/` |
| 设置/清除元数据、附件 | pypdf | `pdf_meta.py --set-meta / --attach / --extract-attachments` |
| 压缩内容流 | pypdf | `pdf_split.py f.pdf --pages 1-N --compress` |

## 操作流程

1. **先检查。** 运行 `pdf_read.py file.pdf --meta`。检查 `encrypted`（若为 true，先用 `pdf_secure.py --decrypt` 解密）与 `likely_scanned_pages`。若页面为纯图像，用 `pdf_page_image.py --pages <scanned> --dpi 300 --out-dir imgs/` 导出，把 PNG 交给 `ocr-and-documents` skill——不要将空文本报告为“无内容”。
2. **创建。** 用 `write_file` 编写 JSON spec（元素：`heading`、`paragraph`、`table`、`image`、`pagebreak`；可选 `title`/`author` 元数据；页码自动添加），然后运行 `pdf_create.py`。若布局重要，用 `vision_analyze` 对渲染出的页面图像做可视化验证。
3. **提取。** `--text` 给出逐页字符串的 JSON 列表；`--tables` 给出每页的行数组，也可输出 CSV 文件。用 `read_file` 读取结果；绝不直接肉眼查看二进制 PDF。
4. **操作。** `pdf_merge.py` 拼接文件，可为每个源文件添加一个书签；`pdf_split.py` 处理页面范围（从 1 开始，如 `1-3,5,9-`）、90° 步进的旋转与 `--compress`。加水印：先准备单页盖章 PDF（如通过 `pdf_create.py`），再用 `pdf_watermark.py` 叠加；单行式盖章（“sign here”、斜向 DRAFT、角落标签）用 `pdf_stamp.py`，在显式坐标处放置文本或图像。
5. **构建表单。** 编写一份表单 spec JSON（字段含 PDF 点单位的 `label_box`/`entry_box`——见 `references/forms.md`），用 `pdf_form_layout.py` 做 lint 并修复报告的每个问题，可选地用 `vision_analyze` 检查 `--render-overlay` PNG，再用 `pdf_make_form.py` 构建，最后用 `pdf_read.py --fields` 确认。
6. **填写表单。** 用 `--fields` 列出字段以获知确切名称与类型，用 `write_file` 写一份 `{"FieldName": "value"}` 的 UTF-8 JSON（复选框接受 `true`/`false`；单选/选择值必须匹配字段的导出选项），然后运行 `pdf_fill_form.py`。用 `--fields` 重新读取以确认值已写入。
7. **元数据与附件。** `pdf_meta.py --set-meta` 写入 Title/Author/Subject/Keywords（DocInfo）；`--clear-meta` 清除它们；`--attach`/`--list-attachments`/`--extract-attachments` 往返处理内嵌文件。
8. **安全。** 用不同的用户/所有者密码与 AES-256 加密。要移除已知密码，`--decrypt` 会写出未加密副本。
9. 报告成功前**验证**（见下文）。

## 常见陷阱

- **扫描版 PDF**：`extract_text()` 为空且存在页面图像，说明没有文本层。转交 `ocr-and-documents`；不要编造文本。
- **扁平化限制**：`pdf_fill_form.py --flatten` 使用 pypdf 的扁平化支持，将控件外观转换为页面内容。它对纯文本字段与复选框可靠，但可能丢失或错误渲染特殊控件（富文本、自定义外观流、某些单选组）。用 `vision_analyze` 对扁平化输出做可视化验证；若要万无一失的扁平化，回退到外部渲染器（如 Ghostscript 或 `pdftoppm`+重新组装）。
- **NeedAppearances**：填写后，只有存在外观流时查看器才会渲染值。填写脚本会设置 AcroForm 的 `NeedAppearances` 标志，让合规的查看器重新生成外观流；部分极简查看器会忽略它——若显示保真度重要，请扁平化。
- **非拉丁表单值**：值存储正确（UTF-16），但字段的默认字体可能缺少字形，因此即使数据往返无误，查看器也可能显示空白。用 `--fields` 验证，不要仅靠目视。
- **压缩预期**：`--compress` 仅对内容流做 deflate。典型压缩率 0–20%；对以图像为主或已是压缩流的 PDF 无效。它不能替代图像降采样（那是 Ghostscript 的领域）。
- **权限标志不具强制力**：所有者密码的权限位（禁止打印、禁止复制）只是查看器可能遵守的礼貌请求；任何库（包括 pypdf）都能读取并剥离它们。只有用户密码通过加密真正限制内容访问。绝不要把权限标志当作安全机制。
- **表格提取是启发式的**：pdfplumber 根据框线/文字对齐检测表格；无边框或合并单元格的表格可能需要调整 `table_settings` 或手动清理。
- **页面索引**：辅助 CLI 接受从 1 开始的页面；pypdf API 从 0 开始。脚本已做转换——不要重复转换。
- **旋转盖章文本的提取**：pdfplumber 的行分组会打乱旋转字形（45° 的 “DRAFT” 提取出来是散乱字母）；改用 `pypdf` 的 `extract_text()` 或渲染图像来验证旋转盖章。
- **单选组**：reportlab 每组至少需要 2 个 `radio()` 控件，填写需要带斜杠的导出值（`"/red"`），且单选是扁平化保真度最差的——见 `references/forms.md`。
- **元数据范围**：`pdf_meta.py` 只写经典 DocInfo 字典；内嵌的 XMP 元数据（如有）保持不变，某些查看器中可能显示不同的值。
- **PDF/A 不在范围内**：pypdf/reportlab 无法生成或验证符合规范的 PDF/A。若需要归档级合规，通过 `terminal` 工具运行 Ghostscript（如 `gs -dPDFA=2 -dPDFACompatibilityPolicy=1 -sColorConversionStrategy=UseDeviceIndependentColor -sDEVICE=pdfwrite -o out.pdf in.pdf`，配合适的 ICC profile），并用 veraPDF 验证——两者都是外部安装，结果仍需验证而非想当然。
- 旋转角度必须是 90 的倍数；加密输入必须先解密才能进行任何其他操作。

## 验证

- 创建/合并/拆分后：`pdf_read.py out.pdf --meta`——确认 `page_count`，旋转过时还要确认每页的 `rotation`。
- 提取后：检查 JSON 非空，抽查一个已知字符串或单元格。
- 表单设计循环：`pdf_form_layout.py spec.json` 必须以 0 退出；然后运行 `--render-overlay boxes.png --pdf form.pdf`，用 `vision_analyze` 检查 PNG（红色 = 带字段名的输入框，蓝色 = 标签框），关注重叠、错位以及标签脱离其字段等问题。迭代 spec → lint → 叠加，直到干净为止。
- 构建表单后：`pdf_read.py form.pdf --fields` 列出 spec 中的每个字段及其正确的类型与选项。
- 填写表单后：`pdf_read.py filled.pdf --fields` 并比对值（精确匹配，包括非 ASCII）。
- 盖章后：重新提取文本（旋转盖章用 pypdf）或用 `pdf_page_image.py` 渲染页面，再用 `vision_analyze` 检查。
- 元数据/附件编辑后：`pdf_read.py --meta` / `pdf_meta.py --list-attachments`，并重新提取附件做逐字节比对。
- 加密后：`--meta` 显示 `"encrypted": true`，无密码打开会失败；解密后，文本提取与原文一致。
- 对任何可视化内容（水印、扁平化表单），用 `vision_analyze` 渲染并检查。
