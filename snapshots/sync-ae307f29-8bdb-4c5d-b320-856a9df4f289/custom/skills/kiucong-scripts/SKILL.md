---
name: kiucong-scripts
description: Write utility scripts for kiucong's server environment — synthesis data processing, CSV tools, encoding-safe output.
metadata:
  hermes:
    triggers:
    - generate a python script
    - write a script for kiucong
    - syn_diff
    - process CSV
    - synthesis results
    platforms:
    - linux
    version: 1.0.1
    category: software-development
---

# Kiucong 脚本编写

为部署到 kiucong 的 CentOS 7 服务器环境而编写 Python 工具脚本的模式与约束。

## 约束

1. **纯 ASCII——整个文件从第一版草稿起就要如此。** 适用于交付给 kiucong 的每个脚本/代码，包括本地辅助工具（如 `piccp`），不只是服务器端脚本。从一开始就写纯 ASCII；不要先写出中文消息/注释再改写——用户会拒绝并要求重来。替换：
   - `→` 换成 `->`，`←` 换成 `<-`，`—`（em-dash）换成 `-`
   - `✓` 换成 `[OK]`，`✗` 换成 `[ERR]`，`⚠` 换成 `[WARN]`
   - 字符串、注释、docstring 和帮助文本中的所有中文/Unicode——用英文
   - 交付前验证：`grep -nP '[^\x00-\x7F]' <file>` 必须无输出
   **用户希望出现在生成的 databook 输出中的中文正文**（不是脚本消息）：脚本仍必须保持 ASCII。两种方式：(a) 把中文放进脚本运行时读取的外部模板文件；(b) 用 `spec-trans` skill 把正文译成规范式英文，作为行内常量嵌入。Kiucong 选择了 (b)——英文行内，无外部文件依赖。不要在 `.py` 中硬编码中文字符串字面量；他会拒绝非 ASCII 脚本。

2. **代码交付：≤20 行在聊天里用 `diff -u`；更大的改动才发完整文件。** 改动约 20 行或更少时，不要发文件——直接把标准 unified diff 粘贴进聊天（`git show <commit> -- <file>` 可以得到）：`--- a/` `+++ b/` 头、`@@ -l,c +l,c @@` hunk 标记，以及带上下文的 `+`/`-` 行，这样 kiucong 能精确看到哪些行有变动。只有改动超过约 20 行时才发送完整文件。
   **通过 WeCom 交付文件——把 `.txt` 副本放进 `~/delivery_tmp/`，绝不能放进 `~/deliverables` 或 home 根目录。** 发送脚本文件时：
   - 附件前先复制到 `~/delivery_tmp/<name>.txt`（home 下的临时文件夹）
   - 告诉用户："把文件名改回 `<name>.<ext>`"
   - `~/deliverables/` 是规范源码的 git 仓库——别让 `.txt` 副本和 `__pycache__/` 混进去。它的 `.gitignore`：`__pycache__/`、`*.pyc`、`*.py.txt`
   - 不要把 `.txt`/`.py` 副本直接乱丢在 `~/`（home 根目录）

3. **编码容错的输入。** 用户工具链产出的 CSV 文件常常是带 BOM 的 UTF-16 LE（`0xFF 0xFE`）。始终检测编码；绝不硬编码 `utf-8`。回退链：UTF-16 LE/BE（BOM）→ UTF-8-SIG（BOM）→ UTF-8 → GBK → latin-1。

4. **CSV 中的元数据行。** 用户的 CSV 文件在真正的表头行之前常有元数据行（TECH、FREQ、Update Time）。扫描包含 `Type` + `Feature` + `Config` 的行来定位真正的表头。输出时保留元数据行。

5. **滚动备份。** 就地修改之前，创建滚动备份：`file.bak.1`、`file.bak.2`、……——绝不覆盖已有备份。找到第一个未占用的 N 并复制到那里。

   ```python
   def backup_file(path: str) -> str:
       n = 1
       while True:
           bak = f"{path}.bak.{n}"
           if not Path(bak).exists():
               break
           n += 1
       shutil.copy2(path, bak)
       print(f"[BACKUP] {path} -> {bak}")
       return bak
   ```

6. **所有文件读取都要做编码检测。** 不只是 CSV 文件——CentOS 7 上 syn_feature 配置文件也可能是 GBK 编码。打开任何文本文件之前都必须调用 `detect_encoding()`。在非 CSV 文件上漏掉这一步，会在 `extract_include_ix()` 之类的函数里引发无声的 `UnicodeDecodeError`。

