---
name: ocr-and-documents
description: Extract text from PDFs, scans, and image files (PNG, JPG, WebP) — pymupdf, marker-pdf, tesseract.
metadata:
  hermes:
    tags:
    - PDF
    - Documents
    - Research
    - Arxiv
    - Text-Extraction
    - OCR
    - Image-OCR
    - Screenshot
    related_skills:
    - powerpoint
    version: 2.5.0
    author: Hermes Agent
    license: MIT
    platforms:
    - linux
    - macos
    - windows
---

# PDF、文档与图片 OCR

处理 DOCX：使用 `python-docx`（解析真实文档结构，远优于 OCR）。
处理 PPTX：参见 `powerpoint` skill（使用 `python-pptx`，支持完整幻灯片与备注）。
本 skill 覆盖 **PDF、扫描文档以及独立图片文件（PNG、JPG、WebP、BMP、GIF）**。

## 第 1 步：是否有远程 URL？

如果文档有 URL，**始终先尝试 `web_extract`**：

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

它通过 Firecrawl 完成 PDF 转 Markdown，无需任何本地依赖。

仅在以下情况使用本地提取：文件在本地、web_extract 失败，或需要批量处理。

## 第 2 步：识别文件类型并选择方案

先运行 `file <path>` 确定实际格式。图片可能以 `.bin` 形式到达，或缺少正确的扩展名。

| 文件类型 | 工具 | 方案 |
|-----------|------|----------|
| PDF（文本型） | pymupdf | 即时提取 |
| PDF（扫描件 / 复杂版式） | marker-pdf | OCR + 版面分析 |
| PDF（扫描件，轻量） | tesseract（逐页） | 快速 OCR，无版面分析 |
| PNG / JPG / WebP / BMP / GIF | tesseract | 图片 OCR |
| 终端截图 | tesseract + 预处理 | 见"图片文件与截图"一节 |
| DOCX | python-docx | 解析结构 |
| PPTX | python-pptx | 参见 `powerpoint` skill |
| EPUB | pymupdf 或 marker-pdf | 完整支持 |

---

## pymupdf（轻量——文本型 PDF）

```bash
pip install pymupdf pymupdf4llm
```

**通过辅助脚本**：
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**内联方式**：
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf（高质量 OCR——扫描型 PDF）

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**通过辅助脚本**：
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI**（随 marker-pdf 安装）：
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## 基于 VLM 的 OCR（视觉语言模型）——首选路径

对独立图片（PNG、JPG、WebP、BMP、GIF）**首选** `vision_analyze`——在终端截图、
代码截图、UI 原型和复杂版式上，它远比 tesseract 准确。仅当 vision_analyze
不可用或图片很简单时才回退到 tesseract
（见下文）。

### 快速上手

```bash
vision_analyze(image_url="/path/to/image.png", question="Read all text in this image exactly as shown")
```

### 当 vision_analyze 失败时（模型被禁用 / 403 / API 错误）

Hermes 辅助视觉系统使用 `~/.hermes/config.yaml` 中 `auxiliary.vision` 下
可配置的模型。常见失败模式：

| 症状 | 可能原因 | 修复 |
|---------|-------------|-----|
| `"Model disabled"` (403) | 配置的模型已被提供商弃用/移除 | 切换模型：`hermes config set auxiliary.vision.model <new-model>` |
| `"Invalid token"` | API key 已过期或与提供商不匹配 | 更新 `auxiliary.vision.api_key` 或更换提供商 |
| `400 code 20015: "height(N) or width(M) must be larger than 28 for Qwen 3 VL models"` | 图片某一维度小于 28px（例如细窄的单行终端/代码截图） | 用 Pillow 放大 2–4 倍，然后重跑 `vision_analyze` |

**排查流程：**

1. **检查当前配置：**
   ```bash
   grep -A5 "auxiliary:" ~/.hermes/config.yaml
   ```

2. **列出提供商可用的视觉模型**（以 SiliconFlow 为例）：
   ```bash
   curl -s "https://api.siliconflow.cn/v1/models" \
     -H "Authorization: Bearer *** -A5 'siliconflow' ~/.hermes/config.yaml | grep 'api_key' | sed 's/.*api_key: *//')" \
     -H "Content-Type: application/json" | python3 -c "
   import sys, json
   data = json.load(sys.stdin)
   for m in data.get('data', []):
     if any(k in m['id'].lower() for k in ['vl','vision','ocr','paddleocr']): print(m['id'])
   "
   ```

3. **直接测试某个模型**，再设为默认：
   ```bash
   curl -s "https://api.siliconflow.cn/v1/chat/completions" \
     -H "Authorization: Bearer *** \
     -H "Content-Type: application/json" \
     -d '{
       "model": "Qwen/Qwen3-VL-32B-Instruct",
       "messages": [{"role":"user","content":[{"type":"text","text":"hello"}]}]
     }'
   ```

4. **设置新模型**（跨会话持久生效）：
   ```bash
   hermes config set auxiliary.vision.model "Qwen/Qwen3-VL-32B-Instruct"
   ```

### 推荐的视觉模型（通过 SiliconFlow）

| 模型 | 规模 | 最适合 | 备注 |
|-------|------|----------|-------|
| **Qwen/Qwen3-VL-32B-Instruct** | 32B | 通用文档/截图 OCR | 全面均衡，终端文字读取表现好 |
| **PaddlePaddle/PaddleOCR-VL-1.5** | 0.9B | **专用 OCR**——表格、表单、公式 | OmniDocBench 94.5%，支持 111 种语言，体积小巧 |
| **Qwen/Qwen3-VL-8B-Instruct** | 8B | 更快、更轻 | 适合速度优先的场景 |
| **stepfun-ai/Step-3.5-Flash** | — | 通用视觉任务 | 备选提供商 |

