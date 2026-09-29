---
name: riscv-doc-library
description: "Search, update, and maintain the Nuclei/Andes/XuanTie document library synced via git (databook repo). Use when the user asks to search their vendor docs, pull doc updates from git, add documents, or query PDK/spec content."
---

# RISC-V 文档库（databook repo）检索与维护

服务器上维护着一个文档库，通过 Git 与 GitHub 同步，用户本地 push 文档后由本技能负责 pull、检索。

## 关键路径

| 项目 | 路径 |
|---|---|
| 仓库根目录 | `/home/ubuntu/riscv_docs` |
| 文档目录 | `/home/ubuntu/riscv_docs/nuclei/{Databook,Errata,Share}/` 与 `/home/ubuntu/riscv_docs/riscv/` |
| 检索工具 | `/home/ubuntu/riscv_docs/bin/rga`（ripgrep-all，静态编译） |
| 远程仓库 | `git@github.com:xiucong-nuclei/databook.git`（分支 `main`） |
| GitHub SSH 密钥 | `~/.ssh/github_key`（`~/.ssh/config` 已配好） |

## 仓库目录结构（重要）

```
nuclei/
  Databook/   # 各系列 Databook：300/600/900/1000/N100/N200/AIA/IOMMU/IOPMP
  Errata/     # 各系列勘误表
  Share/      # 通用规范：SMP、ISA(中/英)、Systick、Debug、STL、ICB、Trace、Case 等
riscv/        # RISC-V 官方规范：privileged/unprivileged/debug/trace/P 扩展
```

## 文档检索（主力操作）

```bash
/home/ubuntu/riscv_docs/bin/rga -m 5 "查询词" /home/ubuntu/riscv_docs/   # 全库搜索
/home/ubuntu/riscv_docs/bin/rga -m 5 "查询词" /home/ubuntu/riscv_docs/nuclei/Share/Nuclei_SMP_Specification.pdf  # 指定文件
```

- 中英文都能搜（UTF-8），结果自带文件名与页码（PDF 显示 "Page N"）。
- 常用参数：`-m N` 每文件最多 N 个命中；`-i` 忽略大小写；`-C 2` 上下文行；`--no-filename` 只出内容。
- 不需要建索引；rga 会缓存已提取的 PDF 文本，重复搜索更快。
- 先确认目标文档是否已 pull 到服务器（见下），再搜，避免结果过时。
- 注意：搜索目录是仓库根 `/home/ubuntu/riscv_docs/`（`docs/` 已不存在，文档分在 `nuclei/` 与 `riscv/` 下）。
- 工具位置可能与仓库根不同目录，但 wrapper 已内置 PATH/LD_LIBRARY_PATH，直接调用即可。

## 拉取用户最新文档（用户 push 后）

```bash
cd /home/ubuntu/riscv_docs && git pull
```

- 用户流程：本地 `git add <新目录>/ && git commit && git push origin main`，然后告诉本 agent 更新。pull 后若有新文档，可直接搜索。
- **走代理**：SSH 已配 `ProxyCommand nc -X 5 -x 127.0.0.1:7890 %h %p`（sing-box SOCKS5，7890 mixed / 7891 http），大文件拉取不再超时。若某次 fetch/pull 卡住，检查 sing-box 是否在跑（`pgrep -a sing-box`），配置在 `/home/ubuntu/singbox/config.json`。

## 添加文档到库

1. 服务器上有文件时：按目录约定放入 `/home/ubuntu/riscv_docs/` 对应子目录（nuclei/Databook 或 nuclei/Share 或 riscv/），或让用户本地 push。
2. `bin/` 目录已被 `.gitignore` 忽略，绝不提交工具二进制。
3. 单文件限制 100MB（GitHub 硬限制）；超大文件需先换 Git LFS 方案。

## 环境背景（勿重建轮子）

- rga 是静态二进制，不需要安装；wrapper 脚本 `/home/ubuntu/riscv_docs/bin/rga` 会设置 `PATH` 与 `LD_LIBRARY_PATH` 指向同目录 `poppler/`（官方 deb 解压出的 `pdftotext`）。
- 容器禁了 sudo（"no new privileges"），apt 系统安装不可用；补充系统工具一律用 `apt download <pkg>` + `dpkg -x` 解压到用户目录 + wrapper 设环境变量的方式。
- 若搜索 DOCX/EPUB 报缺 pandoc，用同样方式补齐官方 pandoc deb，再更新本 skill 的说明。
