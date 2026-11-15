#Predicting fire in spacecrafts based on NASA flight test data and other relevant datasets.
from datetime import datetime, timezone
import json
import os
import sys
import uuid
import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
try:
    from Pages import combustion_physics
except ImportError:
    import combustion_physics

#Majorly SI for training and analysis
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)


def _load_predictor_bundle(bundle_path, bundle_mtime):
    import train_fire_models
    bundle = joblib.load(bundle_path)
    predictor = train_fire_models.OrbIgnitePredictor(bundle["artifacts"], bundle["psi117"])
    return predictor, bundle



@st.cache_resource
def get_cached_fire_predictor(bundle_mtime):
    bundle_path = os.path.join(_BASE_DIR, "models", "orb_ignite_fire_models.joblib")
    if not os.path.exists(bundle_path):
        import train_fire_models
        train_fire_models.main()
    return _load_predictor_bundle(bundle_path, bundle_mtime)



def _map_ui_fuel_to_model_fuel(fuel_type, exp_context):
    fl = (fuel_type or "").lower()
    ec = (exp_context or "").lower()
    is_dust = ("dust" in fl) or ("daft" in fl) or ("daft" in ec)
    if "heptane" in fl or "octane" in fl:
        return "Heptane", 3.5, is_dust
    if "decane" in fl or "dodecane" in fl:
        return "Dodecane", 3.8, is_dust
    if "methanol" in fl or "alcohol" in fl:
        return "Methanol", 2.8, is_dust
    if "sibal" in fl or "cotton" in fl:
        return "SIBAL", 0.35, is_dust
    if "pmma" in fl or "acrylic" in fl:
        return "PMMA", 2.0, is_dust
    if "ethane" in fl or "propane" in fl or "butane" in fl:
        return "Propane", 3.2, is_dust
    if "h2" in fl or "h₂" in fl or "ch4" in fl or "ch₄" in fl or "sofball" in fl:
        return "Methane", 3.2, is_dust
    if "kapton" in fl or "silicone" in fl or "same" in fl:
        return "Nomex", 1.5, is_dust
    return "PMMA" if is_dust else "Heptane", 2.0, is_dust



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
            g_cfg = st.secrets["google"]
            api_key = g_cfg.get("api_key") or g_cfg.get("gemini_api_key") or g_cfg.get("GOOGLE_API_KEY")
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



def _set_fp_chart_query(text):
    st.session_state["fp_ai_chart_query"] = text



def _compute_composite_hazard(pred, threat):
    life = pred["life_damage_crew"]
    inf = pred["infrastructure_damage_vehicle"]
    co_ratio = min(2.0, life["co_concentration_ppm"] / 55.0)
    ch2o_ratio = min(2.0, life["toxic_formaldehyde_ch2o_mg_m3"] / 0.5)
    flux_ratio = min(2.0, inf["radiative_heat_flux_kw_m2"] / 12.5)
    cool_bonus = 12.0 if inf["cool_flame_reignition_risk"]["cool_flame_active_or_probable"] else 0.0
    score = min(100.0, round(0.45 * threat["threat_score"] + 15.0 * co_ratio + 10.0 * ch2o_ratio + 15.0 * flux_ratio + cool_bonus, 1))
    return score



def _run_scenario_prediction(predictor, fuel_type, exp_context, gravity, oxygen, pressure, ventilation, area_m2):
    model_fuel, char_scale, is_dust = _map_ui_fuel_to_model_fuel(fuel_type, exp_context)
    pred = predictor.predict(
        fuel=model_fuel,
        gravity_g=float(gravity),
        o2_pct=float(oxygen),
        pressure_atm=float(pressure),
        flow_cm_s=float(ventilation),
        area_m2=float(area_m2),
        char_scale_mm=float(char_scale),
    )
    earth_pred = predictor.predict(
        fuel=model_fuel,
        gravity_g=1.0,
        o2_pct=20.9,
        pressure_atm=1.0,
        flow_cm_s=max(1.0, float(ventilation)),
        area_m2=float(area_m2),
        char_scale_mm=float(char_scale),
    )
    state = combustion_physics.evaluate_combustion_state(
        fuel_type,
        gravity,
        oxygen,
        ventilation,
        pressure_atm=pressure,
        area_m2=area_m2,
    )
    return pred, earth_pred, state, model_fuel, is_dust



