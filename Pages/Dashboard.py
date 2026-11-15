#Dashboard page, SI for markdown styling and data-ingestion. 
import streamlit as st
import streamlit.components.v1 as components
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

    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebarContent"],
    div[data-testid="stSidebarUserContent"] {{
        overflow-y: auto !important;
        max-height: 100vh !important;
        overscroll-behavior: contain !important;
        -webkit-overflow-scrolling: touch !important;
    }}

    [data-testid="stSidebarContent"]::-webkit-scrollbar {{
        width: 6px;
    }}
    [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
    }}
    [data-testid="stSidebarContent"] > div:first-child {{
        padding-bottom: 4rem !important;
    }}


    .block-container {{
        padding-top: 4rem !important;
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

    .stAppHeader,
    header[data-testid="stHeader"] {{
        background-color: #05070B !important;
        height: 3.25rem !important;
        min-height: 3.25rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        z-index: 99990 !important;
    }}
    .stAppHeader button,
    header[data-testid="stHeader"] button,
    .stAppHeader svg,
    header[data-testid="stHeader"] svg {{
        color: #E2E8F0 !important;
        fill: currentColor;
    }}
    [data-testid="stToolbar"] {{
        padding-right: 3.5rem !important;
    }}
    [data-testid="stAppDeployButton"],
    [data-testid="stDecoration"] {{
        display: none !important;
    }}
    a, a:visited, a:hover, a:active {{
        text-decoration: none !important;
    }}
    iframe[height="0"],
    [data-testid="stElementContainer"]:has(iframe[height="0"]),
    .element-container:has(iframe[height="0"]) {{
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    [data-theme="light"] .stApp,
    .stApp[data-theme="light"],
    [data-base-theme="light"] .stApp {{
        --background-color: #F8FAFC;
        --secondary-background-color: #FFFFFF;
        --text-color: #0F172A;
        color: #0F172A !important;
        color-scheme: light;
    }}
    [data-theme="light"] .stApp h1,
    [data-theme="light"] .stApp h2,
    [data-theme="light"] .stApp h3,
    [data-theme="light"] .stApp h4,
    [data-theme="light"] .stApp h5,
    [data-theme="light"] .stApp h6,
    [data-theme="light"] .stApp p,
    [data-theme="light"] .stApp li,
    [data-theme="light"] .stApp label,
    [data-theme="light"] .stApp [data-testid="stMetricValue"],
    [data-theme="light"] .stApp [data-testid="stMetricLabel"] {{
        color: #0F172A;
    }}
    [data-theme="light"] .stApp .orb-brand-tag {{
        color: #475569 !important;
    }}
    [data-theme="light"] .stApp [data-testid="stExpander"],
    [data-theme="light"] .stApp [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(255, 255, 255, 0.85) !important;
        border-color: rgba(15, 23, 42, 0.14) !important;
    }}
    [data-theme="light"] .stApp [data-testid="stSidebar"] {{
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
    }}
    [data-theme="light"] .stApp [data-baseweb="select"] > div,
    [data-theme="light"] .stApp [data-baseweb="input"] > div,
    [data-theme="light"] .stApp [data-baseweb="base-input"] > input,
    [data-theme="light"] .stApp textarea {{
        background-color: rgba(255, 255, 255, 0.94) !important;
        color: #0F172A !important;
        border-color: rgba(15, 23, 42, 0.18) !important;
    }}
    [data-theme="light"] .stApp button[kind="secondary"],
    [data-theme="light"] .stApp [data-testid="stPopover"] > button {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #0F172A !important;
        border-color: rgba(15, 23, 42, 0.18) !important;
    }}
    [data-theme="dark"] .stApp,
    .stApp[data-theme="dark"],
    [data-base-theme="dark"] .stApp {{
        --background-color: #0B0F19;
        --secondary-background-color: #131B2E;
        --text-color: #E2E8F0;
        color: #E2E8F0;
        color-scheme: dark;
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
        font-size: 0.85rem;
        font-style: italic;
        color: #8C9FB5;
        letter-spacing: 0.04em;
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

components.html(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        const MOON_SVG = '<svg viewBox="0 0 24 24" width="21" height="21" fill="rgba(226,232,240,0.22)" stroke="#E2E8F0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 6px rgba(226,232,240,0.55));"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        const SUN_SVG = '<svg viewBox="0 0 24 24" width="22" height="22" fill="rgba(245,158,11,0.28)" stroke="#F59E0B" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 7px rgba(245,158,11,0.65));"><circle cx="12" cy="12" r="4.5"/><line x1="12" y1="2" x2="12" y2="4.5"/><line x1="12" y1="19.5" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="6.7" y2="6.7"/><line x1="17.3" y1="17.3" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="4.5" y2="12"/><line x1="19.5" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="6.7" y2="17.3"/><line x1="17.3" y1="6.7" x2="19.07" y2="4.93"/></svg>';

        if (!doc.getElementById('orb-pull-style')) {
            const st = doc.createElement('style');
            st.id = 'orb-pull-style';
            st.textContent =
                '#orb-pull{position:fixed;top:0;right:clamp(1rem,3vw,2.5rem);z-index:999999;width:32px;pointer-events:none;display:flex;flex-direction:column;align-items:center;}' +
                '#orb-pull .orb-chain{width:0;border-left:2px dotted #94A3B8;height:calc(22px + var(--pull,0px));transition:height 0.35s cubic-bezier(0.3,1.6,0.5,1);}' +
                '#orb-pc{pointer-events:auto;width:30px;height:30px;margin-top:-2px;padding:0;border:0;background:transparent;cursor:grab;touch-action:none;display:grid;place-items:center;transition:transform 0.2s ease;}' +
                '#orb-pc:active{cursor:grabbing;}' +
                '#orb-pc:hover{transform:scale(1.12);}' +
                '@media print{#orb-pull{display:none!important;}}';
            doc.head.appendChild(st);
        }

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

            const rest = () => {
                y0 = null;
                ch.style.transition = '';
                ch.style.setProperty('--pull', '0px');
            };
            pc.onpointerdown = (e) => {
                y0 = e.clientY;
                dy = 0;
                try { pc.setPointerCapture(e.pointerId); } catch (_) {}
                ch.style.transition = 'none';
            };
            pc.onpointermove = (e) => {
                if (y0 === null) return;
                dy = Math.max(0, Math.min(68, e.clientY - y0));
                ch.style.setProperty('--pull', dy + 'px');
            };
            pc.onpointerup = () => {
                if (y0 === null) return;
                const go = dy >= 18 || dy < 4;
                rest();
                if (go) flip();
            };
            pc.onpointercancel = rest;
            pc.onclick = (e) => { if (e.detail === 0) flip(); };
        }

        applyTheme(getTheme());
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


