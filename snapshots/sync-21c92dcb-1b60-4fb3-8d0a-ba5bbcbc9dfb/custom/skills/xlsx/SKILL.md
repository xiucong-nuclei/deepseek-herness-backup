---
name: xlsx
description: Create, read, edit Excel .xlsx workbooks and CSVs.
metadata:
  hermes:
    tags:
    - excel
    - spreadsheet
    - xlsx
    - csv
    - openpyxl
    - productivity
    category: productivity
    related_skills:
    - docx
    - pdf
    - powerpoint
    version: 1.1.0
    author: Nous Research
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Xlsx 技能

使用 Python 和 openpyxl 处理 Excel .xlsx 工作簿：构建带公式和图表的样式化多工作表工作簿，检查或导出已有文件，编辑单元格与结构，以及与 CSV 互转。所有辅助脚本都是 argparse CLI，输出 JSON 并显式使用 UTF-8 I/O。

## 适用场景

- 创建 .xlsx 报告：多工作表、数字格式、样式、合并单元格、冻结窗格、自动筛选、条件格式、图表、数据有效性下拉、原生 Excel 表格、定义名称、超链接、单元格批注、工作表保护。
- 读取工作簿：工作表清单、将数据导出为 JSON 或 CSV、列出公式与缓存值对照、批注、定义名称、表格。
- 编辑已有文件：设置单元格、追加行、插入/删除行/列（通过 `xlsx_restructure.py` 感知引用）、复制/重命名工作表、表格、名称、批注、保护。
- 通过 LibreOffice 无头重算公式（`xlsx_recalc.py`）。
- CSV 互操作，支持类型推断和非 UTF-8 编码。
- 不适用于旧版 .xls 二进制格式（先用 LibreOffice 转换：`soffice --headless --convert-to xlsx old.xls`）。

## 前置条件

- Python 3.10+ 并安装 `openpyxl`（`pip install openpyxl`）。不需要其他第三方包；其余都是标准库。
- 可选：LibreOffice（`soffice`），用于无头重算或格式转换。

## 运行方式

在本技能 `scripts/` 目录下用 `terminal` 工具运行辅助脚本（每个脚本都支持 `--help`）：

```bash
python scripts/xlsx_create.py spec.json report.xlsx   # build from JSON spec
python scripts/xlsx_read.py report.xlsx --sheets      # inventory
python scripts/xlsx_read.py report.xlsx --json --sheet Data
python scripts/xlsx_read.py report.xlsx --formulas
python scripts/xlsx_edit.py report.xlsx --sheet Data --set B2=42 --recalc
python scripts/xlsx_restructure.py report.xlsx --sheet Data --insert-rows 3:2
python scripts/xlsx_recalc.py report.xlsx
python scripts/csv_to_xlsx.py data.csv out.xlsx --encoding utf-8
python scripts/xlsx_to_csv.py report.xlsx out.csv --sheet Data
```

用 `write_file` 编写 JSON spec，用 `read_file` 或直接从 stdout 查看脚本的 JSON 输出。

## 快速参考

| 任务 | 命令 |
|---|---|
| 从 spec 创建工作簿 | `xlsx_create.py spec.json out.xlsx` |
| 工作表名称 + 尺寸 | `xlsx_read.py f.xlsx --sheets` |
| 将工作表导出为 JSON | `xlsx_read.py f.xlsx --json --sheet S` |
| 将工作表导出为 CSV | `xlsx_read.py f.xlsx --csv --out d.csv` |
| 列出公式 + 缓存值 | `xlsx_read.py f.xlsx --formulas` |
| 设置单元格 / 公式 | `xlsx_edit.py f.xlsx --set "A1==SUM(B:B)"` |
| 追加一行 | `xlsx_edit.py f.xlsx --append '[1,"x",true]'` |
| 插入 2 行，引用不移动 | `xlsx_edit.py f.xlsx --insert-rows 3:2` |
| 插入 2 行，引用随之移动 | `xlsx_restructure.py f.xlsx --insert-rows 3:2` |
| 删除一列，引用随之移动 | `xlsx_restructure.py f.xlsx --delete-cols B` |
| 创建原生表格 | `xlsx_edit.py f.xlsx --add-table Sales:A1:C9` |
| 在表格内追加 | `--table-append 'Sales=["West",5]'` |
| 列出表格 | `xlsx_edit.py f.xlsx --list-tables` |
| 定义名称 | `--define-name "Rates='Data'!$B$2:$B$9"` / `--delete-name Rates` / `xlsx_read.py f.xlsx --names` |
| 超链接 | `--hyperlink "A1=https://example.com|Docs"` |
| 单元格批注 | `--note "B2=Check this|Reviewer"`；用 `xlsx_read.py f.xlsx --notes` 读取 |
| 保护工作表（见常见陷阱） | `--protect your-password --unlock B2:B9` |
| 通过 LibreOffice 重算 | `xlsx_recalc.py f.xlsx` |
| 复制 / 重命名工作表 | `--copy-sheet Src:New --rename-sheet Old:New` |
| 打开时强制重算 | `xlsx_edit.py f.xlsx --recalc` |
| CSV -> 样式化 xlsx | `csv_to_xlsx.py in.csv out.xlsx` |
| xlsx -> CSV | `xlsx_to_csv.py f.xlsx out.csv --encoding utf-8` |

## 操作流程

