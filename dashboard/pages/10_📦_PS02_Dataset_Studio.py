"""PS02 Dataset Studio: safe archive audit and labelled sample import."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from core.db import Database
from dashboard.provenance_banner import render_provenance_banner
from ingestion.ps02_dataset import PS02DatasetError, PS02DatasetReader, safe_extract_zip, load_starter_lexicon
from ingestion.worker import IngestionWorker

st.set_page_config(page_title="PS02 Dataset Studio | OSINT Monitor", page_icon="📦", layout="wide")
render_provenance_banner(page_title="PS02 Dataset Studio")

st.title("📦 PS02 Hackathon Dataset Studio")
st.caption("Archive validation, source-aware parsing, media/OCR audit and controlled import.")

st.warning(
    "This workflow is for the supplied synthetic hackathon dataset. Imported posts are labelled "
    "HACKATHON_SAMPLE. The separate masked complaint repository and real-channel reference list "
    "are not ingested into the alert or entity graph."
)

uploaded = st.file_uploader("Upload the complete PS02 ZIP archive", type=["zip"], accept_multiple_files=False)
if uploaded is not None:
    try:
        archive_bytes = uploaded.getvalue()
        archive_hash = hashlib.sha256(archive_bytes).hexdigest()
        work_dir = ROOT / "data" / "imported_datasets" / "ps02" / archive_hash
        archive_copy = work_dir / "source.zip"
        extract_dir = work_dir / "extracted"
        work_dir.mkdir(parents=True, exist_ok=True)
        if not archive_copy.exists():
            archive_copy.write_bytes(archive_bytes)
        if not extract_dir.exists() or not any(extract_dir.iterdir()):
            dataset_root = safe_extract_zip(archive_copy, extract_dir)
        else:
            from ingestion.ps02_dataset import find_dataset_root
            dataset_root = find_dataset_root(extract_dir)
        st.session_state["ps02_dataset_root"] = str(dataset_root)
        st.session_state["ps02_archive_sha256"] = archive_hash
    except Exception as exc:
        st.error(f"Archive validation failed: {exc}")

dataset_root_value = st.session_state.get("ps02_dataset_root")
if dataset_root_value:
    dataset_root = Path(dataset_root_value)
    st.caption(f"Validated dataset directory: {dataset_root.name}")
    try:
        audit_reader = PS02DatasetReader(dataset_root, ocr_enabled=False)
        audit = audit_reader.audit()
        st.session_state["ps02_audit"] = audit

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Primary posts", f"{audit['total_posts']:,}")
        k2.metric("Telegram exports", audit["telegram_export_count"])
        k3.metric("Poster SHA checks", f"{audit['verified_poster_hashes']}/{audit['poster_count']}")
        k4.metric("Missing post media", len(audit["missing_telegram_photos"]) + len(audit["missing_social_photos"]))

        st.subheader("Dataset composition")
        c1, c2, c3 = st.columns(3)
        c1.metric("Telegram", f"{audit['telegram_posts']:,}", f"{audit['telegram_photo_references']} image refs")
        c2.metric("Social posts", f"{audit['social_posts']:,}", f"{audit['social_photo_references']} image refs")
        c3.metric("Unique image files", audit["unique_image_hashes"], f"{audit['jpeg_file_count']} stored copies")

        activity_a, activity_b, activity_c = st.columns(3)
        activity_a.metric("Forwarded Telegram posts", audit["telegram_forwarded_posts"])
        activity_b.metric("Edited Telegram posts", audit["telegram_edited_posts"])
        activity_c.metric("Empty-text Telegram posts", audit["telegram_empty_text_posts"])

        if audit["warnings"]:
            for warning in audit["warnings"]:
                st.warning(warning)
        else:
            st.success("Primary post counts, media references and indexed poster hashes passed the archive audit.")

        with st.expander("Telegram export inventory", expanded=False):
            st.dataframe(pd.DataFrame(audit["telegram_channels"]), use_container_width=True, hide_index=True)
        with st.expander("Social platform breakdown", expanded=False):
            st.dataframe(
                pd.DataFrame([{"Platform": key, "Posts": value} for key, value in audit["social_platforms"].items()]),
                use_container_width=True, hide_index=True
            )
        with st.expander("Starter lexicon (reference only)", expanded=False):
            lexicon_rows = load_starter_lexicon(dataset_root)
            st.caption(f"{len(lexicon_rows)} source terms. Generic/context-dependent terms are not automatically promoted to high-confidence rules.")
            st.dataframe(pd.DataFrame(lexicon_rows), use_container_width=True, hide_index=True)

        if audit["masked_repository_files"]:
            st.info(
                f"Separate masked repository detected: {audit['masked_repository_files']} CSV files, "
                f"{audit['masked_repository_rows']:,} records. It is intentionally excluded from ingestion, "
                "alert scoring and entity correlation; complaint narratives are not displayed."
            )
        if audit["reference_channel_rows"]:
            st.caption(
                f"{audit['reference_channel_rows']} public reference-channel rows are present for background context only. "
                "They are not monitored, contacted or imported."
            )
        if not audit["answer_key_present"]:
            st.caption("No judge-only answer key was supplied; precision/recall and official ground-truth accuracy cannot be calculated.")

        st.divider()
        st.subheader("Import controls")
        run_ocr = st.checkbox("Run multilingual OCR on referenced media (English + Hindi + Marathi)", value=True)
        st.caption("OCR is executed once per unique SHA-256 image. OCR output is stored as analysis metadata; the original message text and media remain preserved separately.")
        st.warning(
            "Importing writes the 1,850 primary posts into the configured SQLite database. "
            "Existing records are not reset. Re-importing the same dataset is idempotent."
        )
        if st.button("Import 1,850 primary posts", type="primary", use_container_width=True):
            reader = PS02DatasetReader(dataset_root, ocr_enabled=run_ocr)
            worker = IngestionWorker(db=Database())
            with st.spinner("Processing posts, identifiers, media hashes, OCR and evidence blocks..."):
                report = reader.import_into_worker(worker)
            st.session_state["ps02_import_report"] = report

        report = st.session_state.get("ps02_import_report")
        if report and report.get("dataset_id") == audit["dataset_id"]:
            st.subheader("Latest import result")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Processed", f"{report['total_records']:,}")
            r2.metric("Inserted", f"{report['inserted']:,}")
            r3.metric("Duplicates", f"{report['duplicates']:,}")
            r4.metric("Failures", f"{report['failures']:,}")
            st.caption(
                f"Provenance: {report['provenance']} · OCR engine: {report['ocr_engine']} · "
                f"OCR-success records: {report['ocr_successes']}"
            )
            if report["errors"]:
                st.error("Some records failed. Review the bounded error list below; do not assume a complete import.")
                st.dataframe(pd.DataFrame(report["errors"]), use_container_width=True, hide_index=True)
            elif report["inserted"] + report["duplicates"] == report["total_records"]:
                st.success("Every primary record was either newly inserted or safely recognized as an existing duplicate.")
    except PS02DatasetError as exc:
        st.error(f"PS02 dataset validation error: {exc}")
    except Exception as exc:
        st.exception(exc)
else:
    st.info("Upload the supplied PS02 ZIP to begin the dataset audit. No data is imported just by uploading.")
