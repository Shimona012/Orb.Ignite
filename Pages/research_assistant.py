import json
import os
import re
import urllib.parse
import streamlit as st


def _data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data")


@st.cache_data
def _load_ntrs_catalog():
    path = os.path.join(_data_dir(), "ntrs_links.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


@st.cache_data
def _load_experiments():
    path = os.path.join(_data_dir(), "experiments.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _get_gemini_client():
    api_key = None
    try:
        api_key = (
            st.secrets.get("GEMINI_API_KEY")
            or st.secrets.get("GOOGLE_API_KEY")
            or st.secrets.get("gemini_api_key")
            or st.secrets.get("google_api_key")
        )
        if not api_key and "google" in st.secrets:
            g = st.secrets["google"]
            api_key = g.get("api_key") or g.get("gemini_api_key") or g.get("GOOGLE_API_KEY")
    except Exception:
        pass
    api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _search_offline_knowledge(query, ntrs_docs, experiments):
    q_tokens = set(re.findall(r"\w+", query.lower()))
    if not q_tokens:
        return []

    results = []
    for doc in ntrs_docs:
        score = 0
        text = (
            f"{doc.get('title', '')} {doc.get('mission', '')} {doc.get('fuel', '')} "
            f"{doc.get('summary', '')} {doc.get('ntrs_id', '')} {doc.get('pdf_file', '')} "
            f"{doc.get('resource_type', '')}"
        ).lower()
        for tok in q_tokens:
            if tok in text:
                score += 2 if tok in doc.get("title", "").lower() or tok in str(doc.get("ntrs_id", "")).lower() else 1
        if score > 0:
            results.append({"type": "resource", "score": score, "data": doc})

    for exp in experiments:
        score = 0
        text = f"{exp.get('name', '')} {exp.get('mission', '')} {exp.get('fuel_name', '')} {exp.get('key_phenomenon', '')} {exp.get('ntrs_document_id', '')}".lower()
        for tok in q_tokens:
            if tok in text:
                score += 2 if tok in exp.get("name", "").lower() else 1
        if score > 0:
            results.append({"type": "experiment", "score": score, "data": exp})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _build_grounded_context(ntrs_docs, experiments, active_query=""):
    matches = _search_offline_knowledge(active_query, ntrs_docs, experiments) if active_query else []
    selected_resources = [m["data"] for m in matches if m["type"] == "resource"][:8]
    if not selected_resources:
        selected_resources = ntrs_docs[:10]

    lines = ["Orb.Ignite Combustion Knowledge Base (NASA NTRS, NASA Experiment Summaries & External Papers):"]
    for d in selected_resources:
        rtype = d.get("resource_type") or ("NTRS Technical Report" if d.get("ntrs_id") else "Reference Document")
        ref_tag = f"NTRS-{d.get('ntrs_id')}" if d.get("ntrs_id") else (d.get("pdf_file") or d.get("id", "DOC"))
        lines.append(
            f"- [{rtype}] [{ref_tag}]: {d.get('title')}. Mission: {d.get('mission')}. "
            f"Fuel: {d.get('fuel')}. Summary: {d.get('summary')}. Citation: {d.get('citation_url') or 'Local Repository'}"
        )
    for e in experiments[:6]:
        lines.append(f"- [Flight Experiment] [{e.get('id')} - {e.get('name')}]: Fuel: {e.get('fuel_name')}. Phenomenon: {e.get('key_phenomenon')}. NTRS: {e.get('ntrs_document_id')}")
    return "\n".join(lines)


def _set_ra_query(q_text):
    st.session_state["ra_search_input"] = q_text


def render():
    st.subheader("AI Flight Surgeon & Research Assistant")
    st.caption("Citation-grounded research intelligence and metric knowledge base across NASA NTRS reports, experiment summaries, and indexed research papers.")

    ntrs_docs = _load_ntrs_catalog()
    experiments = _load_experiments()
    gemini_client = _get_gemini_client()

    mode_tabs = st.tabs(["Research Assistant (Q&A / Search)", "Metric Guide & Knowledge Base"])

    with mode_tabs[0]:
        c_search, c_btn = st.columns([5, 1])
        with c_search:
            search_query = st.text_input(
                "Search Documents, Missions, or Combustion Physics",
                placeholder="e.g. Spalding B number, cool flame persistence, Saffire-I flame spread, NTRS-20170008805...",
                key="ra_search_input",
            )
        with c_btn:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            search_clicked = st.button("Search", key="ra_search_btn", use_container_width=True)

        pill_cols = st.columns([1, 1, 1, 1])
        with pill_cols[0]:
            st.button(
                "Cool Flame Threat",
                key="pill_cf",
                use_container_width=True,
                on_click=_set_ra_query,
                args=("Why are cool flames dangerous in spacecraft and what causes them?",),
            )
        with pill_cols[1]:
            st.button(
                "Spalding B Number",
                key="pill_spalding",
                use_container_width=True,
                on_click=_set_ra_query,
                args=("What is Spalding Transfer Number B_T and how is burning rate K calculated?",),
            )
        with pill_cols[2]:
            st.button(
                "Saffire vs FLEX",
                key="pill_saffire",
                use_container_width=True,
                on_click=_set_ra_query,
                args=("Compare Saffire large-scale solid burns with FLEX single droplet combustion.",),
            )
        with pill_cols[3]:
            st.button(
                "Smoke vs Dust",
                key="pill_smoke",
                use_container_width=True,
                on_click=_set_ra_query,
                args=("How does DAFT and SAME distinguish smouldering smoke from cabin dust in 0g?",),
            )

        st.caption("Note: External paper sources are also involved, please check before beliving")

        active_query = search_query.strip()
        if active_query:
            st.markdown("---")
            st.markdown(f"#### Query: *\"{active_query}\"*")

            ai_answered = False
            if gemini_client is not None:
                with st.spinner("AI Flight Surgeon synthesizing citation-grounded response via Gemini API..."):
                    try:
                        context = _build_grounded_context(ntrs_docs, experiments, active_query=active_query)
                        prompt = f"""You are the Orb.Ignite AI Flight Surgeon and Microgravity Combustion Research Assistant for the NASA Space Apps Challenge.
Answer the user's question with scientific accuracy, citing relevant numbered NASA NTRS document IDs, NASA flight experiment summaries (FLEX, Saffire, SoFIE, ACME, BASS, SAME, DAFT, FLARE, SLICE, SPICE), or external academic papers when applicable, clearly distinguishing official NASA reports from external papers.

Context Data:
{context}

User Question: {active_query}
"""
                        response = gemini_client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt,
                        )
                        if response and response.text:
                            st.markdown(response.text)
                            st.caption("Powered by Gemini API | Citation Grounded")
                            ai_answered = True
                    except Exception as err:
                        st.caption(f"Note: Cloud Gemini API returned ({err}). Falling back to local index.")

            if not ai_answered:
                with st.container(border=True):
                    st.markdown("##### Research Intelligence Summary (Local Engine)")
                    q_lower = active_query.lower()
                    if "cool" in q_lower or "flame" in q_lower:
                        st.markdown(
                            r"**Cool-Flame Microgravity Dynamics:** Low-temperature combustion ($500\text{--}800\text{ K}$) occurs via partial hydrocarbon oxidation. "
                            r"In microgravity ($0g$), absence of buoyancy prevents rapid convective dissipation of heat and radical species, allowing quasi-steady spherical cool flames to survive around droplets (FLEX / CFI-G). "
                            r"**Spacecraft Threat:** Unlike sealed test chambers, space habitats have continuous ECLSS airflow and oxygen replenish, preventing radiative starvation and maintaining latent reignition risks into violent hot flames."
                        )
                    elif "spalding" in q_lower or "burning rate" in q_lower or "d2" in q_lower:
                        st.markdown(
                            r"**Spalding Transfer Number ($B_T$) & $d^2$ Law:** Droplet gasification driving force is given by "
                            r"$B_T = \frac{c_{p,g}(T_\infty - T_s) + \Delta h_c Y_{\text{O}_2,\infty} / \nu}{L_v}$. "
                            r"Under spherical symmetry, the burning rate constant $K = \frac{8 k_g}{\rho_l c_{p,g}} \ln(1 + B_T)$, satisfying $d(t)^2 = d_0^2 - K t$ (FLEX-1/2)."
                        )
                    elif "saffire" in q_lower or "solid" in q_lower or "spread" in q_lower:
                        st.markdown(
                            r"**Saffire Solid Flame Spread:** Flight burns aboard Cygnus vehicles demonstrate concurrent spread velocities ($V_f \approx 2.1\text{--}2.6\text{ mm/s}$) "
                            r"exceeding 1g Earth lab equivalents ($0.6\text{--}1.2\text{ mm/s}$) due to sustained boundary-layer residence times. Large area scales ($>1.8\text{ m}^2$) accelerate enclosure pressure rise ($\Delta P$) and carbon monoxide toxicity."
                        )
                    elif "smoke" in q_lower or "dust" in q_lower or "same" in q_lower or "daft" in q_lower:
                        st.markdown(
                            r"**Smoke vs. Dust Discrimination:** Under microgravity smouldering (SAME), smoke particles agglomerate via Brownian coagulation into large soot chains ($d_p > 1.0\text{--}2.0\ \mu\text{m}$), "
                            r"reducing conventional ionization detector sensitivity. DAFT established that ISS cabin dust background exhibits distinct optical mass-to-number ratios from pyrolytic aerosols."
                        )
                    else:
                        st.markdown(
                            r"Indexed technical data retrieved for combustion state analysis across documented NASA flight test envelopes and external literature."
                        )

            matches = _search_offline_knowledge(active_query, ntrs_docs, experiments)
            if matches:
                st.markdown("##### Relevant Technical Reports, Experiment Summaries & Research Papers")
                for m in matches[:6]:
                    d = m["data"]
                    if m["type"] == "resource":
                        title = d.get("title", "Document")
                        ntrs_id = (d.get("ntrs_id") or "").strip()
                        rtype = d.get("resource_type") or ("NTRS Technical Report" if ntrs_id else "Reference Document")
                        url = (d.get("citation_url") or "").strip()
                        pdf_file = (d.get("pdf_file") or "").strip()
                        with st.container(border=True):
                            c1, c2 = st.columns([4, 1])
                            with c1:
                                id_badge = f"`NTRS-{ntrs_id}`" if ntrs_id else f"`{pdf_file or d.get('id', '')}`"
                                st.markdown(f"**{title}** {id_badge} · *{rtype}*")
                                st.caption(f"Mission: {d.get('mission')} | Fuel: {d.get('fuel')} | Year: {d.get('year')}")
                                st.write(d.get("summary", ""))
                            with c2:
                                if url and ntrs_id:
                                    st.markdown(
                                        f"<div style='text-align:right;'><a href='{url}' target='_blank' rel='noopener noreferrer' style='color:#02BFE7; font-family:DMMono; text-decoration:none; font-size:0.8rem;'>View NTRS ↗</a></div>",
                                        unsafe_allow_html=True,
                                    )
                                elif pdf_file:
                                    st.markdown(
                                        f"<div style='text-align:right;'><span style='color:#8C9FB5; font-family:DMMono; font-size:0.75rem;'>Data/{pdf_file}</span></div>",
                                        unsafe_allow_html=True,
                                    )
                    else:
                        with st.container(border=True):
                            st.markdown(f"**{d.get('name')}** `{d.get('id')}` — Mission: `{d.get('mission')}`")
                            st.caption(f"Platform: {d.get('platform')} | Fuel: {d.get('fuel_name')} ({d.get('fuel_category')}) | Risk: {d.get('safety_risk_level')}")
                            st.write(d.get("key_phenomenon", ""))

    with mode_tabs[1]:
        st.markdown("### Metric Guide & Evaluation Index")
        st.write(
            "Orb.Ignite computes physical combustion metrics based on documented NASA flight test "
            "and ground experiments (FLEX, Saffire, SoFIE, ACME, BASS, SAME, SOFBALL, FLARE, DAFT, and PSI-62). "
            "Below is how to interpret each parameter and output:"
        )

        st.markdown("#### Primary Environment Inputs")
        st.markdown(
            r"- **Gravity Level ($g$):** Ambient acceleration relative to standard Earth gravity ($1.0g$). Microgravity ($0.0g$) removes buoyancy, creating spherical flames. Lunar ($0.16g$) and Martian ($0.38g$) introduce partial natural convection where limiting oxygen concentrations are lowest." "\n"
            r"- **Oxygen Concentration ($\%\ \text{O}_2$):** Normal ambient is $21\%$. Spacecraft exploration habitats (e.g., Artemis Gateway) test elevated oxygen ($26\%\text{--}34\%\ \text{O}_2$), which accelerates flame spread and ignition." "\n"
            r"- **Cabin Airflow / Ventilation ($u_\infty$, cm/s):** Forced air velocity from ECLSS fans. Critical for microgravity flames; without airflow, combustion products ($\text{CO}_2, \text{H}_2\text{O}$) accumulate and induce radiative quenching ($<5\text{ cm/s}$)." "\n"
            r"- **Cabin Pressure ($P$, atm):** Ambient atmospheric pressure. Reduced pressures ($0.56\text{--}0.70\text{ atm}$) alter chemical time scales and flammability envelopes."
        )

        st.markdown("#### Core Governing Physics & Metrics")
        st.markdown(
            r"- **Category Surety ($\%$):** Confidence percentage indicating how closely the chosen fuel and environmental state align with validated NASA experimental envelopes." "\n"
            r"- **Spalding Transfer Number ($B_T$):** Thermodynamic driving force for droplet gasification and mass transfer in liquid fuel combustion (FLEX)." "\n"
            r"- **Burning Rate Constant ($K$, $\text{mm}^2/\text{s}$):** Regression slope of the classical $d^2$ law: $d(t)^2 = d_0^2 - K t$." "\n"
            r"- **Damköhler Number ($Da$):** Ratio of convective residence time to chemical kinetic reaction time ($\tau_{\text{flow}} / \tau_{\text{chem}}$). Values below $1.0$ indicate high blow-off risk." "\n"
            r"- **Ignition Delay ($t_{\text{ig}}$, s):** Time required for solid polymers to ignite under surface radiative heat flux, inversely proportional to the material's thermal inertia ($k_s \rho_s c_s$)." "\n"
            r"- **Surface Conduction ($q_{\text{cond}}''$) & Radiative Loss ($q_{\text{rad}}''$):** Heat transferred through the solid matrix versus Stefan-Boltzmann radiation emitted from the hot surface ($\sigma (T_s^4 - T_\infty^4)$)." "\n"
            r"- **Flame Spread Velocity ($V_f$, mm/s):** Rate at which the flame front propagates over thin or thick solids (de Ris formulation)." "\n"
            r"- **Grashof ($Gr$) & Rayleigh ($Ra$) Numbers:** Dimensionless ratios characterizing the strength of buoyant natural convection relative to viscous and thermal diffusion in partial gravity." "\n"
            r"- **Lewis ($Le$) & Peclet ($Pe$) Numbers:** Evaluates preferential mass diffusion of light fuels (e.g., $\text{H}_2$) forming stationary spherical flame balls without convective motion (SOFBALL)." "\n"
            r"- **Agglomerated Smoke Diameter ($d_p$, $\mu\text{m}$):** Particulate growth via Brownian coagulation under non-convective smouldering (SAME). In microgravity, soot chains grow larger ($>1.0\text{--}2.0\ \mu\text{m}$), cutting traditional ionization sensor sensitivity." "\n"
            r"- **Threat Score ($0\text{--}100$) & Probabilistic Hazard Rate ($h(t)$):** Composite fire hazard score integrating combustion rates, oxygen enrichment, cool-flame persistence, and spatial scaling alongside instantaneous failure rate $h(t) = f(t) / (1 - F(t))$." "\n"
            r"- **Exposure Factor ($EF$) & Loss Expectancy ($ALE$):** Fraction of enclosed assets exposed ($EF \in [0, 1]$) and scaled risk expectancy index via $SLE = AV \times EF$ and $ALE = SLE \times ARO$." "\n"
            r"- **Spatial Area Scaling ($A$, $\text{m}^2$):** Decreasing area ($A < 0.6\ \text{m}^2$) confines thermal energy, elevates radiative wall feedback and $\text{HCl}/\text{HF}$ sensor adsorption lag, and promotes cool-flame regime shifts; increasing area ($A > 1.8\ \text{m}^2$) accelerates exposed surface pyrolysis and causes non-buoyant $0g$ smoke dispersion across large cabin volumes."
        )

        st.markdown("#### Indexed Document & Resource Registry")
        if ntrs_docs:
            ntrs_only = [d for d in ntrs_docs if d.get("resource_type") == "NTRS Technical Report" or (d.get("ntrs_id") and not d.get("resource_type"))]
            nasa_exp_docs = [d for d in ntrs_docs if d.get("resource_type") == "NASA Experiment / Guide"]
            ext_papers = [d for d in ntrs_docs if d.get("resource_type") == "External Research Paper"]
            other_docs = [d for d in ntrs_docs if d not in ntrs_only and d not in nasa_exp_docs and d not in ext_papers]

            reg_tabs = st.tabs([
                f"NTRS Reports ({len(ntrs_only)})",
                f"NASA Experiment Summaries & Guides ({len(nasa_exp_docs)})",
                f"External Research Papers ({len(ext_papers)})",
            ])

            with reg_tabs[0]:
                st.caption("Official numbered NASA NTRS technical reports with direct citation links.")
                for doc in ntrs_only:
                    with st.expander(f"{doc.get('title')} (NTRS-{doc.get('ntrs_id', '')})"):
                        st.markdown(f"**Mission:** `{doc.get('mission')}` | **Fuel/Target:** `{doc.get('fuel')}` | **Year:** `{doc.get('year')}`")
                        if doc.get("pdf_file"):
                            st.caption(f"Local File: `Data/{doc.get('pdf_file')}`")
                        st.write(doc.get("summary", ""))
                        citation_url = doc.get("citation_url")
                        if citation_url:
                            st.markdown(f"[Open NASA NTRS Citation ↗]({citation_url})")

            with reg_tabs[1]:
                st.caption("Named NASA Combustion Science page experiment sheets and reduced-gravity researcher guides (separate from numbered NTRS files).")
                for doc in nasa_exp_docs:
                    with st.expander(f"{doc.get('title')} ({doc.get('pdf_file') or doc.get('id', '')})"):
                        st.markdown(f"**Mission:** `{doc.get('mission')}` | **Fuel/Target:** `{doc.get('fuel')}` | **Year:** `{doc.get('year')}`")
                        st.write(doc.get("summary", ""))

            with reg_tabs[2]:
                st.caption("Notice: External academic/conference papers included for Research Assistant coverage; please verify independently.")
                for doc in ext_papers + other_docs:
                    with st.expander(f"{doc.get('title')} ({doc.get('pdf_file') or doc.get('id', '')})"):
                        st.markdown(f"**Topic/Mission:** `{doc.get('mission')}` | **Fuel/Target:** `{doc.get('fuel')}` | **Year:** `{doc.get('year')}`")
                        st.write(doc.get("summary", ""))

