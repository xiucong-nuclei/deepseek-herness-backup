# Chinese Technical Text Reorganization (预翻译中文重组)

When the user says "帮我重新整理这段话，使其看上去更清晰" or "更容易被理解",
reorganize the Chinese source text before any translation. This is a pre-translation
step — the output is still Chinese, just restructured.

## Trigger

- "重新整理这段话"
- "使其看上去更清晰"
- "更容易被理解"
- User sends a dense wall of Chinese technical text and asks for readability help

**Not the same as !spec-trans.** Reorganization keeps Chinese; translation converts to English.

## Restructuring Pattern

1. **Split long paragraphs** into short sections with headings (### or bold text)
2. **Extract common mechanism** into a standalone paragraph (避免每个场景重复描述相同逻辑)
3. **Parallel conditions → bullet points**: same-level scenarios use `-` lists
4. **Monospace**: register names, field names, signal names → `` `xxx` ``
5. **Bold**: exception codes, key values, critical conditions
6. **Blockquote notes**: `>` for caveats and software requirements
7. **Hierarchy**: 概览 → 分节详述 → 共同机制 → 注意事项

## Example (from session)

**Input (wall of text):**

> 堆栈溢出检测分为堆栈栈顶溢出检测和堆栈栈底下溢检测。在堆栈溢出检测模式下，当mstack_ctrl的 OVF_EN域为1...如果通用寄存器的sp被写入的值，小于mstack_bound寄存器中的BOUND值，内核会上报堆栈栈顶溢出异常，mcause的异常编码会更新成24，同时mstack_ctrl的OVF_EN域会被自动清零...因此，退出堆栈栈顶溢出异常handler时，需要软件将mstack_ctrl的OVF_EN域置1...在堆栈溢出检测模式下，当mstack_ctrl的 UDF_EN域为1...如果通用寄存器的sp被写入的值，大于mstack_base寄存器中的BASE值...mcause的异常编码会更新成25...

**Output (reorganized):**

> 堆栈溢出检测分为**栈顶溢出检测**和**栈底下溢检测**两种。
>
> **栈顶溢出检测**
> 当 `mstack_ctrl.OVF_EN = 1` 时：
> - 若 `sp` < `mstack_bound.BOUND` → 上报栈顶溢出异常
> - `mcause` → **24**
> - `OVF_EN` 自动清零
> ...
>
> **栈底下溢检测**
> （同上结构）
>
> **共同机制**：两种检测的使能位在异常触发后均硬件自动清零，退出 handler 前由软件重新置位。
