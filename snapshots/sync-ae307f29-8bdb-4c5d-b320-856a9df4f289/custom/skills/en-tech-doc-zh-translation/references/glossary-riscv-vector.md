# 术语对照表（GLOSSARY）

本表在翻译开始前冻结，全书统一使用。缩写保留英文，首次出现写作 `中文（English）`。

## 1. 架构与配置参数

| English | 中文 | 首现/说明 |
|---|---|---|
| RISC-V Vector Extension (RVV) | RISC-V 向量扩展（RVV） | 之后用 RVV |
| ratified specification | 已批准的规范 | |
| standard extension | 标准扩展 | |
| custom instruction | 自定义指令 | |
| opcode space | 操作码空间 | |
| configurable parameter | 可配置参数 | 构建期确定 |
| extensible | 可扩展 | ISA 层面 |
| programmable | 可编程 | 运行期由软件决定 |
| SEW (Selected Element Width) | 元素位宽（SEW） | |
| LMUL (register grouping) | 寄存器分组倍数（LMUL） | 亦称长度倍数 |
| fractional LMUL | 分数 LMUL | LMUL < 1 |
| VLEN | 向量寄存器位宽（VLEN） | 单个向量寄存器位数 |
| VL | 向量长度（VL） | 当前指令处理的元素数 |
| VLMAX | 最大向量长度（VLMAX） | |
| DLEN | 数据通路位宽（DLEN） | |
| vtype / vstart / vl | `vtype` / `vstart` / `vl` | CSR 名不译 |
| vsetvl / vsetvli / vsetivli | 同左 | 指令名不译 |
| vector configuration instruction | 向量配置指令 | |

## 2. 微架构

| English | 中文 | 首现/说明 |
|---|---|---|
| lane | 通道（lane） | 之后用 lane |
| vector register file (VRF) | 向量寄存器堆（VRF） | |
| XRF / FRF | 整数寄存器堆（XRF）/ 浮点寄存器堆（FRF） | |
| chaining | 链接（chaining） | 向量运算的流水衔接 |
| strip mining | 条带挖掘（strip mining） | 处理任意长度的循环技巧 |
| out-of-order execution | 乱序执行 | |
| register renaming | 寄存器重命名 | |
| precise exception | 精确异常 | |
| pipeline stall | 流水线停顿 | |
| register file port | 寄存器堆端口 | |
| port pressure | 端口压力 | |
| micro-op | 微操作 | |
| datapath | 数据通路 | |
| coprocessor | 协处理器 | |
| functional unit | 功能单元 | |
| issue queue | 发射队列 | |
| dependency / RAW hazard | 依赖 / 写后读相关 | |
| throughput / latency | 吞吐 / 延迟 | |
| IPC | 每周期指令数（IPC） | |
| scratchpad | 便笺存储器 | 按需保留英文 |
| systolic array | 脉动阵列 | |

## 3. 向量语义与指令

| English | 中文 | 首现/说明 |
|---|---|---|
| element | 元素 | |
| element index | 元素索引 | |
| mask / masking | 掩码 / 掩码操作 | |
| tail elements | 尾部元素 | |
| tail-agnostic / tail-undisturbed | 尾部不可知 / 尾部保持 | |
| unit-stride | 单位步长 | |
| constant stride | 常量步长 | |
| strided | 跨步 | |
| indexed | 索引 | |
| gather / scatter | 收集 / 散布 | |
| segment load/store | 段加载 / 段存储 | |
| whole-register load/store | 整寄存器加载 / 存储 | |
| widening / narrowing | 加宽 / 缩窄 | |
| reduction | 归约 | |
| slide | 滑动 | |
| permutation | 置换 | |
| vrgather / vcompress | 同左 | 指令名不译 |
| fixed-point | 定点 | |
| saturating arithmetic | 饱和运算 | |
| rounding mode | 舍入模式 | |
| mask query instruction | 掩码查询指令 | |

## 4. 矩阵与 AI 计算

| English | 中文 | 首现/说明 |
|---|---|---|
| Matrix Extension | 矩阵扩展 | |
| tile | 瓦片（tile） | 之后用瓦片 |
| tile geometry | 瓦片几何形状 | |
| PE array | PE 阵列 | |
| GEMM | 通用矩阵乘（GEMM） | |
| MAC (multiply-accumulate) | 乘累加（MAC） | |
| register blocking | 寄存器分块 | |
| cache blocking / tiling | 缓存分块 | |
| data reuse | 数据复用 | |
| arithmetic intensity | 计算强度 | |
| deterministic execution | 确定性执行 | |
| memory-bound / compute-bound | 访存受限 / 计算受限 | |
| memory bandwidth | 内存带宽 | |
| cache line | cache 行 | cache 不译 |

## 5. 通用与文体

| English | 中文 | 首现/说明 |
|---|---|---|
| architect | 架构师 | |
| compiler engineer | 编译器工程师 | |
| edge AI | 边缘 AI | |
| portability | 可移植性 | |
| time–space duality | 时间—空间对偶 | |
| Flynn's taxonomy | Flynn 分类法 | |
| array processor | 阵列处理器 | |
| SIMD | 单指令多数据（SIMD） | 之后用 SIMD |
| memory locality | 访存局部性 | |
| first-person narrative | 第一人称叙事 | 保留"我"，不改为"笔者" |

