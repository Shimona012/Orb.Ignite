#Background ambient aurora atmosphere synced to active presets
#Used SI for base aurora formation
import streamlit as st


AMBIENCE_THEMES = {
    "ISS Microgravity (0g)": {
        "color_1": "rgba(14, 165, 233, 0.16)",
        "color_2": "rgba(99, 102, 241, 0.18)",
        "color_3": "rgba(30, 27, 75, 0.28)",
        "accent": "rgba(56, 189, 248, 0.12)",
        "tag": "Cosmic Microgravity Ionized Glow",
    },
    "Lunar Gateway (0.16g)": {
        "color_1": "rgba(226, 232, 240, 0.16)",
        "color_2": "rgba(56, 189, 248, 0.15)",
        "color_3": "rgba(71, 85, 105, 0.22)",
        "accent": "rgba(148, 163, 184, 0.14)",
        "tag": "Lunar Regolith Surface Exosphere Halo",
    },
    "Mars Habitat (0.38g)": {
        "color_1": "rgba(234, 88, 12, 0.20)",
        "color_2": "rgba(185, 28, 28, 0.16)",
        "color_3": "rgba(69, 10, 10, 0.26)",
        "accent": "rgba(245, 158, 11, 0.14)",
        "tag": "Martian Atmospheric Twilight Aura",
    },
    "Earth Lab (1.0g)": {
        "color_1": "rgba(251, 146, 60, 0.18)",
        "color_2": "rgba(14, 165, 233, 0.16)",
        "color_3": "rgba(15, 23, 42, 0.20)",
        "accent": "rgba(245, 158, 11, 0.12)",
        "tag": "Terrestrial Buoyant Daylight Atmosphere",
    },
    "Custom": {
        "color_1": "rgba(168, 85, 247, 0.18)",
        "color_2": "rgba(14, 165, 233, 0.18)",
        "color_3": "rgba(234, 88, 12, 0.16)",
        "accent": "rgba(52, 211, 153, 0.14)",
        "tag": "Harmonic Dynamic Custom Aurora",
    },
}


def render_ambience(preset_name=None):
    if not preset_name:
        preset_name = st.session_state.get("shared_env_preset", "ISS Microgravity (0g)")
    theme = AMBIENCE_THEMES.get(preset_name, AMBIENCE_THEMES["ISS Microgravity (0g)"])

    c1 = theme["color_1"]
    c2 = theme["color_2"]
    c3 = theme["color_3"]
    c4 = theme["accent"]

    css = f"""
    <style>
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"] {{
        background-color: transparent !important;
    }}

    [data-testid="stAppViewContainer"] {{
        position: relative;
        background-image:
            radial-gradient(ellipse 65% 55% at 20% 18%, {c1} 0%, transparent 68%),
            radial-gradient(ellipse 60% 50% at 82% 24%, {c2} 0%, transparent 65%),
            radial-gradient(ellipse 70% 60% at 50% 88%, {c3} 0%, transparent 72%),
            radial-gradient(ellipse 45% 40% at 75% 78%, {c4} 0%, transparent 60%) !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
        background-size: cover !important;
        transition: background-image 1.2s ease-in-out;
    }}

    [data-theme="light"] [data-testid="stAppViewContainer"],
    .stApp[data-theme="light"] [data-testid="stAppViewContainer"],
    [data-base-theme="light"] [data-testid="stAppViewContainer"] {{
        background-color: #f8fafc !important;
        background-image:
            radial-gradient(ellipse 65% 55% at 20% 18%, {c1} 0%, transparent 68%),
            radial-gradient(ellipse 60% 50% at 82% 24%, {c2} 0%, transparent 65%),
            radial-gradient(ellipse 70% 60% at 50% 88%, {c3} 0%, transparent 72%),
            radial-gradient(ellipse 45% 40% at 75% 78%, {c4} 0%, transparent 60%) !important;
        background-attachment: fixed !important;
    }}

    [data-theme="dark"] [data-testid="stAppViewContainer"],
    .stApp[data-theme="dark"] [data-testid="stAppViewContainer"],
    [data-base-theme="dark"] [data-testid="stAppViewContainer"] {{
        background-color: #0b0f19 !important;
        background-image:
            radial-gradient(ellipse 65% 55% at 20% 18%, {c1} 0%, transparent 68%),
            radial-gradient(ellipse 60% 50% at 82% 24%, {c2} 0%, transparent 65%),
            radial-gradient(ellipse 70% 60% at 50% 88%, {c3} 0%, transparent 72%),
            radial-gradient(ellipse 45% 40% at 75% 78%, {c4} 0%, transparent 60%) !important;
        background-attachment: fixed !important;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
        pointer-events: none;
        background:
            radial-gradient(ellipse 65% 55% at 20% 18%, {c1} 0%, transparent 68%),
            radial-gradient(ellipse 60% 50% at 82% 24%, {c2} 0%, transparent 65%),
            radial-gradient(ellipse 70% 60% at 50% 88%, {c3} 0%, transparent 72%),
            radial-gradient(ellipse 45% 40% at 75% 78%, {c4} 0%, transparent 60%);
        filter: blur(48px);
        opacity: 0.88;
        transform: translateZ(0);
        animation: orbAuroraDrift 28s ease-in-out infinite alternate;
        transition: background 1.2s ease-in-out, opacity 1.2s ease-in-out;
    }}

    @keyframes orbAuroraDrift {{
        0% {{
            transform: scale(1.0) translate(0px, 0px);
        }}
        50% {{
            transform: scale(1.05) translate(-14px, 12px);
        }}
        100% {{
            transform: scale(1.02) translate(14px, -10px);
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
