---
name: mk-mode
description: Wrap entire response in a single Markdown code block for clean copy-paste into Typora. Triggered by !mk prefix (NOT /mk — Hermes gateway intercepts slash commands).
metadata:
  hermes:
    tags:
    - markdown
    - format
    - typora
    - copy
    - wecom
    version: 1.1.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# !mk Mode — Single Code-Block Markdown Output

## When to Use

User's message starts with `!mk` prefix.

Reason for `!` instead of `/`: Hermes gateway (WeCom, etc.) intercepts `/` as a built-in slash command prefix. Any custom trigger starting with `/` causes "unknown command". Use `!` instead.

When triggered, the ENTIRE response must be wrapped in a single code block so the user can copy it into Typora (or any Markdown editor) without formatting corruption from the chat platform's rich-text rendering.

## Workflow

### Step 1: Detect the trigger

Check if the user's message begins with `!mk`:

- `!mk <content>` — user wants the response in a code block
- Strip the `!mk` prefix and treat the rest as the actual message
- Do NOT try to register `!mk` as a slash command — it's purely an agent-level cue

### Step 2: Format the response

Generate the response normally with full Markdown formatting. Then wrap the ENTIRE content in a SINGLE code block:

````
```md
[Your full Markdown response here — one continuous block]
```
````

### Step 3: Code block rules

- Opening fence: ````md` (or bare ````)
- Closing fence: ````
- **Entire response inside ONE block** — no splitting across multiple code blocks
- All Markdown elements go inside: headings, tables, lists, code, bold/italic, links
- Internal code snippets: use **4-space indentation** instead of triple backticks to avoid nesting issues with the outer fence
- No blank lines immediately before/after the opening/closing fences

### Step 4: Content formatting inside the block

- Standard Markdown throughout (headings with `##`, tables with `|`, lists with `-`)
- For inline code: use single backticks `` ` `` (safe inside the outer fence)
- For code blocks: use 4-space indent, not triple backticks
- Keep the content self-contained — the user will paste the entire block into Typora

## Platform Notes

- **WeCom (企业微信)** renders the outer fence as a single scrollable text area. The inner Markdown content is NOT rendered — it stays as plain text. The user copies the entire text area and pastes into Typora, which then renders it.
- **Other platforms** (CLI, Telegram) may render the inner Markdown differently. On those platforms, consider whether `!mk` mode is even needed.

## Examples

### Example 1: Code analysis

User: `!mk 分析这段代码的逻辑`

Response:

````
```md
## 函数分析

| 函数 | 作用 |
| :--- | :--- |
| foo() | 初始化硬件 |
| bar() | 执行核心逻辑 |

### 执行流程

1. foo() 配置寄存器
2. bar() 开始轮询
```
````

### Example 2: Bug with nested code

If the response contains code blocks, use 4-space indent inside instead of backticks:

````
```md
## 配置方法

运行以下命令启动服务：

    systemctl start myservice
    systemctl enable myservice

| 参数 | 说明 |
| :--- | :--- |
| --port | 监听端口 |
```
````

## Pitfalls

- **Nested backticks** — never put triple backticks inside a ```` fence. Use 4-space indent for code blocks.
- **Don't split** — one response = one code block. Never split across multiple blocks.
- **Don't use `/mk`** — slash prefix causes "unknown command" on Hermes gateway. Always use `!mk`.
- **Long content** — very long Markdown may be slow to copy, but that's acceptable for the use case.
- **Image extraction accuracy** — vision models occasionally miss lines (esp. near edges, or when the first line differs from prior images). When extracting text from screenshots: (1) count lines and verify completeness against user expectations; (2) if the user says a line is missing, re-extract immediately — the user sees the image and the model doesn't; (3) if the user compares to a prior image showing N lines and the current extraction shows N-1, the screenshot capture likely cut off a line rather than the model hallucinating it. Never argue with the user about what's visible in an image.

## User Preferences: 精简 + 无验证

This user has explicitly requested:

### 精简 (Be Concise)

- Strip all fluff, extra explanations, and verbose preamble
- No "我来帮你分析" / "Let me explain" type intros — go straight to the answer
- Use the fewest words that convey the full meaning
- Prefer tables or bullet points over paragraphs
- When the user says "精简一些", remove 30-50% of the text: cut adjectives, filler phrases, and redundant restatements

### 无验证 (No Verification Section)

- **Do NOT** include a "验证" (Verification / Validation) subsection or section
- Examples of what to omit: "验证方法", "如何验证", "改之前 dump 一下...",
  comparison tables of before/after behavior, test commands to run, or any
  "可以这样验证" instructions
- The output should be the solution/prediction/findings only — not a guide
  on how to confirm it works
- If the natural response has a verification step, either drop it entirely or
  merge the key point (one sentence max) into the main flow

### 图片提取 (Image Extraction) — CRITICAL

- When user sends an image with `!mk` (and no other prompt), output is the raw
  text from the image only. **Nothing else.**
- Do NOT add: tables, analysis, explanations, commentary, headers, labels,
  "图片内容：", or any interpretive content whatsoever
- Output just the extracted text lines, verbatim. If the image shows 7 lines,
  output 7 lines — no more, no less.
- If the user says "你少了一行", **they are right** — re-extract immediately,
  don't argue or insist the extraction was complete. The vision model is not
  infallible; the user knows their content.
- For screenshots where top lines might be cut off (e.g., scroll position),
  the user may compare against a prior image — if a known line is absent, flag
  it as likely a capture issue rather than claiming the image doesn't contain it.
- Vision model size limit: Qwen VL models require width > 28px AND height > 28px.
  If either dimension ≤ 28px, the API returns HTTP 400. Ask the user to re-capture
  with a larger screenshot area.

### 格式: 单一代码块

- The ENTIRE response must be inside ONE outer code fence ```` ``` ````
- No nested code fences (use 4-space indent for internal code examples)
- No text before or after the outer code fence
- The outer fence contains pure Markdown — the user copies it into Typora
- Verify the final output: if the platform shows multiple code blocks or text
  outside the block, adjust
