---
name: grounded-citations
description: Ground answers and documents in cited, verifiable sources.
metadata:
  hermes:
    tags:
    - Research
    - Citations
    - Grounding
    - Sources
    - Web
    - Reports
    category: research
    related_skills:
    - research-paper-writing
    - arxiv
    - ocr-and-documents
    version: 1.1.0
    author: Hermes Agent + Teknium
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# 有据引用

所有取自外部来源的说法都要带上行内编号引用和一份 `Sources:` 列表，风格类似 Perplexity。账本（ledger）脚本负责维护 `url → [n]` 的映射，因此编号和 URL 都来自检索结果，绝不来自记忆——模型只输出被交给它的小整数。

对于高风险工作，同一份账本还兼任事实核查链：每个来源都附上逐字引用（除非逐字出现在抓取到的页面文本中，否则拒绝），来自模型知识的说法标记为 `[unverified]`，而 `verify --evidence` 会让任何引用的来源没有证据的草稿判定失败。

本 skill 覆盖聊天中的回答、书面文档（markdown、PDF、docx、幻灯片）和研究报告。不涉及学术 BibTeX 流水线——会议论文请用 `research-paper-writing` skill，本 skill 为其提供输入（见 `references/citation-formats.md`）。

## 何时使用

只要答案或产出物基于你检索到的信息（而非本来就知道的信息），就用它：

- 研究、对比、新闻摘要、"X 现在处于什么状态"
- 任何写入磁盘、会引用/转述/报告外部事实的产出物——报告、简报、文档、演示文稿、wiki 页面
- 用户会想核查你工作成果的事实调研
- 多来源综合，冲突的来源必须分别注明出处

当检索只是另一项任务的附带操作时，跳过行内引用——编码间隙快速查一下语法/版本、日常闲聊、创意写作。只有在用户很可能想要该链接时才提 URL。

## 前置条件

除标准工具集外无其他要求。`scripts/sources.py` 是仅依赖标准库的 Python 3 脚本。检索来自已配置的任何途径：`web_search`、`web_extract`、`browser_navigate` 或 `terminal`（curl、CLI）。

账本位置：`$HERMES_HOME/cache/citations/ledger.json`（按 profile 区分）。可按任务用 `--ledger <path>` 或 `HERMES_CITATION_LEDGER` 覆盖。

## 运行方式

```bash
S=~/.hermes/skills/research/grounded-citations/scripts/sources.py

python "$S" reset                                  # start a clean ledger
python "$S" add https://example.com/a --title "A"  # prints: [1]
python "$S" add https://example.com/b --title "B"  # prints: [2]
python "$S" list                                   # ledger table
python "$S" render                                 # Sources: block
python "$S" verify draft.md                        # catch bad citations
```

`add` 是幂等的且会对 URL 做规范化：同一页面在同一账本内总是返回同一 id，因此多次搜索/提取轮次中 id 保持稳定。

## 快速参考

| 操作 | 命令 |
|---|---|
| 为新任务开启全新账本 | `sources.py reset` |
| 登记来源并获取其 id | `sources.py add <url> [--title T]` |
| 一次登记多个来源 | `sources.py add <url1> <url2> ...` |
| 从 JSON 工具输出登记 | `sources.py ingest results.json` |
| 为来源附加逐字证据 | `sources.py quote <id> --text "exact wording" --from page.txt` |
| 查看账本 | `sources.py list [--json]` |
| 渲染 Sources 块 | `sources.py render [--style markdown\|plain\|footnotes\|bibtex\|evidence] [--only 1,3]` |
| 只渲染草稿引用到的来源 | `sources.py render --cited-in draft.md` |
| 就地重写草稿的 Sources 块 | `sources.py render --replace-in draft.md` |
| 检查草稿的引用 | `sources.py verify draft.md [--strict] [--min-coverage 0.6] [--evidence]` |

## 流程

① **重置账本**：在会产生有据回答或文档的任务开始时执行。若继续的工作其 id 已出现在草稿中，则跳过重置——复用账本可保持编号稳定。

② **在检索时登记每个来源。** 每次 `web_search` / `web_extract` / `browser_navigate` / 抓取之后，把 URL 交给 `sources.py add`（或把原始 JSON 管道给 `sources.py ingest`）。务必在写正文*之前*完成。事后凭记忆补登记，正是本 skill 要防止的失败模式。

③ **边起草边引用。** 把带方括号的 id 紧跟在每个被该来源支持的句子后面：

```
Ice floats because it is less dense than liquid water.[1][2]
```

- 方括号前不留空格；每个 id 用各自的方括号。
- 每句最多 3 个 id。逐句引用，而不是结尾一次性堆砌。
- 只用账本返回过的 id。绝不编造 id 或 URL。
- 出自你自身知识的说法不加引用。
- 来源冲突时：两种解读都给出，各自带自己的 id。
- 数字、日期、名称要按来源原样引用；缺口要明确标注（"未找到 X 的来源"），而不是含糊带过。

④ **追加 Sources 块**：用 `sources.py render --cited-in <draft>`，让 id → URL 映射由账本机械生成，而不是手打。非 markdown 目标请选择匹配的 `--style`，并按 `references/citation-formats.md` 决定放置方式（docx 用脚注、PDF/LaTeX 用尾注、演示文稿加 Sources 幻灯片、wiki 输出按页列来源）。

