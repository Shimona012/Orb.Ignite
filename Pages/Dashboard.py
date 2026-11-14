#Dashboard page, WIP, SI for markdown styling and data-ingestion. 
import streamlit as st
import os
import base64
import json
import mission_catalog
import flame_lab
import fire_predictor
import research_assistant
import Music
#Will import other modules as they are developed.

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

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Tighten top padding so title above tabs doesn't push content down */
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

    /* Compact Orb.Ignite Title above Tabs */
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
        font-size: 1.4rem;
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

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background-color: var(--secondary-background-color);
        padding: 4px;
        border-radius: 4px;
        border: 1px solid rgba(128, 128, 128, 0.25);
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'PublicSans', sans-serif;
        font-weight: 700;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 8px 16px;
        border-radius: 2px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: var(--background-color) !important;
        border-bottom: 2px solid #FC3D21 !important;
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


with st.sidebar:
    st.markdown("### Orb.Ignite")
    st.divider()
    scenario_preset = st.selectbox(
        "Environment Preset",
        ["ISS Microgravity (0g)", "Lunar Gateway (0.16g)", "Mars Habitat (0.38g)", "Earth Lab (1.0g)", "Custom"],
        index=0
    )
    st.divider()


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


tab_catalog, tab_lab, tab_predictor, tab_assistant = st.tabs([
    "Mission Catalog",
    "3D Flame Lab",
    "Fire Predictor",
    "Research Assistant"
])

with tab_catalog:
    mission_catalog.render(experiments_data)

with tab_lab:
    flame_lab.render()

with tab_predictor:
    fire_predictor.render()

with tab_assistant:
    research_assistant.render()