针对 OCR 专项任务（小票、身份证、密集文本文档、多栏版式），
**PaddleOCR-VL-1.5 是最佳选择**。基准测试与能力详见
`references/paddleocr-vl.md`。

### 重要：需要重启会话

通过 `hermes config set` 所做的配置更改只在**新会话**中生效。
使用 `/reset`（CLI 中）或新开会话来启用新的视觉模型。

---

## 图片文件与截图（tesseract OCR——后备方案）

在以下情况使用 tesseract：
- 文件是 PNG / JPG / WebP / BMP / GIF（独立图片，而非 PDF）
- `vision_analyze` 不可用（模型被禁用、API 错误、没有视觉模型）
- marker-pdf 过重（约 5GB），而你只需要从图片中提取文字
- 手头是终端截图、代码截图或 UI 原型图
- 图片是简单的白底黑字、无复杂版式

### 1. 安装依赖

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-jpn  # Add languages as needed
python3 -m venv ocr_venv
ocr_venv/bin/pip install pytesseract Pillow
```

### 2. 基础 OCR

```bash
ocr_venv/bin/python -c "
import pytesseract
from PIL import Image
text = pytesseract.image_to_string(Image.open('image.png'), lang='eng')
print(text)
"
```

中英混合内容：`lang='chi_sim+eng'`。
日英混合：`lang='jpn+eng'`。

### 3. 预处理以获得更好结果

终端截图、代码截图和低对比度图片可从预处理中获益。完整指南见 `references/image-ocr-preprocessing.md`。

快速模式：

```python
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

img = Image.open('image.png')

# Pattern A: Screenshot / terminal — scale up + threshold
big = img.resize((w*4, h*4), Image.LANCZOS)
gray = big.convert('L')
binary = gray.point(lambda x: 0 if x < 160 else 255, '1')
text = pytesseract.image_to_string(binary, lang='eng', config='--psm 4 --oem 3')

# Pattern B: Colored text (e.g. blue terminal text on light bg)
# Isolate text-colored pixels
img_rgb = img.convert('RGB')
w, h = img_rgb.size
new = Image.new('L', (w, h), 255)
new_px = new.load()
pixels = img_rgb.load()
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        # Dark pixels or heavily blue/colored pixels
        if (r < 40 and g < 40 and b < 40) or (b > 100 and b > r + 30):
            new_px[x, y] = 0
scaled = new.resize((w*4, h*4), Image.NEAREST)
text = pytesseract.image_to_string(scaled, lang='eng', config='--psm 4 --oem 3')

# Pattern C: Run multiple PSM modes and pick the best result
for psm in [3, 4, 6, 7]:
    text = pytesseract.image_to_string(img, config=f'--psm {psm} --oem 3')
    # Compare lengths, fewer garbage chars = better
```

### 4. 多轮识别与投票

当 OCR 质量不确定时，运行 2-3 种变体（不同的阈值、缩放、PSM 模式）并比较输出。终端字体中 OCR 常见的易混淆字符：
- `0` ↔ `O` ↔ `o` ↔ `8`
- `l` ↔ `1` ↔ `I` ↔ `|`
- `n` ↔ `r` ↔ `n`（大写）
- `9` ↔ `g` ↔ `q`

用已知领域术语交叉核对输出（例如 RISC-V 构建目录中的 "mmu_rv64"、"smp_rv32"）。

---

## Arxiv 论文

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## 拆分、合并与搜索

pymupdf 原生支持这些操作——使用 `execute_code` 或内联 Python：

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

无需额外依赖——pymupdf 一个包即可覆盖拆分、合并、搜索与文本提取。

---

## 易错点

- **vision_analyze 在代码截图上会幻觉**——Verilog/SystemVerilog 端口列表、HDL 代码和密集等宽代码截图在 Qwen3-VL 上不可靠（会臆造信号名、合并信号、捏造位宽）。遇到这些情况，跳过 vision_analyze，直接用 tesseract + 预处理（4× 放大 + 阈值）。信号数量不一致时，用第二种 PSM 模式交叉验证。
- **深色背景 OCR 中 `6` ↔ `0` 混淆**——tesseract 在深色终端上经常把 `0` 读成 `6`，反之亦然。结合领域知识判断（例如 `[2:6]` 不太可能出现，应纠正为 `[2:0]`）。拿不准时，尝试反色阈值的预处理。

## 备注

- `web_extract` 永远是 URL 的首选
- pymupdf 是稳妥的默认选择——即时、无模型、随处可用
- marker-pdf 用于 OCR、扫描文档、公式与复杂版式——仅在需要时安装
- **tesseract 是独立图片文件（PNG、JPG、WebP）的首选**——轻量（约 30MB），无需 PyTorch
- 两个辅助脚本均支持 `--help` 查看完整用法
- marker-pdf 首次使用会下载约 2.5GB 模型到 `~/.cache/huggingface/`
- 处理 Word 文档：`pip install python-docx`（优于 OCR——解析真实结构）
- 处理 PowerPoint：参见 `powerpoint` skill（使用 python-pptx）
- **PEP 668**：现代 Linux 上 pip 拒绝全局安装。务必先创建 venv。
- 详细预处理方案见 `references/image-ocr-preprocessing.md`
