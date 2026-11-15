#Dashboard page, SI for markdown styling and data-ingestion. 
#Used SI for optimization in all OS,screens and browsers
import streamlit as st
import streamlit.components.v1 as components
import os
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


#Setting page config for dashboard
st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="collapsed")


@st.dialog("Help / Metric Guide", width="large")
def show_help_dialog():
    KnowledgeBase.render()


@st.dialog("About Orb.Ignite", width="large")
def show_about_dialog():
    About.render()


@st.dialog("Contact Us", width="small")
def show_contact_dialog():
    contact_us.render()


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;1,400&family=Inter:wght@300..800&family=Public+Sans:ital,wght@0,300..900;1,300..900&display=swap');

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
    [data-testid="stSidebarContent"],
    div[data-testid="stSidebarUserContent"] {
        overflow-y: auto !important;
        max-height: 100vh !important;
        overscroll-behavior: contain !important;
        -webkit-overflow-scrolling: touch !important;
    }

    [data-testid="stSidebarContent"]::-webkit-scrollbar {
        width: 6px;
    }
    [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
    }
    [data-testid="stSidebarContent"] > div:first-child {
        padding-bottom: 4rem !important;
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
    [data-testid="stDecoration"] {
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
    [data-theme="light"] .stApp [data-testid="stMetricValue"],
    [data-theme="light"] .stApp [data-testid="stMetricLabel"] {
        color: #0F172A;
    }
    [data-theme="light"] .stApp .orb-brand-tag {
        color: #475569 !important;
    }
    [data-theme="light"] .stApp [data-testid="stExpander"],
    [data-theme="light"] .stApp [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.85) !important;
        border-color: rgba(15, 23, 42, 0.14) !important;
    }
    [data-theme="light"] .stApp [data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
    }
    [data-theme="light"] .stApp [data-baseweb="select"] > div,
    [data-theme="light"] .stApp [data-baseweb="input"] > div,
    [data-theme="light"] .stApp [data-baseweb="base-input"] > input,
    [data-theme="light"] .stApp textarea {
        background-color: rgba(255, 255, 255, 0.94) !important;
        color: #0F172A !important;
        border-color: rgba(15, 23, 42, 0.18) !important;
    }
    [data-theme="light"] .stApp button[kind="secondary"],
    [data-theme="light"] .stApp [data-testid="stPopover"] > button {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #0F172A !important;
        border-color: rgba(15, 23, 42, 0.18) !important;
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

    @media (pointer: coarse) {
        button, [role="button"] {
            min-height: 40px;
        }
        .orb-section-nav a {
            padding: 10px 16px !important;
        }
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
                dy = Math.max(0, Math.min(90, e.clientY - y0));
                ch.style.setProperty('--pull', dy + 'px');
            };
            pc.onpointerup = () => {
                if (y0 === null) return;
                const go = dy >= 22 || dy < 4;
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


