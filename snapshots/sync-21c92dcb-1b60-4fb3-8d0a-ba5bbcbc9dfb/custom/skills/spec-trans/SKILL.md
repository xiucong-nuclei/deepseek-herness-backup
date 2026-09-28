---
name: spec-trans
description: Translate Chinese technical text into spec-style English — concise, precise, active voice, suitable for hardware specs and technical documentation.
metadata:
  hermes:
    tags:
    - translation
    - chinese
    - english
    - technical-writing
    - spec
    - documentation
    version: 1.2.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# Spec-Style Technical Translation (中文 → 规范级英文)

Translate Chinese technical text into **spec-grade English** suitable for hardware reference manuals, ISA specifications, and low-level technical documentation. Output reads like RISC-V spec / ARM TRM / datasheet prose: **concise, precise, imperative, no fluff.**

## When to Use

**Trigger MUST be explicit:**

### ✅ 触发条件

1. 消息包含 `!spec-trans`：前面所有中文为待翻译文本，后面有中文则同时翻译
   ```
   "!spec-trans 复位后，CPU通过系统总线从系统内存取指"
   "删除不应该存在的 fab case !spec-trans"  ← 末尾触发，前面中文为输入
   ```

2. 用户明确说"翻译成规范英文" / "spec 风格翻译" 等

3. 图片 + `!spec-trans`：OCR 中文原文后翻译

### ❌ 不触发

- 普通翻译请求（不是技术文档风格）
- 非技术内容翻译

### ⚠️ 特殊方向

- **英译中（技术图表/图片）**：用户发送英文技术图并要求"翻译成中文"时触发。适用于已有英文标注的架构图、流程图、寄存器表等。保留原图结构，仅翻译标注文字。
- **中文译回英文（已翻译内容回退）**：用户发送之前翻译过的中文图要求"翻译成英文"时触发。参照之前的英文原文或按 spec 风格重新撰写。

## Workflow

### Step 1 — 读取原文

如果是图片，先用 `vision_analyze` OCR 提取中文原文。

### Step 2 — 翻译

遵循以下规则：

**语法规范：**
- **主动语态**：`The CPU fetches...`，不用 `Instructions are fetched by...`
- **一般现在时**：`After reset, the CPU...`，不用 `After reset, the CPU will...`
- **祈使/陈述混合**：规范文本以陈述事实为主，偶尔用 imperative
- **短句**：中文长句拆成英文短句，每句一个要点
- **逻辑主语明确**：CPU / hardware / the core / the cache / the bus — 不省略主语

**术语规范：**
- 保持技术术语原文：`Icache`, `Dcache`, `L2cache`, `AXI`, `AHB`, `TCM`, `cacheable`
- 完整中文→英文术语映射表（100+ 条，含 Nuclei 专有术语 CPPI/CIDU/IOCP/CLM/CC/ECLIC/PLIC/BPU/BTB/RAS/VLM/SBA/PMA/EDC 等）见 `references/terminology-table.md`，按需加载


**风格规范：**
- **表格单元格模式（Table-cell mode）**：用户明确要求"简短一点，像短语一样，要放在表格中"时，译文用**箭头链式短语**而非完整句子。去掉冠词、主语、be 动词，用 `→` 连接操作序列。例：
  ```
  完整句 ❌: The hardware reads, then modifies the sub-word, recomputes ECC, and writes back to SRAM.
  表格格 ✅: Read → modify sub-word → recompute ECC → write back
  ```
- **不要定语从句**：不用 `which` / `that` / `where` 从句，拆成两个简单句或用介词短语替代。Spec 英语追求简单 SVO 结构，不写长难句
- **读者英语水平**：译文面向英语非母语读者，避免不必要的复杂从句和生僻词，但保持 spec 的精确性和正式感。不刻意降级词汇，该用 `configure` 就用 `configure`，不用 `set` 凑合
- 不用 AI 味词：`delve into`, `unleash`, `robust`, `seamless`, `empower`, `leverage`
- 不用主观评价：`obviously`, `clearly`, `interestingly`
- 不加解释性内容：只翻译原文，不补"这是因为..."、"换句话说..."
- **有限润色**：允许修正原文的重复、歧义、不通顺之处，但不改变原意。典型场景：中文原句重复堆叠词汇（如"支持 D-Cache 和 D-Cache 的支持的特性"），翻译时合并重复、理顺表达
- **字面值用 monospace**：文件名、模块名、配置选项名、信号名、字符串前缀等**字面值**统一用反引号包裹（`like_this`），不用双引号。这是技术文档的惯例，和 `CFG_CORE_PFX`、`nuclei300_`、`nuclei300_core_wrapper.v` 等标识符的处理一致。RST 中等价于 inline code（monospace 渲染），Markdown 中等价于代码片段
- **缩略语用全称**：技术文档中使用全称而非缩略语。`synchronous` / `asynchronous` / `reverse_ratio` / `asynchronous_fifo`，不用 `sync` / `async` / `ratio_rev` / `async_fifo`。参数名、选项值等 literal 值保持原文不变
- **插图引用放句尾**：中文\"XX 如图所示\"译文结构为 `... as shown in the diagram below.`，放在句子末尾，不在句中。便于用户在图的前后插入图片引用指令

