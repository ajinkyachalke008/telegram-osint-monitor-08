"""Centralized Design System & Theme Engine for PS02 OSINT Law Enforcement Dashboard.

Provides:
1. Unified elite dark-command cyber styling (colors, typography, elevation, micro-interactions).
2. Consistent Plotly chart theming.
3. Reusable UI components (KPI cards, section headers, hash containers, badge pills).
4. Responsive desktop/tablet/mobile optimizations and reduced-motion accessibility.
"""

from typing import Optional, Dict, Any, List
import streamlit as st
import plotly.graph_objects as go

# Master Color Palette
PALETTE = {
    "bg_main": "#080C14",
    "bg_surface": "#0E1424",
    "bg_card": "#121A2D",
    "bg_card_hover": "#17223B",
    "border_subtle": "#1E2B45",
    "border_glow": "rgba(0, 173, 181, 0.35)",
    "cyan": "#00ADB5",
    "cyan_bright": "#00E5FF",
    "blue": "#3B82F6",
    "purple": "#8B5CF6",
    "green": "#10B981",
    "amber": "#F59E0B",
    "red": "#FF3366",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
}


def inject_theme():
    """Inject master CSS design system into current Streamlit page."""
    st.markdown("""
    <style>
        /* Base typography & dark canvas */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #080C14 !important;
            color: #F1F5F9 !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Monospace font stack for technical metadata & hashes */
        code, pre, .mono-text, .hash-text {
            font-family: "JetBrains Mono", "SF Mono", Consolas, "Courier New", monospace !important;
        }

        /* Sidebar Command Rail */
        [data-testid="stSidebar"] {
            background-color: #0A0F1D !important;
            border-right: 1px solid #162238 !important;
        }
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3 {
            color: #F1F5F9 !important;
            letter-spacing: -0.01em;
        }
        [data-testid="stSidebarNav"] {
            padding-top: 8px;
        }
        [data-testid="stSidebarNav"] a {
            border-radius: 6px !important;
            padding: 8px 12px !important;
            color: #94A3B8 !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            margin-bottom: 2px !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(0, 173, 181, 0.12) !important;
            color: #00E5FF !important;
            transform: translateX(3px);
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, rgba(0, 173, 181, 0.22) 0%, rgba(0, 173, 181, 0.05) 100%) !important;
            color: #00E5FF !important;
            font-weight: 700 !important;
            border-left: 3px solid #00ADB5 !important;
        }

        /* Streamlit Native Metric Cards */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #0F172A 0%, #131E34 100%) !important;
            border: 1px solid #1E2B45 !important;
            border-radius: 8px !important;
            padding: 14px 18px !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        [data-testid="stMetric"]:hover {
            border-color: rgba(0, 173, 181, 0.4) !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 173, 181, 0.12) !important;
        }
        [data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
        }
        [data-testid="stMetricValue"] {
            color: #F8FAFC !important;
            font-weight: 700 !important;
            font-size: 26px !important;
            line-height: 1.15 !important;
        }

        /* Buttons & Interactive Controls */
        .stButton > button {
            background: linear-gradient(135deg, #0F1B2F 0%, #14243F 100%) !important;
            color: #E2E8F0 !important;
            border: 1px solid #233554 !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            padding: 8px 16px !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .stButton > button:hover {
            border-color: #00ADB5 !important;
            color: #00E5FF !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(0, 173, 181, 0.25) !important;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #00ADB5 0%, #00897B 100%) !important;
            color: #080C14 !important;
            font-weight: 700 !important;
            border: none !important;
        }
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #00E5FF 0%, #00ADB5 100%) !important;
            color: #05080F !important;
            box-shadow: 0 4px 20px rgba(0, 229, 255, 0.4) !important;
        }

        /* Tabs styling */
        [data-testid="stTabs"] button[role="tab"] {
            color: #94A3B8 !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            padding: 10px 18px !important;
            border-radius: 6px 6px 0 0 !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stTabs"] button[role="tab"]:hover {
            color: #00E5FF !important;
            background-color: rgba(0, 173, 181, 0.08) !important;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #00E5FF !important;
            border-bottom: 2px solid #00ADB5 !important;
            background: linear-gradient(180deg, rgba(0, 173, 181, 0.12) 0%, rgba(0, 173, 181, 0.02) 100%) !important;
        }

        /* Form Inputs, Selectboxes, Multiselects */
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stTextInput input {
            background-color: #0C1220 !important;
            border: 1px solid #1E2B45 !important;
            border-radius: 6px !important;
            color: #E2E8F0 !important;
            transition: border-color 0.2s ease !important;
        }
        .stSelectbox div[data-baseweb="select"] > div:focus-within,
        .stMultiSelect div[data-baseweb="select"] > div:focus-within,
        .stTextInput input:focus {
            border-color: #00ADB5 !important;
            box-shadow: 0 0 0 1px #00ADB5 !important;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            background-color: #0D1424 !important;
            border: 1px solid #1A263D !important;
            border-radius: 8px !important;
            margin-bottom: 10px !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stExpander"]:hover {
            border-color: rgba(0, 173, 181, 0.35) !important;
        }

        /* DataTables */
        [data-testid="stDataFrame"] {
            background-color: #0C1220 !important;
            border: 1px solid #1A263D !important;
            border-radius: 8px !important;
        }

        /* Alert Cards (Severity Edge Indicators) */
        .threat-card-high {
            background: linear-gradient(135deg, #180D12 0%, #201118 100%);
            border: 1px solid #3B1B25;
            border-left: 4px solid #FF3366;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(255, 51, 102, 0.08);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .threat-card-high:hover {
            border-color: #5C2535;
            border-left-color: #FF3366;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(255, 51, 102, 0.16);
        }

        .threat-card-med {
            background: linear-gradient(135deg, #17140B 0%, #221D0E 100%);
            border: 1px solid #3D3316;
            border-left: 4px solid #FFAA00;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(255, 170, 0, 0.08);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .threat-card-med:hover {
            border-color: #5E4E1F;
            border-left-color: #FFAA00;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(255, 170, 0, 0.16);
        }

        .threat-card-low {
            background: linear-gradient(135deg, #0A1616 0%, #0F2020 100%);
            border: 1px solid #163638;
            border-left: 4px solid #00ADB5;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(0, 173, 181, 0.08);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .threat-card-low:hover {
            border-color: #1F4F52;
            border-left-color: #00E5FF;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 173, 181, 0.16);
        }

        /* Sleek Badge Pills */
        .badge-pill {
            display: inline-flex;
            align-items: center;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11.5px;
            font-weight: 600;
            letter-spacing: 0.02em;
            margin-right: 6px;
            margin-bottom: 4px;
        }
        .badge-upi { background-color: rgba(255, 211, 105, 0.12); color: #FFD369; border: 1px solid rgba(255, 211, 105, 0.35); }
        .badge-phone { background-color: rgba(255, 87, 34, 0.12); color: #FF8A80; border: 1px solid rgba(255, 87, 34, 0.35); }
        .badge-crypto { background-color: rgba(156, 39, 176, 0.14); color: #EA80FC; border: 1px solid rgba(156, 39, 176, 0.4); }
        .badge-user { background-color: rgba(33, 150, 243, 0.12); color: #82B1FF; border: 1px solid rgba(33, 150, 243, 0.35); }
        .badge-source { background-color: rgba(148, 163, 184, 0.12); color: #CBD5E1; border: 1px solid rgba(148, 163, 184, 0.3); }
        .badge-verified { background-color: rgba(16, 185, 129, 0.14); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }

        /* Cryptographic Evidence & Hash Containers */
        .hash-container {
            background-color: #080D18;
            border: 1px solid #18253D;
            border-radius: 6px;
            padding: 10px 14px;
            font-family: "JetBrains Mono", Consolas, monospace;
            font-size: 12px;
            color: #38BDF8;
            word-break: break-all;
            line-height: 1.45;
            margin: 6px 0 12px 0;
        }

        /* Generic Intelligence Card */
        .intel-card {
            background: linear-gradient(135deg, #0E1628 0%, #131E35 100%);
            border: 1px solid #1C2B47;
            border-radius: 8px;
            padding: 18px 22px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            margin-bottom: 16px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .intel-card:hover {
            border-color: rgba(0, 173, 181, 0.4);
            transform: translateY(-2px);
        }

        /* Reduced motion accessibility */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation: none !important;
                transition: none !important;
                transform: none !important;
            }
        }

        /* Mobile responsiveness adjustments */
        @media (max-width: 768px) {
            [data-testid="stMetric"] {
                padding: 10px 12px !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 20px !important;
            }
            .hash-container {
                font-size: 11px;
                padding: 8px 10px;
            }
        }
    </style>
    """, unsafe_allow_html=True)