def _render_ai_generated_chart(chart_req, predictor, model_fuel, fuel_type, gravity, oxygen, pressure, ventilation, area_m2, pred, earth_pred):
    q = chart_req.strip().lower()
    chart_type = "auto"
    ai_caption = ""

    client = _get_gemini_client()
    if client is not None:
        try:
            prompt = (
                "Select the best single chart_key from: "
                "['regime_probs', 'harm_radar', 'co_timeline', 'gravity_sweep', 'earth_compare', 'area_sweep'] "
                f"for user request: '{chart_req}'. Return JSON ONLY: {{\"chart_key\": \"...\", \"insight\": \"1-2 sentence scientific insight referencing the current CO={pred['life_damage_crew']['co_concentration_ppm']} ppm, burn={pred['duration_and_persistence']['burn_duration_s']} s, flux={pred['infrastructure_damage_vehicle']['radiative_heat_flux_kw_m2']} kW/m2\"}}."
            )
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            if resp and resp.text:
                cleaned = resp.text.strip().strip("`")
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                parsed = json.loads(cleaned)
                chart_type = parsed.get("chart_key", "auto")
                ai_caption = parsed.get("insight", "")
        except Exception:
            chart_type = "auto"

    if chart_type == "auto":
        if any(k in q for k in ("regime", "probab", "cool flame", "color", "colour", "classification")):
            chart_type = "regime_probs"
        elif any(k in q for k in ("time", "timeline", "smac", "co", "oxygen", "o2", "deplet")):
            chart_type = "co_timeline"
        elif any(k in q for k in ("gravity", "0g", "lunar", "mars", "sweep", "g-level")):
            chart_type = "gravity_sweep"
        elif any(k in q for k in ("earth", "1g", "counterpart", "compare")):
            chart_type = "earth_compare"
        elif any(k in q for k in ("space", "area", "confin", "enclosure", "volume")):
            chart_type = "area_sweep"
        else:
            chart_type = "harm_radar"

    life = pred["life_damage_crew"]
    inf = pred["infrastructure_damage_vehicle"]
    fig = go.Figure()

    if chart_type == "regime_probs":
        probs = pred["regime_and_optics"]["regime_probabilities"]
        names = list(probs.keys())
        vals = [round(v * 100.0, 1) for v in probs.values()]
        fig.add_trace(go.Bar(x=names, y=vals, marker_color=["#3B82F6" if "Cool" in n else "#FC3D21" for n in names], text=[f"{v}%" for v in vals], textposition="auto"))
        fig.update_layout(title=f"AI Chart: Predicted Flame Regime Probabilities ({model_fuel})", yaxis_title="Probability (%)")
    elif chart_type == "co_timeline":
        dur = max(10.0, pred["duration_and_persistence"]["burn_duration_s"])
        ts = [round(dur * i / 12.0, 1) for i in range(13)]
        co_curve = [round(life["co_concentration_ppm"] * (1.0 - pow(2.71828, -2.2 * (t / max(1.0, dur)))), 2) for t in ts]
        ch2o_curve = [round(life["toxic_formaldehyde_ch2o_mg_m3"] * (t / max(1.0, dur)), 2) for t in ts]
        fig.add_trace(go.Scatter(x=ts, y=co_curve, mode="lines+markers", name="CO (ppm)", line={"color": "#FC3D21", "width": 3}))
        fig.add_hline(y=55.0, line_dash="dash", line_color="#FFB302", annotation_text="NASA 1-hr CO SMAC (55 ppm)")
        fig.add_trace(go.Scatter(x=ts, y=[c * 10.0 for c in ch2o_curve], mode="lines", name="CH₂O ×10 (mg/m³)", line={"color": "#38BDF8", "width": 2}))
        fig.update_layout(title="AI Chart: Toxic Gas Growth & NASA SMAC Margin Over Burn Window", xaxis_title="Elapsed Time (s)", yaxis_title="Concentration (ppm / scaled)")
    elif chart_type == "gravity_sweep":
        gs = [0.0, 0.05, 0.16, 0.38, 0.65, 1.0]
        durs, fluxes = [], []
        for g_val in gs:
            tmp_p, _, _, _, _ = _run_scenario_prediction(predictor, fuel_type, "", g_val, oxygen, pressure, ventilation, area_m2)
            durs.append(tmp_p["duration_and_persistence"]["burn_duration_s"])
            fluxes.append(tmp_p["infrastructure_damage_vehicle"]["radiative_heat_flux_kw_m2"])
        fig.add_trace(go.Scatter(x=gs, y=durs, mode="lines+markers", name="Burn Duration (s)", line={"color": "#02BFE7", "width": 3}))
        fig.add_trace(go.Scatter(x=gs, y=fluxes, mode="lines+markers", name="Radiative Heat Flux (kW/m²)", line={"color": "#FC3D21", "width": 3}))
        fig.update_layout(title="AI Chart: Gravity Sweep (0g Microgravity → 0.16g Lunar → 0.38g Mars → 1.0g Earth)", xaxis_title="Gravity (g)", yaxis_title="Duration (s) / Heat Flux (kW/m²)")
    elif chart_type == "earth_compare":
        metrics = ["Burn Duration (s)", "CO (ppm)", "Heat Flux (kW/m²)", "Peak Temp (÷100 K)"]
        space_vals = [
            pred["duration_and_persistence"]["burn_duration_s"],
            life["co_concentration_ppm"],
            inf["radiative_heat_flux_kw_m2"],
            round(inf["peak_flame_temp_K"] / 100.0, 2),
        ]
        earth_vals = [
            earth_pred["duration_and_persistence"]["burn_duration_s"],
            earth_pred["life_damage_crew"]["co_concentration_ppm"],
            earth_pred["infrastructure_damage_vehicle"]["radiative_heat_flux_kw_m2"],
            round(earth_pred["infrastructure_damage_vehicle"]["peak_flame_temp_K"] / 100.0, 2),
        ]
        fig.add_trace(go.Bar(name=f"Spacecraft ({gravity:.2f}g)", x=metrics, y=space_vals, marker_color="#02BFE7"))
        fig.add_trace(go.Bar(name="Earth Counterpart (1.00g)", x=metrics, y=earth_vals, marker_color="#FC3D21"))
        fig.update_layout(barmode="group", title="AI Chart: Spacecraft Scenario vs. Earth 1.0g Counterpart")
    elif chart_type == "area_sweep":
        areas = [0.2, 0.5, 1.0, 2.0, 4.0, 8.0]
        cos, prs = [], []
        for a_val in areas:
            tmp_p, _, _, _, _ = _run_scenario_prediction(predictor, fuel_type, "", gravity, oxygen, pressure, ventilation, a_val)
            cos.append(tmp_p["life_damage_crew"]["co_concentration_ppm"])
            prs.append(tmp_p["infrastructure_damage_vehicle"]["cabin_pressure_rise_kPa"])
        fig.add_trace(go.Scatter(x=areas, y=cos, mode="lines+markers", name="CO Concentration (ppm)", line={"color": "#FC3D21", "width": 3}))
        fig.add_trace(go.Scatter(x=areas, y=prs, mode="lines+markers", name="Overpressure ΔP (kPa)", line={"color": "#FFB302", "width": 3}))
        fig.update_layout(title="AI Chart: Effect of Compartment Area (Confinement vs. Expansion)", xaxis_title="Enclosure Area (m²)", yaxis_title="CO (ppm) / ΔP (kPa)")
    else:
        labels = ["CO vs 1-hr SMAC", "CH₂O vs SMAC", "Heat Flux vs Avionics", "O₂ Drawdown Risk", "Pressure Rise"]
        ratios = [
            round(life["co_concentration_ppm"] / 55.0, 2),
            round(life["toxic_formaldehyde_ch2o_mg_m3"] / 0.5, 2),
            round(inf["radiative_heat_flux_kw_m2"] / 12.5, 2),
            round(life["o2_consumed_pct_vol"] / 2.0, 2),
            round(inf["cabin_pressure_rise_kPa"] / 10.0, 2),
        ]
        fig.add_trace(go.Bar(x=labels, y=ratios, marker_color=["#FC3D21" if r >= 1.0 else "#02BFE7" for r in ratios], text=[f"{r}×" for r in ratios], textposition="auto"))
        fig.add_hline(y=1.0, line_dash="dash", line_color="#FFB302", annotation_text="1.0× Critical NASA Limit")
        fig.update_layout(title="AI Chart: Normalized Crew Life & Infrastructure Harm Ratios", yaxis_title="Ratio to Threshold (1.0 = Limit)")

    fig.update_layout(height=360, margin=dict(l=15, r=15, t=48, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    if ai_caption:
        st.caption(f"AI Chart Analysis: {ai_caption}")
    else:
        st.caption(
            f"Generated chart `{chart_type}` directly from current scenario outputs "
            f"(CO `{life['co_concentration_ppm']} ppm`, CH₂O `{life['toxic_formaldehyde_ch2o_mg_m3']} mg/m³`, "
            f"Heat Flux `{inf['radiative_heat_flux_kw_m2']} kW/m²`, Burn `{pred['duration_and_persistence']['burn_duration_s']} s`)."
        )


#Used SI for Model training and identifying best datasets
def render():
    combustion_physics.ensure_preset_state()

    
    pending_load = st.session_state.pop("_pending_scenario_load", None)
    if isinstance(pending_load, dict):
        st.session_state["shared_env_preset"] = "Custom"
        for pk in ("sidebar_env_preset", "fl_env_preset", "fp_env_preset"):
            st.session_state[pk] = "Custom"
        if pending_load.get("fuel_type") in combustion_physics.FUEL_TYPES:
            st.session_state["fp_fuel_type"] = pending_load["fuel_type"]
        st.session_state["fp_g"] = float(pending_load.get("gravity_g", 0.0))
        st.session_state["fp_o2"] = float(pending_load.get("o2_pct", 21.0))
        st.session_state["fp_flow"] = float(pending_load.get("flow_cm_s", 0.0))
        st.session_state["fp_p"] = float(pending_load.get("pressure_atm", 1.0))
        st.session_state["fp_area"] = float(pending_load.get("area_m2", 1.0))
        st.session_state["fl_g"] = float(pending_load.get("gravity_g", 0.0))
        st.session_state["fl_o2"] = float(pending_load.get("o2_pct", 21.0))
        st.session_state["fl_flow"] = float(pending_load.get("flow_cm_s", 0.0))
        st.session_state["fl_area"] = float(pending_load.get("area_m2", 1.0))

    st.subheader("Spacecraft Fire Predictor")
    st.caption("Hybrid XGBoost + NASA Microgravity Combustion Physics Predictor calibrated on PSI-69 FLEX, PSI-159 CFI-G, PSI-107 SPICE, PSI-25 BASS-II, and PSI-117.")

    c_top1, c_top2, c_top3 = st.columns([1.2, 1.4, 1.4])
    with c_top1:
        scenario_preset = st.selectbox(
            "Environment Preset",
            combustion_physics.PRESET_OPTIONS,
            key="fp_env_preset",
            on_change=combustion_physics.on_preset_change,
            args=("fp_env_preset",),
        )
        if scenario_preset == "Custom":
            if st.button("Save Custom Preset", key="fp_save_custom", use_container_width=True):
                combustion_physics.save_custom_preset()
                st.success("Custom preset saved.")
    with c_top2:
        exp_context = st.selectbox(
            "Experiment / Mission Context",
            [
                "Auto-Detect from Fuel & Environment",
                "FLEX / FLEX-2 (Droplet)",
                "Saffire I–VI (Large Solid Enclosure)",
                "SoFIE (Polymer Ignition & Quench)",
                "ACME / CFI-G (Gaseous Cool Flame)",
                "BASS / BASS-II (Solid Flow Spread)",
                "SAME / SAME-R (Smouldering Aerosol)",
                "SOFBALL (Premixed Flame Ball)",
                "FLARE / FM2 (Partial Gravity)",
                "DAFT (Dust Discrimination)",
                "PSI-62 (Concurrent Solid Pyrolysis)",
            ],
            index=0,
            key="fp_exp_context",
        )
    with c_top3:
        fuel_type = st.selectbox(
            "Fuel / Material Type",
            combustion_physics.FUEL_TYPES,
            index=0,
            key="fp_fuel_type",
        )

    s_row1_1, s_row1_2, s_row1_3 = st.columns(3)
    with s_row1_1:
        gravity = st.slider(
            "Gravity Level (g)",
            0.0,
            1.0,
            step=0.01,
            key="fp_g",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fp",),
        )
    with s_row1_2:
        oxygen = st.slider(
            "Oxygen Concentration (% O₂)",
            10.0,
            50.0,
            step=0.1,
            key="fp_o2",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fp",),
        )
    with s_row1_3:
        ventilation = st.slider(
            "Cabin Airflow / Ventilation (cm/s)",
            0.0,
            30.0,
            step=0.5,
            key="fp_flow",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fp",),
        )

    s_row2_1, s_row2_2 = st.columns(2)
    with s_row2_1:
        pressure = st.slider(
            "Cabin Pressure (atm)",
            0.3,
            2.0,
            step=0.05,
            key="fp_p",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fp",),
        )
    with s_row2_2:
        area_m2 = st.slider(
            "Enclosure / Sample Area (m²)",
            0.1,
            10.0,
            step=0.1,
            key="fp_area",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fp",),
        )

    
    ds_state = combustion_physics.get_dataset_and_model_state()
    predictor, _ = get_cached_fire_predictor(ds_state["bundle_mtime"])
    pred, earth_pred, state, model_fuel, is_dust = _run_scenario_prediction(
        predictor, fuel_type, exp_context, gravity, oxygen, pressure, ventilation, area_m2
    )
    threat = state["threat"]
    flex_m = combustion_physics.calc_flex_droplet(gravity, oxygen, ventilation)
    saf_m = combustion_physics.calc_saffire_radiation(gravity, oxygen, ventilation)

    dur_info = pred["duration_and_persistence"]
    kin_info = pred["droplet_kinetics"]
    reg_info = pred["regime_and_optics"]
    life_dmg = pred["life_damage_crew"]
    infra_dmg = pred["infrastructure_damage_vehicle"]
    cool_reig = infra_dmg["cool_flame_reignition_risk"]
    est_burn_s = dur_info["burn_duration_s"]
    composite_hazard = _compute_composite_hazard(pred, threat)

    
    bm = ds_state.get("benchmarks", {})
    m3_f1 = bm.get("model3_fire_regime", {}).get("final_test_metrics", {}).get("macro_f1", 0.8329) * 100.0
    m3_ba = bm.get("model3_fire_regime", {}).get("final_test_metrics", {}).get("balanced_accuracy", 0.8208) * 100.0
    m1a_f1 = bm.get("model1a_persistence", {}).get("final_test_metrics", {}).get("macro_f1", 0.7989) * 100.0
    m1b_mae = bm.get("model1b_burn_duration", {}).get("final_test_metrics", {}).get("mae", 18.1)
    m1b_r2 = bm.get("model1b_burn_duration", {}).get("final_test_metrics", {}).get("r2", 0.49)
    m2a_r2 = bm.get("model2a_burning_rate_K", {}).get("final_test_metrics", {}).get("r2", 0.668)
    m5a_r2 = bm.get("model5a_delta_O2_pct", {}).get("final_test_metrics", {}).get("r2", 0.581)
    m5c_r2 = bm.get("model5c_delta_CO_ppm", {}).get("final_test_metrics", {}).get("r2", 0.514)
    psi_k_mae = bm.get("_psi117_validation", {}).get("psi117_cool_K_mae_mm2_s", 0.0378)

    conf_extra = f"\n\n{pred['warning']}" if pred.get("warning") else ""
    st.warning(
        f"**Model Benchmark & Confidence Notice (`{pred['confidence_tier']}` | Trained `{ds_state.get('model_trained_at_utc', 'N/A')[:19]}`):** "
        f"Flame Regime & Cool-Flame Classifier: **{m3_f1:.1f}% Macro-F1** ({m3_ba:.1f}% Balanced Acc) | "
        f"Persistence Stage: **{m1a_f1:.1f}% Macro-F1** | "
        f"Burn Duration MAE: **±{m1b_mae:.1f} s** ($R^2={m1b_r2:.2f}$) | "
        f"Droplet Rate $K$: $R^2={m2a_r2:.2f}$ (PSI-117 Cool-Flame validation MAE `{psi_k_mae} mm²/s`) | "
        f"Enclosure Gas Signatures ($\\Delta \\text{{O}}_2$ / $\\text{{CO}}$): $R^2={m5a_r2:.2f} / {m5c_r2:.2f}$."
        f"{conf_extra}"
    )

    
    evac_triggers = []
    if life_dmg["co_concentration_ppm"] >= 55.0:
        evac_triggers.append(f"CO `{life_dmg['co_concentration_ppm']} ppm` breaches NASA 1-hr SMAC (`55 ppm`)")
    if life_dmg["toxic_formaldehyde_ch2o_mg_m3"] >= 1.5:
        evac_triggers.append(f"Formaldehyde CH₂O `{life_dmg['toxic_formaldehyde_ch2o_mg_m3']} mg/m³` (>3× SMAC)")
    if life_dmg["ambient_o2_remaining_pct"] <= 16.5:
        evac_triggers.append(f"Ambient O₂ drops to `{life_dmg['ambient_o2_remaining_pct']}%` (hypoxia zone)")
    if infra_dmg["radiative_heat_flux_kw_m2"] >= 18.0:
        evac_triggers.append(f"Radiative heat flux `{infra_dmg['radiative_heat_flux_kw_m2']} kW/m²` threatens avionics & panels")
    if infra_dmg["peak_flame_temp_K"] >= 933.0:
        evac_triggers.append(f"Peak temp `{infra_dmg['peak_flame_temp_K']} K` exceeds 6061-T6 Aluminum melt limit (`933 K`)")
    if infra_dmg["cabin_pressure_rise_kPa"] >= 15.0:
        evac_triggers.append(f"Cabin overpressure ΔP `{infra_dmg['cabin_pressure_rise_kPa']} kPa` stresses module seals")
    if cool_reig["cool_flame_active_or_probable"] and oxygen >= 18.0:
        evac_triggers.append(f"Invisible O₂-fed Cool Flame active (hot reignition risk ~`{cool_reig['estimated_hot_reignition_window_s']} s`)")
    if composite_hazard >= 72.0 and not is_dust:
        evac_triggers.append(f"Composite Hazard Score `{composite_hazard}/100`")

    if evac_triggers and est_burn_s > 0.1 and not is_dust:
        st.markdown(
            f"""
            <div style="border: 2px solid #FF2E2E; background: rgba(255, 30, 30, 0.14); padding: 18px 20px; border-radius: 10px; margin: 10px 0 16px 0;">
                <div style="color: #FF2E2E; font-size: 1.55rem; font-weight: 900; letter-spacing: 0.02em; line-height: 1.25;">
                    EVACUATION & CRITICAL EMERGENCY MEASURE REQUIRED
                </div>
                <div style="color: #FFE4E6; font-size: 1.02rem; font-weight: 700; margin-top: 8px;">
                    Immediate hatch isolation, crew evacuation from affected module, Portable Breathing Apparatus (PBA) donning, and full ECLSS airflow shutoff recommended.
                    {' Do NOT restore oxygen ventilation for at least 45 minutes — invisible Cool Flame hot reignition risk detected!' if cool_reig['cool_flame_active_or_probable'] else ''}
                </div>
                <div style="color: #FCA5A5; font-size: 0.90rem; margin-top: 6px;">
                    Triggered by: {' | '.join(evac_triggers)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    #Add what would be input, what is predicted output, what fire happens, behaviour of the fire dependent on space and temperature alogn with methods of prevention and precaution measures
    with st.container(border=True):
        st.markdown("##### Live XGBoost + Physics Prediction Summary")
        st.caption(
            f"Preset: `{scenario_preset}` | Context: `{exp_context}` | Fuel Mapping: `{model_fuel}` ({pred['inputs']['phase']}) | Matched Suite: `{state['code']}` ({state['surety_pct']}% Surety)"
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Predicted Burn Duration", f"{est_burn_s} s", delta=dur_info["persistence_stage"].replace("_", " "))
        m2.metric("Flame Regime", reg_info["fire_regime"].replace("_", " "))
        m3.metric("Droplet Burn K / d_ext", f"{kin_info['burning_rate_K_mm2_s']} mm²/s", delta=f"d_ext {kin_info['extinction_diameter_mm']} mm")
        m4.metric("Composite Hazard Score", f"{composite_hazard} / 100", delta=threat["threat_tier"])

        st.info(
            f"**Duration & Optics:** {dur_info['duration_statement']} | "
            f"**Optical Signature:** `{reg_info['flame_colour']}` | "
            f"**Physics Behavior:** {state['optical_regime_desc']}"
        )
        if cool_reig["cool_flame_active_or_probable"]:
            st.error(
                f"**Cool Flame Alert (`P = {cool_reig['cool_flame_probability']*100:.1f}%`):** "
                f"{cool_reig['mechanism_note']} Estimated secondary hot reignition window: `{cool_reig['estimated_hot_reignition_window_s']} s`."
            )

    
    with st.container(border=True):
        st.markdown("##### AI Chart Studio — Ask for Any Custom Chart from These Results")
        ch_c1, ch_c2 = st.columns([5, 1])
        with ch_c1:
            ai_chart_req = st.text_input(
                "Ask AI to generate a chart based on these prediction results",
                placeholder="e.g., CO and CH2O timeline vs SMAC, gravity sweep 0g to 1g, regime probabilities, less space sensitivity, Earth vs Space...",
                key="fp_ai_chart_query",
            )
        with ch_c2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Plot", key="fp_ai_chart_btn", use_container_width=True)

        qp1, qp2, qp3, qp4 = st.columns(4)
        qp1.button("Regime Probabilities", key="fp_qp1", use_container_width=True, on_click=_set_fp_chart_query, args=("Show predicted flame regime probabilities",))
        qp2.button("CO & CH₂O vs SMAC", key="fp_qp2", use_container_width=True, on_click=_set_fp_chart_query, args=("Plot CO and CH2O concentration timeline vs NASA SMAC limits",))
        qp3.button("Gravity Sweep (0g–1g)", key="fp_qp3", use_container_width=True, on_click=_set_fp_chart_query, args=("Show gravity sweep from 0g to 1g for duration and heat flux",))
        qp4.button("Space vs Earth 1.0g", key="fp_qp4", use_container_width=True, on_click=_set_fp_chart_query, args=("Compare Space scenario vs Earth 1g counterpart",))

        if ai_chart_req and ai_chart_req.strip():
            _render_ai_generated_chart(
                ai_chart_req, predictor, model_fuel, fuel_type, gravity, oxygen, pressure, ventilation, area_m2, pred, earth_pred
            )

    
    with st.expander("Precautions (Before Ignition) & Conditional 'If-Then' Space / Condition Scenarios", expanded=True):
        st.markdown("###### Precautions to Avoid Ignition")
        st.markdown(f"- **Primary Material / Atmosphere Protocol:** {state['prevention']}")
        st.markdown(
            f"- **Operational Guardrails (`{model_fuel}` at `{oxygen:.1f}% O₂`, `{pressure:.2f} atm`):** "
            f"{'Enforce UV/CH₂O* (350–450 nm) optical monitoring around alkane droplets and purge O₂ pocket traps; ' if cool_reig['eclss_o2_sustained_hazard'] else ''}"
            f"Keep combustibles clear of `{area_m2:.1f} m²` avionics airflow stagnation corners and verify `{gravity:.2f}g` material LOC limits before powering heaters."
        )

        st.markdown("###### If-Then Contingency Scenarios (Including 'If Less Space')")
        confined_area = round(max(0.15, min(0.45, area_m2 * 0.45)), 2)
        tight_pred, _, _, _, _ = _run_scenario_prediction(
            predictor, fuel_type, exp_context, gravity, oxygen, pressure, ventilation, confined_area
        )
        tight_co = tight_pred["life_damage_crew"]["co_concentration_ppm"]
        tight_dp = tight_pred["infrastructure_damage_vehicle"]["cabin_pressure_rise_kPa"]
        tight_ch2o = tight_pred["life_damage_crew"]["toxic_formaldehyde_ch2o_mg_m3"]

        if_c1, if_c2 = st.columns(2)
        with if_c1:
            st.markdown(
                f"- **If LESS SPACE / Confined Bay (`{confined_area} m²` vs `{area_m2:.1f} m²`):** "
                f"Thermal wall feedback traps heat, shifting combustion toward cool-flame / smouldering incomplete oxidation. "
                f"CO spikes from `{life_dmg['co_concentration_ppm']} ppm` → **`{tight_co} ppm`**, CH₂O climbs to **`{tight_ch2o} mg/m³`**, "
                f"and chamber ΔP jumps to **`{tight_dp} kPa`** with longer HCl/HF wall adsorption sensor lag."
            )
            st.markdown(
                f"- **If MORE SPACE / Open Module (`> 2.5 m²`):** Exposed solid pyrolysis surface accelerates ($\\propto A^{{0.42}}$), "
                f"while 0g spherical smoke dispersion dilutes particulates away from ceiling detectors, extending detection lag."
            )
        with if_c2:
            st.markdown(
                f"- **If COOL FLAME Enters (`500–800 K`, NO Visible Soot):** Visible cameras see total extinguishment, yet ECLSS O₂ supply sustains silent fuel consumption. "
                f"Restoring airflow or opening vents triggers sudden **hot reignition within `~{cool_reig['estimated_hot_reignition_window_s'] or 35.0} s`**."
            )
            st.markdown(
                f"- **If VENTILATION Drops `< 2 cm/s` vs Surges `> 15 cm/s`:** At `0g`, low flow (`<2 cm/s`) starves O₂ and cools flame toward radiative quench; "
                f"high flow (`>15 cm/s`) blows O₂ into the pyrolysis zone like a blowtorch, driving heat flux above `{infra_dmg['radiative_heat_flux_kw_m2']} kW/m²`."
            )

    
    with st.expander("Preventions (If Fire Occurs) & Possible Collateral / Damage", expanded=True):
        st.markdown("###### Active Prevention & Emergency Response Actions (If This Happens)")
        st.markdown(f"- **Detection & Verification:** {state['detection']}")
        st.markdown(f"- **Suppression & Containment:** {state['suppression']}")
        st.markdown(
            f"- **Mandatory Isolation Sequence:** Cut fan power (`{ventilation:.1f} cm/s` → `0 cm/s`) immediately, seal module dampers, "
            f"{'maintain 45-minute zero-flow hold to prevent cool-flame hot reignition,' if cool_reig['cool_flame_active_or_probable'] else 'monitor gas CO/CO₂ decay curve before re-entry,'} "
            f"and purge scrubbed atmosphere."
        )

        imp1, imp2 = st.columns(2)
        with imp1:
            st.markdown("###### Possible Life / Crew Collateral & Damage")
            st.markdown(
                f"- **Carbon Monoxide (CO):** `{life_dmg['co_concentration_ppm']} ppm` (NASA 1-hr SMAC: `{life_dmg['nasa_smac_1hr_co_ppm']} ppm` | 24-hr: `{life_dmg['nasa_smac_24hr_co_ppm']} ppm`)\n"
                f"- **Formaldehyde (CH₂O) Yield:** `{life_dmg['toxic_formaldehyde_ch2o_mg_m3']} mg/m³` (NASA SMAC: `{life_dmg['nasa_smac_ch2o_mg_m3']} mg/m³`)\n"
                f"- **O₂ Depletion & Residual Air:** `-{life_dmg['o2_consumed_pct_vol']}%` consumed → `{life_dmg['ambient_o2_remaining_pct']}% O₂` left (Hypoxia limit: `15.0%`)\n"
                f"- **CO₂ Accumulation & Purser FED Dose:** `+{life_dmg['co2_added_pct_vol']}% CO₂` | Incapacitation FED Ratio: `{life_dmg['fractional_effective_dose_fed']}` | Time to CO SMAC: `{life_dmg['time_to_crew_co_smac_s'] or 'N/A'} s`"
            )
        with imp2:
            st.markdown("###### Possible Infrastructure & Hardware Collateral")
            st.markdown(
                f"- **Surface Radiative Heat Flux:** `{infra_dmg['radiative_heat_flux_kw_m2']} kW/m²` (Avionics/Cable damage threshold: `{infra_dmg['avionics_damage_flux_threshold_kw_m2']} kW/m²`)\n"
                f"- **Peak Flame Temperature:** `{infra_dmg['peak_flame_temp_K']} K` vs Structural 6061-T6 Aluminum melt (`{infra_dmg['aluminum_6061_melt_K']} K`)\n"
                f"- **Cabin Overpressure ($\\Delta P$):** `+{infra_dmg['cabin_pressure_rise_kPa']} kPa` ($P_{{max}}/P_0 =$ `{infra_dmg['pressure_ratio_Pmax_P0']}×`)\n"
                f"- **Burned / Charred Collateral Area:** `{infra_dmg['char_length_cm']} cm` char length (`{infra_dmg['damaged_area_m2']} m²` affected surface)"
            )

    
    with st.expander("Earth Counterpart (1.0g Terrestrial Baseline) Comparison", expanded=True):
        e_dur = earth_pred["duration_and_persistence"]["burn_duration_s"]
        e_reg = earth_pred["regime_and_optics"]
        e_life = earth_pred["life_damage_crew"]
        e_inf = earth_pred["infrastructure_damage_vehicle"]

        ec1, ec2, ec3, ec4 = st.columns(4)
        ec1.metric("Earth Burn Duration (1g)", f"{e_dur} s", delta=f"{round(est_burn_s - e_dur, 1):+g} s in {gravity:.2f}g")
        ec2.metric("Earth Regime & Colour", e_reg["fire_regime"].replace("_", " "), delta=e_reg["flame_colour"])
        ec3.metric("Earth CO / CH₂O", f"{e_life['co_concentration_ppm']} ppm", delta=f"CH₂O {e_life['toxic_formaldehyde_ch2o_mg_m3']} mg/m³")
        ec4.metric("Earth Heat Flux / Temp", f"{e_inf['radiative_heat_flux_kw_m2']} kW/m²", delta=f"{e_inf['peak_flame_temp_K']} K")

        comp_df = pd.DataFrame(
            [
                {"Metric": "Burn Duration (s)", f"Spacecraft ({gravity:.2f}g)": est_burn_s, "Earth Counterpart (1.00g)": e_dur},
                {"Metric": "Flame Regime", f"Spacecraft ({gravity:.2f}g)": reg_info["fire_regime"], "Earth Counterpart (1.00g)": e_reg["fire_regime"]},
                {"Metric": "Optical Color", f"Spacecraft ({gravity:.2f}g)": reg_info["flame_colour"], "Earth Counterpart (1.00g)": e_reg["flame_colour"]},
                {"Metric": "Burning Rate K (mm²/s)", f"Spacecraft ({gravity:.2f}g)": kin_info["burning_rate_K_mm2_s"], "Earth Counterpart (1.00g)": earth_pred["droplet_kinetics"]["burning_rate_K_mm2_s"]},
                {"Metric": "CO Concentration (ppm)", f"Spacecraft ({gravity:.2f}g)": life_dmg["co_concentration_ppm"], "Earth Counterpart (1.00g)": e_life["co_concentration_ppm"]},
                {"Metric": "CH₂O Yield (mg/m³)", f"Spacecraft ({gravity:.2f}g)": life_dmg["toxic_formaldehyde_ch2o_mg_m3"], "Earth Counterpart (1.00g)": e_life["toxic_formaldehyde_ch2o_mg_m3"]},
                {"Metric": "Radiative Heat Flux (kW/m²)", f"Spacecraft ({gravity:.2f}g)": infra_dmg["radiative_heat_flux_kw_m2"], "Earth Counterpart (1.00g)": e_inf["radiative_heat_flux_kw_m2"]},
                {"Metric": "Peak Temperature (K)", f"Spacecraft ({gravity:.2f}g)": infra_dmg["peak_flame_temp_K"], "Earth Counterpart (1.00g)": e_inf["peak_flame_temp_K"]},
            ]
        )
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        st.caption(
            "Why Earth (1.0g) differs: Buoyant convection immediately pulls hot soot and combustion gases upward in a teardrop plume, "
            "preventing the quasi-steady spherical 500–800 K Cool Flame plateau observed in 0g FLEX/CFI-G tests."
        )

    
    auth_user = st.session_state.get("auth_user")
    with st.container(border=True):
        st.markdown("##### Save Scenario to Account & History")
        if not auth_user:
            st.warning("You are not signed in. Please sign in via the sidebar **User Authentication** panel to save, rank, rename, and sync scenarios to your Profile tab.")
            if st.button("Save Scenario (Sign In Required)", key="fp_save_guest_btn"):
                st.error("Please sign in from the sidebar User Authentication panel first so this scenario can sync to your account.")
        else:
            sv1, sv2, sv3 = st.columns([3.0, 1.2, 1.4])
            default_scen_name = f"{model_fuel} ({gravity:.2f}g, {oxygen:.0f}% O₂)"
            with sv1:
                scen_name = st.text_input("Scenario Name", value=default_scen_name, key="fp_save_scen_name")
            with sv2:
                scen_rank = st.number_input("Priority Rank (1 = Top)", min_value=1, max_value=5, value=2, step=1, key="fp_save_scen_rank")
            with sv3:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("Save Scenario to Account", key="fp_save_scen_btn", use_container_width=True):
                    now_ts = datetime.now(timezone.utc).isoformat()
                    scen_ver = max(ds_state.get("model_trained_at_utc", ""), ds_state.get("last_admin_change_utc", ""), now_ts)
                    rec = {
                        "id": str(uuid.uuid4())[:8],
                        "name": (scen_name or default_scen_name).strip(),
                        "user_rank": int(scen_rank),
                        "inputs": {
                            "fuel_type": fuel_type,
                            "exp_context": exp_context,
                            "gravity_g": float(gravity),
                            "o2_pct": float(oxygen),
                            "flow_cm_s": float(ventilation),
                            "pressure_atm": float(pressure),
                            "area_m2": float(area_m2),
                        },
                        "model_fuel": model_fuel,
                        "burn_duration_s": est_burn_s,
                        "fire_regime": reg_info["fire_regime"],
                        "flame_colour": reg_info["flame_colour"],
                        "composite_hazard": composite_hazard,
                        "co_ppm": life_dmg["co_concentration_ppm"],
                        "ch2o_mg_m3": life_dmg["toxic_formaldehyde_ch2o_mg_m3"],
                        "heat_flux_kw_m2": infra_dmg["radiative_heat_flux_kw_m2"],
                        "fed": life_dmg["fractional_effective_dose_fed"],
                        "confidence_tier": pred["confidence_tier"],
                        "model_version_utc": scen_ver,
                        "evaluated_at_utc": now_ts,
                    }
                    combustion_physics.save_user_scenario(auth_user, rec)
                    st.success(f"Saved '{rec['name']}' to account `{auth_user}` (synced with your Profile tab).")
                    st.rerun()

    
    if auth_user:
        saved_scenarios = combustion_physics.load_user_scenarios(auth_user)
        with st.expander(f"Scenario History & Ranking ({len(saved_scenarios)} saved for {auth_user})", expanded=bool(saved_scenarios)):
            if not saved_scenarios:
                st.caption("No scenarios saved yet. Save a scenario above to track, rank, and compare across conditions.")
            else:
                latest_data_ts = ds_state.get("last_admin_change_utc", "")
                latest_model_ts = ds_state.get("model_trained_at_utc", "")

                stale_ids = set()
                for sc in saved_scenarios:
                    s_ver = sc.get("model_version_utc", "") or sc.get("evaluated_at_utc", "")
                    if (latest_data_ts and s_ver < latest_data_ts) or (latest_model_ts and s_ver < latest_model_ts):
                        stale_ids.add(sc.get("id"))

                if stale_ids:
                    st.warning(
                        f"**Update Recommended (`{len(stale_ids)}` outdated scenario(s)):** New dataset files or records were added in Admin "
                        f"(and models retrained at `{latest_model_ts[:19]}`). Please click **Rerun & Update** on highlighted scenarios below to refresh results."
                    )

                rank_mode = st.selectbox(
                    "Rank Scenarios By",
                    [
                        "Overall Composite Hazard (High → Low)",
                        "Crew Life Harm — CO & FED (High → Low)",
                        "Infrastructure Harm — Heat Flux (High → Low)",
                        "Burn Duration (Long → Short)",
                        "User Priority Rank (1 → 5)",
                    ],
                    index=0,
                    key="fp_history_rank_mode",
                )

                if rank_mode == "Crew Life Harm — CO & FED (High → Low)":
                    ordered = sorted(saved_scenarios, key=lambda x: (float(x.get("co_ppm", 0.0)), float(x.get("fed", 0.0))), reverse=True)
                elif rank_mode == "Infrastructure Harm — Heat Flux (High → Low)":
                    ordered = sorted(saved_scenarios, key=lambda x: float(x.get("heat_flux_kw_m2", 0.0)), reverse=True)
                elif rank_mode == "Burn Duration (Long → Short)":
                    ordered = sorted(saved_scenarios, key=lambda x: float(x.get("burn_duration_s", 0.0)), reverse=True)
                elif rank_mode == "User Priority Rank (1 → 5)":
                    ordered = sorted(saved_scenarios, key=lambda x: (int(x.get("user_rank", 3)), -float(x.get("composite_hazard", 0.0))))
                else:
                    ordered = sorted(saved_scenarios, key=lambda x: float(x.get("composite_hazard", 0.0)), reverse=True)

                board_rows = []
                for pos, sc in enumerate(ordered, start=1):
                    inp = sc.get("inputs", {})
                    sid = sc.get("id")
                    board_rows.append(
                        {
                            "Rank #": pos,
                            "Priority": f"#{sc.get('user_rank', 3)}",
                            "Scenario Name": sc.get("name", "Untitled"),
                            "Status": "Rerun Needed" if sid in stale_ids else "Up to Date",
                            "Env": f"{inp.get('gravity_g', 0.0):.2f}g / {inp.get('o2_pct', 21.0):.1f}% O₂ / {inp.get('area_m2', 1.0):.1f} m²",
                            "Duration (s)": sc.get("burn_duration_s", 0.0),
                            "Regime": sc.get("fire_regime", ""),
                            "CO (ppm)": sc.get("co_ppm", 0.0),
                            "Flux (kW/m²)": sc.get("heat_flux_kw_m2", 0.0),
                            "Hazard (/100)": sc.get("composite_hazard", 0.0),
                        }
                    )
                st.dataframe(pd.DataFrame(board_rows), use_container_width=True, hide_index=True)

                for pos, sc in enumerate(ordered, start=1):
                    sid = sc.get("id", f"s{pos}")
                    inp = sc.get("inputs", {})
                    is_stale = sid in stale_ids
                    with st.container(border=True):
                        h_c1, h_c2 = st.columns([3.5, 2.5])
                        with h_c1:
                            badge = "⚠️ **Rerun & Update Needed**" if is_stale else "✅ **Synced & Current**"
                            st.markdown(f"**Rank #{pos}: {sc.get('name', 'Untitled')}** (User Priority `#{sc.get('user_rank', 3)}`) — {badge}")
                            st.caption(
                                f"Fuel: `{sc.get('model_fuel', 'Heptane')}` | `{inp.get('gravity_g', 0.0):.2f}g` | `{inp.get('o2_pct', 21.0):.1f}% O₂` | "
                                f"`{inp.get('pressure_atm', 1.0):.2f} atm` | `{inp.get('area_m2', 1.0):.1f} m²` | "
                                f"Burn `{sc.get('burn_duration_s', 0.0)} s` | Hazard `{sc.get('composite_hazard', 0.0)}/100`"
                            )
                        with h_c2:
                            b1, b2, b3 = st.columns(3)
                            with b1:
                                if st.button("Load", key=f"hist_ld_{sid}_{pos}", use_container_width=True):
                                    st.session_state["_pending_scenario_load"] = inp
                                    st.rerun()
                            with b2:
                                if st.button("Rerun & Update", key=f"hist_rr_{sid}_{pos}", use_container_width=True):
                                    new_p, _, new_st, new_mf, _ = _run_scenario_prediction(
                                        predictor,
                                        inp.get("fuel_type", combustion_physics.FUEL_TYPES[0]),
                                        inp.get("exp_context", "Auto-Detect from Fuel & Environment"),
                                        float(inp.get("gravity_g", 0.0)),
                                        float(inp.get("o2_pct", 21.0)),
                                        float(inp.get("pressure_atm", 1.0)),
                                        float(inp.get("flow_cm_s", 0.0)),
                                        float(inp.get("area_m2", 1.0)),
                                    )
                                    now_ts = datetime.now(timezone.utc).isoformat()
                                    sc["model_fuel"] = new_mf
                                    sc["burn_duration_s"] = new_p["duration_and_persistence"]["burn_duration_s"]
                                    sc["fire_regime"] = new_p["regime_and_optics"]["fire_regime"]
                                    sc["flame_colour"] = new_p["regime_and_optics"]["flame_colour"]
                                    sc["composite_hazard"] = _compute_composite_hazard(new_p, new_st["threat"])
                                    sc["co_ppm"] = new_p["life_damage_crew"]["co_concentration_ppm"]
                                    sc["ch2o_mg_m3"] = new_p["life_damage_crew"]["toxic_formaldehyde_ch2o_mg_m3"]
                                    sc["heat_flux_kw_m2"] = new_p["infrastructure_damage_vehicle"]["radiative_heat_flux_kw_m2"]
                                    sc["fed"] = new_p["life_damage_crew"]["fractional_effective_dose_fed"]
                                    sc["confidence_tier"] = new_p["confidence_tier"]
                                    sc["model_version_utc"] = max(latest_model_ts, latest_data_ts, now_ts)
                                    sc["evaluated_at_utc"] = now_ts
                                    combustion_physics.save_user_scenario(auth_user, sc)
                                    st.success(f"Updated '{sc.get('name')}' with latest retrained model.")
                                    st.rerun()
                            with b3:
                                if st.button("Delete", key=f"hist_dl_{sid}_{pos}", use_container_width=True):
                                    combustion_physics.delete_user_scenario(auth_user, sid)
                                    st.rerun()

#https://psi.nasa.gov/physci/repo/data/investigations/PSI-102 if time
#DATASETS LOADED
#reference to ppt's and such (add in data)for precatution along with hard coded data