### Step 3 — 输出

```markdown
📝 原文：<中文原文>

🇬🇧 Spec 风格：
<翻译结果>
```

## Examples

### Example 1 — 缓存模式说明

> **输入**：复位后，CPU 通过系统总线从系统内存取指，若 Icache 被配置且指令地址的物理内存属性为 cacheable，指令会被缓存到 Icache。

**输出**：
```
After reset, the CPU fetches instructions from system memory via the system bus.
If Icache is configured and the physical memory attribute of the instruction
address is cacheable, the instructions are cached into Icache.
```

### Example 2 — 总线特性

> **输入**：与 AXI 总线一样，ICB 采用分离的地址和数据阶段，支持地址非对齐访问，使用字节掩码控制部分写操作。

**输出**：
```
Like AXI, ICB uses separate address and data phases. It supports misaligned
accesses and uses byte masks (write strobes) to control partial writes.
```

### Example 3 — 简单陈述

> **输入**：此模式下 RESET_VECTOR 作为系统内存。

**输出**：
```
In this mode, RESET_VECTOR is treated as system memory.
```

### Example 4 — 避免定语从句

> **输入**：不同的 run mode，决定了程序被加载和执行在哪种区域。

**❌ 错误（含定语从句）**：
```
The run mode determines which memory region the program is loaded into
and executed from.
```

**✅ 正确（简单 SVO + 介词短语）**：
```
The run mode selects the memory region for program download and execution.
```

## References

- `references/terminology-table.md` — full Chinese→English terminology table (100+ terms, Nuclei-specific)
- `references/terminology.md` — terminology decisions: GUI vs screen vs TUI, configurable options convention
- `references/term-conventions.md` — session-accumulated term mappings and style decisions (GUI vs Screen, option vs configuration, article usage).
- `references/edc-ecc-terminology.md` — Bus Fabric EDC/ECC domain knowledge, protection code sizing, error injection flow.
- `references/option-description-conventions.md` — Option description pattern for Nuclei databook, en-dash list of values, no current/default state rule.
- `references/smp-cluster-terminology.md` — SMP/Cluster domain knowledge for N600: component glossary (CPPI, CLM, IOCP, CIDU), sub-screen structure, Latency Levels vs individual access cycles.
- `references/exclusive-feature-terminology.md` — RISC-V Exclusive/Atomic feature terminology, lr/sc documentation, bus response tables, table header translations.
- `references/stack-detection-terminology.md` — Stack detection / overflow / underflow / tracking terminology, mstack_* CSR register naming.
- `references/chinese-text-reorganization.md` — pre-translation Chinese restructuring workflow
- `references/icache-scratchpad-terminology.md` — I-Cache Scratchpad domain knowledge (cache vs scratchpad modes, key terms, plain-language explainer)

## Style Reference Documents

Translations follow the writing style of these Nuclei reference documents
(in priority order):

1. **Nuclei N300 Series Databook** — primary style reference. Uses
   `The XXX is...` pattern for definitions, en-dash (`–`) for list
   items, concise declarative sentences.
2. **Nuclei Processor Integration Guide** — instructional/direct tone.
   Uses `if user...` pattern, inline monospace for commands and file
   names.
3. **RISC-V Unprivileged Specification** — formal spec English baseline.
   Uses `This document describes...`, ratified/draft status markers.

Key style rules inherited from these documents:

- Definition sentences use `The XXX is...` or `The XXX provides...`
- List items use `–` (en-dash), not `-` or `•`
- Direct instructional tone (not academic hedging): `just replace`,
  `configure`, `generate`
