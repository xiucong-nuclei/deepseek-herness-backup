---
name: top-portlist-zh-doc
description: 把 SoC 顶层模块端口清单（CSV：name,width,direction）结合 IP/核 databook PDF，生成中文集成文档的“顶层接口描述”章节——信号分组、每组 1-3 句简介、四列表格（信号名/位宽/方向/描述）。描述优先从 databook 意译（不加标），无确切出处按命名拟写并在行尾标 **(生成)**；产物推送到 deliverables git 仓库。触发语如：“分析这份端口清单”“写顶层接口描述”“把接口信号分组生成表格”。
metadata:
  hermes:
    tags:
    - soc
    - integration-doc
    - port-list
    - csv
    - interface-signals
    - databook
    - chinese-doc
    version: 1.0.0
    platforms:
    - linux
---

# 顶层端口清单 → 中文接口描述文档（SoC 集成文档）

把“顶层 module 端口列表”整理为客户集成文档的接口章节。首次跑通实例：pd_subsys_top（484 个信号，产物 `pd_subsys_top_ports_zh.md`）。

## 触发条件

用户给出（或引用 doc 仓库里的）：
1. 顶层端口清单 `xxx_top_ports.csv`，列固定为 `name,width,direction`（direction 为 `input`/`output`，**以顶层模块自身为参考**）；
2. 该 SoC 用到的 IP/核 databook PDF（Nuclei 外设手册、核 Product/Core Databook、InSight、Bus Fab/ICB 规范等）；
3. 要求：分组 → 每组简介 → 生成“信号名/位宽/方向/描述”表格。

## 输入与产物约定

- CSV 经 `.dsh-uploads/` 附件或工作区路径给出；先 `read` 全文确认列名与行数。
- PDF 文本缓存放工作区 `_unsorted/_iface_txt/*.txt`，生成器脚本同目录 `build.py`。
- 产物 Markdown 放在工作区根（如 `pd_subsys_top_ports_zh.md`），确认无误后推送到 `/home/ubuntu/deliverables`（hermes-deliverables git 仓库）并 commit/push（**只 add 新产物，勿带上其它脏改动**）。

## 工作流程

### 第 1 步：读端口清单，识别模块前缀
按名称前缀即可判断归属（实例命名规律，如 `usart0_*`、`qspi_xip0_*`、`npu_axi_mst_*`、`sram0_ram_*`、`core0_*`、`sync_<clk>_<mod>_rst_n`）。总线接口靠中缀协议词识别：`_apb_`、`_ahbl_`、`_axi_`、`_icb_`。pad 接口靠后缀 `_i_ival/_o_oval/_o_oe/_o_pue/_o_pde/_o_keep`。

### 第 2 步：抽取 PDF 文本（pymupdf）
```python
import pymupdf, os
for p in pdfs:                       # pdfs = 附件/资料目录里的 PDF 全路径
    d = pymupdf.open(p)
    with open(os.path.splitext(os.path.basename(p))[0] + ".txt", "w") as f:
        for i, pg in enumerate(d):
            f.write(f"\n<<<PAGE {i+1}>>>\n" + pg.get_text())
```
再用 `grep -n -B2 -A6` 在 txt 里定位信号名所在表格，不要整篇通读（省 token）。文档正文里带 `<<<PAGE n>>>` 标记，便于回读原文页码。

### 第 3 步：按信号族检索文档出处（描述的第一来源）
| 信号族 | 出处（Nuclei 文档） |
|---|---|
| 外设 pad / clk / rst / 寄存器配置 ICB | 各外设手册 §9 “Full Signal Interface” / “Register Configuration Signal Interface”（表头含 Signal Name/Dir/Width/Description） |
| 核启动/低功耗/系统信号（reset_vector、hart_id、sysrstreq、core_wfi_mode、mtime_toggle_a、stop_on_reset、icache_disable_init 等） | 300 Product Databook Table 6.42 “Other Functional Interface”；NA300 Core Databook |
| 核时钟/复位（core_clk_aon、por_reset_n、core_reset_n、reset_bypass、clkgate_bypass） | NA300 Core Databook Table 6.1 “Clock and Reset Signals” |
| DMI / 调试控制（tap2dmi_*、dmi2tap_*、dbg_no_sleep、i_dbg_stop、dbg_stop_at_boot、override_dm_sleep、dbg_stoptime） | InSight Specification §9.2 DMI Interface、§9.3 Debug Control Interface |
| AHB-Lite / AXI / APB / ICB 协议信号 | Nuclei Bus Fab Specification §9（ICB §9.1、AHB-L §9.2、AXI §9.3、APB §9.4 端口表）；ICB 协议规范；外设文档寄存器配置接口表 |
| SPI Flash 模式输入（flash_dw32_sel、flash_spare_sel）、XIP | SPI(NUQSPI) 手册信号表 / XIP 章节 |
| GPIO pad 后缀语义（ival/oval/oe/pue/pde/keep） | LGPIO 手册 §9 |

