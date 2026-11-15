#Dashboard page, SI for markdown styling and data-ingestion. 
#Used SI for optimization in all OS,screens and browsers
import streamlit as st
import streamlit.components.v1 as components
import os
import json
import base64
import mission_catalog
import flame_lab
import fire_predictor
import research_assistant
import Music
import Authentication
import About
import KnowledgeBase
import contact_us
import combustion_physics
import ambience


#Setting page config for dashboard
st.set_page_config(page_title="Orb.Ignite", layout="wide", initial_sidebar_state="collapsed")


@st.dialog("Help / Metric Guide", width="large")
def show_help_dialog():
    KnowledgeBase.render()


@st.dialog("About Orb.Ignite", width="large")
def show_about_dialog():
    About.render()


@st.dialog("Contact Us", width="small")
def show_contact_dialog():
    contact_us.render()


@st.cache_data(show_spinner=False)
def _load_ms_madi_font_css() -> str:
    font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Fonts", "MsMadi-Regular.ttf")
    if not os.path.exists(font_path):
        return ""
    with open(font_path, "rb") as f:
        b64_font = base64.b64encode(f.read()).decode("ascii")
    src = f"url('data:font/ttf;base64,{b64_font}') format('truetype')"
    return (
        f"@font-face {{ font-family: 'Ms Madi'; src: {src}; font-weight: 100 900; font-style: normal; font-display: swap; }}\n"
        f"@font-face {{ font-family: 'Ms.Maddi'; src: {src}; font-weight: 100 900; font-style: normal; font-display: swap; }}"
    )


