---
name: debugging
description: '4-phase root-cause debugging; playbooks: Makefile shell & RISC-V CPU boot hangs.'
metadata:
  hermes:
    tags:
    - debugging
    - troubleshooting
    - root-cause
    - makefile
    - riscv
    - cpu
    - boot
    - verdi
    category: software-development
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# 调试（系统化根因定位方法 + 领域剧本）

类级调试技能：四阶段根因定位方法（在理解 bug 之前绝不修复），加上本机实际调试领域积累的剧本——内嵌 shell 的 Makefile 配方，以及 RISC-V CPU 启动阶段卡死。整合了原有的 `systematic-debugging`、`makefile-shell-debugging` 和 `riscv-cpu-boot-debug` 技能。

## 铁律

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

随机修复浪费时间还会制造新 bug；快速补丁会掩盖底层问题。如果尚未完成阶段 1，就不能提出修复。

## 四个阶段

### 阶段 1 — 根因调查
1. **仔细阅读错误信息**——堆栈跟踪、行号、错误码通常直接指向解决方案。在代码库中找到该错误字符串。
2. **稳定复现**——步骤完全一致、每次都能复现吗？不能复现 → 收集更多数据，不要猜测。
3. **检查最近的改动**——`git log --oneline -10`、`git diff`、`git log -p --follow <file>`。
4. **在多组件系统中收集证据**——提出修复之前，先在每个组件边界添加诊断插桩（记录输入、输出、配置/环境变量传递、各层的状态）；运行一次找出问题出在哪一环，再深入调查该组件。
5. **追踪数据流**——坏值从哪里来？一路向上游追踪到源头；修复源头，而不是症状。

完成清单：已读错误信息、已复现、已审查改动、已收集证据、已隔离问题、已形成根因假设。在理解 WHY 之前**停下**。

### 阶段 2 — 模式分析
在同一个代码库中找到类似的**能正常工作**的代码；完整阅读参考实现（不得跳读）；列出正常与故障实现之间的每一处差异；理解其中的依赖和假设。

### 阶段 3 — 假设与测试
形成一个**单一**的具体假设（"X 是根因，因为 Y"）；用**最小**的改动来测试，一次只变一个变量；成功 → 进入阶段 4，失败 → 提出新假设（不要堆叠修复）。不知道就说不知道并去查证，而不是装作知道。

### 阶段 4 — 实施
先创建失败测试/复现；只为根因实施**一个**修复（不要"顺手"改进）；验证修复并运行完整测试套件检查回归。

- **三次法则**：连续 3 次以上修复失败 = 停下并质疑架构（每次修复都在别处暴露出新的耦合、修复需要大规模重构、不断出现新症状 = 架构问题，而非假设失败）。在第 4 次尝试之前先与用户讨论。

### 危险信号 —— 停下并回到阶段 1
"先快速修一下，回头再查" · "就试着把 X 改一下" · 一次做多处改动 · 跳过测试 · "大概是 X，让我修一下" · 在追踪数据流之前就提出修复 · 连续失败 2 次以上仍"再试一次修复"。

## Hermes 集成

- **调查工具**：`search_files`（追踪调用、查找错误字符串）、`read_file`（带行号的源码）、`terminal`（复现、查 git 历史）、`web_search`/`web_extract`（研究错误信息）。
- **多组件系统** → 派发一个调查子代理，使证据收集不带修复偏见（调整 delegate_task 的 goal/context）：
  ```python
  delegate_task(
      goal="Investigate why [specific test/behavior] fails",
      context="""Follow the systematic-debugging method:
      1. Read the error message carefully
      2. Reproduce the issue
      3. Trace the data flow to find root cause
      4. Report findings — do NOT fix yet
      Error: <paste>  File: <path>  Test command: <exact>""",
      toolsets=['terminal', 'file']
  )
  ```
- **TDD 联动**：阶段 4 从一个失败测试/复现开始（RED），然后做根因修复（GREEN）；该测试保留下来作为回归防护。

## 领域剧本：Makefile Shell 配方

