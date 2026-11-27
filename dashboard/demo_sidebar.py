"""Reusable Sidebar Demo Maintenance Component for Streamlit Dashboard.

Visible ONLY when DEMO_MODE=1.
Provides evaluator actions:
- 'Inject scripted demo post'
- 'Wipe & Reseed Demo Database'
Refined with elite cyber-command styling and protective confirmation.
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

    st.sidebar.markdown("""
    <div style="border-top: 1px solid #1A2840; margin: 16px 0 12px 0; padding-top: 12px;">
        <span style="background-color: rgba(0, 173, 181, 0.15); color: #00E5FF; border: 1px solid rgba(0, 173, 181, 0.35); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase;">
            🛠️ EVALUATOR TOOLS
        </span>
        <div style="color: #64748B; font-size: 11.5px; margin-top: 4px;">Simulation &amp; Stream Injection Controls</div>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("💉 Inject Scripted Threat Post", use_container_width=True, key="btn_inject_scripted_demo"):
        res = inject_scripted_demo_post(db)
        st.sidebar.success(f"Injected! Sealed at Block #{res['block_height']}")
        st.toast(f"🚨 Scripted demo post injected! Sealed at Block #{res['block_height']}", icon="💉")
        st.rerun()

    confirm_reset = st.sidebar.checkbox("Enable database reset & reseed", key="confirm_demo_reset")
    if confirm_reset:
        if st.sidebar.button("🚨 Wipe & Reseed Demo DB", use_container_width=True, key="btn_reset_demo_db", type="primary"):
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