7. **Argparse 在环境检查之前。** 如果 `check_env()`（在缺少 `PROJ_SRC_ROOT`/`PROJ_NAME` 时退出）先于 `parse_args()` 运行，`-h`/`--help` 就会被挡住——用户连用法都看不到。`main()` 的结构永远是这样：

   ```python
   def main():
       parser = argparse.ArgumentParser(...)
       args = parser.parse_args()   # <-- FIRST
       check_env()                   # <-- AFTER
   ```

8. **交付仓库与工作副本会漂移。** 一个脚本可能既作为工作副本（`/home/ubuntu/<name>.py`）存在，又归档在 `~/deliverables/`（git）中。两者不会自动同步——对工作副本的修复不会传播到归档。编辑前先确认哪个副本是规范的；修复后，同步到两者。用 git 诊断陈旧：只有初始 "Archive existing generated files" 提交（之后无提交）的文件是修复前的快照。（真实案例：应用到 `/home/ubuntu/syn_diff.py` 的 `if config_name else None` 保护，在 `~/deliverables/tools/syn_diff.py` 里缺失，因为归档早于该修复。）`~/deliverables` 仓库的 `origin=git@github.com:xiucong-nuclei/hermes-deliverables.git`（SSH）；kiucong 在自己的 Windows/VS Code 上 pull 它来同步。

   **AUTO-PUSH 规则（强制）：在 `~/deliverables` 中每次 `git commit` 之后，同一轮内运行 `git push origin master`——不要停在 `git commit`，不要询问，不要攒批。这是 kiucong 明确要求的。** 报告完成之前验证推送成功（检查 `remote:` 行显示分支已更新，或 `git log origin/master -1` 等于本地 HEAD）。如果推送失败（如本地分支落后于远端），先解决分歧再推送，然后才结束。

## 交互工作流

对于多步骤的功能新增（新子命令 / 语义含糊的 flag），先复述需求，列出待决点（覆盖处理、冲突行为、参数类型），并在生成代码前等待用户确认——kiucong 对非平凡改动走这种"先确认后生成"的循环。小而明确的新增（如 `pwd` 关键字）可以直接写代码。

复述必须 DETAILED（详尽），而不是摘要——太简略的话 kiucong 会要求"再详细一些"。要覆盖：每个命令的精确流程、边界情况（空输入、缺少配置、命令未找到），以及——最重要的一点——在每一个你的解读偏离用户字面表述的地方标 ⚠️（例如"先查后提交 vs 先提交后查"、配置名是否带 `.v` 扩展名）。写代码之前宁可先给出一张完整的规格表。

## LSF / make / subprocess 工作流

kiucong 的综合流程是从 Python 驱动 `make`，`make` 内部调用 `bsub` 向 LSF 提交真实作业。脚本不应自己 `bsub`——只运行 `make` 并轮询 `bjobs`。

- **subprocess 继承 shell 环境。** `subprocess.run([...])`（不带 `env=`）会整体复制 `os.environ`，所以 `make` 看到的 `PROJ_SRC_ROOT`、`PROJ_NAME`、`PATH` 和 LSF 变量与 shell 中完全一致。只有 `export` 过的 shell 变量会传递；`.zshrc` / `spr_cpu` 里裸写的 `VAR=x` 不会到达子进程。
- **make 的时序**：`make CFG=syn_feature/<cfg> only_compile` 先做约几十秒的本地预处理，然后 bsub 并返回。它不会阻塞到作业结束。
- **用 bjobs（RUN+PEND）限流，而不是数 make 进程。** 用 `bjobs -r -w` + `bjobs -p -w` 统计活跃的 LSF 作业，把以数字（JOBID）开头的行数相加；忽略表头和 "No ... job" 消息。每 60 秒轮询一次，只在计数 < 6 时提交下一个 make。
- **单个前台 make 的 tee（终端 + 日志）**：
  ```python
  with open(log, 'a') as f:
      p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
      for line in p.stdout:
          print(line, end='', flush=True); f.write(line)
      p.wait()
  ```
- **带每配置日志的并行 make（已交付的方案）**：后台启动最多 `MAX_JOBS` 个 make（Popen），每个写自己的 `<prefix>_logs/<stem>.log`，只打印一行 `[i/N] start cfg` 摘要（并行 stdout 交织会变成乱码）。等待空位时，要同时满足存活 make 数 < `MAX_JOBS` 且 bjobs RUN+PEND < `MAX_JOBS`。
- **每个配置走自己的 list 文件——不要用 `CFG=syn_feature/<cfg>`**。`CFG=syn_feature/<cfg.v>`（单例）和 `CFG=syn_feature/<list>` 会让 Makefile 把结果放到不同的位置；kiucong 要的是 list 模式的位置，所以写 `<stem>.list`（内容一行 `syn_feature/<cfg.v>`）并传 `CFG=syn_feature/<stem>.list`。make 在启动时读取 list（include 阶段），所以单个配置的 list 文件可以在它的 make 仍在运行时被清理——见 `references/lsf-flow-driver.md`。

