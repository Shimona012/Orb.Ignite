#Dashboard page, SI for markdown styling and data-ingestion. 
import streamlit as st
import os
import base64
import json
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
import importlib
import sys

def _reload_updated_modules():
    mods = [
        combustion_physics,
        mission_catalog,
        flame_lab,
        fire_predictor,
        research_assistant,
        Music,
        Authentication,
        About,
        KnowledgeBase,
        contact_us,
        ambience,
    ]
    tracked = st.session_state.setdefault("_module_mtimes", {})
    for m in mods:
        m_file = getattr(m, "__file__", None)
        if m_file and os.path.exists(m_file):
            mtime = os.path.getmtime(m_file)
            prev = tracked.get(m.__name__)
            if prev is None:
                tracked[m.__name__] = mtime
            elif mtime > prev:
                importlib.reload(sys.modules[m.__name__])
                tracked[m.__name__] = mtime

_reload_updated_modules()



@st.dialog("Help / Metric Guide", width="large")
def show_help_dialog():
    KnowledgeBase.render()


@st.dialog("About Orb.Ignite", width="large")
def show_about_dialog():
    About.render()


@st.dialog("Contact Us", width="small")
def show_contact_dialog():
    contact_us.render()

#Setting page config for dashboard
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="collapsed")

#Brand guidlines and typography
def load_font_b64(rel_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, "Fonts", rel_path)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

font_public_sans = load_font_b64("PublicSans-VariableFont_wght.ttf")
font_inter = load_font_b64("Inter-VariableFont_opsz,wght.ttf")
font_dm_mono = load_font_b64("DMMono-Regular.ttf")

st.markdown(
    f"""
    <style>
    @font-face {{
        font-family: 'PublicSans';
        src: url(data:font/truetype;charset=utf-8;base64,{font_public_sans}) format('truetype');
        font-weight: 100 900;
        font-style: normal;
    }}
    @font-face {{
        font-family: 'Inter';
        src: url(data:font/truetype;charset=utf-8;base64,{font_inter}) format('truetype');
        font-weight: 100 900;
        font-style: normal;
    }}
    @font-face {{
        font-family: 'DMMono';
        src: url(data:font/truetype;charset=utf-8;base64,{font_dm_mono}) format('truetype');
        font-weight: 400;
        font-style: normal;
    }}

    html {{
        scroll-behavior: smooth;
        -webkit-text-size-adjust: 100%;
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}


    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: 'PublicSans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}

    code, pre, [data-testid="stMetricValue"] {{
        font-family: 'DMMono', monospace !important;
    }}


    .stAppHeader {{
        background-color: transparent;
    }}


    .orb-topbar {{
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin: 0 0 0.4rem 0;
        padding: 0;
    }}
    .orb-brand-title {{
        font-family: 'PublicSans', sans-serif;
        font-weight: 800;
        font-style: italic;
        font-size: 5.4rem;
        color: #CF5408;
        letter-spacing: 0.03em;
        line-height: 1.1;
        margin: 0;
    }}
    .orb-brand-tag {{
        font-family: 'DMMono', monospace;
        font-size: 0.72rem;
        color: #8C9FB5;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}


    .orb-section-nav {{
        position: -webkit-sticky;
        position: sticky;
        top: 0;
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
    }}
    .orb-section-nav a {{
        font-family: 'PublicSans', sans-serif;
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
    }}
    .orb-section-nav a:hover,
    .orb-section-nav a:focus {{
        background-color: var(--background-color);
        border-bottom: 2px solid #FC3D21;
    }}
    .orb-section-anchor {{
        scroll-margin-top: 3.5rem;
    }}
    button[kind="tertiary"][key*="btn_footer_"] p,
    button[data-testid="baseButton-tertiary"] p {{
        font-family: 'PublicSans', sans-serif !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }}
    button[kind="tertiary"][key*="btn_footer_"]:hover p,
    button[data-testid="baseButton-tertiary"]:hover p {{
        color: #FC3D21 !important;
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 1rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }}
        .orb-topbar {{
            flex-wrap: wrap;
            gap: 0.25rem;
        }}
        [data-testid="stHorizontalBlock"] {{
            flex-direction: column;
            gap: 0.5rem;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_data
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
    st.markdown("### Orb.Ignite")
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

ambience.render_ambience(scenario_preset)

admin_portal_open = st.session_state.get("show_admin_portal", False)


col_hdr, col_music = st.columns([8, 2])
with col_hdr:
    st.markdown(
        """
        <div class="orb-topbar">
            <span class="orb-brand-title">Orb.Ignite</span>
            <span class="orb-brand-tag">TO BE ADDED TAGLINE</span>
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

    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 3.0])
    with f_col1:
        if st.button("About Us", key="btn_footer_about", use_container_width=True):
            st.session_state["active_footer_view"] = "about" if st.session_state.get("active_footer_view") != "about" else None
            st.rerun()
    with f_col2:
        if st.button("Contact Us", key="btn_footer_contact", use_container_width=True):
            st.session_state["active_footer_view"] = "contact" if st.session_state.get("active_footer_view") != "contact" else None
            st.rerun()
    with f_col3:
        st.caption("Click any button above to view platform mission or get in touch.")

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


