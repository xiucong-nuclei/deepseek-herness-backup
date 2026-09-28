---
name: nuclei-databook-writing
description: 'Nuclei databook: spec English, list-tables, OCR, CSV macros.'
metadata:
  hermes:
    tags:
    - nuclei
    - databook
    - spec
    - translation
    - sphinx
    - rst
    - ocr
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Nuclei Databook 内容编写（N300/N600/N900）

编写与翻译 Nuclei 处理器 databook 内容：spec 级英文、Sphinx RST 表格、规格图 OCR 与 CSV 驱动的参数小节。与用户自有的 `spec-trans` skill 互补（后者承载完整的翻译规则集）；本 skill 承载会话中积累的 databook 内容生产工作流、格式与领域知识。

## 核心约定（用户已确认）

- 纯英文输出。用户尝试过"一行中文一行英文"中英对照，判定"没啥用"后撤回 —— 不要默认输出双语。中文原文只作翻译输入。
- 参数/字段表用 Sphinx list-table（`:header-rows: 1`，两列 `Macro | Description`），宏名/字段名反引号；不用 en-dash 列表。
- 表名用 The X of Y 模式（`The Entry Fields of ITLB`、`The Tag RAM Fields of MTLB`）；表前后要有描述句。
- 无 a/an；主动语态；短句；不用定语从句（which/that）。
- 禁 concept/configuration 小标题；平行子组用前缀平行标签（`**MBUS Fetch**` / `**MBUS Cacheable Access (CA)**` / `**MBUS Non-Cacheable Access (NC)**` / `**MBUS Device Access (DEV)**` / `**MBUS Common Attributes**`）。
- 大任务先复述需求 + 列 ≤3 个待定问题（每个带推荐项，编号顺序即推荐度），用户用 "1.1 2.1 3.1" 式短答确认后再动手。

## CSV → databook 参数小节工作流

1. 读源 CSV，总结结构：分类层级（大类→子类→子组）、条目数、参数类型分布（OUTS_NUM / LATENCY / *_WIDTH / BUS_TYPE）。
2. 列数据质量问题（笔误 / 重复条目 / 宏名与描述冲突）+ ≤3 个待定问题（小节名、输出形式与位置、错误处理方式），均带推荐。
3. 确认后一次性产出：小节名（`===` 下划线）+ 开篇介绍（"This section introduces the microarchitecture macro parameters in `xxx.csv` of the delivery package. ..." 句式）+ 大类（`---`）→ 子组（粗体标签）→ list-table。
4. 校验：数据行数 = 源条目数去重后、宏名无重复、每行格数一致。用 Python UTF-8 校验（grep 对 en-dash/中文不可靠）。
5. 输出到 `~/delivery_tmp/`（非 git；交付包来源/机密内容不入 `~/deliverables`）。

## 数据修复规则

- 宏名与描述冲突 → 以描述为准（例：CLUSTER_MBUS_WRITE_NC_OUTS_NUM 描述为"CA写请求" → 确认改名 `WRITE_CA_OUTS_NUM`。用户确认过："你是对的，根据描述改为 CA"）。
- 明显笔误直接修正并附修正清单（NUN→NUM、DCAHE→DCACHE、icahce→I-Cache bus、去请求→写请求）。
- 拿不准的用 RST 注释 `.. CSV note:` 标记（构建不可见、源文件可见），发布前可删。

## 图片 OCR（databook 截图/参数表）

- 大 PNG（> ~1MB）跳过 vision_analyze（会 400 payload 错误），直接用 tesseract：4× LANCZOS 放大 + 灰度 + autocontrast + 阈值，`lang='chi_sim+eng'`，`--psm 6` 与 `--psm 4` 双跑交叉验证；关键格需两次读出一致。
- 字段名/位宽按组内对称性校验：SEC_MDOE→SEC_MODE、MMODE_PXP_R/W→MMODE_PMP_R/W（P 后 M 被读成 X）、TARGET_DCACHE 易读成 TARGET_DEVICE（按描述判断）、ASID 位宽（ITLB/DTLB=16，MTLB 读成 1 需核对）。
- OCR 疑似笔误/位宽不一致列出给用户确认，勿静默修改。

## 翻译结构陷阱（用户纠正过）

- **"通过 X 将 Y 切换到 Z"：Y 是主语，X 是方式状语**。译 `The cache organization can be switched to 4-way associative through this option.`，不要改写成 `The option switches the cache...`（把方式状语升级为施动者改变原意。用户原话："你翻译的不符合我的原意"）。

## 电子表格 → RST（Excel/CSV 表格转换）

把指令/参数/特性表格从 .xlsx/.csv 转成 databook RST 小节的机械流程（merge-aware
单元格读取、类型列前向填充、延迟/吞吐单元格精确字典翻译、list-table 渲染、LEAD IN
引言要求、RST 表格形式与合并单元格限制）见 `references/spreadsheet-to-rst.md`。
要点：引言只"引出"表格不总结数据；ZFH 助记符统一大写 `H_*`；空吞吐格按数据相关
处理渲染 `—` 并加 note，不要臆造 `1`。中文散文翻译仍走 `spec-trans`。

## 参考资料

- `references/mmu-tlb-terminology.md` — MMU/TLB 术语与 entry 字段表（ITLB/DTLB/MTLB、地址参数 VATAG/PAGESIZE_WIDTH、图片表格 OCR 易错点）
