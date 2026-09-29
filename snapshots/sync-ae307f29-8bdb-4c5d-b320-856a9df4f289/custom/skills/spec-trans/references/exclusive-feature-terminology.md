# Exclusive Feature Terminology (RISC-V Atomic Operations)

Session-accumulated translations and phrasing for CPU exclusive/atomic access documentation.

## Core Terms

| Chinese | English |
|---------|---------|
| 独占访问窗口 | exclusive access window |
| Local Monitor | Local Monitor |
| Global Monitor | Global Monitor |
| exclusive flag | `exclusive_flag` |
| lr 指令 | `lr` instruction |
| sc 指令 | `sc` instruction |
| Load Reserved | Load Reserved |
| Store Conditional | Store Conditional |
| 访存指令 | memory access instruction (load or store) |
| 执行单元 | execution unit |
| 总线层 | bus layer |
| AXI 协议 | AXI protocol |
| ICB 协议 | ICB protocol |
| device 属性 | device memory attribute |
| non-cacheable 属性 | non-cacheable memory attribute |
| 外部组件 | external component |
| 总线响应 | bus response |
| 清零 | clear / cleared to 0 |
| 置 1 | set to 1 |
| 成功/失败 | Success / Fail |
| 维持 | (do NOT use — use `implement` or `track` instead) |

## Table Naming Convention

| Context | English Table Name |
|---------|-------------------|
| Local Monitor sc conditions | `sc` Instruction Outcome |
| Global Monitor CSR_ENABLE switch | `CSR_EXCL_ENABLE` Behavior |
| Global Monitor bus-mode scenarios | `sc` Instruction Outcome (Bus Mode) |

## Key Phrases

- "二者协同实现 Exclusive 特性" → "Together they implement the Exclusive feature."
- "数据被写入到对应的地址" → "data written to the target address"
- "sc 返回 0/1" → "`sc` returns 0/1"
- "不发请求" → "Not issued" (table cell)
- "CPU 内部维护" → "The CPU maintains ... internally"

## Table Headers

| Chinese | English |
|---------|---------|
| 访问区域类型 | Access Region Type |
| 外部 exclusive flag | External `exclusive_flag` |
| 总线返回状态 | Bus Response Status |
| 内部 exclusive flag | Internal `exclusive_flag` |

## Pitfalls

- Do NOT translate `lr`/`sc` to full English in headings — keep as `lr`/`sc` in monospace.
- `OKAY` and `EXOKAY` are AXI response literals — keep as bare uppercase, no monospace needed in tables.
- "维持" is vague — use `implements`, `maintains`, or `tracks` depending on context.
