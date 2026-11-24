"""Unit tests for Workstream I: Demo Generator and OCR Fallback."""
import pytest
from pathlib import Path
from scripts.generate_demo_data import generate_demo_dataset, SAMPLE_DATA_DIR
from addons.ocr_extractor import OCRExtractor


def test_generate_demo_dataset():
    records = generate_demo_dataset()
    assert len(records) >= 10

    json_path = SAMPLE_DATA_DIR / "demo_multiplatform_dataset.json"
    csv_path = SAMPLE_DATA_DIR / "demo_dataset.csv"
    assert json_path.exists()
    assert csv_path.exists()

    # Verify cross-channel actor presence in demo dataset
    upis = [r.get("text", "") for r in records if "mule.syndicate@ybl" in r.get("text", "")]
    assert len(upis) >= 2, "Expected cross-channel syndicate presence across multiple demo posts"


def test_ocr_extractor_fallback():
    ocr = OCRExtractor()
    # Non-existent file
    res = ocr.extract_text(Path("non_existent_image.png"))
    assert res["success"] is False

    # Existing demo flyer image
    demo_img = SAMPLE_DATA_DIR / "demo_images" / "ad_flyer_1.png"
    if demo_img.exists():
        res2 = ocr.extract_text(demo_img)
        # Should either succeed if tesseract/easyocr installed or return graceful fallback
        assert "engine" in res2
