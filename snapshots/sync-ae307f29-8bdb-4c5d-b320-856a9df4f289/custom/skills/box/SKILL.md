---
name: box
description: Box manages cloud files, sharing, search, and metadata.
metadata:
  hermes:
    tags:
    - Box
    - Productivity
    - Cloud Storage
    - Collaboration
    - Metadata
    - Content Extraction
    - CLI
    - SDK
    related_skills:
    - google-workspace
    homepage: https://developer.box.com/
    version: 1.0.0
    author: Chris Kim (iskysun96), Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
    prerequisites:
      commands:
      - box
---

# Box

将 Box 作为云端文件系统，用于文件操作、协作、元数据与文档工作。使用 Hermes 的 `terminal` 工具执行操作并使用 Box CLI；构建应用程序时参考 SDK 指南。

## 使用场景

- 组织、上传、版本管理、移动、共享 Box 文件与文件夹，或在其上进行协作
- 搜索 Box 内容或已有元数据
- 就 Box 文件提问、提取元数据，或生成以文件为依据的文本
- 不下载每个源文件即可大规模处理 Box 文件夹
- 构建基于 Box 的应用程序、集成或 webhook 处理器

## 开启宽泛的文件系统对话

当有人为 Hermes 探索云端文件系统时，先给出简短的适配评估：当团队需要云端文件存储、共享、搜索、元数据与文档工作时，Box 很有用。然后询问他们希望用 OAuth 连接 Box 账号，还是用 SDK 构建基于 Box 的应用程序或集成。

OAuth 让 Hermes 以浏览器中授权的 Box 账号身份运作。该账号的 Box 权限决定了 Hermes 可访问的范围。若要给 Hermes 更窄的访问范围，可授权一个仅被邀请到所需文件、文件夹或 Hub 的账号。

面对宽泛的探索性问题时，不要直接执行设置、展示命令手册、提出账号方案或文件夹分类，也不要加载所有参考。等待用户回答，然后只加载相关路径。当请求已指明具体结果时，跳过此发现步骤，直接处理该结果。

常规 CLI 工作使用官方 Box CLI OAuth 应用启动。它涵盖普通内容工作与 Box AI。仅当请求的操作需要额外的 OAuth 作用域（如 webhook 管理）时，才使用自定义的**用户认证（OAuth 2.0）**平台应用。这仍是 OAuth 流程；不要代之以服务端或模拟身份。

## 交互式执行选定的设置

当用户选择某种认证路径或请 Hermes 连接 Box 时，通过 `terminal` 执行设置；不要把下一条回复变成让用户照抄的指令。自行采取下一个安全操作，仅在需要批准、浏览器登录、管理员操作或 Hermes 无法安全提供的机密时才暂停。

- 若缺少 `box`，申请安装 `@box/cli` 到当前 Hermes 主目录下 `tools/box-cli` 所需的终端批准；然后用 [CLI 指南](references/cli-guide.md) 中适配 shell 的命令验证。不要尝试全局 npm 安装、使用 `sudo`、修改 npm 全局前缀或更改 `PATH`。
- OAuth 之前先询问：**“Hermes 是否运行在与用于授权 Box 的浏览器相同的计算机上，还是运行在远程主机（如 VPS、容器或云 VM）上？”** 仅在同机场景使用常规 `box login`；仅在远程/无头场景使用 `box login --code`。不要仅凭操作系统推断运行时拓扑；用户回答后阅读 [OAuth 设置](references/oauth-setup.md)。
- 开始浏览器授权前，声明 Hermes 将以其中登录的 Box 账号身份运作。若用户需要更窄的访问范围，可授权一个仅被邀请到所需文件、文件夹或 Hub 的账号。不要为了解锁特殊操作而把该账号设为管理员。
- 若必须使用自定义 OAuth 平台应用，使用 CLI 的交互式平台应用流程。仅让用户在本地 CLI 提示符中输入其 client secret；绝不要在聊天中索要、写入 Hermes 配置或提交到版本库。
- 若安装、浏览器授权、环境切换或权限变更需要批准，先申请批准，获批后继续设置。不要用命令清单代替实际操作。

## 开始每项任务

1. 确认 CLI 与当前身份。在 POSIX shell 中用 `command -v box` 探测，或在 PowerShell 中用 `Get-Command box -ErrorAction SilentlyContinue`。若 `box` 在 `PATH` 中，直接使用。若 Hermes 将 CLI 安装在其当前主目录下，用 [CLI 指南](references/cli-guide.md) 中适配 shell 的已验证运行方式替代每个开头的 `box`。然后用该运行方式执行 `box users:get me --json --fields id,name,login`。
   若成功，记录该身份并继续。不要再询问认证。仅将 `folders:items 0` 视为该身份根目录的列表；它不能证明共享文件、文件夹或 Hub 不可访问。对已知文件或文件夹，直接验证其 ID；对 Hub，使用 [Box Hubs](references/hubs.md) 中的 Hubs 发现路径。
2. 若缺少认证，请用户用 OAuth 连接 Box 账号，然后询问 Hermes 与授权浏览器运行在同一台计算机还是不同主机上。阅读 [OAuth 设置](references/oauth-setup.md)。
3. 操作前阅读相关参考。优先使用已文档化的命令；仅当请求需要参考中未覆盖的选项，或已安装的 CLI 拒绝文档化形式时，才运行子命令帮助。