## 批量文件工具（粘贴友好的 stdin、CSV 驱动的生成）

来自被吸收的 `batch-file-tools` skill：从粘贴的换行分隔名称批量创建文件（用 `input()` 循环，绝不用 `sys.stdin.read()`——shell 会把粘贴的换行当作回车执行），以及 CSV 驱动的配置生成。脚本：`scripts/touchs`（从粘贴的名称批量 touch）、`scripts/gen_syn_config.py`（从 CSV 生成 Verilog 配置 + `.list` 清单；文档在 `references/gen-syn-config.md`）。完整指南：`references/batch-file-tools.md`。

## Python 坑

- **局部变量遮蔽模块函数。** `main()` 里的 `x = x([...])` 使 `x` 成为局部变量，于是右侧调用会抛 `UnboundLocalError`。给局部变量改名（`cp = common_prefix([...])`）。
- **加名称前缀需要尾部下划线**——`'micro' + 'dual_issue.v'` → `microdual_issue.v`。用 `prefix + '_' + base`。
- **docutils 不是面向 Sphinx 的 databook rst 的校验器。** 它会对 `:ref:` 和 `.. _xxx.v::` 双冒号标签误报 "Unknown interpreted text role ref" / "malformed hyperlink target" / "Unknown target name"。只有 docutils 的 grid-table 解析错误是真实的；最终检查需要 Sphinx。
- **csv2 的数值列名随工具版本而变**——绝不要按精确表头名查找 area/gate（或 Feature/Base Config/Comment）；会返回 '' 且表格单元格为空。用模糊匹配：转小写、去掉空格/下划线，再匹配 area / base area / added area / added gate，与 syn_diff.py 的 `resolve_diff_columns` 保持一致。
- **在保持脚本 ASCII 的同时输出非 ASCII。** 如果生成的 rst/doc 必须携带正确符号（如平方微米用 `µm²`，而不是 ASCII 的 `um2`），不要把 Unicode 字符粘贴进 `.py`——那会破坏 ASCII grep。把它写成 Python unicode 转义：`'\u00b5m\u00b2'`（`µ`=U+00B5，`²`=U+00B2）。源字节保持 ASCII（grep 干净），生成的 rst 正确。每个特殊字符都是单宽度，所以 grid-table 列对齐与 ASCII 形式相比不变。
- **RST 标题装饰级别。** 同级小节必须共用同一个装饰字符。为子标题引入新级别（如给`评估方法`用 `-`）会把现有配置小节的标题（`=`）推到更深的级别 → docutils 报 "Inconsistent title style: skip from level 1 to 3"。修复：与同级别的兄弟标题使用同一个字符（前言的子标题用 `=`，与配置标题一致）。生成前选好装饰字符，让整个文档的嵌套一致。
  **kiucong 的 databook 约定：** 章节标题用 `+` 下划线，小节标题用 `#`——他明确要求把 config/`Evaluation*` 标题从 `=` 换成 `#`（"符合我的 databook 的章节格式"）。这本 databook 用 `+`（章节）/ `#`（小节），不用 `=`。

## 参考

- `references/syn-diff-pattern.md` — 完整的 syn_diff.py 模式：元数据跳过、CSV 查找、diff 计算、汇总输出，以及 `-u/--update` 同步到文件的模式（重命名 + include_ix、模糊匹配、备份文件夹、复查日志）。
- `references/syn-report-to-rst.md` — syn_report_to_rst.py：从 csv2 生成 databook RST（csv2 schema、大类分组、锚点命名、带换行的纯文本配置单元格且无链接、`:widths:` 控制、下划线边界换行、`_esc_ref`、include_ix 重写、Sphinx venv 校验）。
- `references/piccp.md` — piccp 命令集。**`sync-v` 只认精确名称——用户明确回退了模糊匹配（"回退，不要模糊匹配了"）；不要给 piccp 重新加回 difflib 模糊匹配。**
- `references/lsf-flow-driver.md` — syn_flow.py 流程驱动（-rtl/-compile/-syn）：make+bsub+bjobs 限流、cpu_cct 检查、tee。

## 编码检测代码段

```python
def detect_encoding(path: str) -> str:
    with open(path, 'rb') as f:
        head = f.read(4)
    if head.startswith(b'\xff\xfe'):
        return 'utf-16-le'
    if head.startswith(b'\xfe\xff'):
        return 'utf-16-be'
    if head.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    for enc in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(path, encoding=enc) as f:
                f.read(1024)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'latin-1'
```
