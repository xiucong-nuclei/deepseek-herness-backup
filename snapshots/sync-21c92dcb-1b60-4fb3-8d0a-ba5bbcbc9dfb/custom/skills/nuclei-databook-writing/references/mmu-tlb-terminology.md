# MMU / TLB 术语（Nuclei databook MMU 章节）

## TLB 基础（给用户解释用，中文即可）

TLB = Translation Lookaside Buffer，MMU 核内缓存「虚拟地址 → 物理地址」映射的小缓存。命中免页表遍历；未命中触发 page table walk（Sv39 最多 3 次访存），结果回填 TLB。

## 三种 TLB（用户文档结构）

- ITLB (Instruction TLB)：缓存取指地址转换，本实现 8 entries
- DTLB (Data TLB)：缓存 load/store 地址转换，8 entries
- MTLB (Main/Global TLB)：ITLB/DTLB 兜底，256 entries，物理分 TAG RAM + DATA RAM 两部分

章节引言句式：
`ITLB (Instruction TLB) caches the address translations for instruction fetches. ITLB contains 8 entries. Each entry stores the following fields:`

表名（The X of Y 模式）：`The Entry Fields of ITLB` / `The Entry Fields of DTLB`；MTLB 两张表用 `The Tag RAM Fields of MTLB` / `The Data RAM Fields of MTLB`。

## MMU 地址参数（mmu 参数表）

- PA_SIZE — 物理地址位宽
- VATAG_SIZE — VA 有效高位位宽（SV48: 36 / SV39: 27 / SV32: 20）
- VATAG_SIZE_REAL — TLB 中实际保存的 VA 有效高位位宽 = `max(VATAG_SIZE, PA_SIZE-12)`（图片中常误写 VTAG_SIZE，需确认）
- PAGESIZE_WIDTH — page size 位宽（不配置 NAPOT 为 2，配置 NAPOT 为 3）

## ITLB entry 字段（17 个）

VALID, USER(U模式), PAGESIZE(经PMP对齐后大小), PAGESIZE_RAM(原始PAGE大小), PPN(`PA_SIZE-12`), PBMT(2), VATAG(`VATAG_SIZE_REAL`), ASID(16), SEC_MODE, NMODE_PMP_X/R, MMODE_PMP_X/R, DM(DEBUG区域), BARE_FLAG(裸机映射), NC, DEVICE

## DTLB entry 字段（28 个）

比 ITLB 多：EXECUTABLE/WRITEABLE/READABLE/DIRTY、NMODE/MMODE_PMP_W、TARGET_* 组（TARGET_NC / TARGET_DEVICE / TARGET_DCACHE / TARGET_VLM / TARGET_DLM / TARGET_ILM / TARGET_LBIU — 物理地址访问目的，宽 1）

## MTLB（TAG RAM 6 + DATA RAM 7）

- TAG RAM: VALID, PAGE_SIZE(位宽 2/3 = PAGESIZE_WIDTH), GLOBAL(页表 global 属性), ASID, VATAG, SEC_MODE
- DATA RAM: EXECUTABLE, WRITEABLE, READABLE, DIRTY, USER, PPN, PBMT

## 图片表格 OCR 易错点（tesseract 读出后需给用户确认，勿静默修改）

- SEC_MDOE → SEC_MODE
- MMODE_PXP_R / MMODE_PXP_W → MMODE_PMP_R / MMODE_PMP_W（P 后 M 被读成 X，按同组 X/R/W 对称性判断）
- TARGET_DCACHE 常被读成 TARGET_DEVICE（看描述"访问目的为DCACHE"判断）
- ASID 位宽：ITLB/DTLB 为 16，MTLB 读成 1 需核对
- 同组重复行：重复宏名 + 不同描述 → 通常是以描述为准的宏名笔误
