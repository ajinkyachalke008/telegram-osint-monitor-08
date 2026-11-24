"""OCR Text Extraction Module for Image Flyers and Payment Screenshots.

Provides graceful fallback:
- Tries pytesseract (if installed and configured)
- Tries easyocr (if installed)
- Otherwise falls back to mock/no-op gracefully without crashing
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class OCRExtractor:
    """Extracts text from flyers, payment screenshots, and scam posters."""

    def __init__(self):
        self._reader = None
        self.engine_name = "none"

        if PYTESSERACT_AVAILABLE:
            self.engine_name = "pytesseract"
        elif EASYOCR_AVAILABLE:
            self.engine_name = "easyocr"

    def extract_text(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract text from image path.
        Returns dict with extracted text, engine used, and success status.
        """
        if not image_path or not Path(image_path).exists():
            return {
                "success": False,
                "text": "",
                "engine": "none",
                "error": "Image file does not exist"
            }

        if not PIL_AVAILABLE:
            return {
                "success": False,
                "text": "",
                "engine": "none",
                "error": "PIL not installed"
            }

        try:
            if PYTESSERACT_AVAILABLE:
                img = Image.open(str(image_path))
                text = pytesseract.image_to_string(img)
                return {
                    "success": True,
                    "text": text.strip(),
                    "engine": "pytesseract",
                    "error": None
                }
            elif EASYOCR_AVAILABLE:
                if self._reader is None:
                    self._reader = easyocr.Reader(['en'], gpu=False)
                results = self._reader.readtext(str(image_path))
                text = " ".join([res[1] for res in results])
                return {
                    "success": True,
                    "text": text.strip(),
                    "engine": "easyocr",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "text": "",
                    "engine": "fallback_none",
                    "error": "No OCR library installed (pytesseract or easyocr)"
                }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "engine": self.engine_name,
                "error": str(e)
            }
