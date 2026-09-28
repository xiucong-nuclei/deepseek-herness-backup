---
name: synthesis-result-analysis
description: Compute synthesis result diffs — area & gate count delta between feature configs.
metadata:
  hermes:
    tags:
    - synthesis
    - csv
    - area
    - gate-count
    - diff
    - n300
    - syn_feature
    - include_ix
    - ppa
    related_skills: []
    version: 4.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
---

# 综合结果差异分析

用于 Nuclei N300/N900 综合结果分析。一个脚本包含五个子命令
（`syn_diff.py`，在用户环境中通常称为 `area_diff`）：

| 命令 | 参数 | 说明 |
|---------|------|-------------|
| `-d`（diff） | csv1 csv2 | 从 syn_feature 文件提取 base config，计算面积/门数差异，写入 csv2 |
| `-e`（extract） | csv2 | 从 syn_feature 文件中提取 `include_ix` 到 csv2 的 Base Config 列 |
| `-c`（collect） | csv1 csv2 | 运行 ppa，把 csv2 中各 config 的综合结果收集到 csv1 |
| `-g`（gen） | csv2 | 从 csv2 生成全部 syn config 文件，写出各 section 的 .list 文件与 syn_config_all.list |
| `-k`（check） | csv2 kconfig | 将 syn_feature 文件中的 `define 宏与 kconfig 比对检查 |

## 文档输出风格

当用户要求为这个脚本编写文档（“写到文档里面”、
“介绍下 area_diff”）——尤其是用于 NuCLei databook/文档时：

- 使用**编号条目**（1. 2. 3. 4. 5.），每个子命令一条。
- **不要小节标题**（不要 `###`，不要 `**功能**` / `**处理流程**` 这类标签）。
- 每条涵盖（a）命令做什么、（b）路径依赖、（c）关键参数及其作用——简洁但不只是一句话带过。
- 顶部一行约 50 字的概述可独立成段。
- 带表格和小节的详细参考格式（如
  `references/area_diff_cn_doc.md`）只用于深入技术评审，不用于
  面向用户的文档输出。

## 环境

需要 `PROJ_SRC_ROOT` 与 `PROJ_NAME` 环境变量（通过 `spr_cpu` 设置）。
两者任一缺失时脚本会打印消息退出。

完整中文文档：[references/area_diff_cn_doc.md](references/area_diff_cn_doc.md)

`ppa` 工具内部机制（报告路径解析、`-get_data` 标志、报告文件名
约定、`pre_setm` PrimeTime 错误）：[references/ppa_tool_internals.md](references/ppa_tool_internals.md)

兄弟工具 `syn_flow.py`（综合流程驱动器——rtl/compile/syn 模式、
其 cfg 机制与 `-list` 参数）：[references/syn_flow_driver.md](references/syn_flow_driver.md)

路径解析：
- **csv1**：`$PROJ_SRC_ROOT/cpu_cct/syn/<csv1_name>`
- **csv2**：`$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<csv2_name>`
- **syn_feature 配置文件**：`$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<Config>`

## `-d`（diff）的工作原理

1. 用滚动后缀备份 csv2：`csv2.bak.1`、`csv2.bak.2`……（绝不覆盖已有备份）
2. 将 csv1（综合结果）载入 `{config: {Area, Gate_num(k)}}` 映射
3. 对 csv2 的每一行：
   - 在 csv1 中查找 `Config` → 填入 `Area` 列（格式：`area/gate`）
   - 读取 `$SYN_FEATURE/<Config>` 文件，提取 `include_ix "xxx"` → 即 Base Config
   - 若 csv2 还有 `Base Config` 列且与文件值不一致，报告 `[MISMATCH]` 警告
   - 在 csv1 中查找解析出的 Base Config → 填入 `Base Area`
   - 计算 `Added Area = Area - Base Area`、`Added Gate = Gate_num - Base Gate_num`
4. 写回 csv2（保留元数据行）

## `-e`（extract）的工作原理

1. 用滚动后缀备份 csv2
2. 对每一行，读取 `syn_feature/<Config>` 并提取 `include_ix`
3. 把值写入 csv2 的 `Base Config` 列（列缺失时添加）
4. 对值发生变化的每一行打印一行

## `-c`（collect）的工作原理

1. 从 csv2 读取所有 `Config` 值
2. 构造 `-f "syn_feature/cfg1 syn_feature/cfg2 ..."` 参数列表
3. 在 `$PROJ_SRC_ROOT/cpu_cct/syn/` 下运行（不是 `cpu_cct/`）：
   ```
   ../bin/ppa -syn -f "<config_list>" --freq=100 --tech=22,9t -dc_flat=1 -get_data --csv=<csv1_name>
   ```
4. PPA 参数（`--freq`、`--tech`、`-dc_flat`）是脚本顶部的常量，便于修改

## `-g`（gen）的工作原理

1. 读取 csv2（含 Type/Feature/Config/Base Config 列的 CSV 表），收集所有 config→base_config 映射与 section 边界
2. 从 csv2 生成全部 config 文件（无列表文件过滤）：
   - 跳过名称包含 “base” 的 config（不区分大小写）——这些是基线 config，不应自动生成
   - 跳过 Base Config 在所有 config 名称中找不到的 config——报告 ERROR
   - 每个 config 文件内容为 `` `include_ix "Base_Config" ``（文件已存在则跳过）
3. 写出 `syn_config_00X.list` section 文件（仅含成功生成的 config）
4. 在 syn_feature/ 目录写出 `syn_config_all.list`——所有已生成 config 的合并列表

## `-k`（check）的工作原理

1. 从 syn_feature/ 读取 kconfig 文件（若存在；优雅处理文件缺失）
2. 从 csv2 读取所有 config 名称
3. 对每个 config，读取 syn_feature 文件并提取所有 `` `define MACRO `` 模式
4. 将每个宏与 kconfig 内容比对（整词匹配）
5. 对 kconfig 中找不到的宏报告 ERROR
6. 若 kconfig 不存在，报告 define 总数但不报错

