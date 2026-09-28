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

# WeCom (企业微信) Platform Conventions

## File Delivery

WeCom may block certain file extensions (e.g., `.py`, `.sh`, `.exe`). To ensure delivery:

1. Copy the file with a `.txt` suffix into the delivery temp dir: `cp foo.py ~/delivery_tmp/foo.py.txt`
2. Send via `MEDIA:/home/ubuntu/delivery_tmp/foo.py.txt`
3. Tell the user the original extension to rename back to: "收到后改回 `.py`"

**Delivery `.txt` copies live in `~/delivery_tmp/` ONLY** — never drop them into the working dir or `~/deliverables`. `~/deliverables` is a git repo for source files only; keep it clean (user: "不要到处拉屎"). Add `__pycache__/`, `*.pyc`, `*.py.txt` to `~/deliverables/.gitignore` so cache/delivery artifacts never get committed.

Do NOT send files with blocked extensions — they will be silently dropped.
Do NOT just paste the file content in chat when the user asks to send the file — use MEDIA: with the renamed copy.

## Code Change Delivery

When delivering code changes to the user via WeCom:

- **≤10 lines**: Print the `diff -u` snippet inline (with `@@` hunk header, `+`/`-` markers, file path). Do NOT send the whole file.
- **>10 lines**: Send the complete file via MEDIA: (with .txt rename). Do NOT paste the diff in chat — just send the file and a one-line summary.

## Formatting

- Markdown is supported
- Images (.jpg, .png, .webp) up to 10 MB are sent as native photos
- Other files (.pdf, .docx, .xlsx, .md, .txt) up to 20 MB as downloadable documents
- Videos (.mp4) play inline
- Image URLs in markdown `![alt](url)` are auto-downloaded and sent as native photos
