#Work in progress logic, need to debug the searching, use of SI for searching, and the filtering of the data.
import base64
import os
import urllib.parse
import streamlit as st
import plotly.graph_objects as go
try:
    from Pages import combustion_physics
except ImportError:
    import combustion_physics

#experimented with funnel sort, will provide option to view funnel view or direct rearrangement of the experiments with beter filtration.
def _load_icon_b64(fname):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(base_dir, "Data", fname)
    if os.path.exists(p):
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


_b64_filter_white = _load_icon_b64("filter_white.png")
_b64_filter_black = _load_icon_b64("filter_black.png")

FUNNEL_ICON_HTML = f"""
<span class="orb-funnel-icon-box" style="display:inline-flex; align-items:center; vertical-align:middle; margin-right:8px;">
    <style>
        .orb-funnel-img {{
            width: 20px;
            height: 20px;
            object-fit: contain;
            vertical-align: middle;
            display: inline-block;
        }}
        .orb-funnel-dark {{ display: inline-block; }}
        .orb-funnel-light {{ display: none; }}
        @media (prefers-color-scheme: light) {{
            .orb-funnel-dark {{ display: none !important; }}
            .orb-funnel-light {{ display: inline-block !important; }}
        }}
        [data-theme="light"] .orb-funnel-dark,
        .stApp[data-theme="light"] .orb-funnel-dark,
        [data-base-theme="light"] .orb-funnel-dark {{
            display: none !important;
        }}
        [data-theme="light"] .orb-funnel-light,
        .stApp[data-theme="light"] .orb-funnel-light,
        [data-base-theme="light"] .orb-funnel-light {{
            display: inline-block !important;
        }}
        [data-theme="dark"] .orb-funnel-dark,
        .stApp[data-theme="dark"] .orb-funnel-dark,
        [data-base-theme="dark"] .orb-funnel-dark {{
            display: inline-block !important;
        }}
        [data-theme="dark"] .orb-funnel-light,
        .stApp[data-theme="dark"] .orb-funnel-light,
        [data-base-theme="dark"] .orb-funnel-light {{
            display: none !important;
        }}
    </style>
    <img src="data:image/png;base64,{_b64_filter_white}" class="orb-funnel-img orb-funnel-dark" alt="Funnel" />
    <img src="data:image/png;base64,{_b64_filter_black}" class="orb-funnel-img orb-funnel-light" alt="Funnel" />
</span>
"""


TIER_COLORS = {
    "CRITICAL": "#FC3D21",
    "HIGH": "#FF7F11",
    "MODERATE": "#FFB302",
    "LOW": "#02BFE7",
}


