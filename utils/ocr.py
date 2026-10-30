import os
import pytesseract
from PIL import Image, ImageOps, ImageFilter

# On Windows, set TESSERACT_CMD in your .env if tesseract isn't on PATH, e.g.:
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
tesseract_cmd = os.getenv("TESSERACT_CMD")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def _preprocess(image: Image.Image) -> Image.Image:
    """Light preprocessing to improve OCR accuracy on photographed labels."""
    image = image.convert("L")  # grayscale
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def extract_text(filepath: str) -> str:
    """Extract raw text from a nutrition/ingredients label image."""
    image = Image.open(filepath)
    image = _preprocess(image)
    text = pytesseract.image_to_string(image)
    return text.strip()