1. **创建**：编写 JSON spec（schema 见 `xlsx_create.py --help` 及其 docstring）。每个工作表支持 `rows`（标量或样式化单元格对象）、稀疏 `cells` 覆盖、`column_widths`、`row_heights`、`merges`、`freeze_panes`、`autofilter`、`conditional_formats`（cell_is 规则和色阶）、`charts`（基于单元格区域的柱状/折线/饼图）、`validations`（列表下拉）、`tables`（带样式名的原生 Excel 表格）和 `protection`。工作簿级 `defined_names` 将名称映射到引用。单元格对象还支持 `hyperlink` 和 `note`。类型化值：JSON 数字/布尔值直接透传；日期用 `{"value": "2026-01-31", "type": "date"}`。数字格式是 Excel 格式字符串：货币 `"$#,##0.00"`、百分比 `"0.0%"`、日期 `"yyyy-mm-dd"`。
2. **公式**：在 spec 中用 `"formula": "SUM(B2:B9)"`，或在编辑器中用 `--set "C1==SUM(A:A)"` 设置。写入公式时加上 `"full_calc_on_load": true`（spec）或 `--recalc`（编辑器）；这会设置工作簿的 `fullCalcOnLoad` 标志，让 Excel/LibreOffice 在打开时重新计算所有内容。openpyxl 本身绝不计算公式。
3. **读取**：`--sheets` 做清单（名称、尺寸、合并区域、图表数量、表格、保护、定义名称），`--json`/`--csv` 导出数据，`--formulas` 把每个公式字符串与其缓存结果配对，`--notes` 查看单元格批注，`--names` 查看定义名称。只有文件最后是由真正的电子表格应用保存的，缓存结果才存在；刚从 openpyxl 出来的文件在那里返回 `null`。要无头物化结果，运行 `xlsx_recalc.py file.xlsx`（使用 LibreOffice；`soffice` 缺失时输出 `{"recalculated": false, ...}` 并以 0 退出），然后用 `--data-only` 重新加载。
4. **编辑**：`xlsx_edit.py` 先应用重命名/复制，再执行结构性行/列变更，然后做 `--set`/`--append`。默认就地编辑，除非给定 `--out`——需要保留原件时先复制文件。
5. **重构**：对带公式、合并、表格或筛选的工作表做插入/删除时，用 `xlsx_restructure.py` 而不是 `xlsx_edit.py`。它会在**所有**工作表上重写公式引用（绝对 `$` 引用、区域、跨工作表引用），移动合并区域、自动筛选、冻结窗格、数据有效性和条件格式区域、表格引用、定义名称以及行/列尺寸，然后打印包含 `not_shifted` 列表的 JSON 报告。规则和限制：`references/restructuring.md`。
6. **CSV 互操作**：`csv_to_xlsx.py` 逐单元格推断 int/float/bool/ISO 日期，并给表头行加样式；`xlsx_to_csv.py` 写出 ISO 日期，空单元格写空字符串。两者默认 UTF-8，并接受 `--encoding`（例如 Excel 友好的 BOM 用 `utf-8-sig`，旧版 Windows 导出用 `cp1252`）。

## 转换为 PDF

LibreOffice 可无头转换（也可用于单工作表 CSV 导出）：

```bash
soffice --headless --convert-to pdf report.xlsx --outdir out/
soffice --headless --convert-to csv report.xlsx --outdir out/  # 1st sheet only
```

只有第一个工作表会落到 CSV；其他工作表用 `xlsx_to_csv.py --sheet NAME`。如果缺少 `soffice`，安装 LibreOffice，或把文件原样交给用户。

## 常见陷阱

- **openpyxl 不计算。** 公式结果只能通过 `load_workbook(path, data_only=True)` 获得，且仅当文件之前由 Excel/LibreOffice 保存过。否则得到 `None`。
- **`xlsx_edit.py` 的插入/删除不会移动引用**（openpyxl 原生行为）。改用 `xlsx_restructure.py`，它会移动——但即便如此，它也移动不了图表锚点、图片或条件格式的 RULE 公式；阅读其 JSON 报告的 `not_shifted` 列表和 `references/restructuring.md`。
- **工作表保护不是安全措施。** `--protect` 设置的是标准 xlsx 工作表保护哈希：它只是向行为规范的应用程序传达"不要编辑这个"，仅此而已。任何人都可以通过编辑 zip 中的 XML 或在 LibreOffice 中取消勾选来移除它。绝不要依赖它来保证机密性或完整性；它不加密任何内容。
- **`data_only=True` 后保存**会静默丢弃所有公式（缓存值取而代之）。除非这正是目的，否则绝不要保存以这种方式加载的工作簿。
- **加载会剥离图表/图片**：openpyxl 无法往返图表，因此编辑带图表的工作簿并保存会丢掉图表。编辑后重新添加图表，或避免重新保存带图表的文件。
- **CSV 区域设置陷阱**：始终显式传入编码（脚本已经这样做），并记住欧洲 CSV 常用 `;` 分隔符和小数逗号——使用 `--delimiter ';'`，并预期 `"12,5"` 这样的字符串保持为字符串。
- **日期是 datetime**：Excel 将日期存为序列号；openpyxl 返回 `datetime`/`date` 对象。此处的导出输出 ISO 字符串。
- 工作表名称上限 31 个字符，且不允许 `[ ] : * ? / \`。

## 验证

- 创建后：`xlsx_read.py out.xlsx --sheets`，确认工作表名称、尺寸、合并区域和图表数量符合预期。
- 用 `--json` 导出数据，并与源值比对。
- 编辑后：重新导出受影响的区域；如果写入了公式，确认 `--formulas` 能列出它们且已应用 `--recalc`。
- 运行 `xlsx_restructure.py` 后：阅读其 JSON 报告，再运行 `--formulas` 和 `--sheets`，确认引用和区域落在预期位置。
- 要完整目视检查，可在 LibreOffice 中打开：`soffice --headless --convert-to pdf out.xlsx` 并查看 PDF。
