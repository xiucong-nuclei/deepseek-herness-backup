# Translation Convention Notes

Session-specific term choices and patterns that emerged during translation work.

## GUI vs Screen

- **terminal-based GUI** — acceptable for ncurses/dialog-style TUIs that have menus, buttons, dialogs. The user's nuclei_gen tool falls in this category.
- **Main Configuration Screen** — preferred over `Main GUI Configuration Screen`. When the surrounding text already establishes this is a GUI tool, do not redundantly stack `GUI` in the title.
- For image captions, use `:name: Main Configuration Screen`.

## Option vs Configuration

- **Option** — a single configurable item in the GUI (e.g., `IDEV Option`, `System Bus Protocol Type Option`).
- **Configuration** — a chapter, section, or group of related settings (e.g., `IREGION Configuration`, `Memory Protection Configuration`).

## Chinese → English Patterns

| Chinese | English | Notes |
|---------|---------|-------|
| 配置总界面 | Main Configuration Screen | Not "Main GUI Configuration Screen" |
| 二级界面 | sub-screen | |
| 子界面 | Sub-Screen | Capital S-S |
| 悬浮窗口 | pop-up window | |
| 光标在 XX 行 | Cursor on the XX row | |
| 将光标移至 XX 行 | Move the cursor to the XX row | |
| 按下 Enter | press Enter | Capital E |
| 按下 enter | press Enter | Always capitalize Enter |
| 参见 《XXX》 | See *XXX* | Italicize doc title |
| 正式版本包 | release package | |
| 评估阶段 | evaluation only / for evaluation only | |
| 使能/开启 | enable / is enabled / Enabling... | Active voice preferred |
| 可见但不可操作 | visible but non-operable / visible but inaccessible | |
| 可完全配置 | fully configurable | |
| 周期计数器 / 已执行指令计数器 | mcycle / minstret | Use RISC-V CSR official names; never translate as "cycle counter" or "instructions-retired counter" |
| 仲裁策略 | arbitration scheme | User correction: use "scheme" not "policy" for Bus Fab context |
| 访存对齐 | misaligned memory accesses | |
| 硬件访存对齐 | hardware misaligned memory accesses | Add "hardware" qualifier only when distinguishing from software-level handling |
| 分支预测 unit | branch prediction unit / BPU | |
| 不生成 (RTL电路) | omits / does not implement | Both acceptable; "omits" is more concise for RTL generation context |
| 冗余校验码 | ECC / redundant check code | Use "ECC" when context is established |
| 校验并纠错 | check and correct | |
| 未命中 | miss | Cache miss context |
| 预取 | prefetch | |
| 数据访问模式 | data access patterns | |
| 顺序访问 | sequential access | |
| 跨步访问 | strided access | |
| 指针跳转 | pointer chasing | |
| 非缓存连续访问合并 | non-cacheable consecutive access merge | |
| 电源域 | power domain | |
| 保持上电 | remain powered on | |
| 上电 / 下电 | power-up / power-down | |
| 软件开关 | software enable (noun) | Not "software switch" |
| 系统总线数据位宽 | system bus data width | |
| 流水线停顿 | pipeline stall | |
| 吞吐率 | throughput | |
| 隐藏延迟 | hide latency | Active voice preferred |
| 高并发 | high-concurrency | |
| 访存吞吐率 | memory access throughput | |
| 超时 | timeout / on timeout | |
| Tag ram | Tag RAM | Capitalize RAM |
| 写0 | writing zeros | Plural in spec context |
| 逐一对 | entry by entry | For iterative per-entry operations |
| 复位后 | after reset | |
| 硬件初始化 | hardware initialization / hardware initializes | |
| 信号控制 | signal controls / the signal determines | |
| 露出 / 多一个信号 | exposes the signal | For RTL interface description |
| 非0值 | Non-zero value | Capital N in spec prose |
| 配置了...之后 | After ... is enabled / When ... is supported | |
| 收满 | fills / the accumulated data fills | For buffer-fill semantics |
| 已有的合并数据 | accumulated merged data | |
| 暂存的 | cached / previously cached | DCACHE context |
| 直接使用 | immediately accessible | Not "directly usable" in spec style |
| 拉高 (信号) | pulls high / drives high | NOT "asserts". "Assert" means "set to active level", not "pull high" specifically |
| 伴随码 | syndrome | ECC context |
| 物理出口 | physical exit | |
| 物理入口 | physical entrance | |
| 挂接 | attached to | |
| 安全屏障 | protection | Not literally "barrier" |
| 防御原理 | protection principle | Not "defense principle" |
| 常规设备 | conventional device | |
| 异构设备 | heterogeneous device | |
| 混合配置 | mixed configuration | |
| 互联防护 | interconnect protection | |
| 片上传输 | on-chip transmission | |
| 原生实现 | native support / natively implements | |
| 紧耦合 | tightly-coupled | |
| 车规级 | automotive-grade | |
| 命令通道 | command channel | |
| 响应通道 | response channel | |
| FIFO深度 | FIFO depth | |
| 直通 | pass-through | |
| 乒乓buffer | ping-pong buffer | |
| 基地址 | base address | |
| 地址位宽 | address width | |
| 默认slave port | default slave port | |
| EDC | EDC (Error Detection Code) | |
| 注错 | error injection | |
| 一分多 | fan-out | |
| 汇总 | aggregated | |
| 串行处理 | serializes / serialize | |
| synchronous / asynchronous / ratio / reverse_ratio / asynchronous_fifo | synchronous / asynchronous / ratio / reverse_ratio / asynchronous_fifo | Clock types: always use full form (`synchronous`), not abbreviated (`sync`). Exception: literal option values in monospace follow source |

