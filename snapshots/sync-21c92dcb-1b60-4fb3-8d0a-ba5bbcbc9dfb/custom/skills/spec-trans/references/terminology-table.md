# Terminology Mapping

Full Chinese-to-English terminology mapping accumulated across sessions.
Load this file on demand when translating domain-specific / Nuclei-specific terms.

**术语规范：**
- 保持技术术语原文：`Icache`, `Dcache`, `L2cache`, `AXI`, `AHB`, `TCM`, `cacheable`
- 中文 → 英文术语映射（常见）：
  | 中文 | 英文 |
  |------|------|
  | 复位 | reset |
  | 取指 | instruction fetch / fetch instructions |
  | 系统总线 | System Bus |
  | 系统内存 | system memory |
  | 缓存 | cache / cached into |
  | 配置 | configured / if ... is configured |
  | 属性 | attribute |
  | 物理内存属性 | physical memory attribute |
  | 地址区间 | address range |
  | 非对齐访问 | unaligned access / misaligned access |
  | 字节掩码 | byte mask / write strobe |
  | 乱序 | out-of-order |
  | 流水线 | pipeline |
  | 桥接 | bridge |
  | 主设备/从设备 | master / slave |
  | 300产品 | N300 |
  | 参见 xx 章 xx 文档 | See Section xx, *Document Name*. |
  | 配置到 Core 内部/外部 | resides inside/outside the core |
  | 快速外设访问 | fast peripheral access |
  | 单周期访问 | single-cycle access |
  | 多周期访问 | multi-cycle access |
  | 仲裁策略/方案 | arbitration scheme |
  | ECC 校验/检查 | ECC checking |
  | EDC | EDC (Error Detection Code) |
  | 注错 | error injection |
  | 一分多 | fan-out |
  | 汇总 | aggregated |
  | 串行处理 | serializes / serialize |
  | EDC 检查 | EDC checking |
  | EDC 码 | EDC code |
  | 注错 | error injection |
  | on-the-fly 纠错 | on-the-fly correction |
  | protection code | protection code |
  | 检错 | error detection |
  | 纠错 | error correction |
  | 信号真实可靠 | signal integrity |
  | 重生成 | regenerate / regeneration |
  | 直通 | pass-through |
  | 乒乓buffer | ping-pong buffer |
  | 伴随码 | syndrome |
  | 物理出口/入口 | physical exit / entrance |
  | PPI (私有外设接口) | PPI (Private Peripheral Interface) |
  | 中断控制器 | interrupt controller |
  | ECLIC | ECLIC (Enhanced Core-Local Interrupt Controller) |
  | PLIC | PLIC (Platform-Level Interrupt Controller) |
  | 端到端 | End-to-End |
  | 中断信号 | interrupt signal |
  | 总线通路 | bus pathway |
  | 反压 / 背压 | backpressure |
  | 吞吐 / 吞吐能力 | throughput |
  | 突发 / 连续突发 | burst / continuous burst |
  | 握手 | handshake |
  | 时序收敛 | timing closure |
  | 组合逻辑路径 | combinational logic path |
  | 解耦 | decouple |
  | 面积开销 | area overhead |
  | 延迟开销 | latency overhead |
  | 不使能 | disabled |
  | 使能 | enabled |
  | 源时钟 | source clock |
  | 同源同频 | share the same clock source at the same frequency |
  | 独立时钟 | independent clocks |
  | 多级同步器 | multi-stage synchronizers |
  | 高电平脉宽 | high pulse width |
  | fmax | maximum frequency |
  | CPPI | CPPI (Core Private Peripheral Interface) |
  | CLM | CLM (Cluster Local Memory) |
  | IOCP | IOCP (IO Coherency Port) |
  | CIDU | CIDU (Cluster Internal Distribution Unit) |
  | CC | Cluster Cache |
  | BPU | BPU (Branch Prediction Unit) |
  | BTB | BTB (Branch Target Buffer) |
  | RAS | RAS (Return Address Stack) |
  | mtime | mtime (RISC-V machine timer register) |
  | ZC 扩展 | ZC extension (code size reduction) |
  | 例化 | instantiate / instantiation |
  | 打拍 | register / add pipeline stage |
  | 前推 | forwarding / data forwarding |
  | 多核 | multi-core / SMP |
  | 建议 / 推荐 | is recommended (not "it is recommended that") |
  | 预设 | preset |
  | 粒度 | granularity (coarse-grain / fine-grain) |
  | 从端口 | slave port |
  | 主设备 / 从设备 (IO) | master / slave |
  | 半精度浮点 | half-precision floating-point / FP16 |
  | 影子寄存器 | shadow register |
  | 分页 | paging |
  | 上下文切换 | context switching |
  | 不可用 | unavailable |
  | 子界面 | sub-interface |
  | 可利用 | available |
  | 不可利用 / 不可用 | unavailable |
  | 认证 | authentication |
  | 调试模块 | debug module |
  | 交叉触发 | cross-trigger |
  | 异构多核 | heterogeneous multi-core |
  | 联动调试 | coordinated debugging |
  | 鲁棒性 / 鲁棒 | robustness / robust |
  | SBA | SBA (System Bus Access) |
  | 半精度浮点 | half-precision floating-point / FP16 |
  | Zfa 扩展 | Zfa extension (Additional Floating-Point Instructions) |
  | Sv48 分页 | Sv48 paging |
  | 双 Status | dual Status |
  | 扩展特性支持 | extension feature support |
  | 可利用选项 | options available |
  | PMA | PMA (Physical Memory Attributes) |
  | 动态配置 | dynamic configuration |
  | 起始地址 | start address |
  | 结束地址 | end address |
  | 数据流 | data flow |
  | 数据追踪 | Data Trace |
  | 指令追踪 | Instruction Trace |
  | 鉴权逻辑 | authentication logic |
  | 调试通路 | debug access path |
  | 硬件预取 | hardware prefetch |
  | 误复位 | accidental reset |
  | 软复位 | soft-reset / soft-reset register |
  | 访存模式 | memory access pattern |
  | 数据地址 | data address |
  | 数据值 | data value |
  | 指令流 | instruction trace / instruction stream |
  | Outstanding | Outstanding (pending transactions) |
  | NC/Dev | NC/Dev (Non-Cacheable / Device) |
  | Etrace | Etrace (Enhanced Trace) |
  | SBA | SBA (System Bus Access) |
  | dmactive | dmactive (debug module active register) |
  | 自定义 | custom |
  | VLM | VLM (Vector Local Memory) |
  | 基地址 | base address |
  | 地址位宽 | address width |
  | 级数（同步器） | number of stages (synchronizer) |
  | 小面积 | small-area |
  | 默认端口 | default port |
  | CDC 同步器 | CDC (Clock Domain Crossing) synchronizer |
  | SBA 总线 | SBA bus (System Bus Access) |
  | 鉴权 | authentication |
  | 鉴权逻辑 | authentication logic |
  | 调试通路 | debug access path |
  | 自定义 Vector 扩展 | custom vector extension |
  | 标准 RVV | standard RVV (RISC-V Vector Extension) |
  | 矢量扩展 | vector extension |
  | 放到 / 放在 (Core 内) | integrated inside the core |
  | 同时进入/退出 | enter and exit simultaneously |
