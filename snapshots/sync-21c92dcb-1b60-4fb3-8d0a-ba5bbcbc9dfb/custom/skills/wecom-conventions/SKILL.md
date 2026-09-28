---
name: wecom-conventions
description: 'WeCom (企业微信) platform conventions: file delivery, formatting, and limitations.'
metadata:
  hermes:
    tags:
    - WeCom
    - 企业微信
    - file-delivery
    - platform
    version: 1.0.0
    author: Hermes Agent
    license: MIT
---

# WeCom（企业微信）平台约定

## 文件交付

WeCom 可能会拦截某些文件扩展名（例如 `.py`、`.sh`、`.exe`）。为确保交付成功：

1. 把文件复制为带 `.txt` 后缀的副本放入交付临时目录：`cp foo.py ~/delivery_tmp/foo.py.txt`
2. 通过 `MEDIA:/home/ubuntu/delivery_tmp/foo.py.txt` 发送
3. 告诉用户需要改回的原扩展名：“收到后改回 `.py`”

**交付用 `.txt` 副本只放在 `~/delivery_tmp/`**——绝不能丢进工作目录或 `~/deliverables`。`~/deliverables` 是只存放源文件的 git 仓库；请保持整洁（用户原话：“不要到处拉屎”）。把 `__pycache__/`、`*.pyc`、`*.py.txt` 加入 `~/deliverables/.gitignore`，确保缓存/交付产物永远不会被提交。

不要发送带被拦截扩展名的文件——会被静默丢弃。
用户要求发送文件时，不要只在聊天里粘贴文件内容——要用改名后的副本走 MEDIA:。

## 代码改动交付

通过 WeCom 向用户交付代码改动时：

- **≤10 行**：在聊天里直接输出 `diff -u` 片段（含 `@@` hunk 头、`+`/`-` 标记、文件路径）。不要发送整个文件。
- **>10 行**：通过 MEDIA: 发送完整文件（改名为 .txt）。不要在聊天里粘贴 diff——只发文件和一行摘要。

## 格式限制

- 支持 Markdown
- 图片（.jpg、.png、.webp）最大 10 MB，以原生照片形式发送
- 其他文件（.pdf、.docx、.xlsx、.md、.txt）最大 20 MB，以可下载文档形式发送
- 视频（.mp4）可内联播放
- Markdown 中的图片 URL `![alt](url)` 会被自动下载并以原生照片形式发送