## 6. 不翻译项

人名（Thang Tran、Paul Miller、Jonah McLeod）、公司（Simplex Micro、Andes Technology、AMD、TI、Cray）、产品与芯片代号（AndesCore NX27V、Cray-1、MMX、AVX-512）、指令与 CSR 名、代码块、公式、URL、书目引用与 BibTeX。

补充保留英文：`vill`/`vma`/`vta`/`vsew`/`vlmul`、`ELMUL`/`ESEW`、`vlenb`、`AVL`、`rd`/`rs1`/`x0`、`OPI`/`OPF`/`OPM`、指令字段名（`nf`/`mew`/`mop`/`vm`/`rs1`/`rs2`/`vd`/`vs2`/`vs3`/`lumop`/`sumop`）、`prestart` 元素、`bank`（分 bank）、`FP`/`VPU`/`PPA`。

## 7. 术语补充（翻译过程中冻结）

**执行与流水线**

| English | 中文 |
|---|---|
| scoreboard | 记分板 |
| reorder buffer (ROB) | 重排序缓冲（ROB） |
| in-flight instruction | 在飞指令 |
| retirement / commit | 提交 |
| commit point | 提交点 |
| replay queue | 重放队列 |
| forwarding / bypass path | 前递 / 旁路通路 |
| predication | 谓词执行 |
| speculative execution / speculation / misprediction | 推测执行 / 推测 / 预测错误 |
| control hazard / bubble | 控制冒险 / 气泡 |
| loop buffer | 循环缓冲 |
| non-blocking | 非阻塞 |
| unrolling | 循环展开 |
| register pressure / spilling | 寄存器压力 / 寄存器溢出 |
| fire-and-forget | "发射后不管" |
| flush path | 冲刷路径 |
| cycle-accurate simulation | 周期精确仿真 |
| instruction-level profiling | 指令级剖析 |
| timing closure / timing pressure | 时序收敛 / 时序压力 |
| PPA | 功耗、性能与面积（PPA） |

**访存**

| English | 中文 |
|---|---|
| memory traffic | 访存流量 |
| load-store unit | 加载存储单元 |
| burst size | 突发长度 |
| coherent cache | 一致性 cache |
| multi-bank main memory | 多体主存 |
| cache thrashing | cache 抖动 |
| page fault | 页错误 |
| streaming | 流式传输 |

**向量指令补充**

| English | 中文 |
|---|---|
| first-fault load（`vle*ff`） | 仅首次故障加载 |
| splat | 广播（splat） |
| clip / clipping | 裁剪 |
| merge / move | 合并 / 搬移 |
| iota（`viota`） | 向量 iota |
| population count（`vcpop`） | 置位计数 |
| AoS / SoA | 结构体数组（AoS）/ 数组结构体（SoA） |
| carry / borrow | 进位 / 借位 |
| sign-extend / zero-extend | 符号扩展 / 零扩展 |
| prefix sum | 前缀和 |
| interleave / de-interleave | 交织 / 解交织 |
| clamp | 钳制 |
| mantissa | 尾数 |
| Q-format | Q 格式 |
| element packing / element mapping | 元素打包 / 元素映射 |
| shuffle | 混洗 |
| fused multiply-add (FMA) | 融合乘加（FMA） |

**矩阵与性能**

| English | 中文 |
|---|---|
| scalable / vector-length agnostic | 可伸缩 / 向量长度无关 |
| kernel | 核心 |
| tiling | 分块 |
| data marshaling | 数据编配 |
| specialization | 专用化 |
| operand-stationary / output-stationary | 操作数驻留 / 输出驻留 |
| compute fabric | 计算结构 |
| first-class object | 一等对象 |
| tile register file | 瓦片寄存器堆 |
| spatial reuse | 空间复用 |
| performance envelope | 性能包络 |
| capacity planning / power management | 容量规划 / 功耗管理 |
| software longevity | 软件寿命 |

## 8. 全书体例约定（冻结）

- **破折号**：正文 em dash（`—`）译作 `——`；术语内部的连接号保留单破折号，如 `时间—空间对偶`（time–space duality）。
- **图注**：`Figure N-M.` → `图 N-M.`；图注来源行统一为 `*改编自《RISC-V Vector Extension Specification, Version 1.0》第 X 节，RISC-V International，依 CC-BY 4.0 许可。*`（原文无节号则省略节号）；References 文献条目保持英文原样。
- **小节标题**：`Summary` → `小结`（全书统一；第 3–6 章已一致）。
- **首现写法**：各章首现独立处理，形式为 `中文（缩写）`；原文同时给出英文全称时保留为 `中文（缩写，English Full Name）`；缩写、CSR 名、指令字段名不译。
- **数值与表达式**：数值区间与位域保留半角（`2–3`、`v0–v1`、`XLEN-2:8`、`5:3`、`vlmul[2:0]`）；数学表达式保留半角括号与运算符，散文性插入语用全角括号。
- **引号**：正文用中文引号；英文文章标题、书目条目等引用内容保留 ASCII 引号。
