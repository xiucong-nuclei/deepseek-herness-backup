---
name: bus-interface-analysis
description: Analyze hardware bus interface port lists (AXI, AHB-Lite, ICB, APB) from Verilog/SV code images — extract signals, format as documentation tables with M→S/S→M direction and spec-style English descriptions.
metadata:
  hermes:
    tags:
    - hardware
    - bus
    - axi
    - ahb
    - icb
    - verilog
    - documentation
    - verdi
    version: 1.0.0
    platforms:
    - linux
---

# 总线接口信号分析

从图像中分析总线接口的 Verilog/SystemVerilog 端口声明，并以可直接用于文档的表格呈现。

## 触发条件

用户发送一张含信号名、方向与位宽的 Verilog/SV 端口声明图像。通常来自总线接口模块（AXI、AHB-Lite、ICB、APB）。触发语如 “帮我分析这些信号”、“一样的处理”，或连续发送接口图像。

## 工作流程

### 第 1 步——提取端口

用 `vision_analyze` 从图像中逐行读取：方向（`input`/`output`）、位宽 `[N:M]` 与信号名。没有方括号时信号为 1 位。

### 第 2 步——与已知总线协议交叉核对

视觉模型（Qwen3-VL）处理代码截图不可靠。将提取的信号与已知总线协议规范交叉核对。需要纠正的常见幻觉：

| 视觉输出 | 可能的事实 | 总线 |
|---------------|-------------|-----|
| `input [63:0] wvalid` | `input [63:0] wdata` + `input wvalid` | AXI |
| `input [7:0] wlast` | `input wlast` | AXI |
| `output [1:0] bvalid` | `output bvalid` + `output [1:0] bresp` | AXI |
| 已知模式之外的额外信号 | 幻觉，删除 | 任意 |

不确定时，标记异常，但给出符合规范的正确解读。

### 第 3 步——按通道分组

按总线通道对信号分组：

- **AXI**：AW（写地址）、W（写数据）、B（写响应）、AR（读地址）、R（读数据）
- **ICB**：cmd（请求）、rsp（响应）
- **AHB-Lite**：单通道（地址与数据阶段共用信号）
- **APB**：单通道

每个通道作为独立子表格呈现，并带标签标题。

### 第 4 步——格式化表格

列顺序：`信号` | `方向` | `位宽` | `说明`

**方向必须使用 M→S / S→M——绝不能使用 input/output。** 原因：`input`/`output` 是相对于当前模块的，对阅读总线互联（fabric）文档的人没有意义。M→S / S→M 才是绝对的总线方向。

映射（当模块为从机侧时，`i_` 前缀约定）：
- `input` → M→S（主机把该信号驱动进从机模块）
- `output` → S→M（从机把该信号驱动给主机）

若模块是主机侧（较少见），对调。运用总线协议知识确保正确。

### 第 5 步——编写说明（规范风格英文）

说明写入 `说明` 列。规则：
- **简洁、适合表格单元格**：短语，不用完整句子
- **不用冠词（a/an）**：遵循 Nuclei 文档惯例
- **序列用 → 表示**：`Read → Modify → Write back`
- **信号名用等宽字体**：`` `araddr` ``
- **编码表内联**：`0 = OKAY, 1 = EXOKAY, 2 = SLVERR, 3 = DECERR`
- **标准总线术语**：使用 AMBA / 总线协议规范中的术语

关于行文风格的更多细节，参见 `spec-trans` skill。

### 第 6 步——添加概要

在所有表格之后，添加紧凑的配置概要：

| 参数 | 值 |
|-----------|-------|
| 数据位宽 | 64b |
| 地址位宽 | 32b |
| ID 位宽 | 4b（16 个 outstanding） |
| 协议 | AXI4 Full |
| 信号总数 | ~37 |

## 方向规则（关键）

```
input/output  →  fab 里面看不出什么  →  USE M→S / S→M
```

- **M→S**：主机驱动，从机接收。AW/AR/W 通道载荷 + valid，B/R 的 ready。
- **S→M**：从机驱动，主机接收。AW/AR/W 的 ready，B/R 通道载荷 + valid。

Valid/Ready 的方向按通道而定：
- `*valid` 与载荷方向一致
- `*ready` 与载荷方向相反

## 总线协议参考文档

| 总线 | 文档 | 关键规范 |
|-----|----------|-----------|
| AXI4 Full | ARM IHI 0022 | 5 个通道、Burst、ID、乱序 |
| AHB-Lite | ARM IHI 0033 | 单通道、流水化地址/数据、无仲裁 |
| APB | ARM IHI 0024 | 简单、无流水、低功耗 |
| ICB | Nuclei 内部 | 2 个通道（cmd+rsp）、类 AXI 简化、无 burst（基础版） |

## 优先 OCR 提取（tesseract）与说明深度

当来源是代码截图时，优先用 **tesseract OCR** 而非视觉模型——
4× LANCZOS 放大 + 灰度 + 阈值，`--psm 6`（交叉核对 `--psm 4`）；仅在回退时使用
`vision_analyze`，并且始终交叉验证。完整工作流、AXI4/AHB-Lite/ICB
信号说明速查表以及 EDC（`_p`/`_edc`/`_hi`/`_lo`）信号模式见
`references/bus-signal-table-workflow.md`。

说明深度——用户的容忍窗口：
- 太短（“Request valid”）→ 会被打回；过于 Fab 化（“Fab forwards to downstream”）→ 会被拒绝。
- **目标**：协议层面——“Indicates master is driving valid write address and control.”。描述信号本身，而不是系统对它的反应。
- 全局/时钟/复位信号（`clk`、`rst_n`、各通道 `*_clk`）使用 `in`/`out`，放在单独的 “Global Signals” / “Channel Clock and Reset” 表格中。
- 信号顺序必须与源图像完全一致；列顺序为 信号 | 方向 | 位宽 | 说明（用户偏好）。

## 常见陷阱

- **表格中绝不要用 `input`/`output`**：用户明确拒绝过。“input output 到 fab 里面看不出什么”
- **视觉模型会幻觉信号名与位宽**：始终与已知总线协议规范交叉核对。Qwen3-VL 尤其会混淆 `wvalid`↔`wdata`、`wlast` 的位宽、`bvalid`↔`bresp`。
- **方向映射取决于协议**：同一模块中，AWREADY 是 S→M，但 AWVALID 是 M→S。核对协议，不要对每个信号都盲目地把 `input` 映射为 M→S。
- **列顺序很重要**：方向在位宽之前（`方向` → `位宽`）。用户明确把默认顺序对调过。
- **Nuclei 代码库中的 `i_` 前缀**：`i_axi_awvalid` 这类信号用 `i_` 前缀表示从机侧模块端口。模块把主机驱动的信号作为输入接收，把响应信号作为输出驱动。

## 参考

- `references/bus-signal-reference.md` — AXI4、AHB-Lite、ICB、APB 的信号表格，含位宽、方向与说明。
