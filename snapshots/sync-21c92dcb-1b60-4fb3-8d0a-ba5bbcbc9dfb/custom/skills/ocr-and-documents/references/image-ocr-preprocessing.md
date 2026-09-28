# Image OCR Preprocessing Techniques

Recipes for improving tesseract OCR quality on different image types.

## General Principles

- **Scale up**: Tesseract works best at 300+ DPI. For small screenshots (e.g. 653×244), scale 3–6× before OCR.
- **Binarize**: Black text on white background is tesseract's native habitat. Remove noise, keep text.
- **Multi-pass**: Run 2–3 preprocessing variants — no single recipe works for all images.
- **PSM modes**: Try multiple Page Segmentation Modes (3=auto, 4=single column, 6=uniform block, 7=single line).

## Recipe A: Terminal Screenshots (dark/blue text on light BG)

```python
from PIL import Image, ImageEnhance
import pytesseract

img = Image.open('screenshot.png').convert('RGB')
w, h = img.size
pixels = img.load()

# Isolate text-colored pixels (dark or colored text)
new = Image.new('L', (w, h), 255)
new_px = new.load()
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        # Terminal text is either dark or strongly colored (blue, green)
        if (r < 50 and g < 50 and b < 50) or \
           (b > 80 and b > r + 30) or \
           (g > 80 and g > r + 30 and g > b):
            new_px[x, y] = 0

scaled = new.resize((w * 4, h * 4), Image.NEAREST)
text = pytesseract.image_to_string(scaled, lang='eng', config='--psm 4 --oem 3')
```

## Recipe B: General Screenshots / UI (various colors)

```python
img = Image.open('capture.png')
w, h = img.size

# Scale 4x
big = img.resize((w * 4, h * 4), Image.LANCZOS)
gray = big.convert('L')

# Increase contrast
enhancer = ImageEnhance.Contrast(gray)
gray = enhancer.enhance(2.0)

# Sharpen
gray = gray.filter(ImageFilter.SHARPEN)

# Threshold
binary = gray.point(lambda x: 0 if x < 160 else 255, '1')
text = pytesseract.image_to_string(binary, lang='eng', config='--psm 3 --oem 3')
```

## Recipe C: Low-contrast / Faded text

```python
from PIL import ImageOps

img = Image.open('faded.png')
gray = img.convert('L')

# Auto-contrast stretch
auto = ImageOps.autocontrast(gray, cutoff=5)

# Scale
scaled = auto.resize((auto.width * 3, auto.height * 3), Image.LANCZOS)
text = pytesseract.image_to_string(scaled, lang='eng', config='--psm 3 --oem 3')
```

## Recipe D: Batch PSM sweep (find best mode)

```python
img = Image.open('unknown.png').convert('L')
# Scale 3x
img = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)

results = {}
for psm in [3, 4, 6, 7, 11, 12]:
    text = pytesseract.image_to_string(img, config=f'--psm {psm} --oem 3')
    # Simple score: more alphanumeric chars, fewer special chars
    clean = sum(c.isalnum() or c.isspace() for c in text)
    total = len(text) or 1
    results[psm] = (clean / total, text)

best_psm = max(results, key=lambda p: results[p][0])
print(f'Best PSM: {best_psm}')
print(results[best_psm][1])
```

## Recipe E: Two-column / Side-by-side layout

Use PSM 4 (single column) or PSM 6 (uniform block) on each half:

```python
img = Image.open('two_column.png')
w, h = img.size
left = img.crop((0, 0, w // 2, h))
right = img.crop((w // 2, 0, w, h))

text_left = pytesseract.image_to_string(left, config='--psm 4 --oem 3')
text_right = pytesseract.image_to_string(right, config='--psm 4 --oem 3')
```

## Recipe F: Image arrives as .bin or unknown extension

```bash
file unknown.bin           # Identify actual format
cp unknown.bin image.png   # Use correct extension
```

## Common OCR Confusions in Terminal Fonts

| Glyph | Often misread as |
|-------|-----------------|
| `0` (zero) | `O`, `o`, `8` |
| `1` (one) | `l`, `I`, `|` |
| `|` (pipe) | `1`, `l`, `I` |
| `l` (lower L) | `1`, `I`, `|` |
| `n` / `r` | Can swap in small fonts |
| `9` / `g` / `q` | Lower loop confuses |
| `.` (dot) | Often lost or becomes `,` |
| `_` (underscore) | Often lost in thresholding |
| `$` (prompt) | Can read as `s`, `5`, or `$` |

## When to Give Up on OCR

- Image is smaller than ~200×100 pixels (text too small even at 6× scale)
- More than 40% of the output is non-alphanumeric garbage
- The text is anti-aliased extremely heavily (white-on-pastel)
- Content is clearly a photo of a physical screen (moire patterns, curved text)

In these cases, report "image too degraded for OCR" and ask the user to provide the text directly or capture a clearer screenshot.
