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

# PDF, Document & Image OCR

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs, scanned documents, and standalone image files (PNG, JPG, WebP, BMP, GIF)**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Identify File Type & Choose Approach

Run `file <path>` first to determine the actual format. The image may arrive as `.bin` or without a proper extension.

| File type | Tool | Approach |
|-----------|------|----------|
| PDF (text-based) | pymupdf | Instant extraction |
| PDF (scanned / complex) | marker-pdf | OCR with layout analysis |
| PDF (scanned, light) | tesseract (per-page) | Quick OCR, no layout |
| PNG / JPG / WebP / BMP / GIF | tesseract | Image OCR |
| Terminal screenshot | tesseract + preprocessing | See Image OCR section |
| DOCX | python-docx | Parse structure |
| PPTX | python-pptx | See `powerpoint` skill |
| EPUB | pymupdf or marker-pdf | Full support |

---

## pymupdf (lightweight — text-based PDFs)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR — scanned PDFs)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## VLM-based OCR (Vision Language Model) — Preferred Path

Use `vision_analyze` FIRST for standalone images (PNG, JPG, WebP, BMP, GIF) — it
is dramatically more accurate than tesseract on terminal screenshots, code
captures, UI mockups, and complex layouts. Only fall back to tesseract (below)
when vision_analyze is unavailable or the image is trivial.

### Quick start

```bash
vision_analyze(image_url="/path/to/image.png", question="Read all text in this image exactly as shown")
```

### When vision_analyze fails (Model disabled / 403 / API error)

The Hermes auxiliary vision system uses a configurable model under
`auxiliary.vision` in `~/.hermes/config.yaml`. Common failure modes:

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `"Model disabled"` (403) | The configured model was deprecated/removed by the provider | Switch model: `hermes config set auxiliary.vision.model <new-model>` |
| `"Invalid token"` | API key expired or wrong for the provider | Update `auxiliary.vision.api_key` or switch providers |
| `400 code 20015: "height(N) or width(M) must be larger than 28 for Qwen 3 VL models"` | Image is <28px in one dimension (e.g. a thin single-line terminal/code capture) | Resize up 2–4× with Pillow, then re-run `vision_analyze` |

**Troubleshooting workflow:**

1. **Check current config:**
   ```bash
   grep -A5 "auxiliary:" ~/.hermes/config.yaml
   ```

2. **List available vision models on the provider** (SiliconFlow example):
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

3. **Test a model directly** before setting it as default:
   ```bash
   curl -s "https://api.siliconflow.cn/v1/chat/completions" \
     -H "Authorization: Bearer *** \
     -H "Content-Type: application/json" \
     -d '{
       "model": "Qwen/Qwen3-VL-32B-Instruct",
       "messages": [{"role":"user","content":[{"type":"text","text":"hello"}]}]
     }'
   ```

4. **Set the new model** (persists across sessions):
   ```bash
   hermes config set auxiliary.vision.model "Qwen/Qwen3-VL-32B-Instruct"
   ```

### Recommended vision models (via SiliconFlow)

| Model | Size | Best for | Notes |
|-------|------|----------|-------|
| **Qwen/Qwen3-VL-32B-Instruct** | 32B | General document/screenshot OCR | Strong all-rounder, good terminal text reading |
| **PaddlePaddle/PaddleOCR-VL-1.5** | 0.9B | **Dedicated OCR** — tables, forms, formulas | 94.5% OmniDocBench, 111 languages, tiny footprint |
| **Qwen/Qwen3-VL-8B-Instruct** | 8B | Faster, lighter | Good when speed matters |
| **stepfun-ai/Step-3.5-Flash** | — | General vision tasks | Alternative provider |

For OCR-specific tasks (receipts, ID cards, dense text documents, multi-column
layouts), **PaddleOCR-VL-1.5 is the best choice**. See `references/paddleocr-vl.md`
for benchmarks and capabilities.

### Important: session restart required

Config changes made via `hermes config set` take effect only in **new sessions**.
Use `/reset` (in CLI) or start a new session to pick up the new vision model.

---

## Image Files & Screenshots (tesseract OCR — Fallback)

Use tesseract when:
- The file is PNG / JPG / WebP / BMP / GIF (standalone image, not a PDF)
- `vision_analyze` is unavailable (model disabled, API error, no vision model)
- marker-pdf is too heavy (~5GB) and you just need text from an image
- You have a terminal screenshot, code screenshot, or UI mockup image
- The image is simple black-on-white text with no complex layout

### 1. Install dependencies

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-jpn  # Add languages as needed
python3 -m venv ocr_venv
ocr_venv/bin/pip install pytesseract Pillow
```

### 2. Basic OCR

```bash
ocr_venv/bin/python -c "
import pytesseract
from PIL import Image
text = pytesseract.image_to_string(Image.open('image.png'), lang='eng')
print(text)
"
```

For Chinese + English mixed content: `lang='chi_sim+eng'`.
For Japanese + English: `lang='jpn+eng'`.

### 3. Preprocessing for Better Results

Terminal screenshots, code captures, and low-contrast images benefit from preprocessing. See `references/image-ocr-preprocessing.md` for the full guide.

Quick patterns:

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

### 4. Multiple Passes & Voting

When OCR quality is uncertain, run 2-3 variations (different thresholds, scales, PSM modes) and compare outputs. Common characters that OCR confuses in terminal fonts:
- `0` ↔ `O` ↔ `o` ↔ `8`
- `l` ↔ `1` ↔ `I` ↔ `|`
- `n` ↔ `r` ↔ `n` (uppercase)
- `9` ↔ `g` ↔ `q`

Cross-reference output with known domain terminology (e.g. "mmu_rv64", "smp_rv32" for RISC-V build dirs).

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

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

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Pitfalls

- **vision_analyze hallucinates on code screenshots** — Verilog/SystemVerilog port lists, HDL code, and dense monospaced code captures are unreliable with Qwen3-VL (hallucinates signal names, merges signals, fabricates bit widths). For these, skip vision_analyze and go straight to tesseract + preprocessing (scale 4× + threshold). Cross-verify with a second PSM mode when signal count differs.
- **`6` ↔ `0` in dark-background OCR** — tesseract on dark terminals frequently reads `0` as `6` and vice versa. Use domain knowledge (e.g., `[2:6]` is unlikely; correct to `[2:0]`). When in doubt, try preprocessing with inverted threshold.

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- **tesseract is the go-to for standalone image files** (PNG, JPG, WebP) — lightweight (~30MB), works without PyTorch
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
- **PEP 668**: On modern Linux pip refuses global installs. Always create a venv first.
- See `references/image-ocr-preprocessing.md` for detailed preprocessing recipes
