# CLM & IOCP Domain Notes (Nuclei SMP feature, from PDF p10-16 / p18-33)

Condensed domain knowledge for the SMP feature chapter. Source:
《Nuclei Cluster Cache，CLM与IOCP 介绍（对外）.pdf》 — Confidential, parsed at
/home/ubuntu/parsed/nuclei_cc_clm_iocp.md (NOT in git deliverables).

## CLM reset: RTL signals vs registers (user corrected twice)

`clm_base_addr` / `clm_way_en` are **RTL input signals from the CPU
interface** — NOT registers. At reset, hardware loads these signal values as
the **reset values** of the `CLM_ADDR_BASE` / `CLM_WAY_EN` SMP registers.
After reset, software rewrites those registers via CSR. The reset-signal
propagation architecture figure is `fig_clm_reset_arch.svg` (title:
`Reset Signal Propagation Architecture`).

## CLM Slave Port (p16)

AXI slave interface for external components to access CLM directly.
**Address valid bits** depend on CLM configuration, two cases:
1. Single contiguous CLM block → valid bits from that block's size.
2. Multiple non-contiguous CLM blocks → valid bits from the range between
   the lowest and highest blocks.
Upper address bits ignored; accessing a non-CLM address returns an Error.
(User: 不要例子 in this section; formula/rule only.)

## CLM software configuration flow (p15)

Two phases: Boot (3 steps: `CLM_WAY_EN`=0 → `CLM_ADDR_BASE` aligned to whole
L2 size → `CLM_WAY_EN`) and Program Runtime (6 steps: single core only →
check `SNOOP_PENDING`/`TRANS_PENDING` → disable L2 via `CC_CFG` →
`WBINVAL_ALL` via `CC_mCMD` → set base/way → enable L2). No explanation of
why step order exists (user: 不解释).

## IOCP Outstanding capacity (user: describe feature, not computation)

Capacity determined by MULTIPLE factors: Line Buffer depth + Prefetch +
Streaming (NOT only LBUF depth). Depth value references the cpufeature.csv
macro in the databook. Read vs write capacity differ: one LBUF is reserved
for writes, so READ capacity = WRITE minus one (user's exact wording:
"因为需要留一个 Buffer Line 给 write，因此写比读少一" — note user says write
is one more; frame as read one less). Out-of-order supported — mention in
content only, never in the title.

## IOCP Line Buffer (p19-21)

Centralized buffer between AXI port and cluster cache; converts AXI
transactions to cache-line-granular accesses. Entry = fixed-size storage of
one complete cache line (512 bits). Configurable 2/4/8/16/32/48 entries,
shared across all IOCP ports. Burst mapping: exactly one cacheline → 1 entry
(best); larger → split at cacheline boundaries, multiple entries; smaller →
1 entry underutilized. Pipelined workflow: receive burst → entry initiates
cache access (read starts at first beat, write after full receipt) → respond
to AXI → release → accept new transaction. Merges multiple read bursts from
same port within same cacheline range (avoids repeated cache access).

## IOCP Write Streaming vs Prefetch (p26)

Both use `STM_CTRL` enable bit + `STM_CFG` threshold, per-port independent
training, same method across ports:
- Write Streaming: `STM_CTRL` bit1; `STM_CFG`[29:20] threshold (bytes of
  consecutive writes); `STM_TIMEOUT`[10:0] timeout — if no data within same
  cache line in the configured time, stop waiting and send received data.
  Merges contiguous-address writes into one cacheline write, sends downstream
  after a full cacheline. Only Cacheable/Non-Cacheable writes.
- Prefetch: `STM_CTRL` bit0; `STM_CFG`[9:0] threshold (bytes of consecutive
  reads); [14:12] prefetch address lead (cache lines ahead of current port
  address); [18:16] cache lines per prefetch. Loads future-read data into
  cluster cache in advance.
Lead-in first (what it does), then per-port training mechanism. (User
deleted the write-streaming comparison paragraph: "第三段删掉吧".)

## IOCP transfer support (p30)

Cacheable / Non-Cacheable (NC) / Device accesses; any access size; burst
lengths per AXI4 (INCR 1–256, FIXED 1–16, WRAP 2/4/8/16); no crossing 4K
boundary; no early termination. User removed the "recommend full-size
access" sentence.

## IOCP usage notes (p33) — paragraph style, not numbered points

For the same address, IOCP master and core must have the same address
attribute; Device addresses need `AxCache` 0b0000/0b0001 from master and
Device config on the core side (`CFG_DEVICE_REGION`, `csr_mattri0`, page
table). Coherence with cluster Dcache requires `SMB_ENB` enable for the IOCP.
`prot[1]`=1 non-secure / =0 secure when hardware supports isolation,
ignored otherwise. Read/write complete cache lines recommended. Section
starts with lead-in: "使用 IOCP 时需注意以下事项" / "The following points
should be noted when using IOCP:".

## Other chapter structure decisions (user-driven)

- 6.7 latency table section: dropped (用户舍弃).
- AxCache/AxPROT mapping section and vs-ARM-ACP comparison: dropped.
- Read + write merged into one "读写操作" section.
- Streaming and Prefetch kept as separate sections.
