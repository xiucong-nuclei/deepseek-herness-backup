---
name: daily-work-recall
description: "回忆/复盘某一天（或最近几天）在这台机器上做了什么：用 daylog.py 汇总当天的 DSH 会话时间线、git 提交与推送状态、改动文件、mnemon 知识归档。触发语如\"我今天都干嘛了\"\"昨天做了什么\"\"这周干了啥\"\"帮我复盘一下这天的工作\"，也用于回答\"我 push 了没有\"\"那个功能是哪天做的\"\"上次那个改动在哪\"。"
metadata:
  hermes:
    tags: [recall, journal, sessions, git, retrospective]
    version: 1.0.0
    platforms: [linux]
---

# 每日工作复盘（daily work recall）

**触发**：用户想知道"某一天/这几天我干了什么"、某件事是哪天做的、某个提交有没有推。

**核心工具**：`/home/ubuntu/deliverables/tools/daylog/daylog.py`（v1.0.0，纯只读，不写文件）。
配套说明：同目录 `README.md`。不要为这件事现写扫描脚本——先跑 daylog，缺什么再补。

## 1. 运行

```bash
python3 /home/ubuntu/deliverables/tools/daylog/daylog.py              # 今天
python3 /home/ubuntu/deliverables/tools/daylog/daylog.py yesterday    # 昨天
python3 /home/ubuntu/deliverables/tools/daylog/daylog.py 2026-09-18   # 指定日期（也接受 -1 / -3）
python3 /home/ubuntu/deliverables/tools/daylog/daylog.py week         # 最近 7 天
```

耗时：单天约 2 秒，`week` 约 30 秒。可调环境变量：`DAYLOG_ROOTS`（额外扫描根，冒号分隔）、`DAYLOG_DAYS`（week 天数）。

## 2. 输出怎么读

四段：`[会话]`、`[提交]`、`[改动文件]`、`[知识归档]`。

- **会话行**：`起止时间  工作区  《自动标题》  工具调用数  #会话id前8位`。下面缩进的带时间是**用户原话**；`└` 是子代理数量与时间；`→` 是该会话当天**最长的一段回复**（按最长挑，通常就是结论——最后一段常是过渡话）。
- **提交行**：当天提交（含改了几个文件）+ `推送状态 <repo>：已推送/领先 N 个提交` + `[工作区未提交]`。回答"push 没 push"看这一行。
- **改动文件**：按 mtime 判定，只是旁证；**真正的产物以会话原话和提交为准**。
- **知识归档**：当天新建/更新的 mnemon 文档，对应"这天沉淀了什么"。

## 3. 下钻（需要更细的细节时）

1. **会话文件**：`~/.dsh/sessions/<工作区转义目录>/<会话id>/session.jsonl.zstd`，用 id 前 8 位 glob 定位，`zstd -dc` 解压后逐行 `json.loads`。事件结构见第 4 节。
2. **git**：`git log --since=<date> 00:00 --until=<date>+1 00:00 --shortstat`；推没推 `git rev-list --left-right --count @{u}...HEAD`；未提交 `git status --porcelain`。
3. **知识归档**：读 `<工作区>/.mnemon/documents/active/*.md` 的 frontmatter（`title` / `created_at` / `updated_at`）。

## 4. 坑（照此解释，别把噪音当工作）

- **时间只用事件的 `time`（epoch 毫秒）**，不要用文件 mtime。会话头的 `createdAt` 在恢复会话时会被刷新成恢复时刻（曾出现"09:51 的提问配 14:27 的 createdAt"），不能当开始时间；daylog 已改为只按当天事件算跨度。
- 事件按 `type` 解析（**没有 `role` 字段**）：`session`（会话头：`id`/`createdAt`/`cwd`/`parentSession`/`origin`/`delegationDepth`）、`session/title`（`data.title`）、`user/message`（`data.content`，字符串或 `[{type:text}]`）、`assistant/message`（`data.message.content`，元素 `type` 为 `text`/`reasoning`）、`tool/call`、`tool/result`、`turn/start`、`step/start`。
- **过滤合成消息**，前缀：`Current runtime`、`<system-reminder`、`[MNEMON`、`MNEMON RUNTIME`、`This is an automatically`（checkpoint 压缩包）、`The approval policy changed`、`[Subagent`、`[Steering`、`Bounded completed checkpoint`。不过滤会被系统噪音淹没。
- 只有 `origin=root` 是主会话；`origin=subagent` 挂到 `parentSession` 下计数，不单独成条。
- **产物可能只在对话里**（例如直接在聊天中给出的译文/译文修订），那天既没提交也没文件改动——别据此判定用户没干活。
- 工作区可能嵌套（`~` 与 `~/deliverables`），统计文件时要跳过子工作区，否则同一文件统计两遍。

## 5. 汇报格式

时间线式摘要：按上午/下午/晚上分段，每段写清**在哪个工作区、做了什么、产出落在哪（文件路径 / 提交号）**，最后点出**未完成、待确认或已搁置的事**。
用户不要看代码片段：给路径、提交号和结论即可。
