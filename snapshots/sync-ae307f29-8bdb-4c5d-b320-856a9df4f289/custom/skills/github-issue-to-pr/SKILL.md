---
name: github-issue-to-pr
description: Carry a GitHub issue to a verified PR with honest CI state.
metadata:
  hermes:
    tags:
    - GitHub
    - Issues
    - Coding
    - Pull-Requests
    - CI
    related_skills:
    - github-issues
    - github-pr-workflow
    - systematic-debugging
    - test-driven-development
    - requesting-code-review
    version: 0.1.0
    author: Ben Barclay (benbarclay), Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# 从 GitHub Issue 到 Pull Request

把一个 GitHub issue 变成经过测试、核验过的 PR。本 skill 负责端到端的纪律——前提验证、重复扫描、类级修复和如实报告 CI 状态；相关的 GitHub 与开发类 skill 负责各自的实现细节。

## 何时使用

- "修复 issue #123 并打开一个 PR。"
- "实现这个 GitHub 功能请求。"
- "把这个 bug 从 issue 一直做到 CI 全绿。"

不适用于：评审已有 PR，或回答没有变更要求的代码问题。

## 流程

### 1. 读最新的 issue——正文和完整评论串

用 `terminal` 运行 `gh issue view <N> --comments`。正文是提交时的快照；最新评论承载着当前状态：已合并的部分修复、新的根因分析、维护者决定，或针对你、会改变任务的提问。还要用 `read_file` 读仓库说明（`AGENTS.md`、贡献文档）。当目前要求的行为、非目标和评论串里任何未回答的问题都已明确时，本步完成。

### 2. 扫描已有的和重复的工作

动笔前，先运行 `gh pr list --search "#<N>" --state all`，再加上至少两种症状关键词/同义词变体（`gh pr list --search "<subsystem> <symptom>" --state open`）。热门 issue 会吸引多个独立的修复；重复实现既浪费功夫也浪费功劳。还要检查近期是否有提交已修复它：`git log --oneline -20 -- <relevant files>`。当你知道涉及该 issue 的所有未合并 PR 和近期提交，或确认它们不存在时，本步完成。

### 3. 对照当前代码验证前提——并对照设计意图

在当前默认分支上用失败的测试或 fixture 复现 bug 或演示缺失的行为，用 `search_files` 和 `read_file` 追踪所报告的路径。然后回答第二个问题：这个"bug"其实是有意的设计吗？对 issue 要求修改的代码运行 `git log -p -S "<symbol>"`，读懂原始提交的意图——缺失的链接或限制往往正是功能本身。要质疑过时或有缺陷的 issue 描述，而不是盲目照做。当根因或功能缺口已在当前代码中得到演示，且改动不与有意的设计相冲突时，本步完成。

### 4. 定义验收标准与风险

列出验收标准、接口、迁移/状态变更、兼容性、安全/隐私、发布和回滚。把每个标准映射到一个测试或明确的验证。当评审有了明确的契约时，本步完成。

### 5. 实现最小而完整的改动——并修复同类问题

在独立的分支或 worktree 上工作，当 bug 类别需要时加载 `systematic-debugging` 或 `test-driven-development`。先加回归测试，再实现修复。修复在手后，用 `search_files` 在同类调用点查找相同的 bug 形态，并在本 PR 中修复整个类别——留下已知同类问题未修的半截修复比不修更糟。每个改动的行都必须能追溯到 issue；不做顺手清理。当针对性测试通过、原故障不再复现、同类调用点已修复或明确排除时，本步完成。

### 6. 证明回归测试确实有效（破坏性验证）

临时恢复被测函数的旧行为，运行新测试，确认它失败；然后恢复修复，确认它通过。无论有没有修复都通过的回归测试证明不了任何东西。当测试在修复前的代码上确实失败时，本步完成。

### 7. 跑仓库质量关卡，然后立即打开 PR

在受影响区域运行格式化、lint、类型检查和仓库的标准测试入口；对 diff 使用 `requesting-code-review`。然后立即 push 并打开 PR——PR 才是触发 CI 的动作，而 CI 延迟是主要瓶颈；不要把已完成的工作攥在手里。加载 `github-pr-workflow` 了解 PR 细节：规范的分支/提交、正文中链接 issue 并说明问题、方法、测试、风险和排除项。回读 PR，核验 head SHA、base、标题和文件。当 PR 以预期 diff 存在且 CI 正在运行时，本步完成。

### 8. 如实跟进 CI 并闭环

通过 `gh pr checks` / `gh run view --log-failed` 检查实时的检查项和失败日志。区分你的 diff 引入的失败与既有的基线或基础设施失败——不确定就在默认分支上复现，只有真正的基础设施抖动才重跑一次。没有那个确切状态的实时证据，就绝不说 "green"、"merged" 或 "released"。PR 合并后，在 issue 上评论 PR 链接和一行说明，让报告者能得到可追踪的解决记录。当 CI 状态、剩余阻碍项和 issue 评论串都反映真实情况时，本步完成。

## 常见陷阱

- 没读 issue 评论、没扫描重复 PR、没读当前代码就开始写代码。
- "修复"了原始提交显示是有意设计的行为。
- 只在一个调用点修症状，同类调用点仍保留同样的 bug。
- 交付了没有修复也照样通过的回归测试。
- 打开 PR 时测试没跑过，或夹杂无关的格式改动。
- 因为 PR 存在就宣称 issue 已交付。

## 验证

- [ ] 完整阅读 issue 评论串；最新评论状态已反映在计划中。
- [ ] 用 issue 编号 + 2 种关键词变体执行过重复 PR 扫描。
- [ ] 前提已在当前代码上复现；已通过 git 历史核查设计意图。
- [ ] 已证明回归测试在没有修复时失败。
- [ ] 同类调用点已修复或明确排除。
- [ ] 每个改动的行都能追溯到 issue。
- [ ] CI 状态仅依据实时证据报告；已用 PR 链接评论 issue。
