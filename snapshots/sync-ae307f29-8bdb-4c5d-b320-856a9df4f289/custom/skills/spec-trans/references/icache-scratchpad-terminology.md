# I-Cache Scratchpad terminology (Nuclei)

Terminology for translating "I-Cache Scratchpad" doc sections and answering
plain-language questions. Written from agent knowledge — verify specifics
(option names, sizes, mode details) against the N300/N900 databook when the
doc is reachable.

## Core concept

- Scratchpad = part of the Icache SRAM **carved out** to behave like a small
  dedicated SRAM instead of a cache.
- cache mode (缓存模式) — normal tag lookup; access may miss.
- scratchpad mode (暂存模式) — fixed address region, direct SRAM access, never
  misses, **deterministic latency**.
- 划走/占用 → `carved out of` / `reserved from`; 缓存容量变小 → `reduces the
  effective cache size`.
- 软件手动拷代码 → `software copies code into the region`; 强调不自加载 →
  `code does not load into the scratchpad automatically`（与 cache 的最大使用差异）。
- 缓存被挤掉 → `evicted` / `cache pollution`（污染 → pollution）。
- 固定基地址可配 → `configurable base address`.

## Translation examples

| 中文 | Spec English |
|---|---|
| I-Cache Scratchpad 的两种模式 | Two Modes of I-Cache Scratchpad / I-Cache Scratchpad: Two Modes |
| 4-ways I-Cache Scratchpad 的两种模式 | Two Modes of the 4-Way I-Cache Scratchpad |
| 访问时间确定 / 延迟可预测 | deterministic access latency |
| 不会被其他代码挤掉 | immune to cache pollution / not affected by other code |
| 从 Icache SRAM 里划走一部分 | a portion of the Icache SRAM is carved out |

## Plain-language explainer (Chinese, reusable for 通俗易懂 answers)

- 普通 Icache = 智能快递柜：第一次去总仓（系统内存）取，miss 慢且耗时不确定；
  scratchpad = 私有保险箱：固定地址、永远命中、延迟确定，但要自己提前放进去。
- 代价三点：实际缓存容量变小；代码不自动加载（软件手动拷贝/链接）；固定地址
  区间不再访问外部内存。
- 用途：中断 handler、boot 代码、RTOS 关键调度 → 硬实时 / WCET 分析。