def render(experiments_data):
    st.markdown(f"### {FUNNEL_ICON_HTML}Mission Catalog Explorer", unsafe_allow_html=True)
    search_q = st.text_input("Search", placeholder="Experiment, fuel, phenomenon, or NTRS ID")

    missions = sorted(set(e.get("mission", "") for e in experiments_data if e.get("mission")))
    fuels = sorted(set(e.get("fuel_category", "") for e in experiments_data if e.get("fuel_category")))

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_mission = st.multiselect("Mission", missions, default=[])
    with col2:
        selected_fuel = st.multiselect("Fuel Category", fuels, default=[])
    with col3:
        cool_only = st.checkbox("Cool Flame Only", value=False)

    t_col1, t_col2, t_col3 = st.columns([1.4, 1.4, 1.2])
    with t_col1:
        sort_by = st.selectbox(
            "Sort / Arrange By",
            [
                "Threat Level: High → Low (Funnel)",
                "Threat Level: Low → High",
                "Year: Newest First",
                "Year: Oldest First",
                "Default Catalog Order",
            ],
            index=0,
            key="mc_sort_by",
        )
    with t_col2:
        selected_tiers = st.multiselect(
            "Threat Tier",
            ["CRITICAL", "HIGH", "MODERATE", "LOW"],
            default=[],
            key="mc_threat_tier",
        )
    with t_col3:
        area_m2 = st.slider(
            "Compartment / Sample Area Scale (m²)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            key="mc_area_scale",
        )

    f_toggle_col1, f_toggle_col2 = st.columns([3, 1])
    with f_toggle_col1:
        st.markdown(
            f"{FUNNEL_ICON_HTML}<span style='font-size:0.95rem; font-weight:600;'>Threat Level Hierarchy Funnel</span>",
            unsafe_allow_html=True,
        )
    with f_toggle_col2:
        show_funnel = st.toggle("Show Funnel View", value=True, key="mc_toggle_funnel")

    filtered = experiments_data
    if search_q:
        q = search_q.strip().lower()
        filtered = [
            e for e in filtered
            if q in e.get("name", "").lower()
            or q in e.get("mission", "").lower()
            or q in e.get("fuel_name", "").lower()
            or q in e.get("key_phenomenon", "").lower()
            or q in e.get("ntrs_document_id", "").lower()
        ]
    if selected_mission:
        filtered = [e for e in filtered if e.get("mission") in selected_mission]
    if selected_fuel:
        filtered = [e for e in filtered if e.get("fuel_category") in selected_fuel]
    if cool_only:
        filtered = [e for e in filtered if e.get("cool_flame_observed") is True]

    enriched = [(e, combustion_physics.match_catalog_record(e, area_m2=area_m2)) for e in filtered]
    if selected_tiers:
        enriched = [(e, m) for e, m in enriched if m["threat_tier"] in selected_tiers]

    if sort_by == "Threat Level: High → Low (Funnel)":
        enriched.sort(key=lambda x: x[1]["threat_score"], reverse=True)
    elif sort_by == "Threat Level: Low → High":
        enriched.sort(key=lambda x: x[1]["threat_score"])
    elif sort_by == "Year: Newest First":
        enriched.sort(key=lambda x: int(x[0].get("year", 0)), reverse=True)
    elif sort_by == "Year: Oldest First":
        enriched.sort(key=lambda x: int(x[0].get("year", 0)))

    st.caption(f"Showing {len(enriched)} of {len(experiments_data)} records | Area Scale: {area_m2:.1f} m²")

    if show_funnel and enriched:
        funnel_items = sorted(enriched, key=lambda x: x[1]["threat_score"], reverse=True)
        fig_funnel = go.Figure(go.Funnel(
            y=[f"{e.get('mission')} ({m['threat_tier']})" for e, m in funnel_items],
            x=[m["threat_score"] for _, m in funnel_items],
            textposition="inside",
            texttemplate="%{x:.1f} / 100",
            marker={"color": [TIER_COLORS.get(m["threat_tier"], "#02BFE7") for _, m in funnel_items]},
            hovertemplate="<b>%{y}</b><br>Threat Score: %{x:.1f}/100<extra></extra>",
        ))
        fig_funnel.update_layout(
            title=f"Mission Threat Hierarchy Funnel (Area Scale: {area_m2:.1f} m²)",
            height=max(260, 42 * len(funnel_items) + 80),
            margin=dict(l=10, r=10, t=42, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

    for exp, matched in enriched:
        ntrs_raw = exp.get("ntrs_document_id", "")
        ntrs_link = (exp.get("ntrs_link") or "").strip()
        if not ntrs_link and ntrs_raw:
            ntrs_num = ntrs_raw.replace("NASA-NTRS-", "").replace("NTRS-", "").strip()
            ntrs_link = f"https://ntrs.nasa.gov/citations/{ntrs_num}" if ntrs_num.isdigit() else f"https://ntrs.nasa.gov/search?q={urllib.parse.quote(ntrs_raw)}"

        tier_color = TIER_COLORS.get(matched["threat_tier"], "#02BFE7")

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(
                    f"**{exp.get('name')}** `{exp.get('id')}` — "
                    f"<span style='color:{tier_color}; font-weight:700;'>Threat: {matched['threat_score']}/100 ({matched['threat_tier']})</span> "
                    f"— **Fuel:** `{exp.get('fuel_name')}` (`{matched['surety_pct']}% Surety`)",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"{exp.get('platform')} | {exp.get('year')} | Area: {matched['area_regime']} | "
                    f"EF: {matched['exposure_factor_EF']} | Lag: {matched['detection_lag_s']}s | Equation: {matched['equation_name']}"
                )
            with c2:
                if ntrs_raw or ntrs_link:
                    label = ntrs_raw or "NTRS Link"
                    if ntrs_link:
                        st.markdown(
                            f"<div style='text-align:right;'><a href='{ntrs_link}' target='_blank' rel='noopener noreferrer' style='color:#02BFE7; font-size:0.78rem; font-family:DMMono; text-decoration:none;'>{label}</a></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div style='text-align:right;'><span style='color:#8C9FB5; font-size:0.78rem; font-family:DMMono;'>{label}</span></div>",
                            unsafe_allow_html=True,
                        )
            st.write(exp.get("key_phenomenon", ""))
            st.caption(f"Spatial Area Effect: {matched['area_effect_summary']}")
#black filter : <a href="https://www.flaticon.com/free-icons/filter" title="filter icons">Filter icons created by Kiranshastry - Flaticon</a>
#white filter: <a href="https://www.flaticon.com/free-icons/filter" title="filter icons">Filter icons created by vectaicon - Flaticon</a>