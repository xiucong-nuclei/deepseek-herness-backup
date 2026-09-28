---
name: single-file-web-tools
description: Develop single-file web page tools (vanilla JS, no deps).
metadata:
  hermes:
    tags:
    - web
    - frontend
    - vanilla-js
    - i18n
    - single-file
    - tooling
    category: software-development
    version: 1.0.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# 单文件 Web 页面工具

为这个用户构建并迭代独立的 Web 工具（如配置生成器/计算器）：一个零依赖的 HTML 文件，深色或浅色主题，常常是双语的。已在 PMA 配置生成器（`~/deliverables/web/pma-calc-landing/index.html`）上验证过。

## 用户约定（默认应用）

- **脚本/代码纯 ASCII**（代码中无中文/非 ASCII；UI 文本用英文或通过 i18n 配对）。用户已要求 3 次——没有商量余地。
- **深色科技风格**（既定约定）：`#0a0f1e` 背景、`#38bdf8`/`#818cf8` 强调色、等宽字体、淡网格背景——与 `~/deliverables/web/` 下现有落地页一致。
- **任何 ≥ 2^53 的地址运算用 BigInt**（如 64 位 PA 尺寸）。十六进制地址绝不用 Number。
- **按需双语 UI**：静态文本用 `data-i18n`，动态字符串用 `t(key,...)`；语言切换在头部，持久化到 `localStorage`。属性/值 token（DEVICE、CACHEABLE、hex）保持英文。
- 交付到 `~/deliverables/web/<name>/`（git 仓库）下，**每批改动后提交**，让每次迭代都可回滚。
- 工作流：写代码前复述需求 + 列出 ≤3 个决策点并附推荐选项；用户行内回答（如 "1A 2B 3A"），或只说"继续"来继续迭代。他们会分批发改动清单——逐批实现、验证、提交。

## 真正踩过的坑

- **输入焦点丢失 = 每次按键都重建表格。** `oninput` 调用全量重渲染（`tbody.innerHTML=""`）会销毁获得焦点的 `<input>`，用户只能打一个字。修复：输入时更新数据模型，只刷新非输入区域（信息栏、预览、图表）；只在结构性变化（增/删行、属性/模式切换）时重建表格。
- **i18n 的 textContent 覆盖会删掉子节点。** 对含子节点的元素执行 `el.textContent = t(...)`（如 `<h2>REGIONS <span id=count>`）会清掉子节点 → 之后的 `getElementById` 返回 null 并崩溃。把可翻译部分包进它自己的嵌套 `<span data-i18n>`，动态子节点留在外面。
- **重复 CSS 规则：后写的生效。** 修复"不起作用"是因为同一规则的一份旧副本位于样式表更靠后的位置并覆盖了它（相同特异性）。深入调试前先 `grep` 该选择器——删掉过期的重复项。
- **主题用 CSS 变量。** 把整个调色板放进 `:root`（bg/panel/text/accent/ok/err/warn/border），这样整套主题切换（如深色→浅色）是一处改动；避免把裸 hex 散落在规则里。
- **响应式缩放。** 字体/间距用 `vw`/`vh` + `clamp()`，让布局随显示缩放；wrapper 上用 `grid` + `display: contents`，让孙元素直接参与外层网格（对多列 + 底部面板布局很方便）。

## 验证

Web 交付物必须做真实浏览器验证——见 `browser-verification-headless` skill（playwright chromium + CDP + `BU_CDP_URL`）和 `references/browser-verification-recipe.md` 的完整本地配方（playwright chromium 路径、snap-chromium 陷阱、BU_CDP_URL 接线、验证清单）。要点：用 playwright 的 chromium 二进制（`~/.cache/ms-playwright/...`），绝不用 snap chromium（headless 永远打不开 CDP 端口）；在 browser_exec 代码的第一行设置 `os.environ["BU_CDP_URL"] = "http://127.0.0.1:9222"`；从一开始就捕获 JS 错误（`window.__errs`）并在结尾断言它为空。后续会话发现的额外坑：`python3 -m http.server`（单线程）可能静默挂起 → 进程活着但 curl 返回 000 → 杀掉并重启；写 harness 脚本时注意嵌入 JS 周围的 Python 字符串引号（用 `json.dumps` 构造 payload）。编辑文件后总是用带缓存失效的 `?v=N` 查询刷新，每次修 bug 后重新验证（修复会破坏兄弟路径）。

## 回归测试（浏览器内测试套件）

对逻辑不平凡的工具（解析器、校验器、生成器、地址/区间运算），把自包含套件作为 `tests/<tool>_test_suite.js` 与页面一起交付，并在真实浏览器中运行——完整模式见 `references/test-suite-pattern.md`（微型断言框架、驱动代码段、Blob 捕获、断言陷阱、回归循环；已在 PMA 配置生成器上验证）。

- **用户要求（强制执行）**：每个新特性/改动都要配套向套件追加对应的回归用例，提交前整套重跑至全绿。把用户真实的配置/样例文件作为字符串字面量嵌入（用 `json.dumps` 生成以避免转义麻烦），并断言精确的计数/尺寸——合成用例会漏掉真实文件才能抓住的回归。
- **每次运行都记日志**：`res.logText` → `tests/logs/<tool>_test_log.txt`（表头 + 按批分组的每条 PASS/FAIL + RESULT 行）；提交一份示例日志。
- **坑**：用 `?ts=' + Date.now()` 获取套件（测试文件独立于页面的 `?v=` 破坏器缓存）；每个测试脚本顶部 mock 掉 `alert`/`confirm`（未 mock 的 `alert()` 会阻塞 CDP Runtime.evaluate 直到超时）；失败时先怀疑测试而不是产品（选择器错、期望宽度错、fixture 越界）；如果 `Target.createTarget`/`Runtime.evaluate` 超时，说明浏览器守护进程卡死了——`pkill -f remote-debugging-port=9222`，重新启动 chromium，验证 `curl http://127.0.0.1:9222/json/version`，再重试。

## 会话召回

PMA 工具的特性积压与过往决策，用 `session_search`（"PMA"）可恢复完整迭代历史；领域规则也在"Nuclei PMA"记忆中。