### Bus Fab Clock Domain Terminology

| Chinese | English | Notes |
|---------|---------|-------|
| 同步时钟 | synchronous clock | Bus Fab and component share the same clock source at the same frequency |
| 异步时钟 | asynchronous clock | Bus Fab and component use independent clocks |
| Ratio 时钟 | Ratio clock | Both share the same clock source; Ratio clock period is integer multiple of source clock period; high pulse width matches the source clock |
| reverse_ratio 时钟 | reverse_ratio clock | Both clocks are integer multiples of source clock; component clock leads Bus Fab clock by one or more cycles |
| Async FIFO | Async FIFO | CDC implementation for asynchronous clock — FIFO-based data buffering across clock domains |
| 同源同频 | share the same clock source at the same frequency | |
| 同源时钟 | share the same clock source | |
| 独立时钟 | independent clocks | |
| 多级同步器 | multi-stage synchronizers | CDC for single-bit control signals (2–3 stage flip-flop chain) |
| 源时钟 | source clock | The base/reference clock from which Ratio clocks are derived |
| 高电平脉宽 | high pulse width | |
| 连接 (Bus Fab–Component) | interfaced | In bus context: emphasizes data interaction, not physical connection. "Connected" is for physical wiring only |

### Bus Fab Interface Pattern

When describing how Bus Fab and a component communicate through a given clock scheme, use the comma-appended participial phrase pattern:

```
✅ Bus Fab and the component share the same clock source at the same frequency, directly interfaced.
✅ Bus Fab and the component use independent clocks, interfaced through multi-stage synchronizers.
✅ Bus Fab and the component are interfaced through FIFO.
```

This pattern keeps the clock relationship as the main clause and appends the interface method as a participial phrase after a comma — concise and spec-idiomatic.

## Bus Fab Transfer Node Terminology

| Chinese | English | Notes |
|---------|---------|-------|
| 传输节点 | transfer node | Processing point on the data path |
| 非直通处理点 | non-passthrough processing point | Signal is not forwarded as-is |
| 信号通路 / 信号路径 | signal path | |
| 数据通路 / 数据传输通路 | data path | |
| 切断 | break / broken | Data path is broken at the transfer node |
| 协议转换 | protocol conversion | Logic operations at transfer node |
| 寄存器延迟 | register delay / register pipeline | Timing delay via registers |
| 组合逻辑 | combinational logic | |
| cmd 传输节点 | `cmd` transfer node | Monospace for signal type |
| rsp 传输节点 | `rsp` transfer node | Monospace for signal type |

## Nuclei Product Hierarchy

| Chinese | English | Notes |
|---------|---------|-------|
| 产品线 | product | Top-level |
| 系列 | series | Under product |
| 型号 | class | Under series. Keep as English `class` in spec prose |
| 向下兼容 | downward compatible | |
| MMU-capable | MMU-capable | Adjective form |
| MMU-less | MMU-less | Adjective form. Not "non-MMU" |

