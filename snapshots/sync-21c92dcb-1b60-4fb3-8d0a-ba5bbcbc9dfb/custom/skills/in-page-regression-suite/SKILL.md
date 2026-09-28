---
name: in-page-regression-suite
description: Use when building a regression test suite inside a web tool.
metadata:
  hermes:
    tags:
    - testing
    - regression
    - browser
    - web-tool
    - verification
    category: software-development
    version: 1.0.0
    author: Hermes Agent
    license: MIT
---

# 页面内回归测试套件（web 工具）

对于需要跨多次编辑保持正确的单文件 / vanilla web 工具，
内嵌一个可复用的测试套件，在真实浏览器中运行（通过 browser_exec），
而不是临时的一次性探测。已在 PMA 配置生成器上验证（199 个用例、
6 个批次、全部通过）。与 `browser-verification-headless` skill 配合
处理 CDP/浏览器底层细节。

## 使用场景

- 在单文件 web 工具（index.html + 内联 JS）上迭代时，回归问题容易引入，人工复测不够。
- 用户希望高覆盖率 + 可重复覆盖多个边界用例。
- 需要一种快速方式来证明某次改动没有破坏相邻路径。

## 结构

1. **独立的测试文件**，与页面一同提供（如 `tests/foo_test_suite.js`）。
   无依赖，纯 ASCII（用户对中文机器的要求）。它定义：
   - 一个微型断言框架：`ok(name,cond,detail)`、`eq`、`eqn`，以及
     捕获抛出异常为 FAIL 的 `T(name, fn)`；
   - 注册在 `suite` 对象上的分批次函数（`suite.unit`、`suite.parse`、`suite.analyze`、
     `suite.render`、`suite.import`、`suite.edge`……）；
   - 运行器 `window.PMATest.run(batch?)`，返回
     `{total, pass, fail, fails:[{name,detail}], groups, logText}`。
2. **单元测试直接调用页面函数**——它们位于页面的全局
   作用域（`parseHex`、`fmtAddr`、`analyzeRegion`、`wrapRange`……）。
3. **UI/集成测试先设置状态再断言 DOM**：给页面的状态数组赋值（`regions = [...]`），调用其渲染函数（`renderGen()`），然后
   `querySelector` 并比较 `textContent`。对无框架的监听器，先设置
   `.value` 再派发 `new Event('input')` / `('change')`，让处理器执行。
4. **用真实文件做 fixture**：把实际用户配置文件作为内联字符串嵌入，并
   断言每个属性的精确数量/尺寸——合成用例会漏掉真实的回归问题。

## 运行方式（browser_exec）

对页面与所获取的测试文件都做缓存破坏——HTML 的 `?v=N` 不会
破坏单独获取的 JS 文件的缓存：

```python
out = js("""(async () => {
  const r = await fetch('/tests/foo_test_suite.js?ts=' + Date.now());
  (0, eval)(await r.text());
  return PMATest.run(0);
})()""")
```

集成测试始终以 `window.alert=()=>{}; window.confirm=()=>true;` 开头，
否则代码路径中某个多余的 `alert` 会卡住 harness（`Runtime.evaluate` 挂起）。

## 逐用例日志

让 `run()` 同时生成 `logText`：头部（时间戳、total/pass/fail、
批次）+ 每个用例一行 `  PASS|FAIL <name>`，按批次分组，以
`RESULT: ALL PASSED` 或 `RESULT: N FAILURE(S)` 结尾。把它写入文件并提交一份
样例，让用户能确切看到跑了什么；提供 `downloadLog()` 供手动
浏览器使用（Blob + a.click，`.txt`）。

## 纪律要求

- **每个新功能 / bug 修复在提交前都要有回归用例**——这是用户对这类工作的明确要求（“每次添加新的测试方案，就添加到回归测试环境中”）。新批次/用例写入现有套件文件，
  然后提交前 `PMATest.run(0)` 必须全部通过。
- **断言失败往往是测试数据的问题，而不是产品缺陷。** 先确认预期语义。观察到的坑：
  - `parseSize("abc")` 是*合法*的裸十六进制值（`0xABC`）；`"3.3 GB"` 的尾部
    会作为十六进制 `B`（parseHex 抓取末尾的十六进制连续段）。
  - `END = base + 4095` 是*合法*的含端点 END（得到 size 4096）。
  - 为某个已满的属性添加第 9 个 region 会*轮转到*下一个属性，
    而不是被阻止。
  - 48 位最大地址测试必须使用空间内 4K 对齐的基址
    （`0xFFFFFFFFE000`），而不是 `0xFFFFFFFFF000`（后者 +0x1000 会溢出）。
  只有在确认是真正的缺陷后才应修改产品。
- **每次改动后重新运行整个套件**；对一条路径的修复常会
  破坏相邻路径。
- 把纯辅助函数（如文件提取函数）抽成具名函数，以便
  直接做单元测试。

## 常见陷阱

- 修补较长的测试/源文件后，重新读取/用 `search_files` 检查，确认修改
  确实落在磁盘上，再相信下一次浏览器运行（patch 工具对大文件
  可能静默不生效）。
- 当某个属性已有 ≥1 个 region 时，逐属性上限可能静默拒绝恰好生成
  `MAX_PER_ATTR` 个块的 SPLIT/apply 操作——应在修复 UI 中明示这一点，
  而不是只弹一个裸 alert。
