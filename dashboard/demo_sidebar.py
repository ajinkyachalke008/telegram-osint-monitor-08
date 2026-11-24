"""Reusable Sidebar Demo Maintenance Component for Streamlit Dashboard.

Visible ONLY when DEMO_MODE=1.
Provides evaluator actions:
- 'Inject scripted demo post'
- 'Wipe & Reseed Demo Database'
"""
import os
import streamlit as st
from ingestion.demo_injector import inject_scripted_demo_post
from scripts.generate_demo_data import seed_demo_database
from core.models import now_utc_iso


def render_demo_maintenance_sidebar(db=None):
    """Render Demo Maintenance sidebar controls when DEMO_MODE=1."""
    if os.environ.get("DEMO_MODE") != "1":
        return

    st.sidebar.divider()
    st.sidebar.markdown("🛠️ **Demo Maintenance (`DEMO_MODE=1`)**")

    if st.sidebar.button("💉 Inject scripted demo post", use_container_width=True, key="btn_inject_scripted_demo"):
        res = inject_scripted_demo_post(db)
        st.sidebar.success(f"Injected! Sealed at Block #{res['block_height']}")
        st.toast(f"🚨 Scripted demo post injected! Sealed at Block #{res['block_height']}", icon="💉")
        st.rerun()

    confirm_reset = st.sidebar.checkbox("Confirm database reset & reseed", key="confirm_demo_reset")
    if confirm_reset:
        if st.sidebar.button("🚨 Wipe & Reseed Demo Database", use_container_width=True, key="btn_reset_demo_db"):
            seed_demo_database(db=db, reset=True)
            if db:
                db.log_audit("demo_reset_executed", {
                    "confirmed": True,
                    "actor": "evaluator_ui",
                    "env_demo_mode": "1",
                    "timestamp": now_utc_iso()
                })
            st.toast("✅ Demo reset successfully! Baseline records and evidence chain reseeded.", icon="🔄")
            st.rerun()
