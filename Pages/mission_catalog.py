#Work in progress logic, need to debug the searching, use of SI for searching, and the filtering of the data.
import base64
import html
import os
import urllib.parse
import streamlit as st
import plotly.graph_objects as go
try:
    from Pages import combustion_physics
except ImportError:
    import combustion_physics

#Used SI for funnel view
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
    st.markdown(
        """
        <style>
        .orb-mission-hover-wrap {
            position: relative;
            display: inline-block;
            cursor: help;
        }
        .orb-hover-badge {
            display: inline-block;
            margin-left: 8px;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-family: 'DMMono', monospace;
            background: rgba(2, 191, 231, 0.14);
            color: #02BFE7;
            border: 1px solid rgba(2, 191, 231, 0.35);
            vertical-align: middle;
        }
        .orb-mission-hover-box {
            visibility: hidden;
            opacity: 0;
            position: absolute;
            z-index: 9999;
            top: 115%;
            left: 0;
            min-width: 340px;
            max-width: 460px;
            padding: 12px 14px;
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.96);
            color: #E2E8F0;
            border: 1px solid rgba(2, 191, 231, 0.45);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
            font-size: 0.80rem;
            line-height: 1.45;
            transition: opacity 0.16s ease-in-out, visibility 0.16s ease-in-out;
            pointer-events: none;
            backdrop-filter: blur(8px);
        }
        .orb-mission-hover-wrap:hover .orb-mission-hover-box,
        .orb-mission-hover-wrap:focus-within .orb-mission-hover-box {
            visibility: visible;
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
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
        show_funnel = st.toggle("Show Funnel View", value=False, key="mc_toggle_funnel")

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

    cached_info_map = combustion_physics.get_cached_mission_catalog_info(experiments_data, area_m2=area_m2)

    for idx, (exp, matched) in enumerate(enriched):
        exp_id = str(exp.get("id") or f"EXP-{idx}")
        info = cached_info_map.get(exp_id, {})
        ntrs_raw = info.get("ntrs_document_id") or exp.get("ntrs_document_id", "")
        ntrs_link = info.get("ntrs_link") or (exp.get("ntrs_link") or "").strip()
        if not ntrs_link and ntrs_raw:
            ntrs_num = ntrs_raw.replace("NASA-NTRS-", "").replace("NTRS-", "").strip()
            ntrs_link = f"https://ntrs.nasa.gov/citations/{ntrs_num}" if ntrs_num.isdigit() else f"https://ntrs.nasa.gov/search?q={urllib.parse.quote(ntrs_raw)}"

        tier_color = TIER_COLORS.get(matched["threat_tier"], "#02BFE7")
        safe_name = html.escape(str(exp.get("name", "")))
        safe_id = html.escape(exp_id)
        safe_fuel = html.escape(str(exp.get("fuel_name", "")))
        hover_html = info.get("hover_summary_html") or f"<b>{safe_name}</b><br/>Fuel: {safe_fuel}"

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(
                    f"""
                    <div class="orb-mission-hover-wrap">
                        <strong>{safe_name}</strong> <code>{safe_id}</code>
                        <span class="orb-hover-badge">Hover Info</span>
                        — <span style="color:{tier_color}; font-weight:700;">Threat: {matched['threat_score']}/100 ({matched['threat_tier']})</span>
                        — <strong>Fuel:</strong> <code>{safe_fuel}</code> (<code>{matched['surety_pct']}% Surety</code>)
                        <div class="orb-mission-hover-box">
                            {hover_html}
                        </div>
                    </div>
                    """,
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

            act_c1, act_c2, act_c3 = st.columns([1.4, 1.6, 3.0])
            dossier_key = f"mc_open_dossier_{exp_id}_{idx}"
            with act_c1:
                with st.popover("Quick Info", use_container_width=True):
                    st.markdown(f"**{info.get('full_name', exp.get('name', ''))}**")
                    st.markdown(f"**Facility:** `{info.get('hardware_facility', exp.get('platform', 'N/A'))}`")
                    st.markdown(f"**Investigator:** {info.get('investigator', 'NASA Glenn Team')}")
                    st.markdown(f"**Three Pillars:** `{info.get('three_pillars_focus', 'N/A')}`")
                    st.markdown(
                        f"**Test Envelope:** `{info.get('gravity_g', 0.0):.2f}g` | "
                        f"`{info.get('oxygen_pct', 21.0):.1f}% O₂` | "
                        f"`{info.get('pressure_atm', 1.0):.2f} atm` | "
                        f"Burn: `{info.get('burn_duration_s', 0.0):.1f}s`"
                    )
                    st.info(info.get("spacecraft_safety_insight", ""))
            with act_c2:
                is_open = st.session_state.get(dossier_key, False)
                btn_label = "Hide Mission Dossier" if is_open else "Full Mission Dossier"
                if st.button(btn_label, key=f"mc_click_info_{exp_id}_{idx}", use_container_width=True):
                    st.session_state[dossier_key] = not is_open
                    st.rerun()

            if st.session_state.get(dossier_key, False):
                with st.container(border=True):
                    st.markdown(f"##### Cached Mission Dossier: {info.get('full_name', exp.get('name', ''))}")
                    d1, d2 = st.columns(2)
                    with d1:
                        st.markdown(f"**Principal Investigator:** {info.get('investigator', 'N/A')}")
                        st.markdown(f"**Hardware Facility:** `{info.get('hardware_facility', 'N/A')}`")
                        st.markdown(f"**Three Pillars Focus:** `{info.get('three_pillars_focus', 'N/A')}`")
                        st.markdown(f"**Cool Flame Observed:** `{'Yes' if info.get('cool_flame_observed') else 'No'}`")
                    with d2:
                        st.markdown(f"**Detection Challenge:** {info.get('detection_challenge', 'N/A')}")
                        st.markdown(f"**Extinction Mechanism:** {info.get('extinction_mechanism', 'N/A')}")
                        st.markdown(f"**Spacecraft Safety Insight:** {info.get('spacecraft_safety_insight', 'N/A')}")

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Burn Duration", f"{info.get('burn_duration_s', 0.0):.1f} s")
                    m2.metric("Droplet Burn K", f"{info.get('burn_rate_mm_s2', 0.0)} mm²/s")
                    m3.metric("Spread Rate V_f", f"{info.get('spread_rate_mm_s', 0.0)} mm/s")
                    m4.metric("Radiative Loss", f"{info.get('q_rad_kw_m2', 0.0)} kW/m²")

                    st.caption(info.get("equation_desc", ""))
                    if info.get("equation_latex"):
                        st.latex(info["equation_latex"])
                    if ntrs_link:
                        st.markdown(f"[Open NTRS Record ({ntrs_raw or exp_id}) ↗]({ntrs_link})")
#black filter : <a href="https://www.flaticon.com/free-icons/filter" title="filter icons">Filter icons created by Kiranshastry - Flaticon</a>
#white filter: <a href="https://www.flaticon.com/free-icons/filter" title="filter icons">Filter icons created by vectaicon - Flaticon</a>