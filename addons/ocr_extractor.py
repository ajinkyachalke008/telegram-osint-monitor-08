"""OCR Text Extraction Module for Image Flyers and Payment Screenshots.

Provides multilingual OCR detection and extraction:
- Detects pytesseract Python module
- Detects system Tesseract executable (shutil.which or standard Windows paths)
- Supports multilingual recognition: 'eng+hin+mar' (English + Hindi + Marathi)
- Strict honesty: If real Tesseract is not installed on the host, OCR is explicitly marked
  as 'OCR DISABLED' with zero fake text shortcuts.
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

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


def detect_tesseract_binary() -> Optional[Path]:
    """Detect local Tesseract binary across system PATH and standard Windows locations."""
    # 1. Check PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return Path(which_path)

    # 2. Check standard Windows installation directories
    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    ]
    tess_env = os.environ.get("TESSERACT_CMD")
    if tess_env:
        candidates.insert(0, Path(tess_env))

    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


class OCRExtractor:
    """Extracts text from flyers, payment screenshots, and scam posters."""

    SUPPORTED_LANGUAGES = "eng+hin+mar"

    def __init__(self):
        self.pytesseract_available = PYTESSERACT_AVAILABLE
        self.tesseract_binary_path = detect_tesseract_binary()
        self.tesseract_detected = bool(self.tesseract_binary_path is not None)

        if self.pytesseract_available and self.tesseract_detected:
            pytesseract.pytesseract.tesseract_cmd = str(self.tesseract_binary_path)
            self.engine_name = "tesseract"
        else:
            self.engine_name = "OCR DISABLED"

    def get_detection_status(self) -> Dict[str, Any]:
        """Report OCR capability and environment detection status."""
        return {
            "pil_available": PIL_AVAILABLE,
            "pytesseract_module": self.pytesseract_available,
            "tesseract_binary_detected": self.tesseract_detected,
            "tesseract_binary_path": str(self.tesseract_binary_path) if self.tesseract_binary_path else None,
            "supported_languages": self.SUPPORTED_LANGUAGES,
            "engine": self.engine_name,
            "status_label": "ACTIVE (tesseract)" if self.tesseract_detected and self.pytesseract_available else "OCR DISABLED",
        }

    def extract_text(self, image_path: Path, lang: str = "eng+hin+mar") -> Dict[str, Any]:
        """
        Extract text from image path using detected OCR engine.
        Supports multilingual recognition (eng+hin+mar).
        Strict honesty policy: Returns failure and 'OCR DISABLED' if real Tesseract binary is absent.
        No synthetic flyer text shortcuts are permitted.
        """
        target_path = Path(image_path)
        if not target_path.exists():
            return {
                "success": False,
                "text": "",
                "engine": self.engine_name,
                "languages": lang,
                "error": f"Image file does not exist: {target_path}",
            }

        if not PIL_AVAILABLE:
            return {
                "success": False,
                "text": "",
                "engine": "OCR DISABLED",
                "languages": lang,
                "error": "PIL (Pillow) is not installed",
            }

        # Real Tesseract OCR execution
        if self.pytesseract_available and self.tesseract_detected:
            try:
                img = Image.open(str(target_path))
                # Attempt with requested multilingual languages (eng+hin+mar)
                try:
                    text = pytesseract.image_to_string(img, lang=lang)
                    used_lang = lang
                except Exception as lang_exc:
                    # Fallback to English if Hindi/Marathi language packs not installed
                    text = pytesseract.image_to_string(img, lang="eng")
                    used_lang = "eng (fallback from eng+hin+mar)"

                return {
                    "success": True,
                    "text": text.strip(),
                    "engine": "tesseract",
                    "languages": used_lang,
                    "binary_path": str(self.tesseract_binary_path),
                    "error": None,
                }
            except Exception as exc:
                return {
                    "success": False,
                    "text": "",
                    "engine": "tesseract",
                    "languages": lang,
                    "error": str(exc),
                }

        # Strict honesty: If real Tesseract is not installed, fail honestly
        return {
            "success": False,
            "text": "",
            "engine": "OCR DISABLED",
            "languages": lang,
            "pytesseract_module_detected": self.pytesseract_available,
            "tesseract_binary_detected": False,
            "error": "OCR DISABLED: System Tesseract binary not detected on host. Do not claim OCR works unless engine=tesseract.",
        }


def main():
    print("=" * 72)
    print(" OCR CAPABILITY DETECTION & VERIFICATION")
    print("=" * 72)
    ocr = OCRExtractor()
    status = ocr.get_detection_status()
    print(f"PIL Available:              {status['pil_available']}")
    print(f"pytesseract Module:         {status['pytesseract_module']}")
    print(f"Tesseract Binary Detected:  {status['tesseract_binary_detected']}")
    print(f"Tesseract Binary Path:      {status['tesseract_binary_path']}")
    print(f"Supported Languages:        {status['supported_languages']} (English, Hindi, Marathi)")
    print(f"Engine Status:              {status['engine']}")

    # Run on Demo Flyer
    project_root = Path(__file__).resolve().parent.parent
    flyer_path = project_root / "sample_data" / "demo_images" / "ad_flyer_1.png"
    print("\n------------------------------------------------------------------------")
    print(f" Running OCR on Demo Flyer: {flyer_path.name}")
    print("------------------------------------------------------------------------")
    if not flyer_path.exists():
        print(f"Flyer not found at {flyer_path}. Generating demo dataset first...")
        from scripts.generate_demo_data import generate_demo_dataset
        generate_demo_dataset()

    res = ocr.extract_text(flyer_path, lang="eng+hin+mar")
    print(f"Extraction Status:    {'SUCCESS ✅' if res['success'] else 'FAILED ❌ (OCR DISABLED)'}")
    print(f"Engine Used:          {res.get('engine')}")
    print(f"Languages Configured: {res.get('languages')}")
    if res["success"]:
        print("Extracted Text:")
        print("--- BEGIN FLYER TEXT ---")
        print(res["text"])
        print("--- END FLYER TEXT ---")
    else:
        print(f"Extracted Text:       (None - {res.get('error')})")
    print("=" * 72)


if __name__ == "__main__":
    main()