## RISC-V Profiles

| Term | Meaning |
|------|---------|
| RVI22 | RISC-V International Profile 2022 |
| RVI20 | RISC-V International Profile 2020 |

RVI = RISC-V International, not RV + I. The two-digit suffix is the ratification year.

## Misc New Terms

| Chinese | English | Notes |
|---------|---------|-------|
| Stack Check | Stack Check feature | |
| 物理地址宽度 | physical address width | Memory interface |
| 行为等同于 | behaves identically to | |
| 作为微控制器工作 | functions as microcontroller | |
| 对应 | corresponding | e.g., "the corresponding MMU-less class" |
| 不可利用 | unavailable | For options gated by conditions: "The X option is unavailable when..." |
| 压栈/弹栈 (寄存器) | saves and restores / push and pop | Interrupt context saving context |
| 中断延迟 | interrupt latency | |
| 中断响应时 | upon interrupt | |
| 影子寄存器 | shadow registers / Shadow GPR | ECLIC interrupt context |
| 硬件自动上下文保存 | hardware automatic context saving | ECLICv2 feature |
| 软件手动保存/恢复 | software intervention / manual save and restore | |
| 自动连带使能 | automatically enables / implicitly enables | Kconfig `select` semantics |
| 直接寻址 SRAM | directly addressable SRAM | CLM/TCM context |
| 从端口 | slave port | Bus interface |
| 最大频率 | maximum frequency | Not `fmax` in prose body |

### Nuclei Acronyms

| Acronym | Full Name | Notes |
|---------|-----------|-------|
| ILM | Instruction Local Memory | |
| DLM | Data Local Memory | |
| CLM | Cluster Local Memory | |
| PPI | Private Peripheral Interface | NOT "Device Private Peripheral Interface" — user correction |
| VPU | Vector Processing Unit | |
| NICE | Nuclei Instruction Co-unit Extension | |
| ECC | Error Correction Code | |
| ECLIC | Enhanced Core Local Interrupt Controller | For real-time systems (RTOS, bare-metal) |
| PLIC | Platform-Level Interrupt Controller | For application systems (Linux); requires MMU |
| VLEN | VPU Register Length | |
| IOCP | I/O Coherent Port | |
| CIDU | Cluster Internal Distribution Unit | SMP interrupt distribution |
| BTB | Branch Target Buffer | BPU component |
| RAS | Return Address Stack | BPU component for function return prediction |
| NAPOT | Naturally Aligned Power Of Two | PMP address matching mode |

## Articles

The user prefers **no `a`/`an`** in spec translations. Always prefer `the`, direct statements, or omitting the article entirely.

- **Rule**: avoid all indefinite articles. Use `the` or rephrase.
- When describing types/specifications: `the` not `a`:
  ```
  ✅ the 1-cycle multiplier, the 2-cycle multiplier
  ❌ a 1-cycle multiplier, a 2-cycle multiplier
  ```
- Common rewrites:
  ```
  ✅ On Icache access, ...          ← drop the article
  ❌ On an Icache access, ...
  ✅ the access is hit              ← the instead of a
  ❌ it is a hit
  ✅ sends the request               ← the instead of a
  ❌ sends a request
  ```
- Priority: `the` > omit article > rephrase > `a`/`an` (last resort)

## Chapter vs Section

- **Chapter** — top-level numbering only (Chapter 1, Chapter 2). Cannot use with subsection numbers.
  ```
  ✅ See Chapter 3.
  ❌ See Chapter 3.2.
  ```
- **Section** — subsection numbering (Section 1.1, Section 3.2.4).
  ```
  ✅ See Section 3.2.
  ❌ See Chapter 3.2.
  ```
- Document title references use italics: `See *Document Name*.`

## Sub-Screen State Descriptions

When describing an option's state on a sub-screen (enabled, disabled, not configured):

- **Unified "with" pattern**: Use `X Sub-Screen with `Y` enabled/not enabled` for all states.
  - ✅ `A Sub-Screen with `B` enabled`
  - ✅ `A Sub-Screen with `B` not enabled`
