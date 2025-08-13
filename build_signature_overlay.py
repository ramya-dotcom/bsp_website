"""
Create a transparent signature overlay PNG cropped tightly to the red-box area
(signature through 'Tamil Nadu') and save to static/signature_overlay.png.

Usage:
  python3 build_signature_overlay.py
"""

from pathlib import Path
from typing import Tuple
import fitz  # PyMuPDF
from PIL import Image, ImageFilter

# ------------- Paths -------------
PDF_PATH = Path("/Users/avinash/Downloads/c382867d-8681-4a61-a151-776608f4eacb.pdf")
OUTPUT_PATH = Path("static/signature_overlay.png")
DPI = 300
# ---------------------------------

# ------------- Exact crop box (percent of page) -------------
# These percentages are tuned to the red box you showed on your reference page.
# If you need micro-adjustments, change by ±0.01 (≈ 1% of width/height).
CROP_BOX_PCT: Tuple[float, float, float, float] = (
    0.615,  # left   ~58.5% of page width from the left
    0.545,  # top    ~44.5% of page height from the top
    0.804,  # right  ~80.4% of page width
    0.706,  # bottom ~74.0% of page height
)
# ------------------------------------------------------------

# Background removal threshold (near-white -> transparent)
WHITE_THRESHOLD = 245
# Optional: small blur to soften white fringes at edges (set 0 to disable)
FRINGE_BLUR_RADIUS = 0.6


def render_pdf_first_page_to_image(pdf_path: Path, dpi: int) -> Image.Image:
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    doc.close()
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def crop_percent(img: Image.Image, box_pct: Tuple[float, float, float, float]) -> Image.Image:
    w, h = img.size
    l = int(max(0, min(box_pct[0], 1.0)) * w)
    t = int(max(0, min(box_pct[1], 1.0)) * h)
    r = int(max(0, min(box_pct[2], 1.0)) * w)
    b = int(max(0, min(box_pct[3], 1.0)) * h)
    l, r = sorted((l, r))
    t, b = sorted((t, b))
    # Clamp to bounds
    l = max(0, min(l, w - 1))
    r = max(l + 1, min(r, w))
    t = max(0, min(t, h - 1))
    b = max(t + 1, min(b, h))
    return img.crop((l, t, r, b))


def white_to_alpha(img: Image.Image, threshold: int = 245) -> Image.Image:
    """
    Convert near-white background to transparency.
    Pixels where R,G,B >= threshold become fully transparent.
    """
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    thr = max(0, min(threshold, 255))
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r >= thr and g >= thr and b >= thr:
                px[x, y] = (r, g, b, 0)
            else:
                px[x, y] = (r, g, b, 255)
    return img


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    full = render_pdf_first_page_to_image(PDF_PATH, DPI)
    print(f"Rendered page size: {full.size}")

    # Exact crop to the red-box area
    cropped = crop_percent(full, CROP_BOX_PCT)
    print(f"Cropped to: {cropped.size}")

    # Remove white background -> alpha
    overlay = white_to_alpha(cropped, WHITE_THRESHOLD)

    # Optional: soften edges slightly to remove white fringes
    if FRINGE_BLUR_RADIUS and FRINGE_BLUR_RADIUS > 0:
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=FRINGE_BLUR_RADIUS))

    # Auto-trim transparent edges tightly
    bbox = overlay.getbbox()
    if bbox:
        overlay = overlay.crop(bbox)

    overlay.save(OUTPUT_PATH, "PNG")
    print(f"Saved overlay to: {OUTPUT_PATH.resolve()} (size={overlay.size})")


if __name__ == "__main__":
    if not PDF_PATH.exists():
        raise SystemExit(f"Input PDF not found: {PDF_PATH}")
    main()