def apply_plotly_theme(fig: go.Figure, height: Optional[int] = None, showgrid: bool = False) -> go.Figure:
    """Applies cohesive, sophisticated dark cyber theme to Plotly figures."""
    grid_color = "rgba(255, 255, 255, 0.06)" if showgrid else "rgba(0, 0, 0, 0)"
    
    layout_update = dict(
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="#0A0F1D",
        font=dict(
            family='Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color="#E2E8F0",
            size=12,
        ),
        title=dict(
            font=dict(
                family='Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                color="#F8FAFC",
                size=15,
            )
        ),
        xaxis=dict(
            showgrid=showgrid,
            gridcolor=grid_color,
            zeroline=False,
            color="#94A3B8",
            tickfont=dict(size=11, color="#94A3B8"),
        ),
        yaxis=dict(
            showgrid=showgrid,
            gridcolor=grid_color,
            zeroline=False,
            color="#94A3B8",
            tickfont=dict(size=11, color="#94A3B8"),
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#00ADB5",
            font=dict(
                family='Inter, -apple-system, sans-serif',
                size=12,
                color="#FFFFFF",
            ),
        ),
        margin=dict(l=15, r=15, t=45, b=25),
    )
    if height:
        layout_update["height"] = height
        
    fig.update_layout(**layout_update)
    return fig


def render_kpi_card(
    title: str,
    value: Any,
    subtitle: Optional[str] = None,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    icon: Optional[str] = None,
) -> str:
    """Returns HTML for an elite dark-command KPI card."""
    icon_html = f"<span style='font-size:18px; margin-right:6px;'>{icon}</span>" if icon else ""
    delta_style = ""
    if delta:
        d_color = "#10B981" if delta_color == "green" else ("#FF3366" if delta_color == "red" else "#00ADB5")
        delta_style = f"<div style='font-size:11.5px; color:{d_color}; font-weight:600; margin-top:3px;'>{delta}</div>"

    sub_html = f"<div style='color:#64748B; font-size:11.5px; margin-top:2px;'>{subtitle}</div>" if subtitle else ""

    return f"""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #131E34 100%); border: 1px solid #1E2B45; border-radius: 8px; padding: 14px 18px; box-shadow: 0 4px 14px rgba(0,0,0,0.35); text-align: left; transition: all 0.2s ease;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
            <span style="color:#94A3B8; font-size:11.5px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em;">
                {title}
            </span>
            {icon_html}
        </div>
        <div style="color:#F8FAFC; font-weight:700; font-size:26px; line-height:1.15;">
            {value}
        </div>
        {delta_style}
        {sub_html}
    </div>
    """