- ❌ **Colon-separated**: Avoid `A Sub-Screen: B not enabled` — colon is not spec-idiomatic.
- ❌ **"on the X Sub-Screen"**: Avoid `Y is disabled on the A Sub-Screen` — extra preposition.
- ❌ **"without" / "has"**: Avoid mixing `without` (disabled) and `has` (enabled) — use `with` uniformly.

### Image Captions for Sub-Screens (RST `:name:`)

When writing RST image captions that describe a sub-screen's appearance:

- **Use "with"** as the preferred connector: `X Sub-Screen with Y`
- ❌ Avoid "when", "—", or clausal constructions: `X Sub-Screen — When Y` or `X Sub-Screen, When Y`
- ✅ `A Sub-Screen with an Unsupported Feature Enabled`
- ✅ `Small Area Support Sub-Screen with Any Unsupported Feature Enabled`

For "任一/只要有一个" semantics (any single one, not all), use **"Any"** (not "One of" or "At Least One"):
- ✅ `with Any Unsupported Feature Enabled`
- ❌ `with One of Unsupported Features Enabled`
- ❌ `with At Least One Unsupported Feature Enabled`

## Cumulative / Hierarchical Dependencies

When features have a tiered dependency (A ⊂ B ⊂ C):

- **Pattern**: "X implies Y" / "Enabling X forces Y on"
- **List form** with inheritance description:
  ```
  - N1 — standalone extension.
  - N2 — includes N1. Enabling N2 implicitly enables N1.
  - N3 — includes N2 and N1. Enabling N3 implicitly enables both.
  ```
- **One-liner**: "The extensions are cumulative: N2 implies N1, and N3 implies both N2 and N1."

## Reference / Cross-Reference

| Chinese | English | Notes |
|---------|---------|-------|
| 参见 XX 章 | See Chapter XX | Chapter for top-level numbering only |
| 参见 XX 章 XX 文档 | See Section XX, *Document Name*. | Italicize document name |

## Placed vs Resides

| Verb | Meaning | Use When |
|------|---------|----------|
| `resides` | Inherent hardware location | Describing where a module/register is physically located by design |
| `placed` | Intentionally positioned | Describing where a tool/user puts something (layout adjustment) |

- ✅ `IDEV resides outside the core.` — hardware design fact
- ✅ `The buffer is placed in SRAM.` — tool/user action
- ❌ `IDEV is placed outside the core.` — implies someone moved it, not design intent

## Conditional Availability ("当...才支持" / "只有...才能")

When the source describes a feature gated by conditions:

- **Standard note format**:
  ```
  .. note::
     This option/feature/configuration is available only when <condition>.
  ```
- **Active-voice variant** (non-note, for body text):
  ```
  <Option> requires <condition>.
  ```
- ❌ Do not translate word-for-word as "when X, only then Y is supported".
- ✅ `This configuration is available only when DLM uses the SRAM protocol and the LSU data width is 32 bits.`
- ✅ `The half-precision support option is available only when single-precision or double-precision floating-point is configured.`

## RTL Signal / Hardware Note Pattern

When describing an RTL input signal that controls post-reset behavior:

> Note: The RTL input signal `signal_name` determines ... after reset. This signal cannot be changed once the CPU comes out of reset.

## Address Space / Formula Pattern

When describing address space constraints with formulas, keep the formula inline in monospace:

> ensure that the regions `ilm_base + ilm_size * 2` and `dlm_base + dlm_size * 2` do not overlap

## Literal Strings and Option Values

When the source refers to a Kconfig option value, RTL signal name, module prefix, or any literal string that is a programmatic identifier:

- **Use backticks (inline monospace)** — never double quotes.
- ✅ `` `nuclei300_` `` — rendered as `nuclei300_`
- ❌ `"nuclei300_"` — double quotes are for prose emphasis, not code identifiers

This applies to: option values, file names, module names, signal names, and string prefixes. When the same literal appears multiple times in the translation, keep the monospace treatment consistent.

In RST source, inline code uses double backticks: ``` ``nuclei300_`` ```. Do not add spaces between the backticks and the content.

## CPU Configuration Context