## 关键特性

- **滚动备份**：`csv2.bak.1`、`csv2.bak.2`……——绝不覆盖已有备份
- **自动编码检测**：支持 UTF-8、UTF-16 LE/BE（BOM）、GBK、latin-1。应用于所有文件读取（CSV1、CSV2、syn_feature 配置文件）
- **元数据头部跳过**：CSV2 在实际表头之前可能有元数据行（TECH、FREQ、Update Time）；脚本自动检测包含 `Type`/`Feature`/`Config` 的行作为真正的表头
- **CSV1 列名自动检测**：模糊匹配包含 “area” 与 “gate” 的列名——不硬编码为 `Area(um2)`/`Gate_num(k)`
- **Base Config 取自权威来源**：`Base Config` 从 syn_feature 配置文件（`include_ix "xxx"`）中提取，而非来自 CSV2 列。CSV2 的 `Base Config` 列会被交叉检查是否不一致
- **仅 ASCII 输出**：所有打印只用 ASCII 字符（无 Unicode 箭头，无中文）

## 常见陷阱

- **`csv.DictReader` 会错误跳过元数据**：csv2 在实际表头之前有元数据行（TECH、FREQ、Update Time）。直接使用 `csv.DictReader` 会把第一条元数据行当作表头 → 所有列查找失败。始终使用 `read_csv2_structured()`，它会先扫描真正的 `Type/Feature/Config` 表头行。
- **所有文件读取的编码**：CentOS 7 上 syn_feature 配置文件可能是 GBK 编码。打开任何文件前都要调用 `detect_encoding()`——不仅是 CSV 文件。漏掉会导致静默 `UnicodeDecodeError` → `include_ix` 提取返回 None。
- **`-c` 在 `cpu_cct/syn/` 下运行，而非 `cpu_cct/`**：ppa 命令以 `cwd=$PROJ_SRC_ROOT/cpu_cct/syn/` 执行，因此 `../bin/ppa` 与 `--csv=<csv1_name>` 路径相对于该目录。
- **UTF-16 编码**：综合工具输出的 CSV 常带 UTF-16 LE BOM（0xFF 0xFE）。脚本会自动检测，但若检测失败，检查文件前 2 个字节。
- **CSV2 中的元数据行**：用户的 CSV2 在实际的 `Type,Feature,...` 表头之前以 `TECH`、`FREQ`、`Update Time` 行开头。脚本保留这些行，但从真正的表头开始解析。
- **仅精确匹配 config 名称**：不做模糊/规范化。若 CSV2 中是 `n300 syn base.v`（空格）而 CSV1 中是 `n300_syn_base.v`（下划线），则不会匹配。
- **输出编码为 UTF-8**：即使输入是 UTF-16，输出也以 UTF-8 写入。
- **syn_feature 配置文件格式**：期望 `include_ix "xxx"`（带双引号）或 `include_ix xxx`（不带引号）。其他格式（如 Tcl 的 `set include_ix xxx`）不会匹配。
- **`-get_data` 是布尔开关，不带值**：`ppa` 的 `-get_data`/`--get_data` 标志是 `action='store_true'`（帮助文本为 “Only extract PPA data”）——直接裸写，绝不要写成 `-get_data=1`。它跳过重新综合，只从已有结果中重新提取 PPA 数据。`syn_diff.py -c` 已无条件附加该标志。
- **`FATAL: must load prime-time Error 9`（pre_setm）**：`setm`/`pre_setm` 步骤在未加载 PT 的 `dc_shell` 中调用仅 PrimeTime 可用的命令。一连串 `dc`/`syn` 的 `Error 2` 行只是 make 在传播失败，不是新错误。根因排查方向见 `references/ppa_tool_internals.md`。
- **syn.log 位于父目录，而非报告目录**：`parse_syn_path` 将 `syn.log` 解析为 `os.path.join(path, "../syn.log")`（即 `dirname(path)/syn.log`），回退到 `latest_syn.log`；若两者都不存在，`path` 被当作列表文件逐行展开。
- **空 `Config` 单元格 → `IsADirectoryError`**：在 `-d`（diff）中，若 CSV2 某行的 `Config` 单元格为空（空行、汇总/合计行或未绑定 config 的特性），`str(Path(sf_dir) / config_name)` 会退化为 `syn_feature` 目录本身（`Path(dir) / "" == Path(dir)`），随后 `detect_encoding()` 执行 `open(dir, 'rb')` → `IsADirectoryError`。要为每次 `extract_include_ix` 调用加防护：`cmd_extract` 已有 `if config_name:` 防护，但 `cmd_diff` 历来没有。修复方式：
  ```python
  file_base = extract_include_ix(str(Path(sf_dir) / config_name)) if config_name else None
  ```
  当 `file_base=None` 时，该行正确回退到 `base_config_name = csv_base`，与空 config 行在面积查找中的既有处理方式一致。
