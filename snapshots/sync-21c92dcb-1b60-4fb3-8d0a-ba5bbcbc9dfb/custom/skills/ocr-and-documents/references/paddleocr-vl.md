# PaddleOCR-VL — Baidu's Specialized OCR Vision-Language Model

> Research compiled 2026-06 from GitHub, HuggingFace, and live API tests.

## Overview

PaddleOCR-VL is a family of **lightweight, OCR-specialized vision-language models**
from Baidu's PaddleOCR team. Unlike general-purpose VLMs (GPT-4V, Qwen-VL, Claude
Vision), it is **purpose-built for document parsing** — reading text, tables, formulas,
charts, seals, and handwriting from images and PDFs.

| Property | Value |
|----------|-------|
| Developer | Baidu (PaddlePaddle / PaddleOCR team) |
| License | Apache 2.0 |
| GitHub | https://github.com/PaddlePaddle/PaddleOCR (84K+ stars) |
| HuggingFace | https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5 |
| Official site | https://www.paddleocr.com |

## Model Versions

| Version | Released | OmniDocBench Accuracy | Key Improvement |
|---------|----------|----------------------|-----------------|
| **PaddleOCR-VL** (1.0) | 2025-10-16 | SOTA at launch | First release: 109 languages, NaViT dynamic resolution |
| **PaddleOCR-VL-1.5** | 2026-01-29 | **94.5%** | PP-DocLayoutV3, 111 languages, seal recognition |
| **PaddleOCR-VL-1.6** | 2026-05-28 | **96.3%** | SOTA on OmniDocBench v1.5 & v1.6, ancient docs, rare chars |

All use the same 0.9B-parameter architecture — upgrades are drop-in replacements.

## Architecture

- **0.9B parameters** total — tiny by VLM standards
- NaViT-style dynamic-resolution visual encoder
- ERNIE-4.5-0.3B language model backbone
- Supports 111 languages (Chinese, English, Japanese, Latin, Arabic, Hindi, Thai,
  Tibetan, Bengali, Cyrillic, etc.)

## Key Capabilities

| Capability | Supported |
|-----------|-----------|
| Scene text recognition | ✅ 100+ languages |
| Document layout parsing | ✅ Tables, formulas, charts |
| Table extraction | ✅ With cell coordinates (via PP-StructureV3) |
| Formula recognition | ✅ LaTeX output |
| Seal recognition & spotting | ✅ (v1.5+) |
| Handwriting recognition | ✅ |
| Ancient document OCR | ✅ (v1.6+ enhanced) |
| Rare character handling | ✅ (v1.6+ significantly improved) |
| Markdown output | ✅ Native |
| JSON output | ✅ Structured |
| DOCX export | ✅ (v3.5.0+) |
| Long documents | ✅ Auto cross-page table merging, hierarchical headings |

## Benchmarks (per official data)

- **OmniDocBench v1.6**: 96.3% (PaddleOCR-VL-1.6) — leads all open-source solutions
- **OmniDocBench v1.5**: SOTA among both open-source and proprietary solutions
- **Real5-OmniDocBench**: New SOTA set by v1.6
- Outperforms general VLMs (GPT-5.5, Qwen3-VL-235B) on document-specific tasks
- PP-OCRv6 detection/recognition: +4.6% / +5.1% over v5, surpassing mainstream VLMs
  with only 34.5M parameters

## Tough Scenarios It Handles (PP-DocLayoutV3)

1. **Skew** — rotated/angled documents
2. **Warping** — curved/bent pages (e.g. book spine)
3. **Scanning artifacts** — moiré patterns, shadows
4. **Illumination** — uneven lighting, glare
5. **Screen photography** — photos of screens, moiré patterns

## Availability via API

### SiliconFlow (recommended)

Model ID: `PaddlePaddle/PaddleOCR-VL-1.5`

```bash
curl -s "https://api.siliconflow.cn/v1/chat/completions" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{
    "model": "PaddlePaddle/PaddleOCR-VL-1.5",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        {"type": "text", "text": "Extract all text and output as markdown"}
      ]
    }]
  }'
```

### HuggingFace Transformers (local inference)

```python
from transformers import AutoModel, AutoTokenizer

model = AutoModel.from_pretrained("PaddlePaddle/PaddleOCR-VL-1.5", trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained("PaddlePaddle/PaddleOCR-VL-1.5", trust_remote_code=True)
```

## When to Choose PaddleOCR-VL vs General VLM

| Scenario | Recommendation |
|----------|---------------|
| Receipt / Invoice OCR | 🏆 **PaddleOCR-VL** — specialized for structured text |
| ID card / Passport OCR | 🏆 **PaddleOCR-VL** — seal recognition, 111 languages |
| Academic paper (dense text + formulas) | 🏆 **PaddleOCR-VL** — formula + table SOTA |
| Terminal / Code screenshot | General VLM (Qwen3-VL-32B) |
| Screenshot of a UI/mobile app | General VLM (Qwen3-VL-32B) |
| Photo of a scene with text | General VLM |
| Handwritten notes | PaddleOCR-VL (strong handwriting support) |