| Chinese | English | Notes |
|---------|---------|-------|
| 乘法器 | multiplier | |
| 除法器 | divider | |
| 触发器 (除法器上下文) | divider | "17-Cycle 触发器" = "17-cycle divider"; not "flip-flop" |
| 扩展指令集 | instruction extensions | |
| 内存保护特性 | memory protection attribute | |
| 物理内存保护 | physical memory protection | PMP context |
| 物理地址的权限 | access permissions on physical addresses | |
| 特权级 | privilege mode | |
| M模式 | Machine mode | |
| U模式 | User mode | |
| 原生JTAG接口 | native JTAG interface | |
| TAP状态机 | TAP state machine | |
| APB接口 | APB interface | |
| AHBL接口 | AHBL interface | |
| 异构多核调试 | heterogeneous multi-core debugging | |
| 单独Power Down | individual core power-down | |
| Flash Bus Interface | Flash Bus Interface | |
| base address | base address | Flash / memory context |
| flash size | flash size | |
| Cacheline Size | cacheline size | |
| 被强制使能 | is forced enabled | |
| PMP Entry Number | PMP Entry Number | |
| PMP entry 个数 | number of PMP entries | |

### "共存" (Two Features Coexisting)

When describing two features that coexist, prefer `provides both ... and ...`:

```
✅ provides both the JTAG state machine and the APB interface
❌ item 1 and item 2 are both present
❌ the native JTAG interface and the APB interface coexist
```

### "while" for Contrast

Use `while` (not `but`) for contrasting where two components reside:

```
✅ Etrace resides inside the core, while the encoder resides outside the core.
❌ Etrace resides inside the core, but the encoder resides outside the core.
```

## Configuration Status Labels (配置了 / 没有配置)

For short-form status labels (sidebar callouts, bullet-point state descriptions):

| Chinese | English |
|---------|---------|
| 配置了 XX | XX configured |
| 没有配置 XX | XX not configured |
| 使能 / 开启 | enabled |
| 未使能 / 关闭 | not enabled |

No articles, no verbs — bare state adjectives.

When an option's availability depends on the chip variant:

- **Pattern**: "... is available only on ... On variant A, the option is ... On variant B, the option is ..."

## Check vs Verify (ECC / Bus Protection)

In ECC, bus protection, and data-integrity contexts:

| English | Use When | Avoid When |
|---------|----------|------------|
| `check` / `checking` | Runtime ECC validation (checking ECC code on received data), hardware self-check | — |
| `verify` / `verification` | Formal verification, testbench validation, design verification | Hardware runtime ECC operations |

- ✅ `ECC generation and checking` — hardware spec standard
- ✅ `the command channel checks the ECC code` 
- ❌ `ECC generation and verification` — user rejection, 不通顺
- ❌ `the command channel verifies the EDC code` — too formal/verification-oriented

Rule: In ECC/bus protection contexts, prefer `check`/`checking` over `verify`/`verification`.

## Execute vs Function / Operate (Hardware)

For hardware logic (checking, detection, error handling):

| English | Use When | Avoid When |
|---------|----------|------------|
| `functions` / `operates` / `works` | Hardware logic behavior, logic correctness testing | — |
| `execute` | Software/instruction execution | Hardware logic description |

- ✅ `test whether the EDC checking logic functions correctly`
- ❌ `test whether the logic executes correctly`

## "解决…导致" — Hypothetical vs Actual

Chinese "为了解决 X 导致 Y 的问题" describes a design motivation: Y is a **hypothetical problem** that the design avoids, not an actual behavior.

| Pattern | English |
|---------|---------|
| 为了解决 X 导致 Y 的问题 | To avoid Y that would occur with X |
| X 会导致 Y | X would cause Y (if not mitigated) |

- ✅ `Generating ECC at wider widths would cause ECC regeneration ... To avoid this, Bus Fab generates EDC per 32-bit data.`
- ❌ `Data width conversion triggers ECC regeneration. To eliminate this, ...` — makes hypothetical sound like actual behavior

## Diagram Caption Pattern

When the Chinese source ends with "如图所示" / "过程如图所示" / "如图" etc.:

- **Pattern**: `... as shown in the diagram below.`
- **Placement**: at the END of the sentence, not in the middle.
- Purpose: lets the user insert `.. drawio-figure::` or `.. image::` directive between text and caption.

Example:
```
✅ Port connects to Bus Fabric as shown in the diagram below.
❌ As shown in the diagram below, the port connects to Bus Fabric.
```
