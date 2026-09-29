---
name: cpu-benchmarking
description: CPU benchmark selection & interpretation (Dhrystone, Whetstone, CoreMark) — version/compiler-flag score inflation, DMIPS/MWIPS conversion, honest reporting.
metadata:
  hermes:
    triggers:
    - dhrystone
    - whetstone
    - coremark
    - DMIPS
    - MWIPS
    - benchmark version
    - DMIPS/MHz
    platforms:
    - linux
    version: 1.0.0
    category: software-development
---

# CPU 基准测试

为 Nuclei RISC-V 内核验证（N300/N900）以及一般嵌入式 CPU 基准测试提供基准选择与结果解读。

## 第一原则：报告版本 + 编译器选项

没有基准测试的**版本**和编译器选项，DMIPS/MWIPS 数字毫无意义。同一基准的两次运行，仅因 `-O2` 与 `-O3`、`-fno-inline` 以及所用的 libc 字符串函数不同，就会相差 10-30%（Dhrystone 高度依赖 strcmp/strcpy，因此链接 newlib 还是手写字符串函数，得分会变化两位数百分点）。

## 版本虚高（编译器死代码消除）

现代优化编译器会在结果未被使用的情况下消除基准测试主体。“诚实”版本加入 `volatile` / 防 DCE 保护，得分**更低**；经典原版得分**更高**（虚高）。

| 基准 | 虚高（更高） | 诚实（更低，更接近实际） |
|-----------|-------------------|---------------------------|
| Dhrystone | 2.1（原版，无 volatile） | 2.2（volatile + 防 DCE） |
| Whetstone | Netlib 1.2（经典 C 版） | Roy Longbottom（volatile） |

- Dhrystone 2.2 的 `dry.c` 头部声明其可防止优化器“移除重要语句”（与 Rick Richardson 合作开发）。
- Roy Longbottom 的 Whetstone 文档出于同样原因设有专门的 “Compiler Optimisation” 章节。

## 换算关系

- 1 DMIPS = 1757 Dhrystones/秒（参考机 VAX 11/780）。
- Whetstone 使用 MWIPS（百万加权指令/秒）；Longbottom 版本还报告每个循环的 MFLOPS（循环 N1-N8）。

## 选择指南

- 内部回归 / 诚实对比 → 使用诚实版本（Dhrystone 2.2 / Longbottom Whetstone）。
- 对齐厂商/历史公开数据 → 使用对方引用的版本（通常是 2.1 / Netlib 1.2），并在报告头部注明。
