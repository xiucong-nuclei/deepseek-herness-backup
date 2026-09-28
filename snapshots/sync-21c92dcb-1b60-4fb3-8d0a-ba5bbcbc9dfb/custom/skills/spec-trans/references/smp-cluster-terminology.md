# SMP / Cluster Domain Terminology (N600)

Accumulated domain knowledge for the N600 SMP Multi-core Support sub-screen.

## Cluster Concept

A **Cluster** is a group of tightly-coupled cores sharing:

- **Cluster Cache** — L2 cache shared by all cores in the cluster
- **Cluster Internal Bus** — interconnect between cores
- **IRQ Sync** — cross-core interrupt coordination
- **Memory Bus Interface** — unified external memory bus port

When SMP Core Number = 1: the cluster still instantiates with all SMP infrastructure (Cluster Cache, internal bus), acting as single-core but with SMP framework ready for future expansion.

## Sub-Screen Structure

The SMP sub-screen contains sections separated by `*** ... ***`:

```
SMP Multi-core Support
├── (1) SMP Core Number in one Cluster
├── *** Cluster Cache Configuration ***
├── *** IOCP Configuration ***
├── *** CLM(Cluster Local Memory) ***
└── *** Synthesis/Harden by Hierarchy ***
```

## Component Glossary

| Abbreviation | Full Name | Description |
|---|---|---|
| CPPI | Core Private Peripheral Interface | Per-core private bus for core-private peripherals (interrupt controller, timer). Dedicated to each core, not shared. |
| CLM | Cluster Local Memory | Cluster Cache reprogrammed as directly-addressable on-chip SRAM (TCM-like). |
| IOCP | IO Coherency Port | Cache-coherent interface for external IO masters (like ARM ACP). |
| CIDU | Cluster Internal Distribution Unit | Routes interrupts to cores within a cluster. |
| CC | Cluster Cache | Shared L2 cache for all cores in the cluster. |
| BPU | Branch Prediction Unit | Predicts branch direction and target. Configurable via `BPU Option` sub-screen. |
| BTB | Branch Target Buffer | Stores branch target addresses. Configurable entry count and associativity. |
| RAS | Return Address Stack | Predicts function return addresses. Depth configurable. |

## Latency Levels vs Individual Access Cycles

- **`Cluster-Cache Access Latency Levels`** — coarse-grain preset that sets both Tag RAM and Data RAM access cycles together (Level 0/1/2)
- **`Cluster-Level Cache Tag-Ram Access Cycles`** — fine-grain control over Tag RAM access latency, bank count, and pipeline/blocking mode (6 options)
- **`Cluster-Level Cache Data-Ram Access Cycles`** — fine-grain control over Data RAM access (similar to Tag-Ram pattern)

## mtime Timer

The `Timer mtime value is provided by Soc` option controls the source of the RISC-V `mtime` counter:

- **Enabled** — mtime sourced externally from the SoC (centralized clock source for all clusters)
- **Disabled** — mtime generated internally within the cluster

In multi-cluster systems, SoC-provided mtime ensures all clusters share the same time base for timer interrupts.

## CLM Explanation Pattern

CLM is the Cluster Cache reconfigured by software as Local Memory mode:

- Precision: "CLM is the Cluster Cache configured by software as Local Memory mode (directly addressable SRAM, not used as cache)."
- Avoid long explanations about TCM analogy — one sentence is enough.
- `Slave Port for CLM` provides an external access port to this local memory.

When an option is a list of discrete named configurations (not just a numeric value), present each as a row in a table with the Option column first:

| Option | Latency | Bank Count | Access Mode | Performance | Area |
|--------|---------|------------|-------------|-------------|------|
| 1cycle | 1 cycle | 1 bank | Pipeline | High | Small |
| 2cycles | 2 cycles | 2 banks | Pipeline | High | Medium |
| 2cycles | 2 cycles | 1 bank | Blocking | Low | Small |
| 3cycles | 3 cycles | 4 banks | Pipeline | High | Large |
| 3cycles | 3 cycles | 2 banks | Blocking | Low | Medium |
| 3cycles | 3 cycles | 1 bank | Blocking | Lowest | Smallest |