### 第 4 步：分组（本文档采用的结构，可套用）
1. 处理器核接口（core0/1、cpu0/1：调试、启动、低功耗、时钟使能）
2. NPU 接口（异步 AHB-L 从 / AXI 主 / AXI 从 + 其时钟复位，按接口分小表）
3. 时钟接口（fab 时钟、各模块 `*_cfg_clk`、rtc_clk 等 + 互连同复位）
4. 模块电源/时钟门控汇总（`*_subm_pd_n`、`*_cfg_clk_en`、`*_subm_clk_en_r`、`*_clk_en`、`sync_*_rst_n`）
5. 系统级复位（por_rst_n）
6. DFT 测试接口（reset_bypass / clkgate_bypass / dftmux_bypass / scan_clk）
7. 总线与存储接口（CRG APB、Test-Fab ICB、SRAM0~3 ICB，各自小表）
8. 外设 IO（每类外设一个小节：USART/QSPI/LGPIO/SAI/WWDG…）
9. 系统中断输入（如 user_soc_irg）

每组标题下写 1-3 句简介：该组信号大概作用 + 归属 + 描述出处。

### 第 5 步：描述规则（务必一致，客户可审计）
- **有确切出处**：中文意译文档描述，可括注出处章节/文档名，**不加标**。总线协议信号（APB/AHB-L/AXI/ICB）按协议规范描述，出处见 Bus Fab/核文档对应表，不必逐条标注。
- **无确切出处**（SoC 集成级命名，如 pd/clk_en/DFT/sync 包装、文档未列的对称位）：按命名规律拟写，行尾统一追加 ` **(生成)**`；描述文本内不要再嵌“（生成）”字样（生成器会统一剥离后置）。
- 文档未逐行列出的对称 pad 位（如 USART 的 `rx_o_oval/oe/pue`）按同 IP 文档的 pad 语义补全并标 (生成)，并在组简介说明。
- 方向/位宽以 CSV 为准直译（input→输入，output→输出）；宽度参数化的在描述中注明（如 ICB addr/wdata）。
- 文档与集成有出入时如实括注（例：InSight 的 dmi2tap_rdata 为 41 位，集成按 32 位引出）。

### 第 6 步：用生成器脚本产出（推荐，避免 400+ 行手写）
模板：本技能 `references/build.py`（pd_subsys_top 跑通的完整版本）。使用要点：
1. 改脚本顶部 `SRC`、`OUT` 为实际 CSV/输出路径；
2. 维护 `EXACT`（逐信号特例）、`MOD_CLK_DOC`（每模块 cfg_clk 的文档语义）、`SYNC`（sync 复位逐条）、pad 函数、`GINFO/INTROS/TITLES`（分组与简介）字典；总线协议字典（ICB_DESC/APB_DESC/AHB_DESC/AXI_DESC）与 pad 语义函数可直接复用；
3. 跑 `python3 build.py`，脚本会打印分组行数统计，并对未映射信号报 `STILL UNMAPPED` / 直接抛错——**必须做到 100% 覆盖**（行数 == CSV 总行数）；
4. 手写/改字典时注意命名规律差异：qspi1/qspi2 无下划线分隔（`qspi1_*`），usart 用 `usart0_*`；正则要写成 `qspi(?:_xip0|[12])` 之类。

### 第 7 步：校验产物
- 表行数 = CSV 信号数；组内行序保持 CSV 原序；
- `grep -c '**(生成)**'` 与“无出处”预期行数一致，无重复标注；
- 抽查若干行（核调试、sync 复位、pad、总线）确认文字无错位。

### 第 8 步：交付推送
```bash
cp <workdir>/xxx_top_ports_zh.md /home/ubuntu/deliverables/
cd /home/ubuntu/deliverables && git add xxx_top_ports_zh.md \
  && git commit -m "docs: add <module> 顶层接口分组与信号描述表(中文)" \
  && git push origin master
```
只 add 本次产物；仓库其它未提交改动不要动。

## 已知陷阱
- 上层命名不规范：`qspi1_*` vs `qspi_xip0_*` 下划线不一致；`npu_ahbl_slv_clk` 前缀是 `npu_ahbl_slv` 而非 `npu_ahbl_slv_async`。
- 每个模块的 cfg 时钟语义在各 IP 文档 §9 的 `clk` 行（外设手册个别有复制粘贴笔误，如 SAI 文档把 sys_clk 描述写成 usart，意译时按“ICB 配置时钟域”处理即可）。
- 某些文档把方向写成主从视角（M→S），CSV 是顶层视角，二者不要混写。
- `sync_*_rst_n` 的模块复位语义取自各 IP 文档 rst_n 行（不加标），但“同步”部分属集成命名；若目标模块文档根本没有 rst 行（如 WWDG），则该条整体标 (生成)。
- 文件沙箱默认只放行当前工作区；写 `/home/ubuntu/.dsh/skills/` 与 `/home/ubuntu/deliverables/` 需以 danger-full-access 提升。

## 参考
- `references/build.py`：pd_subsys_top 跑通的生成器（含全部中文描述字典与渲染逻辑），直接改 SRC/OUT 复用
- `references/sample_pd_subsys_top_ports.csv`：样例输入（484 信号）
- 成品样例：`/home/ubuntu/deliverables/pd_subsys_top_ports_zh.md`（632 行、94 个 (生成)）
- 配套技能：`nuclei-databook-writing`（databook 表格/CSV 规范）、`bus-interface-analysis`（总线端口截图→表格，输入是图像非 CSV）、`spec-trans`（中文→spec 英文）
