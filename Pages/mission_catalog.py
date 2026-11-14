#Work in progress logic, need to debug the searching, use of SI for searching, and the filtering of the data.
import streamlit as st


def render(experiments_data):
    st.subheader("Mission Catalog Explorer")
    search_q = st.text_input("Search", placeholder="Experiment, fuel, phenomenon, or NTRS ID")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.multiselect("Mission", [], default=[])
    with col2:
        st.multiselect("Fuel Category", [], default=[])
    with col3:
        st.checkbox("Cool Flame Only", value=False)

    st.caption(f"Catalogued records: {len(experiments_data)}")

    for exp in experiments_data:
        ntrs_raw = exp.get("ntrs_document_id", "")
        ntrs_num = ntrs_raw.replace("NASA-NTRS-", "").replace("NTRS-", "").strip()
        ntrs_url = f"https://ntrs.nasa.gov/citations/{ntrs_num}" if ntrs_num.isdigit() else f"https://ntrs.nasa.gov/search?q={ntrs_raw}"

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{exp.get('name')}** `{exp.get('id')}`")
                st.caption(f"{exp.get('platform')} | {exp.get('year')}")
            with c2:
                if ntrs_raw:
                    st.markdown(
                        f"<div style='text-align:right;'><a href='{ntrs_url}' target='_blank' style='color:#02BFE7; font-size:0.78rem; font-family:DMMono; text-decoration:none;'>{ntrs_raw}</a></div>",
                        unsafe_allow_html=True
                    )
            st.write(exp.get("key_phenomenon", ""))