当 Makefile 目标用 `\` 续行嵌入多行 shell 脚本时，报错往往难以理解。触发点：`syntax error near unexpected token`、`unexpected end of file`、`[: missing ']'`、`/bin/sh` 行错误、字面 `\033` ANSI 文本、管道中的 `if` 永远不为真、`[ -n "$VAR" ]` 通过但 `for` 循环从不执行。

高频错误 → 修复对照表（完整细节见 `references/makefile-recipe-debugging.md`）：

| 错误 | 原因 | 修复 |
|---|---|---|
| `unexpected end of file` | 续行上缺少 `\` | 除最后一行外每行都以 `\` 结尾 |
| `[: missing ']'` | `[ ... ] cmd` 缺少分隔符 | `] && cmd` |
| ANSI 显示字面 `\033` | `sed` 不展开 `\033`（CentOS 7） | 用 `awk '{printf "\033[32m%s\033[0m\n", $$0}'` |
| `if grep \| sed` 恒为真 | 管道退出码 = 最后一条命令 | 分开执行，再 `if [ -s tmp ]` |
| 配方中 shell 变量为空 | `$var` 被 Make 吞掉 | 用 `$$var`（awk 中也一样，用 `$$0`） |
| `tee` 吞掉退出码 | 管道退出码 = tee 的 0 | 追加 `; exit $${PIPESTATUS[0]}` |
| `for` 从不迭代但检查通过 | `$(VAR)` 是命令替换，不是变量 | 用 `"$VAR"` |
| `$$test` 打印出 PID | `$$` 是 shell 的 PID | 用 `$test` |
| `find -name "$$case"` 结果为空 | 文件尾部带有 `\r`/空格 | `tr -d ' \r'` / `xargs` |
| bsub 等待任务从不启动 | 任务名匹配到自己的 `-w` 模式 | 给收集任务用不同的前缀 |

每次诊断都从 `make -n <target>` 开始——它会打印 Make 实际拼接运行的 shell 脚本，`line N` 错误指向的是该脚本中的行，而不是 Makefile。

## 领域剧本：RISC-V CPU 启动阶段调试

当 CPU 核在启动时卡住（iaddr 冻结、PC 不动——尤其是在 BSS 初始化或早期启动阶段）。完整剧本（波形信号、Verdi 导航、ecall 陷阱级联、ECC 注入、PMA 基础）：`references/riscv-boot-debug-playbook.md`。

**先做判别**：

| 观察现象 | 分类 | 根因类别 |
|---|---|---|
| iaddr 在 2–4 个地址间循环（0x518→0x51c→...） | 软件死循环 | 边界不匹配、回绕溢出 |
| iaddr 逐周期停在同一地址 | 硬件停滞 | 总线无响应、LSU 停滞、I-Cache 未命中、时钟/复位 |
| iaddr = 0 / 0xFFFFFFFF / 未映射 | 非法地址 | 向量错误、内存映射缺失 |

- **软件死循环** → BSS 清零循环：在寄存器文件中抓取 `a0`（`_bss_start`）和 `a1`（`_end`）。`a1` = 0xFFFFFFFF → 链接脚本 `_end` 落在未映射内存之后；`a0` 从 0xFFFFFFFC 回绕到 0 → 无符号 `bltu` 配合 `addi` 溢出；起始时 `a0 > a1` → 段顺序问题。Nuclei SDK 用 `_end`（GNU LD 内建，始终存在）而非 `_bss_end`——与链接器无关。
- **硬件停滞** → 先检查 `clk` 是否翻转、`rst_n` 是否正常，再看取指握手：`ibus_arvalid=1, arready=0` 持续 >10 个周期 = 总线从设备无响应；`arvalid=0` = 取指单元被后端阻塞。后端停滞传播：`lsu_stall`/`load_wait`（最常见——BSS 循环里的单个 `sw` 就可能造成停滞）、`fetch_pc_stall`、`store_buffer_full`；检查 `dtlb_miss` 和数据总线 `awready`/`wready`。
- **陷阱级联**（ecall → mcause=9 → 持续 mcause=2）：ecall 总是跳转到 `mtvec`（任何模式下都不会穿透）。如果 `mtvec` 为 0（在 `ECLIC_Interrupt_Init()` 之前发生 ecall）或指向 .bss/垃圾数据，处理器取到垃圾指令 → mcause=2 → 再次进 mtvec → 死循环。检查 `mtvec` 值 + MODE 位（CLIC 向量模式 = 低两位 `11`）、`mepc`、`mtval`。
- **Verdi**：寄存器文件位于 `u_exu → u_exu_alu → u_exu_alu_rgr` 下（搜索 `*rgr*`）；CSR 位于 `u_exu → u_csr` 下；`mtval` 在 mcause=2 时存放指令编码（0 → 从未初始化内存取指），在 5/7 时存放虚拟地址，ecall 时为 0。`.fsdb` 报 "empty file"/"Wrong file type" = 仿真在 dump 之前崩溃（磁盘配额）或缺少 `$fsdbDumpvars`。
- **ECC 注入**（MECC_CODE 是 XOR 掩码：`0x01` 翻转 ECC 位 0 → 单比特错误）：在任何 `csrc` 之前读取 `MECC_CODE`（csrc 会清除锁存器）；CSR_MCACHE_CTL/MECC_CODE 仅限 M 模式——在 S/U 模式下写入会静默失败（检查 `cpu_mode` / `mstatus.MPP`）；使用全新的蹦床地址或分页隔离的代码，让缓存真正未命中。

## 参考文件

| 文件 | 内容 |
|---|---|
| `references/riscv-embedded-debugging.md` | RISC-V/Nuclei 嵌入式陷阱（Zcmt 跳转表、JVT CSR、工具链标志） |
| `references/riscv-boot-debug-playbook.md` | 完整 RISC-V 启动卡死剧本（iaddr 分类、BSS 循环、陷阱级联、ECC、PMA、Verdi） |
| `references/makefile-recipe-debugging.md` | 完整 Makefile shell 配方调试指南 + 错误→修复对照表 |
| `references/n300-bss-loop-case-study.md` | N300 BSS 循环冻结案例研究 |
| `references/trap-cascade-n900-case-study.md` | N900 ecall 陷阱级联案例研究 |
| `references/hws-dwarf-compatibility.md` | hws/hwsww 的 DWARF 5 → DWARF 4 兼容性修复 |
| `references/makefile-dynamic-targets.md` | 通过 `$(MAKECMDGOALS)` 实现 Makefile 动态目标（getpng/run/show） |
| `references/verification-doc-generation.md` | 从测试用例目录用 Python + Sphinx RST 生成文档 |
| `references/amo-type-portability.md` | AMO 内建函数 `long *` 的 RV32/RV64 可移植性陷阱 |
| `references/sphinx-rst-image-path.md` | RST 图片路径处理 |
| `references/misaligned-bus-error-debug.md` | 非对齐总线错误调试 |
| `references/ansiesc-vim-install.md` | 离线安装 AnsiEsc.vim（CentOS 7），用于在 vim 中渲染 ANSI |
