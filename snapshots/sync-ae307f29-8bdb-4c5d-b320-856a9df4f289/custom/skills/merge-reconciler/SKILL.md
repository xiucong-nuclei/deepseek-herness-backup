---
name: merge-reconciler
description: Neutral third-party resolution of agent merge conflicts.
metadata:
  hermes:
    tags:
    - Multi-Agent
    - Git
    - Merge-Conflict
    - Kanban
    - Arbitration
    related_skills:
    - hermes-agent
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# 合并仲裁器

以不偏不倚的第三方身份，解决两个 AGENT 分支之间的 git 合并冲突。agent 在处理与同行工作的冲突时，往往要么覆盖对方、要么放弃自己的改动 —— 因为它们缺少对方的上下文，并且偏向自己这一边。本 skill 就是解决方案：一个中立的调解器，接收双方 diff 以及双方声明的意图，产出一个合并结果，如同 merge-queue 的仲裁者。

## 使用时机

- 并行行动期间两个 agent 的分支/worktree 发生冲突（kanban 工程流水线、并行 PR 潮、多 worktree 重构）。
- `git merge` 或 `git rebase` 因两个 agent 的工作冲突而中止，且双方原始 agent 都不应自行裁决。
- 不要用于单个 agent 自身工作内的冲突，或琐碎的 lockfile/生成文件冲突（这类直接重新生成即可）。

## 前置条件

- 一个包含已中止合并的仓库检出，或两个分支名加上自行执行合并的权限。
- 双方的意图来源：kanban 完成摘要（在 `terminal` 中运行 `hermes kanban show <task-id>`）、PR 正文，或至少是每个分支的提交信息。
- 项目的构建/测试命令（如果有）。

## 运行方式

**独立运行** —— 由人（或 agent）在发生冲突的仓库内调用本 skill：加载 skill，然后从上到下按流程执行。

**派生中立 agent** —— 多 agent 行动中的首选形态：

- `delegate_task`：派生一个 subagent，其任务消息中包含仓库路径、两个分支名、双方意图摘要的原文，以及遵循本 skill 的指令。
- Kanban 原生方式：创建一张调解卡，指派给**第三个 profile**（不是任一 worker 的 profile），并把两张冲突卡都链接为父卡 —— `kanban_create(title="reconcile branch-a x branch-b", assignee="reconciler", parents=["t_a", "t_b"])`。父卡链接会把双方的完成摘要自动带入调解器的上下文；卡片正文应写明仓库路径和两个分支名。

## 快速参考

| Hunk 类别 | 定义 | 处理方式 |
|---|---|---|
| disjoint-intent | 两处改动服务于不同目标，可以共存 | 合并两者 |
| same-question-different-answer | 双方对同一个设计问题给出了不同答案 | 按声明的意图选其一；明确呈现该决定 |
| superseded | 一方的改动使另一方的假设不再成立 | 保留存续的一方；注明原因 |

中立契约：绝不偏袒派生你的那一方；只改动冲突区域（不做顺路修改）；每个设计问题的取舍都必须明确出现在交还摘要中。

## 流程

### 1. 收集双方信息

- 通过 `terminal` 运行：`git status`（确认冲突状态并列出冲突文件）、`git merge-base <A> <B>`，然后对每个冲突文件分别运行 `git log --oneline <base>..<side>` 和 `git diff <base>..<side> -- <file>`。在已中止的合并中，`HEAD` 是一方，`MERGE_HEAD` 是另一方。
- 收集各方的意图：用 `hermes kanban show <task-id>` 获取完成摘要/元数据，或用 PR 正文，或用上面日志中的提交信息。在改动任何文件之前，先为每一方写下一句话的意图。
- 完成标准：你能用自己的话复述双方意图，并且每个冲突文件都有双方的 diff。

### 2. 为每个冲突 hunk 分类

- 用 `read_file` 打开每个冲突文件，定位每个 `<<<<<<<`/`=======`/`>>>>>>>` 块。
- 按声明的意图 —— 而不是按哪个改动看起来更好 —— 为每个 hunk 从快速参考表中分配恰好一个类别。
- 如果单个 hunk 包含多个独立决定（例如，能干净合并的新逻辑，加上双方答案不同的样式/取整选择），把它分解为子决定并逐一分类。
- 单个文件常常混合多种类别：一个 hunk 可能是设计冲突，而相邻 hunk 是 disjoint。按 hunk 分类，而不是按文件分类。
- 完成标准：每个 hunk 都有写下的类别和一行理由。

### 3. 在中立契约下解决冲突

- 用 `patch` 编辑每个 hunk（整文件重写用 `write_file`）：
  - disjoint-intent → 合并两处改动，使每个意图都得到完整满足。
  - same-question-different-answer → 选择最能满足所声明意图的答案（例如，如果任务要求正确性，则 "严格校验" 胜过 "快速默认值"）。绝不要折中成双方都没要过的混合体。
  - superseded → 保留存续的一方；删掉失效的假设。
- 绝不偏袒派生你的那一方。如果双方意图真的难分高下，就升级处理（阻塞 kanban 卡片 / 上报），而不是猜测。
- 冲突标记之外什么都不改 —— 不做格式调整、重命名或顺手修复。
- 通过 `terminal` 对每个已解决的文件执行 `git add`。
- 完成标准：`search_files` 在仓库中找不到 `<<<<<<<` 标记，且所有已解决的文件都已暂存。

### 4. 验证

- 通过 `terminal` 运行项目的构建/测试；至少要导入/执行受影响的模块。合并后的行为必须能观察到双方的意图（例如，A 方的新语义和 B 方的 disjoint 新增都同时存在）。
- 完成合并：`git commit`（默认合并信息加一段列出 hunk 决定的正文即可）。
- 完成标准：验证通过且合并提交存在。

### 5. 交还

- 产出一份说明**每个** hunk 决定的完成摘要：`file:lines — class — which side(s) kept — rationale`。对每个 same-question-different-answer hunk，写明设计问题和你的取舍，以便人可以否决 —— 绝不掩藏设计决定。
- Kanban：`kanban_complete(summary=...)`。独立运行时：打印摘要。
- 完成标准：摘要已交付并列出所有 hunk。

## 常见陷阱

- **自我偏袒**：如果你是被其中一个冲突 agent 派生的，你就存在结构性偏见 —— 要说明这一点，并刻意权衡对方的意图。优先采用第三方 profile 的形态，让这种情况根本不出现。
- **折中处理**设计冲突会产生没人设计过的混合体；选一个答案并明确呈现。
- **按文件分类**：文件通常混合多种 hunk 类别；把整个文件归为单一类别会悄悄丢掉 disjoint 的改动。
- **顺路修改**会让合并无法审查，并剥夺原始 agent 的决定权。
- **意图缺失**：仅靠提交信息可能太单薄；优先用 kanban 完成摘要或 PR 正文。如果双方意图都无法恢复，就升级处理，而不是猜测。
- **屡犯文件**：同一文件在多个轮次中反复冲突是热点信号，而不是常规调解工作 —— 要标记出来（例如 `hotspot: <path> — <reason>` kanban 评论），让编排器拆分该文件，而不是对它每次新冲突都逐一调解。

## 验证

- `git status` 显示目标分支上的工作树干净，并存在合并提交。
- 没有残留冲突标记（`search_files` 模式 `<<<<<<<`）。
- 构建/测试通过；双方意图确实存在，或被放弃的一方在摘要中被明确点名。
- 交还摘要逐条列出每个 hunk 的类别和理由。
