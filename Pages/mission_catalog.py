#Work in progress logic, need to debug the searching, use of SI for searching, and the filtering of the data.
import urllib.parse
import streamlit as st
try:
    from Pages import combustion_physics
except ImportError:
    import combustion_physics


def render(experiments_data):
    st.subheader("Mission Catalog Explorer")
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

    st.caption(f"Showing {len(filtered)} of {len(experiments_data)} records")

    for exp in filtered:
        ntrs_raw = exp.get("ntrs_document_id", "")
        ntrs_link = (exp.get("ntrs_link") or "").strip()
        if not ntrs_link and ntrs_raw:
            ntrs_num = ntrs_raw.replace("NASA-NTRS-", "").replace("NTRS-", "").strip()
            ntrs_link = f"https://ntrs.nasa.gov/citations/{ntrs_num}" if ntrs_num.isdigit() else f"https://ntrs.nasa.gov/search?q={urllib.parse.quote(ntrs_raw)}"

        matched = combustion_physics.match_catalog_record(exp)

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{exp.get('name')}** `{exp.get('id')}` — **Fuel:** `{exp.get('fuel_name')}` (`{matched['surety_pct']}% Surety`)")
                st.caption(f"{exp.get('platform')} | {exp.get('year')} | Equation: {matched['equation_name']}")
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