标记为 `bash` 的示例使用 POSIX 续行语法。在 PowerShell 中，把 Box 命令写成一行，或将每个行尾的 `\` 换成 PowerShell 的反引号续行符。不要把 POSIX 变量赋值粘贴到 PowerShell 中。

## 不中断地扩展 CLI

当 Box CLI 缺少专用子命令时，用 `box request` 调用对应的 REST 端点并继续常规操作。不要仅仅因为实现走 REST 就让用户做选择；这仍是同一个 Box 任务，且保留已配置的 CLI 身份。当端点需要请求体或自定义头时，阅读 [REST API 回退](references/rest-api.md)。

在删除、协作/共享链接或权限变更、身份变更、宽泛或高成本的批量变更之前，或在目标或范围不明确时，先征询用户。否则直接执行请求的操作并验证。

## 选择正确路径

| 需求 | 阅读 |
| --- | --- |
| CLI 约定、环境、JSON 或 REST 逃生通道 | [CLI 指南](references/cli-guide.md) |
| 文件、文件夹、版本、链接或协作 | [内容工作流](references/content-workflows.md) |
| 搜索、元数据、Box AI 或 AI units | [搜索与 AI](references/search-and-ai.md) |
| 精选的大规模问答或可复用知识库 | [Box Hubs](references/hubs.md) |
| 大量文件或可续传的批处理 | [批量操作](references/bulk-operations.md) |
| 应用代码或 Box SDK | [SDK 开发](references/sdk-development.md) |
| Webhooks 或 Events API | [Webhooks 与事件](references/webhooks-and-events.md) |
| CLI 不可用或缺少 CLI 操作 | [REST API 回退](references/rest-api.md) |
| 认证、权限、速率限制或 API 错误 | [故障排查](references/troubleshooting.md) |

## 内容处理策略

对 Box 托管内容做语义分析时，优先使用 Box AI：它保留 Box 权限，通过 Box 受治理的 AI 集成处理源文件，使源文件正文不进入 Hermes 的编码模型上下文，且无需下载每个文件即可规模化处理文档工作。不要贬低或阻止其他工作流；当用户明确选择时使用它。

确定性查询使用已有的 Box 元数据或元数据查询。否则使用 Box AI：

- `ai:ask` 用于问答、摘要与对比
- `ai:extract-structured` 用于已知字段或元数据模板
- `ai:extract` 用于灵活的键值提取
- `ai:text-gen` 用于以单个 Box 文件为依据的写作

对超过 25 个文件的问答或可复用的精选知识库，优先使用面向 Hub 的 Box AI。先发现一个可访问的现有 Hub；只有在用户批准共享资源变更后才创建或填充 Hub。若没有可用 Hub 且用户不希望创建，用搜索或元数据收窄一次性请求。不要用 Hub 做元数据提取或文本生成。阅读 [Box Hubs](references/hubs.md)。

当用户要求从 Box 文件提取元数据时，除非他们要求预览，否则视为持久化结果的请求。目标 schema 已知时使用带内联字段的结构化提取，字段尚在探索时使用自由格式提取。当某个兼容的现有企业模板能表示所有请求的字段时，复用它。否则把扁平标量结果存入内置的 `global.properties` 元数据实例；当结果包含嵌套对象、表格或必须保留类型的值时，在源文件旁上传 JSON sidecar。读回每次写入并与预期结果比对。绝不静默替换为文件描述、附加不完整或不相关的模板、截断字段或丢弃字段。

不要创建或修改元数据模板。Box 不允许创建全局模板，且企业模板管理不在 Hermes 常规 OAuth 内容工作流范围内。若用户需要可复用的类型化企业元数据但不存在兼容模板，说明必须由 Box 管理员或经授权的共同管理员另行创建，保持现有结构化元数据不变，并报告已持久化的 `global.properties` 实例或 JSON sidecar。完整的提取与写回工作流见 [搜索与 AI](references/search-and-ai.md)。

首次 Box AI 请求前，声明 Box AI 必须启用、会消耗 AI units，并且仍受当前身份权限限制；无需等待用户确认。返回给 Hermes 的 AI 响应仍可能包含敏感信息。仅当大批量任务的文件范围或预期 AI-unit 消耗不明确，或用户未明确要求该规模时，才需要确认。参见 [搜索与 AI](references/search-and-ai.md)。

## 安全操作

- 优先用 ID 而非路径，并在诊断文件缺失前先验证当前身份。
- 用 `--json` 与 `--fields` 控制输出体量。对变更操作，先盘点，确认范围不明确或过大后再执行，然后读回结果。
- 串行执行有顺序的 CLI 变更，确保进度与恢复清晰无歧义。可扩展的工作使用文档化的批量输入支持或受控的 SDK 并发。
- 不要仅为提供导航而创建共享链接。共享链接会改变访问权限，需要明确确认。
- 不要把机密放进聊天、命令输出、版本库或日志中。

## 汇报结果

对每个单独汇报的 Box 条目，包含其 ID 和可点击的导航链接：

- 文件：`https://app.box.com/file/<FILE_ID>`
- 文件夹：`https://app.box.com/folder/<FOLDER_ID>`
- Hub：`https://app.box.com/hubs/<HUB_ID>`

对大批量任务，链接源文件夹与目标文件夹及异常项，而不是逐一列出数百个条目。仅对已连接 Box 账号可见的内容，人工可能无法打开；应明确说明。每次写入摘要中都要包含身份与所执行的验证。

## 验证

每次写入后，用同一身份获取该文件或文件夹，或列出其父目录，确认返回的 ID 与名称。对元数据写入，检索元数据实例，将每个返回字段与预期值比对；仅凭 HTTP 成功不算验证。报告缺失、被规范化或被拒绝的值。对一次性设置检查，创建 smoke 文件夹、验证后，仅在用户授权清理时才删除它。
