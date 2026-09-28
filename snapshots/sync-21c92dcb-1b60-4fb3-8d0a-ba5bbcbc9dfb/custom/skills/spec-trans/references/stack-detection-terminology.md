# Stack Detection Terminology (mstack / CSR)

Session-accumulated translations for stack detection, overflow/underflow, and `mstack_*` CSR register documentation.

## Core Terms

| Chinese | English |
|---------|---------|
| 堆栈检测 | stack detection |
| 堆栈溢出检测 | stack overflow detection |
| 堆栈栈顶溢出检测 | stack top overflow detection |
| 堆栈栈底下溢检测 | stack bottom underflow detection |
| 栈顶溢出 | stack top overflow |
| 栈底下溢 | stack bottom underflow |
| 栈顶追踪模式 | stack top tracking mode |
| 栈顶追踪 | stack top tracking |
| 堆栈是向下生长的 | stack grows downward |
| 栈所到达的最低位置 | lowest stack position reached |
| 最深栈顶 | deepest stack top |
| 历史最小值 | historical minimum |
| 通用寄存器 sp | ``sp`` register |
| 内核 | the core |
| 上报异常 | reports ... exception |
| 退出 handler | exiting the handler |
| 异常 handler | exception handler |
| 重新使能 | re-enable |
| 最大栈空间 | maximum stack space consumed |
| 程序执行期间 | during program execution |

## Register/Mnemonic Convention

All `mstack_*` CSR fields rendered in monospace, no prefix change:

| Chinese | English (keep as-is) |
|---------|---------------------|
| mstack_ctrl | ``mstack_ctrl`` |
| mstack_bound | ``mstack_bound`` |
| mstack_base | ``mstack_base`` |
| MODE 域 | ``MODE`` field |
| OVF_EN 域 | ``OVF_EN`` |
| UDF_EN 域 | ``UDF_EN`` |
| BOUND 值 | ``BOUND`` value |
| BASE 值 | ``BASE`` value |
| mcause | ``mcause`` |
| 异常编码 | exception code |

## Key Phrases

- "mstack_ctrl MODE 域 为 0/1" → "``mstack_ctrl.MODE`` is 0/1"
- "自动清零" → "automatically cleared to 0"
- "防止在异常 handler 中持续的触发" → "preventing repeated triggering of the exception inside the handler"
- "软件需在退出 handler 前将 OVF_EN 重新置 1" → "Software must set ``OVF_EN`` to 1 before exiting the handler"
- "不起作用" → "has no effect"
- "不触发异常" → "does not trigger exceptions"
- "持续跟踪" → "continuously tracks"

## Pitfalls

- "栈所到达的最底位置" is ambiguous: means the LOWEST address the stack has reached (deepest into memory), NOT "bottom of stack". Translate as "lowest stack position reached (the deepest stack top)" for clarity.
- "最大的栈空间" in tracking context means maximum consumption, not maximum available. → "maximum stack space consumed"
