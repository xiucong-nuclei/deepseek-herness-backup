---
name: nuclei-pma-config
description: PMA config gen/check for Nuclei CPUs (Kconfig + web tool).
metadata:
  hermes:
    tags:
    - Nuclei
    - PMA
    - RISC-V
    - Kconfig
    - WebTool
    category: software-development
    related_skills:
    - riscv-cpu-boot-debug
    version: 1.0.0
    author: Hermes Agent + kiucong
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Nuclei PMA 配置

PMA（Physical Memory Attribute，物理内存属性）区域为 Nuclei CPU（N300/N600/N900 系列）定义地址空间属性（Device / Cacheable / Non-Cacheable）。配置存放在 Kconfig 风格的 .config 行中。手工配置容易出错（对齐、掩码格式），因此用户维护了一个网页工具用于生成 + 校验。

## 使用时机

- 生成或校验 Nuclei SoC 的 PMA 区域设置
- 开发 PMA 配置网页工具（~/deliverables/web/pma-calc-landing/index.html）
- 编写关于 PMA 区域语义的 databook/spec 章节

## 核心规则（用户确认）

1. 区域匹配：`(Addr & ~Mask) == (Base & ~Mask)`。Mask 位=1 -> 不关心。Mask=0 -> 仅匹配 Base（单个地址）。
2. Mask = ~(Size - 1)，策略为 **1s-leading（1 前置）**：高位置 1，低位为 0（如 `'hF0000000`），这是网页工具与帮助文档统一采用的输出形式。导入解析时两种形式（1s-leading / 1s-trailing `mask = Size-1`）都能识别，输出统一转成 1s-leading。有效性检查：`all = (1n<<PA) - 1n; mask===0n || maskIsOnesTrailing(all ^ mask)`。
3. Size 必须是 2 的幂且 >= 4K。Base 必须 4K 对齐，且与 size 对齐（`base % size === 0`）。
4. 每种属性类型（DEVICE / CACHEABLE / NC）最多 8 个区域。
5. `PMA_CSR_NUM` = 区域总数（示例：DEVICE 1 + CACHEABLE 1 + NC 0 -> 2）。用户说过 "don't worry about it"：按数量生成，绝不校验。
6. 典型值：默认 0x4000_0000 / 0x03FF_FFFF -> 64MB；示例配置使用 DEVICE 0x1000_0000 +0x0FFF_FFFF（256MB）和 CACHEABLE 0x2000_0000。

## Kconfig 变量格式

```
#
# PMA
#

#
# Base & Mask must be aligned to 4k
#

#
# Device Region
#
CONFIG_N600_CFG_DEVICE_REGION_NUM=1
CONFIG_N600_CFG_DEVICE_REGION0_BASE="`N600_CFG_PA_SIZE'h10000000"
CONFIG_N600_CFG_DEVICE_REGION0_MASK="`N600_CFG_PA_SIZE'h0FFFFFFF"

#
# Cacheable Region
#
CONFIG_N600_CFG_CACHEABLE_REGION_NUM=1
CONFIG_N600_CFG_CACHEABLE_REGION0_BASE="`N600_CFG_PA_SIZE'h20000000"
CONFIG_N600_CFG_CACHEABLE_REGION0_MASK="`N600_CFG_PA_SIZE'h0FFFFFFF"

#
# Non-Cacheable Region
#
CONFIG_N600_CFG_NC_REGION_NUM=0
CONFIG_N600_CFG_PMA_CSR_NUM=2
# end of PMA
```

- 属性：DEVICE、CACHEABLE、NC；每种属性都有 `_REGION_NUM` 以及 `_REGION<n>_BASE` / `_REGION<n>_MASK` 行。
- 值是 Verilog 风格的 `` `MACRO'hHEX `` —— 十六进制位数 = PA_SIZE/4（32 位为 8 位，64 位为 16 位）。
- 需要复现的章节注释：`# PMA`、`# Base & Mask must be aligned to 4k`、`# Device Region`、`# Cacheable Region`、`# Non-Cacheable Region`、`# end of PMA`。

## 生成模式（工具规格）