_ms_madi_font_css = _load_ms_madi_font_css()
if _ms_madi_font_css:
    st.markdown(f"<style>{_ms_madi_font_css}</style>", unsafe_allow_html=True)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;1,400&family=Inter:wght@300..800&family=Ms+Madi&family=Public+Sans:ital,wght@0,300..900;1,300..900&display=swap');

    html {
        scroll-behavior: smooth;
        -webkit-text-size-adjust: 100%;
        text-size-adjust: 100%;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }

    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {
        overflow-y: auto !important;
        max-height: 100vh !important;
        max-height: 100dvh !important;
        overscroll-behavior: contain !important;
        -webkit-overflow-scrolling: touch !important;
    }

    [data-testid="stSidebarContent"] {
        height: 100vh !important;
        height: 100dvh !important;
        display: flex !important;
        flex-direction: column !important;
    }
    [data-testid="stSidebarHeader"] {
        flex: 0 0 auto !important;
    }
    [data-testid="stSidebarContent"] > div:not([data-testid="stSidebarHeader"]):not([data-testid="stSidebarUserContent"]),
    div[data-testid="stSidebarUserContent"],
    div[data-testid="stSidebarUserContent"] > div,
    div[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"],
    div[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {
        flex: 1 0 auto !important;
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stSidebarUserContent"] {
        overflow: visible !important;
        max-height: none !important;
        padding-bottom: 1rem !important;
    }

    [data-testid="stSidebarContent"]::-webkit-scrollbar {
        width: 6px;
    }
    [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
    }

    .block-container {
        padding-top: calc(4.25rem + env(safe-area-inset-top, 0px)) !important;
        padding-bottom: max(1.5rem, env(safe-area-inset-bottom, 0px)) !important;
        padding-left: max(1rem, env(safe-area-inset-left, 0px)) !important;
        padding-right: max(3.75rem, env(safe-area-inset-right, 0px)) !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Public Sans', 'PublicSans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }

    code, pre, [data-testid="stMetricValue"] {
        font-family: 'DM Mono', 'DMMono', monospace !important;
    }

    .stAppHeader,
    header[data-testid="stHeader"] {
        background-color: #05070B !important;
        height: calc(3.25rem + env(safe-area-inset-top, 0px)) !important;
        min-height: calc(3.25rem + env(safe-area-inset-top, 0px)) !important;
        padding-top: env(safe-area-inset-top, 0px) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        z-index: 99990 !important;
    }
    .stAppHeader button,
    header[data-testid="stHeader"] button,
    .stAppHeader svg,
    header[data-testid="stHeader"] svg {
        color: #E2E8F0 !important;
        fill: currentColor;
    }
    [data-testid="stToolbar"] {
        padding-right: 3.5rem !important;
    }
    [data-testid="stAppDeployButton"],
    [data-testid="stDecoration"],
    [data-testid="InputInstructions"],
    .stInputInstructions,
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
    a, a:visited, a:hover, a:active {
        text-decoration: none !important;
    }
    iframe[height="0"],
    [data-testid="stElementContainer"]:has(iframe[height="0"]),
    .element-container:has(iframe[height="0"]) {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    [data-theme="light"] .stApp,
    .stApp[data-theme="light"],
    [data-base-theme="light"] .stApp {
        --background-color: #F8FAFC;
        --secondary-background-color: #FFFFFF;
        --text-color: #0F172A;
        color: #0F172A !important;
        color-scheme: light;
    }
    [data-theme="light"] .stApp h1,
    [data-theme="light"] .stApp h2,
    [data-theme="light"] .stApp h3,
    [data-theme="light"] .stApp h4,
    [data-theme="light"] .stApp h5,
    [data-theme="light"] .stApp h6,
    [data-theme="light"] .stApp p,
    [data-theme="light"] .stApp li,
    [data-theme="light"] .stApp label,
    [data-theme="light"] .stApp summary,
    [data-theme="light"] .stApp [data-testid="stMetricValue"],
    [data-theme="light"] .stApp [data-testid="stMetricLabel"] {
        color: #0F172A;
    }
    [data-theme="light"] .stApp .orb-brand-tag {
        color: #475569 !important;
    }

    [data-theme="light"] .stApp [data-testid="stExpander"],
    .stApp[data-theme="light"] [data-testid="stExpander"],
    [data-theme="light"] [data-testid="stExpander"],
    [data-theme="light"] .stApp [data-testid="stExpander"] details,
    .stApp[data-theme="light"] [data-testid="stExpander"] details,
    [data-theme="light"] [data-testid="stExpander"] details,
    [data-theme="light"] .stApp [data-testid="stExpander"] summary,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary,
    [data-theme="light"] [data-testid="stExpander"] summary,
    [data-theme="light"] .stApp [data-testid="stExpander"] [data-testid="stExpanderDetails"],
    .stApp[data-theme="light"] [data-testid="stExpander"] [data-testid="stExpanderDetails"],
    [data-theme="light"] [data-testid="stExpander"] [data-testid="stExpanderDetails"],
    [data-theme="light"] .stApp [data-testid="stVerticalBlockBorderWrapper"],
    .stApp[data-theme="light"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-theme="light"] .stApp [data-testid="stVerticalBlockBorderWrapper"] > div,
    .stApp[data-theme="light"] [data-testid="stVerticalBlockBorderWrapper"] > div,
    [data-theme="light"] .stApp [data-testid="stForm"],
    .stApp[data-theme="light"] [data-testid="stForm"],
    [data-theme="light"] .stApp [data-testid="stForm"] > div,
    .stApp[data-theme="light"] [data-testid="stForm"] > div {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border-color: rgba(15, 23, 42, 0.16) !important;
        color: #0F172A !important;
    }
    [data-theme="light"] .stApp [data-testid="stExpander"] summary:hover,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary:hover,
    [data-theme="light"] [data-testid="stExpander"] summary:hover,
    [data-theme="light"] .stApp [data-testid="stExpander"] summary:focus,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary:focus,
    [data-theme="light"] [data-testid="stExpander"] summary:focus {
        background-color: #F8FAFC !important;
        background: #F8FAFC !important;
    }
    [data-theme="light"] .stApp [data-testid="stExpander"] summary,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary,
    [data-theme="light"] [data-testid="stExpander"] summary,
    [data-theme="light"] .stApp [data-testid="stExpander"] summary *,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary *,
    [data-theme="light"] [data-testid="stExpander"] summary *,
    [data-theme="light"] .stApp [data-testid="stExpander"] summary p,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary p,
    [data-theme="light"] [data-testid="stExpander"] summary p,
    [data-theme="light"] .stApp [data-testid="stExpander"] summary span,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary span,
    [data-theme="light"] [data-testid="stExpander"] summary span,
    [data-theme="light"] .stApp [data-testid="stExpander"] summary svg,
    .stApp[data-theme="light"] [data-testid="stExpander"] summary svg,
    [data-theme="light"] [data-testid="stExpander"] summary svg {
        color: #0F172A !important;
        fill: #0F172A !important;
    }

    [data-theme="light"] .stApp [data-testid="stSidebar"],
    .stApp[data-theme="light"] [data-testid="stSidebar"],
    [data-theme="light"] [data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
    }
    [data-theme="light"] [data-testid="stSidebar"] hr,
    .stApp[data-theme="light"] [data-testid="stSidebar"] hr {
        border-color: rgba(15, 23, 42, 0.14) !important;
    }

    [data-theme="light"] .stApp input,
    .stApp[data-theme="light"] input,
    [data-theme="light"] input,
    [data-theme="light"] .stApp textarea,
    .stApp[data-theme="light"] textarea,
    [data-theme="light"] textarea,
    [data-theme="light"] .stApp [data-baseweb="input"],
    .stApp[data-theme="light"] [data-baseweb="input"],
    [data-theme="light"] .stApp [data-baseweb="input"] > div,
    .stApp[data-theme="light"] [data-baseweb="input"] > div,
    [data-theme="light"] .stApp [data-baseweb="base-input"],
    .stApp[data-theme="light"] [data-baseweb="base-input"],
    [data-theme="light"] .stApp [data-baseweb="base-input"] > input,
    .stApp[data-theme="light"] [data-baseweb="base-input"] > input,
    [data-theme="light"] .stApp [data-testid="stTextInputRootElement"],
    .stApp[data-theme="light"] [data-testid="stTextInputRootElement"],
    [data-theme="light"] [data-testid="stTextInputRootElement"],
    [data-theme="light"] .stApp [data-testid="stTextInputRootElement"] > div,
    .stApp[data-theme="light"] [data-testid="stTextInputRootElement"] > div,
    [data-theme="light"] .stApp [data-testid="stTextInputField"],
    .stApp[data-theme="light"] [data-testid="stTextInputField"],
    [data-theme="light"] [data-testid="stTextInputField"],
    [data-theme="light"] .stApp [data-testid="stNumberInputContainer"],
    .stApp[data-theme="light"] [data-testid="stNumberInputContainer"],
    [data-theme="light"] .stApp [data-testid="stNumberInputContainer"] > div,
    .stApp[data-theme="light"] [data-testid="stNumberInputContainer"] > div,
    [data-theme="light"] .stApp [data-baseweb="select"],
    .stApp[data-theme="light"] [data-baseweb="select"],
    [data-theme="light"] .stApp [data-baseweb="select"] > div,
    .stApp[data-theme="light"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border-color: rgba(15, 23, 42, 0.22) !important;
        -webkit-text-fill-color: #0F172A !important;
    }
    [data-theme="light"] .stApp input::placeholder,
    .stApp[data-theme="light"] input::placeholder,
    [data-theme="light"] .stApp textarea::placeholder,
    .stApp[data-theme="light"] textarea::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 0.85 !important;
    }
    [data-theme="light"] .stApp [data-baseweb="input"] svg,
    [data-theme="light"] .stApp [data-baseweb="base-input"] svg,
    [data-theme="light"] .stApp [data-testid="stTextInputRootElement"] svg,
    [data-theme="light"] .stApp [data-baseweb="select"] svg {
        color: #475569 !important;
        fill: currentColor !important;
    }

    [data-theme="light"] .stApp button[kind="primary"],
    [data-theme="light"] .stApp button[kind="primaryFormSubmit"],
    [data-theme="light"] .stApp [data-testid="stBaseButton-primary"],
    [data-theme="light"] .stApp [data-testid="baseButton-primary"],
    .stApp[data-theme="light"] button[kind="primary"],
    .stApp[data-theme="light"] button[kind="primaryFormSubmit"],
    .stApp[data-theme="light"] [data-testid="stBaseButton-primary"],
    .stApp[data-theme="light"] [data-testid="baseButton-primary"] {
        background-color: #EA580C !important;
        background: linear-gradient(180deg, #EA580C 0%, #C2410C 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 1px 3px rgba(194, 65, 12, 0.25) !important;
    }
    [data-theme="light"] .stApp button[kind="primary"] *,
    [data-theme="light"] .stApp button[kind="primary"] p,
    [data-theme="light"] .stApp button[kind="primaryFormSubmit"] *,
    [data-theme="light"] .stApp button[kind="primaryFormSubmit"] p,
    [data-theme="light"] .stApp [data-testid="stBaseButton-primary"] *,
    [data-theme="light"] .stApp [data-testid="stBaseButton-primary"] p,
    [data-theme="light"] .stApp [data-testid="baseButton-primary"] *,
    [data-theme="light"] .stApp [data-testid="baseButton-primary"] p,
    .stApp[data-theme="light"] button[kind="primary"] *,
    .stApp[data-theme="light"] button[kind="primary"] p,
    .stApp[data-theme="light"] button[kind="primaryFormSubmit"] *,
    .stApp[data-theme="light"] button[kind="primaryFormSubmit"] p,
    .stApp[data-theme="light"] [data-testid="stBaseButton-primary"] *,
    .stApp[data-theme="light"] [data-testid="stBaseButton-primary"] p,
    .stApp[data-theme="light"] [data-testid="baseButton-primary"] *,
    .stApp[data-theme="light"] [data-testid="baseButton-primary"] p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    [data-theme="light"] .stApp button[kind="primary"]:hover,
    [data-theme="light"] .stApp [data-testid="stBaseButton-primary"]:hover,
    [data-theme="light"] .stApp [data-testid="baseButton-primary"]:hover,
    .stApp[data-theme="light"] button[kind="primary"]:hover,
    .stApp[data-theme="light"] [data-testid="stBaseButton-primary"]:hover,
    .stApp[data-theme="light"] [data-testid="baseButton-primary"]:hover {
        background-color: #C2410C !important;
        background: #C2410C !important;
        color: #FFFFFF !important;
    }

    [data-theme="light"] .stApp button[kind="secondary"],
    [data-theme="light"] .stApp [data-testid="stBaseButton-secondary"],
    [data-theme="light"] .stApp [data-testid="baseButton-secondary"],
    [data-theme="light"] .stApp [data-testid="stPopover"] > button,
    .stApp[data-theme="light"] button[kind="secondary"],
    .stApp[data-theme="light"] [data-testid="stBaseButton-secondary"],
    .stApp[data-theme="light"] [data-testid="baseButton-secondary"],
    .stApp[data-theme="light"] [data-testid="stPopover"] > button,
    [data-theme="light"] .stApp [data-testid="stFormSubmitButton"] button,
    .stApp[data-theme="light"] [data-testid="stFormSubmitButton"] button,
    [data-theme="light"] [data-testid="stFormSubmitButton"] button,
    [data-theme="light"] .stApp button[kind="secondaryFormSubmit"],
    .stApp[data-theme="light"] button[kind="secondaryFormSubmit"],
    [data-theme="light"] button[kind="secondaryFormSubmit"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid rgba(15, 23, 42, 0.2) !important;
    }
    [data-theme="light"] .stApp button[kind="secondary"] *,
    [data-theme="light"] .stApp button[kind="secondary"] p,
    [data-theme="light"] .stApp [data-testid="stBaseButton-secondary"] *,
    [data-theme="light"] .stApp [data-testid="stBaseButton-secondary"] p,
    [data-theme="light"] .stApp [data-testid="baseButton-secondary"] *,
    [data-theme="light"] .stApp [data-testid="baseButton-secondary"] p,
    .stApp[data-theme="light"] button[kind="secondary"] *,
    .stApp[data-theme="light"] button[kind="secondary"] p,
    .stApp[data-theme="light"] [data-testid="stBaseButton-secondary"] *,
    .stApp[data-theme="light"] [data-testid="stBaseButton-secondary"] p,
    .stApp[data-theme="light"] [data-testid="baseButton-secondary"] *,
    .stApp[data-theme="light"] [data-testid="baseButton-secondary"] p,
    [data-theme="light"] .stApp [data-testid="stFormSubmitButton"] button *,
    .stApp[data-theme="light"] [data-testid="stFormSubmitButton"] button *,
    [data-theme="light"] [data-testid="stFormSubmitButton"] button *,
    [data-theme="light"] .stApp button[kind="secondaryFormSubmit"] *,
    .stApp[data-theme="light"] button[kind="secondaryFormSubmit"] *,
    [data-theme="light"] button[kind="secondaryFormSubmit"] * {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }
    [data-theme="light"] .stApp button[kind="secondary"]:hover,
    [data-theme="light"] .stApp [data-testid="stBaseButton-secondary"]:hover,
    [data-theme="light"] .stApp [data-testid="baseButton-secondary"]:hover,
    .stApp[data-theme="light"] button[kind="secondary"]:hover,
    .stApp[data-theme="light"] [data-testid="stBaseButton-secondary"]:hover,
    .stApp[data-theme="light"] [data-testid="baseButton-secondary"]:hover,
    [data-theme="light"] .stApp [data-testid="stFormSubmitButton"] button:hover,
    .stApp[data-theme="light"] [data-testid="stFormSubmitButton"] button:hover,
    [data-theme="light"] [data-testid="stFormSubmitButton"] button:hover {
        background-color: #F8FAFC !important;
        border-color: #EA580C !important;
        color: #EA580C !important;
    }

    /* Tabs in Light Mode */
    [data-theme="light"] .stApp [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom-color: rgba(15, 23, 42, 0.15) !important;
    }
    [data-theme="light"] .stApp [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #475569 !important;
    }
    [data-theme="light"] .stApp [data-baseweb="tab"][aria-selected="true"] {
        color: #EA580C !important;
        font-weight: 700 !important;
    }
    [data-theme="light"] .stApp [data-baseweb="tab-highlight"] {
        background-color: #EA580C !important;
    }
    [data-theme="light"] .stApp [data-testid="stTabs"] [data-testid="stTabContent"] {
        background-color: transparent !important;
        color: #0F172A !important;
    }

    /* Popovers, Dialogs & Modals */
    [data-theme="light"] .stApp [data-testid="stDialog"] [role="dialog"],
    [data-theme="light"] .stApp [data-testid="stModal"] [role="dialog"],
    [data-theme="light"] .stApp [data-baseweb="popover"],
    [data-theme="light"] .stApp [data-baseweb="popover"] > div,
    [data-theme="light"] .stApp [data-baseweb="menu"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border-color: rgba(15, 23, 42, 0.16) !important;
    }

    [data-theme="light"] .stApp [data-testid="stCaptionContainer"],
    [data-theme="light"] .stApp small {
        color: #475569 !important;
    }
    [data-theme="light"] .stApp code {
        background: rgba(15, 23, 42, 0.06) !important;
        color: #0F172A !important;
        border: 1px solid rgba(15, 23, 42, 0.1) !important;
    }
    [data-theme="light"] .stApp hr {
        border-color: rgba(15, 23, 42, 0.12) !important;
    }
    [data-theme="light"] .stApp [style*="color:#94A3B8"],
    [data-theme="light"] .stApp [style*="color: #94A3B8"],
    [data-theme="light"] .stApp [style*="color:#8C9FB5"],
    [data-theme="light"] .stApp [style*="color: #8C9FB5"] {
        color: #64748B !important;
    }
    [data-theme="light"] .stApp [style*="color:#F87171"],
    [data-theme="light"] .stApp [style*="color: #F87171"] {
        color: #DC2626 !important;
    }
    [data-theme="light"] .stApp [style*="color:#FB923C"],
    [data-theme="light"] .stApp [style*="color: #FB923C"] {
        color: #EA580C !important;
    }
    [data-theme="light"] .stApp [style*="color:#FBBF24"],
    [data-theme="light"] .stApp [style*="color: #FBBF24"] {
        color: #D97706 !important;
    }
    [data-theme="light"] .stApp .orb-section-nav {
        background-color: #FFFFFF !important;
        border: 1px solid rgba(15, 23, 42, 0.12) !important;
    }
    [data-theme="light"] .stApp .orb-section-nav a {
        color: #334155 !important;
    }
    [data-theme="light"] .stApp .orb-section-nav a:hover,
    [data-theme="light"] .stApp .orb-section-nav a:focus {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border-bottom: 2px solid #EA580C !important;
    }
    [data-theme="dark"] .stApp,
    .stApp[data-theme="dark"],
    [data-base-theme="dark"] .stApp {
        --background-color: #0B0F19;
        --secondary-background-color: #131B2E;
        --text-color: #E2E8F0;
        color: #E2E8F0;
        color-scheme: dark;
    }


    .orb-topbar {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin: 0 0 0.4rem 0;
        padding: 0;
    }
    .orb-brand-title {
        font-family: 'Public Sans', 'PublicSans', sans-serif;
        font-weight: 800;
        font-style: italic;
        font-size: clamp(2.4rem, 6.5vw, 5.4rem);
        letter-spacing: 0.03em;
        line-height: 1.1;
        margin: 0;
        display: inline-block;
        background-color: transparent !important;
        background-image: linear-gradient(180deg, #F2A650 0%, #E8672A 55%, #C2410C 100%) !important;
        -webkit-background-clip: text !important;
        background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        color: transparent !important;
        filter: drop-shadow(0 0 16px rgba(232, 103, 42, 0.3));
    }
    [data-theme="dark"] .orb-brand-title,
    .stApp[data-theme="dark"] .orb-brand-title,
    [data-base-theme="dark"] .orb-brand-title {
        background-color: transparent !important;
        background-image: linear-gradient(180deg, #F2A650 0%, #E8672A 55%, #C2410C 100%) !important;
        -webkit-background-clip: text !important;
        background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        color: transparent !important;
        filter: drop-shadow(0 0 16px rgba(232, 103, 42, 0.3)) !important;
    }
    [data-theme="light"] .orb-brand-title,
    .stApp[data-theme="light"] .orb-brand-title,
    [data-base-theme="light"] .orb-brand-title {
        background-color: transparent !important;
        background-image: linear-gradient(180deg, #E8832B 0%, #CF5408 55%, #A63A06 100%) !important;
        -webkit-background-clip: text !important;
        background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        color: transparent !important;
        filter: drop-shadow(0 2px 6px rgba(166, 58, 6, 0.18)) !important;
    }
    .orb-brand-tag {
        font-family: 'DM Mono', 'DMMono', monospace;
        font-size: 0.85rem;
        font-style: italic;
        color: #8C9FB5;
        letter-spacing: 0.04em;
    }


    .orb-section-nav {
        position: -webkit-sticky;
        position: sticky;
        top: calc(3.25rem + env(safe-area-inset-top, 0px));
        z-index: 99;
        display: flex;
        gap: 4px;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        white-space: nowrap;
        background-color: var(--secondary-background-color);
        padding: 6px;
        border-radius: 4px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 1rem;
    }
    .orb-section-nav a {
        font-family: 'Public Sans', 'PublicSans', sans-serif;
        font-weight: 700;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 8px 16px;
        border-radius: 2px;
        text-decoration: none;
        color: inherit;
        flex-shrink: 0;
        border-bottom: 2px solid transparent;
    }
    .orb-section-nav a:hover,
    .orb-section-nav a:focus {
        background-color: var(--background-color);
        border-bottom: 2px solid #FC3D21;
    }
    .orb-section-anchor {
        scroll-margin-top: calc(3.8rem + env(safe-area-inset-top, 0px));
    }
    button[kind="tertiary"][key*="btn_footer_"] p,
    button[data-testid="baseButton-tertiary"] p {
        font-family: 'Public Sans', 'PublicSans', sans-serif !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }
    button[kind="tertiary"][key*="btn_footer_"]:hover p,
    button[data-testid="baseButton-tertiary"]:hover p {
        color: #FC3D21 !important;
    }

    .js-plotly-plot, .plot-container {
        max-width: 100% !important;
    }

    [data-testid="stDataFrame"], [data-testid="stTable"] {
        max-width: 100% !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: calc(4rem + env(safe-area-inset-top, 0px)) !important;
            padding-left: max(0.75rem, env(safe-area-inset-left, 0px)) !important;
            padding-right: max(3rem, env(safe-area-inset-right, 0px)) !important;
        }
        .orb-topbar {
            flex-wrap: wrap;
            gap: 0.25rem;
        }
        .orb-brand-title {
            font-size: clamp(2.4rem, 8vw, 4.2rem) !important;
        }
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.6rem !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: calc(50% - 0.4rem) !important;
            flex: 1 1 calc(50% - 0.4rem) !important;
        }
    }

    @media (max-width: 480px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 2.75rem !important;
        }
        .orb-brand-title {
            font-size: clamp(1.9rem, 8vw, 3rem) !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    /* Metric & Prediction Value Text-Wrapping (Flame Regime, Duration, Droplet K, Hazard) */
    [data-testid="stMetric"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"],
    [data-testid="stMetricDelta"],
    div[data-testid="stMetric"] div,
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] span,
    div[data-testid="stMetric"] p {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        text-overflow: unset !important;
    }
    [data-testid="stMetricValue"] {
        font-size: clamp(1.05rem, 1.8vw, 1.7rem) !important;
        line-height: 1.25 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        line-height: 1.2 !important;
    }

    @media (pointer: coarse) {
        button, [role="button"] {
            min-height: 40px;
        }
        .orb-section-nav a {
            padding: 10px 16px !important;
        }
    }

    
    .orb-sidebar-stars-wrap {
        width: 100%;
        padding: 0.85rem 0 1.5rem 0;
        margin-bottom: 0.25rem;
        display: block;
        box-sizing: border-box;
        pointer-events: none;
        user-select: none;
    }
    .orb-stars-cluster {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
        box-sizing: border-box;
        transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.35s ease;
    }
    .orb-star {
        display: inline-block;
        flex-shrink: 0;
        transform-origin: center center;
        transition: transform 0.38s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease, fill 0.25s ease, stroke 0.25s ease;
    }

    /* Outlined (unfilled) vs Filled stars */
    .orb-star.is-outline path,
    .orb-star.is-outline polygon {
        fill: none !important;
        stroke: currentColor !important;
        stroke-width: 1.6px !important;
        stroke-linejoin: round !important;
        stroke-linecap: round !important;
    }
    .orb-star.is-filled path,
    .orb-star.is-filled polygon {
        fill: currentColor !important;
        stroke: none !important;
    }

    /* Distinct individual rotations and natural offsets */
    .orb-star.star-1 { --base-rot: 12deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(12deg); }
    .orb-star.star-2 { --base-rot: -18deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(-18deg); margin-top: -3px; }
    .orb-star.star-3 { --base-rot: 32deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(32deg); margin-top: 2px; }
    .orb-star.star-4 { --base-rot: -8deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(-8deg); margin-top: -2px; }
    .orb-star.star-5 { --base-rot: 42deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(42deg); margin-top: 3px; }
    .orb-star.star-6 { --base-rot: -28deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(-28deg); margin-top: -3px; }
    .orb-star.star-7 { --base-rot: 20deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(20deg); margin-top: 1px; }
    .orb-star.star-8 { --base-rot: -36deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(-36deg); margin-top: -2px; }
    .orb-star.star-9 { --base-rot: 15deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(15deg); margin-top: 2px; }
    .orb-star.star-10 { --base-rot: -24deg; transform: scale(calc(1 - var(--cord-pull, 0) * 0.96)) rotate(-24deg); margin-top: 0px; }

    
    .orb-cord-pulling .orb-star,
    .orb-stars-tuck .orb-star,
    body.orb-cord-pulling .orb-star,
    body.orb-stars-tuck .orb-star,
    html.orb-cord-pulling .orb-star,
    html.orb-stars-tuck .orb-star {
        transform: scale(0.02) rotate(calc(var(--base-rot, 0deg) + 160deg)) !important;
        opacity: 0 !important;
    }
    .orb-cord-pulling .orb-stars-cluster,
    .orb-stars-tuck .orb-stars-cluster,
    body.orb-cord-pulling .orb-stars-cluster,
    body.orb-stars-tuck .orb-stars-cluster,
    html.orb-cord-pulling .orb-stars-cluster,
    html.orb-stars-tuck .orb-stars-cluster {
        transform: scale(0.2) !important;
        opacity: 0 !important;
    }

    /* Not too glowy - clean, subtle, and elegant */
    /* Dark theme: crisp silver-white with soft faint aura */
    .orb-star,
    [data-theme="dark"] .orb-star,
    .stApp[data-theme="dark"] .orb-star,
    [data-base-theme="dark"] .orb-star {
        color: #E2E8F0 !important;
        filter: drop-shadow(0 0 1.5px rgba(255, 255, 255, 0.45)) !important;
        opacity: 0.88;
    }

    /* Light theme: sleek slate/charcoal without glow */
    [data-theme="light"] .orb-star,
    .stApp[data-theme="light"] .orb-star,
    [data-base-theme="light"] .orb-star {
        color: #334155 !important;
        filter: none !important;
        opacity: 0.82;
    }

    
    [data-testid="stElementContainer"]:has(.orb-sidebar-sig),
    .element-container:has(.orb-sidebar-sig),
    [data-testid="stLayoutWrapper"]:has(.orb-sidebar-sig) {
        margin-top: auto !important;
        width: 100% !important;
    }
    .orb-sidebar-sig {
        font-family: 'Ms Madi', 'Ms.Maddi', cursive !important;
        font-size: clamp(1.42rem, 1.85vw, 1.72rem) !important;
        font-weight: 300 !important;
        font-style: normal !important;
        -webkit-text-stroke: 0px transparent !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale;
        letter-spacing: 0.02em;
        line-height: 1.25;
        text-align: center;
        width: 100%;
        padding: 2rem 0 0.75rem 0;
        user-select: none;
        white-space: nowrap;
        color: #FFFFFF !important;
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.45), 0 0 16px rgba(226, 232, 240, 0.22) !important;
        opacity: 0.94;
    }
    [data-theme="dark"] .orb-sidebar-sig,
    .stApp[data-theme="dark"] .orb-sidebar-sig,
    [data-base-theme="dark"] .orb-sidebar-sig,
    [data-theme="dark"] [data-testid="stSidebar"] .orb-sidebar-sig {
        color: #FFFFFF !important;
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.45), 0 0 16px rgba(226, 232, 240, 0.22) !important;
        opacity: 0.94;
    }
    [data-theme="light"] .orb-sidebar-sig,
    .stApp[data-theme="light"] .orb-sidebar-sig,
    [data-base-theme="light"] .orb-sidebar-sig,
    [data-theme="light"] [data-testid="stSidebar"] .orb-sidebar-sig {
        color: #0F172A !important;
        text-shadow: 0 0 7px rgba(15, 23, 42, 0.24), 0 0 14px rgba(51, 65, 85, 0.14) !important;
        opacity: 0.92;
    }
    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_data(show_spinner=False)
def load_experiments():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "Data", "experiments.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

experiments_data = load_experiments()
combustion_physics.ensure_preset_state()


with st.sidebar:
    st.markdown(
        """
        <div class="orb-sidebar-stars-wrap" aria-hidden="true">
            <div class="orb-stars-cluster">
                <svg class="orb-star is-filled star-1" viewBox="0 0 24 24" width="18" height="18"><path d="M12 1 C12 7.5 7.5 12 1 12 C7.5 12 12 16.5 12 23 C12 16.5 16.5 12 23 12 C16.5 12 12 7.5 12 1 Z"/></svg>
                <svg class="orb-star is-outline star-2" viewBox="0 0 24 24" width="14" height="14"><polygon points="12,1.5 15.1,8.3 22.5,9.2 17,14.3 18.5,21.7 12,18 5.5,21.7 7,14.3 1.5,9.2 8.9,8.3"/></svg>
                <svg class="orb-star is-filled star-3" viewBox="0 0 24 24" width="12" height="12"><path d="M12 1 L14.5 10 L23 12 L14.5 14 L12 23 L9.5 14 L1 12 L9.5 10 Z"/></svg>
                <svg class="orb-star is-outline star-4" viewBox="0 0 24 24" width="17" height="17"><path d="M12 1 L14 7 L21 5 L17 11 L23 12 L17 13 L21 19 L14 17 L12 23 L10 17 L3 19 L7 13 L1 12 L7 11 L3 5 L10 7 Z"/></svg>
                <svg class="orb-star is-filled star-5" viewBox="0 0 24 24" width="15" height="15"><polygon points="12,1.5 14.8,7.5 21.5,7.5 16.5,12 18.5,18.5 12,15 5.5,18.5 7.5,12 2.5,7.5 9.2,7.5"/></svg>
                <svg class="orb-star is-outline star-6" viewBox="0 0 24 24" width="11" height="11"><path d="M12 2 Q12 12 2 12 Q12 12 12 22 Q12 12 22 12 Q12 12 12 2 Z"/></svg>
                <svg class="orb-star is-outline star-7" viewBox="0 0 24 24" width="16" height="16"><path d="M12 1 C12 7.5 7.5 12 1 12 C7.5 12 12 16.5 12 23 C12 16.5 16.5 12 23 12 C16.5 12 12 7.5 12 1 Z"/></svg>
                <svg class="orb-star is-filled star-8" viewBox="0 0 24 24" width="13" height="13"><polygon points="12,1.5 15.1,8.3 22.5,9.2 17,14.3 18.5,21.7 12,18 5.5,21.7 7,14.3 1.5,9.2 8.9,8.3"/></svg>
                <svg class="orb-star is-outline star-9" viewBox="0 0 24 24" width="14" height="14"><path d="M12 1 L14.5 10 L23 12 L14.5 14 L12 23 L9.5 14 L1 12 L9.5 10 Z"/></svg>
                <svg class="orb-star is-filled star-10" viewBox="0 0 24 24" width="16" height="16"><path d="M12 1 L14 7 L21 5 L17 11 L23 12 L17 13 L21 19 L14 17 L12 23 L10 17 L3 19 L7 13 L1 12 L7 11 L3 5 L10 7 Z"/></svg>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 style="font-style: italic !important; font-weight: 500 !important; margin: 0 0 0.5rem 0; font-size: 1.45rem;">Orb.Ignite</h3>',
        unsafe_allow_html=True,
    )
    st.divider()
    scenario_preset = st.selectbox(
        "Environment Preset",
        combustion_physics.PRESET_OPTIONS,
        key="sidebar_env_preset",
        on_change=combustion_physics.on_preset_change,
        args=("sidebar_env_preset",),
    )
    st.divider()
    Authentication.render_sidebar_auth()
    st.markdown('<div class="orb-sidebar-sig">Jugaadnauts </div>', unsafe_allow_html=True)

ambience.render_ambience(scenario_preset)

#Used SI for pull chord
components.html(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        const MOON_SVG = '<svg viewBox="0 0 24 24" width="21" height="21" fill="rgba(226,232,240,0.22)" stroke="#E2E8F0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 6px rgba(226,232,240,0.55));"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        const SUN_SVG = '<svg viewBox="0 0 24 24" width="22" height="22" fill="rgba(245,158,11,0.28)" stroke="#F59E0B" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 7px rgba(245,158,11,0.65));"><circle cx="12" cy="12" r="4.5"/><line x1="12" y1="2" x2="12" y2="4.5"/><line x1="12" y1="19.5" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="6.7" y2="6.7"/><line x1="17.3" y1="17.3" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="4.5" y2="12"/><line x1="19.5" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="6.7" y2="17.3"/><line x1="17.3" y1="6.7" x2="19.07" y2="4.93"/></svg>';

        let st = doc.getElementById('orb-pull-style');
        if (!st) {
            st = doc.createElement('style');
            st.id = 'orb-pull-style';
            doc.head.appendChild(st);
        }
        st.textContent =
            '#orb-pull{position:fixed;top:env(safe-area-inset-top,0px);right:0.85rem;z-index:999999;width:32px;pointer-events:none;display:flex;flex-direction:column;align-items:center;}' +
            '#orb-pull .orb-chain{width:0;border-left:2px dotted #64748B;height:calc(68px + var(--pull,0px));transition:height 0.35s cubic-bezier(0.3,1.6,0.5,1);}' +
            '[data-theme="dark"] #orb-pull .orb-chain{border-left-color:#94A3B8;}' +
            '[data-theme="light"] #orb-pull .orb-chain{border-left-color:#475569;}' +
            '#orb-pc{pointer-events:auto;width:32px;height:32px;margin-top:-2px;padding:0;border:0;background:transparent;cursor:grab;touch-action:none;-webkit-tap-highlight-color:transparent;-webkit-touch-callout:none;user-select:none;-webkit-user-select:none;display:grid;place-items:center;transition:transform 0.2s ease;}' +
            '#orb-pc:active{cursor:grabbing;}' +
            '#orb-pc:hover{transform:scale(1.14);}' +
            '@media(max-width:640px){#orb-pull{right:0.5rem!important;}[data-testid="stToolbar"]{padding-right:3.25rem!important;}}' +
            '@media print{#orb-pull{display:none!important;}}';

        function getTheme() {
            try {
                return window.parent.localStorage.getItem('orb_theme') || 'dark';
            } catch (_) {
                return 'dark';
            }
        }

        function applyTheme(t) {
            try { window.parent.localStorage.setItem('orb_theme', t); } catch (_) {}
            const targets = [
                doc.documentElement,
                doc.body,
                doc.querySelector('.stApp'),
                doc.querySelector('[data-testid="stAppViewContainer"]')
            ];
            targets.forEach((el) => {
                if (el) {
                    el.setAttribute('data-theme', t);
                    el.setAttribute('data-base-theme', t);
                }
            });
            if (doc.documentElement) {
                doc.documentElement.style.colorScheme = t;
            }
            const btn = doc.getElementById('orb-pc');
            if (btn) {
                btn.innerHTML = t === 'light' ? SUN_SVG : MOON_SVG;
            }
        }

        function flip() {
            const next = getTheme() === 'light' ? 'dark' : 'light';
            applyTheme(next);
        }

        if (!doc.getElementById('orb-pull')) {
            const pl = doc.createElement('div');
            pl.id = 'orb-pull';
            pl.innerHTML = '<div class="orb-chain"></div><button id="orb-pc" type="button" aria-label="Toggle theme"></button>';
            doc.body.appendChild(pl);

            const ch = pl.querySelector('.orb-chain');
            const pc = pl.querySelector('#orb-pc');
            let y0 = null;
            let dy = 0;

            const triggerTuck = () => {
                try {
                    doc.body.classList.add('orb-stars-tuck');
                    doc.documentElement.classList.add('orb-stars-tuck');
                    setTimeout(() => {
                        doc.body.classList.remove('orb-stars-tuck');
                        doc.documentElement.classList.remove('orb-stars-tuck');
                    }, 450);
                } catch (_) {}
            };

            const rest = () => {
                y0 = null;
                ch.style.transition = '';
                ch.style.setProperty('--pull', '0px');
                try {
                    doc.documentElement.style.setProperty('--cord-pull', '0');
                    doc.body.classList.remove('orb-cord-pulling');
                    doc.documentElement.classList.remove('orb-cord-pulling');
                } catch (_) {}
            };
            pc.onpointerdown = (e) => {
                y0 = e.clientY;
                dy = 0;
                try { pc.setPointerCapture(e.pointerId); } catch (_) {}
                ch.style.transition = 'none';
                try {
                    doc.body.classList.add('orb-cord-pulling');
                    doc.documentElement.classList.add('orb-cord-pulling');
                } catch (_) {}
            };
            pc.onpointermove = (e) => {
                if (y0 === null) return;
                dy = Math.max(0, Math.min(90, e.clientY - y0));
                ch.style.setProperty('--pull', dy + 'px');
                const ratio = Math.min(1, dy / 45);
                try {
                    doc.documentElement.style.setProperty('--cord-pull', ratio.toFixed(3));
                } catch (_) {}
            };
            pc.onpointerup = () => {
                if (y0 === null) return;
                const go = dy >= 22 || dy < 4;
                rest();
                if (go) {
                    triggerTuck();
                    flip();
                }
            };
            pc.onpointercancel = rest;
            pc.onclick = (e) => {
                if (e.detail === 0) {
                    triggerTuck();
                    flip();
                }
            };
        }

        applyTheme(getTheme());

        try {
            const metaDefs = [
                { name: 'description', content: '𝘕𝘰𝘵 𝘢𝘭𝘭 𝘧𝘭𝘢𝘮𝘦𝘴 𝘢𝘳𝘦 𝘮𝘦𝘢𝘯𝘵 𝘵𝘰 𝘣𝘦 𝘧𝘭𝘰𝘸𝘯 𝘵𝘰𝘰 𝘤𝘭𝘰𝘴𝘦 𝘵𝘰.' },
                { property: 'og:title', content: 'Orb.Ignite' },
                { property: 'og:description', content: '𝘕𝘰𝘵 𝘢𝘭𝘭 𝘧𝘭𝘢𝘮𝘦𝘴 𝘢𝘳𝘦 𝘮𝘦𝘢𝘯𝘵 𝘵𝘰 𝘣𝘦 𝘧𝘭𝘰𝘸𝘯 𝘵𝘰𝘰 𝘤𝘭𝘰𝘴𝘦 𝘵𝘰.' },
                { property: 'og:url', content: 'https://orbignite.earth' },
                { property: 'og:site_name', content: 'Orb.Ignite' },
                { name: 'twitter:title', content: 'Orb.Ignite' },
                { name: 'twitter:description', content: '𝘕𝘰𝘵 𝘢𝘭𝘭 𝘧𝘭𝘢𝘮𝘦𝘴 𝘢𝘳𝘦 𝘮𝘦𝘢𝘯𝘵 𝘵𝘰 𝘣𝘦 𝘧𝘭𝘰𝘸𝘯 𝘵𝘰𝘰 𝘤𝘭𝘰𝘴𝘦 𝘵𝘰.' }
            ];
            metaDefs.forEach(m => {
                const sel = m.name ? `meta[name="${m.name}"]` : `meta[property="${m.property}"]`;
                let el = doc.querySelector(sel);
                if (!el) {
                    el = doc.createElement('meta');
                    if (m.name) el.setAttribute('name', m.name);
                    if (m.property) el.setAttribute('property', m.property);
                    doc.head.appendChild(el);
                }
                el.setAttribute('content', m.content);
            });
            doc.title = 'Orb.Ignite';
        } catch (_) {}
    })();
    </script>
    """,
    height=0,
)

admin_portal_open = st.session_state.get("show_admin_portal", False)


col_hdr, col_music = st.columns([8, 2])
with col_hdr:
    st.markdown(
        """
        <div class="orb-topbar">
            <span class="orb-brand-title">Orb.Ignite</span>
            <span class="orb-brand-tag"><em>Orbiting the Flames of Flight.</em></span>
        </div>
        """,
        unsafe_allow_html=True
    )
with col_music:
    Music.render_header_player()


if admin_portal_open:
    Authentication.render_admin_portal()
else:
    st.markdown(
        """
        <nav class="orb-section-nav">
            <a href="#mission-catalog">Mission Catalog</a>
            <a href="#flame-lab">3D Flame Lab</a>
            <a href="#fire-predictor">Fire Predictor</a>
            <a href="#research-assistant">Research Assistant</a>
        </nav>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div id="mission-catalog" class="orb-section-anchor"></div>', unsafe_allow_html=True)
    mission_catalog.render(experiments_data)
    st.divider()

    st.markdown('<div id="flame-lab" class="orb-section-anchor"></div>', unsafe_allow_html=True)
    flame_lab.render()
    st.divider()

    st.markdown('<div id="fire-predictor" class="orb-section-anchor"></div>', unsafe_allow_html=True)
    fire_predictor.render()
    st.divider()

    st.markdown('<div id="research-assistant" class="orb-section-anchor"></div>', unsafe_allow_html=True)
    research_assistant.render()

    st.divider()

    if "active_footer_view" not in st.session_state:
        st.session_state["active_footer_view"] = None

    f_col1, _, f_col2 = st.columns([1.5, 7.0, 1.5])
    with f_col1:
        if st.button("About Us", key="btn_footer_about", use_container_width=True):
            st.session_state["active_footer_view"] = "about" if st.session_state.get("active_footer_view") != "about" else None
            st.rerun()
    with f_col2:
        if st.button("Contact Us", key="btn_footer_contact", use_container_width=True):
            st.session_state["active_footer_view"] = "contact" if st.session_state.get("active_footer_view") != "contact" else None
            st.rerun()

    active_view = st.session_state.get("active_footer_view")
    if active_view:
        with st.container(border=True):
            c_head, c_close = st.columns([10, 2])
            with c_close:
                if st.button("Close Panel", key="btn_close_footer_view", use_container_width=True):
                    st.session_state["active_footer_view"] = None
                    st.rerun()
            with c_head:
                if active_view == "about":
                    About.render()
                elif active_view == "contact":
                    contact_us.render()

    st.markdown(
        """
        <div style="text-align: center; margin-top: 2.5rem; margin-bottom: 0.75rem; font-size: 0.82rem; color: #8C9FB5; font-style: italic; letter-spacing: 0.02em; line-height: 1.6;">
            <div style="margin-bottom: 0.85rem;">Afterall...</div>
            <div>Not all flames are meant to be flown too close to.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