- Keep Nuclei-specific phrasing: `NXXX` as placeholder, `nuclei_gen`
  as tool name
- No `a`/`an` articles — matches Nuclei documentation convention

## Translation Conventions

### 冠词

- **一律不用不定冠词（a/an）**。tech spec 面向定义和特征，不定冠词引入歧义。用特指（`the`）或省略冠词。用户明确指示：`不要用 a 这个量词`、`尽量不要用 a 或者 an 量词，尽可能用特指`。
- 状态词不作可数名词，直接作形容词/补语:
  ```
  ✅ the access is hit / the access is miss
  ❌ it is a hit / it is a miss
  ```
- 描述**类型/规格**（不是数量）时用 `the`：
  ```
  ✅ the 1-cycle multiplier, the 2-cycle multiplier
  ❌ a 1-cycle multiplier, a 2-cycle multiplier
  ```

### 文献引用

- 只用文档名，不加链接。格式：`See *Document Name* (ARM IHI 0033).`
- 不用 URL 超链接
- 中文"参考"统一译为 `please refer to`，不用 `see` / `refer to`。例：`Please refer to *Document Name* for more details.`

### GUI 术语

- 终端 TUI（ncurses/dialog 风格）用 `GUI` 或 `screen` 均可，但 `GUI` 更准确描述交互式界面
- 子界面统一用 `sub-screen`
- 悬浮窗口用 `pop-up window`
- 不堆叠同义词：`Main Configuration Screen` 优于 `Main GUI Configuration Screen`

### 配置位置描述（"配置到 Core 内部/外部"）

- 中文"配置到 Core 内部" → `resides inside the core`（不是 `is configured inside the core`）
- 中文"配置到 Core 外部" → `resides outside the core`
- 同时描述两件事用 `and` 连接短语，不堆从句：`IDEV resides outside the core, and Core-only resides inside the core.`
- 格式：`With ``Option`` enabled, IDEV resides inside the core. The CPU accesses IDEV directly.`

### 表格标题

- 中文"XX 对 YY 支持情况" → `XX Support by YY`（如 `Memory Interface Type Support by N300 CPU Type`）
- 表名中 CPU Type 用 `N300 CPU Type`，不是 `300 Product` 或 `300 Type CPU`

### 选项列表

- 每个选项一行，用 `- **Option Name** — Description.` 格式
- 选项值用 `Options: A or B.` 收尾

### 选项介绍句（Databook 单句描述）

- 用 `The `OptionName` option...` 开头（不用破折号、不用 "This option"）
- 不单独成段，紧跟选项名之后
- 示例：`` The `SMP Option` option enables SMP multi-core support. ``
- 条件可用性：`` This option is available only when SMP core count is greater than 1. ``
- 使能后出现子选项：`` After this option is enabled, the following configuration options appear: ``

### 条件可用性

- 中文"可利用" → `becomes available`（选项可见/可操作），不是 `usable`
- 中文"使能该选项后...才可用" → `become available only after this option is enabled`
- 中文"当 XX 时该选项可利用" → `This option is available only when XX.`
- 中文"仅当 XX 且 YY 时可用" → `This option is available only when XX and YY.`
- 中文"该选项是不可利用的当 XX" → `This option is unavailable when XX.`
- 中文"当 XX 时，这些选项可利用" → `These options are available only when XX.`

### RST 输出

- 当译文包含多个段落或列表时，用 `rst` 代码块输出，方便直接复制到 Sphinx 文档
- 章节标题用 `===` 下划线格式
- `.. note::` 块格式：缩进内容，如：
  ```rst
  .. note::

     When the SMP core count is 4 or above, 2 cycle is recommended.
  ```
- 配置选项表：当选项值是多个子条目时，用 option → value → description 结构逐个列出，如：
  ```rst
  – `CPPI Base Address`
    Sets the CPPI base address. The value is configured through pop-up window
    string input.
  ```
- **破折号用三个英文连字符 `---` 表示** — 需要破折号（列表项分隔、`i.e.,` 的替代等）时，RST 源文件中写三个英文 `---`，这符合 RST 语法（Sphinx smartquotes 渲染为 `—`）。不要在 RST 源文件直接写 Unicode `—` / `–` 字符，避免编码/渲染问题。例：
  ```rst
  - 1 --- the SRAM returns data in the next cycle.
  - 2 --- the SRAM returns data two cycles later.
  ```