输入：PA Size（32/64，需校验）、Prefix（默认 N600），以及每个区域：attribute + Base + End XOR Size（互斥 —— 填了一个就锁定另一个）。输出：

1. 与上述 Kconfig 格式完全一致的配置片段。
2. 地址条可视化：水平矩形，区域按 base 定位、按 size 定宽，最小宽度约 1.2%，让小区块保持可见。
3. 信息框：对齐失败时通过切换按钮提供两种修复方案：
   - **方案 A WRAP（默认显示）**：把 [lo, hi) 包进一个 2 的幂对齐的块。
   - **方案 B SPLIT**：按二进制分解为对齐的 2 的幂块；如果块数 > 8 显示红色警告（不要自动切换 —— 由用户决定）。

## 修复算法（使用 BigInt —— 64 位 PA 对 JS Number 超过 2^53 不安全）

```
wrapRange(lo, hi):
  sz = hiPow2Ceil(hi - lo)          # smallest power of 2 >= span
  b  = lo & ~(sz - 1n)
  while (b + sz < hi): sz <<= 1n; b = lo & ~(sz - 1n)
  return {base: b, size: sz}

splitRange(lo, hi):
  cur = lo; parts = []
  while cur < hi:
    p = hiPow2Le(hi - cur)          # largest power of 2 <= remaining
    while (cur % p != 0n): p >>= 1n # shrink until block is aligned
    parts.push({base: cur, size: p}); cur += p
  return parts
```

两者都从 `lo4k = lo & ~0xFFFn` 开始（向下取整到 4K）。丢弃 size < 4096 或超出 PA 地址空间的块；改为上报。

十六进制解析必须接受 `0x...`、裸十六进制和 `` `MACRO'h... ``（对去除首尾空白后的输入使用正则 `/[0-9a-fA-F_]+$/`），并支持可选的 `_` 分隔符。

## 检查模式（工具规格）

- 输入：粘贴的配置文本。**不提供 PA Size 输入**（用户决定）—— 按值推断。**不做 CSR_NUM 校验**（用户决定）。
- 用正则解析：
  - `^CONFIG_([A-Za-z0-9_]+)_CFG_(DEVICE|CACHEABLE|NC)_REGION_NUM=(\d+)`
  - `^CONFIG_..._REGION(\d+)_(BASE|MASK)=`（按 attr+idx 分组行）
  - `^CONFIG_..._CFG_PMA_CSR_NUM=(\d+)`
  - Prefix = 第一条 CONFIG_ 行的分组。
- 校验：NUM 与实际行数；base 4K 对齐；mask 为 1s-leading（高位连续 1）或可转换的 1s-trailing；size >= 4K；base % size == 0；重叠（同属性 = ERR，跨属性 = WARN）。
- 输出 = **修复后的文件**：除错误的 BASE/MASK 值被替换外（方案 A wrap —— 单块，行数不变），原始行逐字保留，NUM 行被修正，缺失的 NUM 行被追加。提供预览 + 下载按钮（Blob + `a[download]`，之后调用 revokeObjectURL）。

## 常见陷阱

- UI 文本必须为纯 ASCII 英文（用户的既定规则：代码中不允许非 ASCII 字符；状态标签 `[OK]` / `[ERR]` / `[FIX]` / `[WARN]`）。
- 单文件静态 HTML，零依赖，深色科技风（#0a0f1e 背景，#38bdf8 / #818cf8 强调色），与现有 landing page 保持一致。
- 浏览器验证用服务：`python3 -m http.server <port>`，workdir = 项目目录 —— 服务器提供的是其 CWD，目录不对 -> 404。
- `PMA_CSR_NUM` 和检查模式的 PA Size 是刻意排除在范围之外的；不要再与用户重新争论。

## 状态

工具 v1 位于 ~/deliverables/web/pma-calc-landing/index.html（替换了 "PMA计算工具(待上线)" 的 landing 占位页）。浏览器验证在会话中途被中断；在宣布工具完成之前，需要在真实浏览器中验证两种模式并执行 git commit。完整会话规格：references/web-tool-spec.md。