⑤ **交付前验证**——遇到未知 id、与账本不一致的 Sources 块，或（配合 `--min-coverage`）引用过稀的正文，`sources.py verify <draft>` 都会以非零码退出。修正后重新运行。

⑥ **聊天回答**同样遵循这些步骤，草稿就在你的回复中：登记来源、行内引用、以渲染好的 `Sources:` 列表结尾。简短回答可以直接用 `sources.py render --only <ids>` 渲染该块，不必写入文件。

## 事实核查模式

当读者必须能够核查这条证据链时——医疗、法律、金融、安全、有争议的说法，或用户明确要求事实核查——从引用升级为证据：

① **每个来源附一条逐字引用。** 提取页面后，把文本存成文件，并附上承载每个说法的句子：

```bash
python "$S" quote 1 --text "Ice is about 9% less dense than liquid water." --from page1.txt
```

除非引用逐字出现在证据文本中，否则会被拒绝（对空白、大小写和 markdown 标记不敏感——提取文本中的行内链接如 `_[ERAP1](https://…)_` 也能匹配读者看到的纯文本），因此转述或记错的数字无法冒充证据。从抓取到的文本里复制粘贴，绝不重新打字。按读者看到的原样引用句子——匹配器会替你穿透提取器的标记，所以你不必在引用中复现链接语法或转义星号。

② **用 `[unverified]` 标记模型知识的说法。** 无法找到来源的关键说法使用明确标记，而不是引用：

```
The refactor likely predates the 2.0 release.[unverified]
```

`verify --min-coverage` 会把带 `[unverified]` 的句子计为已覆盖——目标是每个说法都有声明的出处，而不是每句都挂引用。关键说法若可核查就去核查；`[unverified]` 留给确实无法核查的内容，而一份以 `[unverified]` 标记为主的核查产出物，应在摘要里如实说明。

③ **用第二个独立来源交叉核对有争议的事实。** 两个来源不一致时，两种解读都引用、各带自己的 id 和引用，并说明你更倚重哪一个及理由。单一来源只是转述，两个独立来源才算相互印证。

④ **用证据门槛验证并渲染证据块：**

```bash
python "$S" verify report.md --evidence --min-coverage 0.5
python "$S" render --style evidence --replace-in report.md
```

只要任一被引用的来源没有附上引用，`--evidence` 就会判定草稿失败。`evidence` 渲染样式会在每个来源的 URL 下方打印其引用，于是产出物呈现 说法 → 来源 → 确切支撑文本 的链条，无需任何盲信。用 `--replace-in <draft>` 就地重写已有的 Sources 块（幂等——补附引用后重跑安全）；`--cited-in` 则输出到 stdout。两者都生成 `## Sources` 标题（`--style plain` 生成 `Sources:`）。

**`--min-coverage` 统计什么。** 覆盖率 = 有声明出处的句子 / 正文句子。正文句子指去掉 Sources 块、标题（`#`）、表格行（`|`）和围栏代码后，4 个词以上的非空行片段；引用块标记会被剥掉。出处由 `[n]` 引用或 `[unverified]` 标记声明，两者兼有的句子只计一次。先不带阈值运行 `verify`，读 `info: stats:` 行看具体计数，再定数值。

## 常见陷阱

- **写完再登记。** 账本必须由工具输出填充，不能从草稿反推——那会重新引入编号机制本想消除的编造 URL 风险。
- **任务中途改编号。** 绝不要手改草稿里的 id。id 是账本中的身份；草稿若引用了 `[4]`，`[4]` 就必须一直是那个来源。只在任务之间运行 `reset`。
- **把 URL 手打进 Sources 块。** 永远用 `render`。手打的 URL 就是一条未经核实的说法。
- **把搜索结果摘要当成读过的页面来引用。** `web_search` 的摘要只支撑它字面说的内容。说法需要正文支撑时，先 `web_extract`，再引用提取出的页面。
- **过度引用。** 一句最多三个 id；每个分句都挂引用会让文本没法读，也掩盖了真正承重的来源。
- **在代码/配置产物里引用账本。** 来源注释应出现在文字型产出物和文档头部，而不是生成的代码内部。
- **并行子代理。** 每个子代理有各自的工作目录；如果它们的输出会被合并，用 `--ledger`（或 `HERMES_CITATION_LEDGER`）让它们都指向同一份账本，否则 id 会冲突。
- **引用摘录而不是页面。** 证据引用必须来自提取出的页面文本，不能来自搜索结果描述——先 `web_extract`、保存文本，再 `quote --from` 那个文件。
- **往 `quote --text` 里填转述。** 逐字校验会拒绝；正确做法是找到原文句子，而不是反复改写直到碰巧匹配。
- **把 `[unverified]` 当逃生门。** 它标记的是确实无法找到来源的少数说法；如果大多数句子都带着它，说明任务需要更多检索，而不是更多标记。
- **手改 Sources 块。** 用 `render --replace-in <draft>`；自己切文件容易留下过期或重复的块，随后被 `verify` 标记。

## 验证

```bash
python "$S" verify report.md --strict --min-coverage 0.5
```

通过意味着：草稿中每个 `[n]` 都存在于账本，Sources 块恰好列出被引用的 id（使用账本中的 URL），且承载来源的句子中被引用的比例达到阈值。即使退出码为 0 也要读警告——已登记却未被引用的来源，通常意味着某个说法在编辑过程中丢了出处。