- **枚举值全部列出，不用 "and so on" / "以此类推"** — 取值有限时（如周期值 1 到 4）全部写出来，不省略。编号直接用数字（`1` `2` `3` `4`），不加 `Value = X` / `周期为 N` 前缀
- **WaveDrom 波形图** — 时序类章节用 `.. wavedrom::` 指令内嵌波形，内容为**严格 JSON**（键必须双引号，否则报 `Property keys must be doublequoted json`）。演示可配置延迟时：请求信号 + 各配置值的返回数据信号行，`"config": { "hscale": 2 }` 调宽度，`...`（三点）表示间隙、`|` 表示断点。也可用 `wavedrom-cli -i x.json -s x.svg` 生成 SVG 后以 `.. image::` 引入，或在 https://wavedrom.com 预览导出
- **章节标题层级一致** — 子章节标题的下划线符号必须与同层标题一致（同层都用 `-` 或都用 `#`），下划线长度与标题文本等长，否则 Sphinx 报 `Inconsistent title style: skip from level 1 to 3`

### Example 5 — 字面值与 monospace

> **输入**：CFG_CORE_PFX选项用来配置CPU生成代码的模块文件的前缀以及模块名称的前缀。当该选项配置为 nuclei300_ ：
> ●CPU生成的RTL的文件名称，都是 nuclei300_ 开头，如 nuclei300_core_wrapper.v
> ●CPU生成的module的名称，都是 nuclei300_ 开头，如  nuclei300_core_wrapper

**输出**：
```
The `CFG_CORE_PFX` option sets the file name prefix and module name prefix for
all CPU-generated code. When set to `nuclei300_`:

- All generated RTL file names use the `nuclei300_` prefix. For example,
  `nuclei300_core_wrapper.v`.
- All generated module names use the `nuclei300_` prefix. For example,
  `nuclei300_core_wrapper`.
```

注意：`CFG_CORE_PFX`（配置名）、`nuclei300_`（字面字符串）、`nuclei300_core_wrapper.v`（文件名）、`nuclei300_core_wrapper`（模块名）全部用反引号（monospace），不用双引号。

## Pitfalls

