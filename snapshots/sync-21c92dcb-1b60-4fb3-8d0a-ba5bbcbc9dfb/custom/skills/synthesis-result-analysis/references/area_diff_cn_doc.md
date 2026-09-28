# syn_diff.py —— 综合结果差异分析工具

`syn_diff.py` 是 Nuclei 综合结果差异分析工具，基于 syn_feature 配置表和 ppa 综合结果，自动完成配置生成、综合收集、基准提取、面积/门数增量计算及宏定义校验，支持编码自适应与滚动备份。

## 路径约定

csv1（综合结果）位于 `$PROJ_SRC_ROOT/cpu_cct/syn/<csv1>`，是 ppa 综合工具输出的面积/门数数据表，由 `-c` 命令生成，供 `-d` 命令读取。csv2（特性配置表）位于 `$PROJ_SRC_ROOT/$PROJ_NAME/configs/syn_feature/<csv2>`，是用户维护的特性矩阵表，包含 Type / Feature / Config / Base Config 列及元数据行（TECH、FREQ、Update Time），所有子命令均围绕 csv2 展开。syn_feature 配置文件同目录，每个文件内容为 `` `include_ix "基准配置名"``，是 Base Config 的唯一真实来源。

## 五个子命令

1. `-d <csv1> <csv2>` — 差异计算。从 csv1 取每条特性的面积/门数，从对应的 syn_feature 文件提取 include_ix 作为 Base Config，再查 csv1 获取基准面积/门数，计算 Added Area 和 Added Gate，连同 csv1 中的 TECH/Date 一起写回 csv2。若 csv2 中 Base Config 列与文件提取值不一致，报告 MISMATCH。

2. `-e <csv2>` — 基准提取。批量读取 syn_feature 配置文件中的 include_ix，写入 csv2 的 Base Config 列（列不存在则自动添加）。

3. `-c <csv1> <csv2>` — 综合收集。从 csv2 读取所有 Config，拼接为 `-f "syn_feature/cfg1 syn_feature/cfg2 ..."` 参数，在 `cpu_cct/syn/` 目录下执行 `../bin/ppa -syn --freq=100 --tech=22,9t -dc_flat=1 -get_data --csv=<csv1>`，将综合结果写入 csv1。频率、工艺、扁平化参数在脚本顶部常量区集中修改。

4. `-g <csv2>` — 配置生成。解析 csv2 中的 section 分组（`syn_config_00X.list` 行），为每条特性生成 `` `include_ix "Base_Config"`` 配置文件（已存在则跳过，名称含 "base" 的跳过），同时写入分 section 的 list 文件和汇总的 `syn_config_all.list`。

5. `-k <csv2> <kconfig>` — 宏定义检查。遍历 csv2 中每条配置对应的 syn_feature 文件，提取所有 `` `define MACRO``，与 kconfig 做全词匹配，未找到的报 ERROR；kconfig 不存在时仅统计宏数量不报错。

## 关键行为

所有文件读取前自动检测编码（UTF-8 / UTF-16 LE/BE BOM / GBK / latin-1）。每次写入 csv2 前创建滚动备份（`.bak.N`，不覆盖已有备份）。csv1 列名通过模糊匹配识别（含 "area" / "gate" 关键词）。`include_ix` 仅识别双引号或无引号格式，不兼容 Tcl 语法。输出统一 UTF-8、ASCII 字符。