- **输出统一使用 UTF-8 编码** — 生成的译文（含反引号、en-dash `–`、`→`、中文等字符）必须以 UTF-8 编码输出或保存。禁止使用 GBK、Latin-1 等其他编码，避免特殊符号或中文乱码。
- **原文是分条时保持分条格式** — 中文原文用 `●` 或 `-` 分条，译文用 `-` 保持同样结构。不要在一条里合并多条内容。
- **不要长句** — 中文一句话可能很长，英文拆成 2-3 句
- **数量前缀用单数复合形容词** — 短语/标题里的数量前缀按英文复合形容词规则用单数：`4-ways I-Cache` → `4-Way I-Cache`（不是 `4-Ways`），与既有规则 `the 2-cycle multiplier` 一致。中文"XX 路/XX 位/XX 周期"同理
- **不要被动语态泛滥** — 规范英语用主动语态为主，被动只在主语不明确时用
- **保留原文结构** — 如果原文是列表/分点/条件句，译文保持同样结构
- **短标题也是输入** — 当用户发送 `!spec-trans CPU case 运行模式介绍` 时，`CPU case 运行模式介绍` 就是待翻译的中文，不要误解为"请先介绍 CPU case 再翻译"。`!spec-trans` 之后的所有文字都是翻译输入，没有例外。**即使包含"图"、"架构图"、"表"等字眼，也是直接翻译该短语**，不要额外询问是否需要发送图片或文件。用户如果真有图片会直接发送
- **不要补内容** — 用户只给了半句话就不要补后半句。用户说"扩展下介绍"时才补充
- **子界面选项状态用 "with" 连接** — 不用 "on the XX Sub-Screen" 或冒号分隔，也不混用 has/without。统一用 `with` 构造：启用 → `A Sub-Screen with `B` enabled`；未启用 → `A Sub-Screen with `B` not enabled`。简洁一致，避免介词堆叠
- **层级继承用 "implies"** — 描述 N1⊂N2⊂N3 类累积特性时用 "N2 implies N1"，不用长从句解释依赖关系
- **不要过度直译，英文要像英文 spec** — 中文"通过修改 A 来修改 B"如果直译成 "modifying A controls B" 会不自然。用 "derives from"、"changing A changes B" 或 "is controlled by adjusting" 等更自然的英文表达。原则：读起来应该像 native English speaker 写的硬件文档，不是中文的逐字翻译。当用户说"语法不太像科技类 spec"时，就是这个问题
- **生僻词触达** — 用户看不懂某个词时（如对 "reveals" 提问），立即提供 2-3 个更简单的替代词（shows / exposes / makes visible），并让用户选。该用术语时保留术语（configure, CSR, cacheable），但动词和连接词以非母语读者能一眼看懂为准
- **vision_analyze 对代码/GUI 截图不可靠** — Qwen3-VL 系列模型对终端截图、Kconfig 代码、nuclei_gen GUI 等界面经常产生严重幻觉（把"配置选项"的截图 OCR 成"scrcpy 终端日志"等完全无关内容）。图片 + `!spec-trans` 时优先请用户直接粘贴原文。不得不 OCR 时，用 `ocr-and-documents` 技能的 tesseract 路径交叉验证
- **"拉高" 不等于 "assert"** — 中文"拉高中断信号"指电平拉高（high），不能用 `asserts`。`assert` 是"置为有效电平"，可高可低，歧义。正确译法：`pulls ... high` 或 `drives ... high`。同理"拉低"用 `pulls ... low`。
- **信号激活用 `asserts`，不用 `returns`** — 中文"激活信号"在硬件规范中译作 `asserts the signal`，不用 `returns`。`returns` 偏软件函数返回值的概念。当信号使能条件成立时，硬件"激活"该信号 → `asserts`。
- **信号撤销用 `deasserts`** — 对应 `asserts`，中文"撤销信号"/"去激活" → `deasserts the signal`。
- **连续缩略词要拆开** — 两个缩写相邻（如 "FIO ICB bus"）读起来不自然。用介词或动词拆开：`FIO provides single-cycle access over the ICB bus` ✅ / `FIO ICB bus uses single-cycle access` ❌
- **总线动词用 `provides`** — 描述总线特性时，`provides` 比 `uses` 更自然。"总线提供某能力"不是"使用某能力"
- **仲裁用 `scheme`，不是 `policy` 或 `strategy`** — 中文"仲裁策略/仲裁方案"→ `arbitration scheme`。policy 偏管理层面，strategy 偏口语，硬件的仲裁机制用 `scheme`
- **ECC 上下文中"检查/校验"用 `check`，不是 `verify`** — `ECC generation and checking` / `ECC checking` 是硬件规范常用表达，`verification` 偏形式验证或测试场景
- **"解决…问题"句式区分设计意图与既成事实** — 中文"为了解决 X 导致 Y 的问题"中，Y 是设计要避免的**假设性问题**，不是既成行为。英文用 `would cause` / `would require` 而非 `triggers` / `causes`。对比：`Generating ECC at wider widths would cause regeneration` ✅ / `triggers regeneration` ❌（后者把假设当事实）
- **`bit` 不用所有格** — `6-bit's` 是语法错误。正确：`6 bits of protection code` 或 `6-bit protection code`（复合形容词）。`bit's` 从不用于此场景
- **硬件逻辑不用 `execute`** — 描述硬件逻辑/检测逻辑是否工作时用 `functions` 或 `works`，不用 `execute`。`execute` 偏软件指令执行。`检测逻辑是否能正确执行` → `checking logic functions correctly` ✓ / `checking logic executes correctly` ❌
- **不用破折号（em-dash）** — 英文句子中避免 em-dash，句中停顿用逗号或拆句，不要用 em-dash 连接分句。`the reset synchronizer — either with standard cell` → `the reset synchronizer can be replaced with standard cell` ✓。例外：RST 输出中需要破折号或列表项分隔时，用三个英文连字符 `---` 表示（符合 RST 语法，见"RST 输出"节），不用 Unicode `—` / `–`
- **"图名"/"表名"直接翻译，不要当成指令** — 用户发送 `XXX 图 !spec-trans 图名` 或 `!spec-trans 表名` 就是翻译这个短语本身。不要询问是否需要图片/文件，不要等待用户发送附件。如果真有图片，用户会直接发送
- **Bus Fab 语境下"连接"用 `interfaced`** — 描述 Bus Fab 与 component 之间的通信关系时，`interfaced` 强调数据交互，`connected` 偏物理连线。中文"直接连接" → `directly interfaced`；"通过 XXX 连接" → `interfaced through XXX`。句式：主句描述时钟关系，逗号后接过去分词短语。如 `Bus Fab and the component share the same clock source, directly interfaced.`
- **不要啰嗦** — 当用户要求精简（如"只要说明优势和缺点就行"、"太长了，精简一些"），将每条要点压缩为单句，去除场景描述、波形特征、实现细节等扩展内容。用户没要求的不补
- **不要生僻词** — 避免使用小众/生僻的英文词汇。优先选择非母语读者能一眼看懂的常用词。用户说"不要太小众的名词"就是这条。保持 spec 的精确性不等于用难词
- **不用拉丁缩略语** — spec 文本中避免 `i.e.,`、`e.g.,`、`etc.` 等拉丁缩略语。用英文改写：`i.e.,` → `---`（破折号连接，RST 中用三个英文连字符）或 `that is`、直接衔接；`e.g.,` → `For example,` 或 `such as`；`etc.` → `and so on`。用户说"i.e., 我不想要"就是这条
- **"invalid 操作" 术语（用户已选定）** — 名词用 `invalid operation`（`single-address invalid operation` / `full-address invalid operation` / `region invalid operation` / `invalid-all`），动词用 `invalidates`，与 RISC-V CMO INVAL 命名风格一致；不用 `invalidation` 名词形式
- **不要无文档推测** — 用户询问不熟悉的选项/特性时，如果没有文档佐证，不要凭选项名猜测含义。直接告知"没有文档佐证，无法确定"，请用户提供截图或文档。不要输出未经证实的推测性描述
- **内容扩展工作流** — 当用户要求扩充某段内容并翻译时，先提供**中文扩展版本**给用户审阅确认，确认后再执行 `!spec-trans` 翻译。不要直接输出英文扩展版本
- **选项介绍不提及当前状态** — Databook 选项介绍中不提及当前选中值或默认状态（如"当前选中 Level 0"、"currently selected"）。用户说"不用说当前特性"就是这条。仅当用户明确要求对比当前值时例外
- **多子选项用独立 Option 列表** — 当一个选项有多个离散的可选子项（如 Latency Levels 中的 Level 0 / 1 / 2），每一行是一个独立的 Option，不要用属性列堆叠。表格第一列命名为"Option"，使读者清楚每行对应下拉框中的一个可选条目
- **模块放置用 `integrated`，不用 `placed`** — 描述模块/组件在 Core 内部的位置时，用 `integrated inside the core`，不用 `placed inside`。`placed` 偏物理摆放，`integrated` 更准确表达"集成在/内嵌在"的设计意图。类似地"放到 Core 内"用 `integrated` 而非 `placed`。
- **When-enabled 句首模式** — 用户有时要求用 `When the X option is enabled, ...` 作为句首，而非默认的 `The X option enables ...`。两种模式都可接受，取决于用户意图：`The X option enables Y` 定义选项功能；`When enabled, Y can be done` 强调使能后的效果/后续能力。当用户要求提供前导 `When` 从句时，不要替换为 `enables` 模式。
- **表名/标题过复杂时主动精简** — 当用户反馈表名、章节标题、小节名"太复杂"、"太长"、"精简一下"时，主动缩短，不需要等待用户提供精简版。去掉冗余状语从句和修饰词，保留核心概念，用括号括注条件。例：`lr 行为当访问落在 device or non-cacheable 区域并且 Global monitor 被使能` → `` `lr` Instruction Behavior (Device/Non-Cacheable, Global Monitor Enabled)``。
- **中文技术文本重组（预翻译步骤）** — 用户要求"重新整理这段话，使其更清晰/更容易理解"时，先对中文原文进行结构重组（不等同于翻译，是对原文的整理），再视需要翻译。重组模式：拆长段落为短段落；用二级/三级标题分节；平行条件用 bullet points；寄存器/信号名加 monospace `` `xxx` ``；异常编码/关键数值加粗；共同机制单独提取为一段。重组完成后用户确认，然后按正常 `!spec-trans` 流程翻译。详见 `references/chinese-text-reorganization.md`。
- **数字+way/位宽 作复合形容词用单数** — 中文"4-ways I-Cache" → ``4-Way I-Cache``（复合形容词不加 `s`，`ways` 只在名词性"路"时用）。"X 的两种模式" 类标题 → `Two Modes of X`（陈述式）或 `X: Two Modes`（章节/屏幕标题式），不加 `the` 以外的冠词。
