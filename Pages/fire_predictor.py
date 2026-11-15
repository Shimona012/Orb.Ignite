#Predicting fire in spacecrafts based on NASA flight test data and other relevant datasets.
import streamlit as st
try:
    from Pages import combustion_physics
except ImportError:
    import combustion_physics


def render():
    combustion_physics.ensure_preset_state()
    st.subheader("Spacecraft Fire Predictor")
    st.caption("Scenario comparison against documented NASA flight test conditions (XGBoost model staging & theoretical physics baseline).")

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

    state = combustion_physics.evaluate_combustion_state(
        fuel_type,
        gravity,
        oxygen,
        ventilation,
        pressure_atm=pressure,
        area_m2=area_m2,
    )
    threat = state["threat"]
    flex_m = combustion_physics.calc_flex_droplet(gravity, oxygen, ventilation)
    saf_m = combustion_physics.calc_saffire_radiation(gravity, oxygen, ventilation)
    est_burn_s = round(
        max(0.5, flex_m["Droplet Lifetime t_burn (s)"] * (0.75 + 0.55 * (area_m2 ** 0.35)) * (21.0 / max(10.0, oxygen))),
        1,
    )
    p_ratio = round(1.0 + (0.045 * (oxygen / 21.0) * (area_m2 ** 0.5) * (1.0 / max(0.3, pressure))), 3)

    if oxygen > 35.0 or pressure < 0.5 or pressure > 1.3 or area_m2 > 4.0 or state["surety_pct"] < 75.0:
        st.warning(
            "Theoretical Extrapolation Notice: Selected parameters extend outside standard ISS PSI test bounds; "
            "values below reflect physics-based baseline scaling until the trained XGBoost model is integrated."
        )

    #Add what would be input, what is predicted output, what fire happens, behaviour of the fire dependent on space and temperature alogn with methods of prevention and precaution measures
    with st.container(border=True):
        st.markdown("##### Fire Regime & Burn Duration Summary (Theoretical Physics Baseline — Model Pending)")
        st.caption(
            f"Preset: `{scenario_preset}` | Context: `{exp_context}` | Matched Suite: `{state['code']}` ({state['surety_pct']}% Surety)"
        )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Predicted Regime", "Cool Flame" if state["is_cool_flame"] else ("Quenching" if state["is_extinguished"] else "Hot Flame"))
        m2.metric("Estimated Burn Duration", f"{est_burn_s} s")
        m3.metric("Threat Score (0–100)", f"{threat['threat_score']} ({threat['threat_tier']})")
        m4.metric("Radiative Loss q_rad", f"{saf_m['Radiative Loss q_rad (kW/m²)']} kW/m²")
        st.info(state["optical_regime_desc"])

    with st.expander("Impact of Space: Life Damage vs. Infrastructure Damage", expanded=True):
        imp1, imp2 = st.columns(2)
        with imp1:
            st.markdown("###### Life / Crew Physiological Hazard")
            co_risk = "ELEVATED (Silent CH₂O*/CO)" if state["is_cool_flame"] else ("MODERATE–HIGH" if oxygen >= 23.0 else "NOMINAL–MODERATE")
            o2_draw_pct_min = round(0.08 * (oxygen / 21.0) * (area_m2 ** 0.5) * (1.0 + 0.04 * ventilation), 3)
            st.markdown(
                f"- **Toxic CO / Aldehyde Risk:** `{co_risk}`\n"
                f"- **Localized O₂ Depletion Rate:** `~{o2_draw_pct_min}% / min` per enclosed segment\n"
                f"- **Sensor Detection Lag:** `{threat['detection_lag_s']} s` ({'Cool flames emit zero visible smoke before toxic buildup' if state['is_cool_flame'] else 'Microgravity smoke agglomeration shifts optical scattering'})"
            )
        with imp2:
            st.markdown("###### Spacecraft Infrastructure & Avionics Hazard")
            st.markdown(
                f"- **Enclosure Pressure Ratio ($P_{{max}}/P_0$):** `{p_ratio}×` at `{pressure:.2f} atm`\n"
                f"- **Surface Flame Spread ($V_f$):** `{saf_m['Spread Rate V_f (mm/s)']} mm/s` | Exposure Factor `EF = {threat['exposure_factor_EF']}`\n"
                f"- **Cable / Panel Thermal Risk:** `{'HIGH (Sustained O₂ & radiative feedback)' if threat['threat_score'] >= 70 else 'MODERATE (Contained within local boundary)'}`"
            )

    with st.expander("Prevention, Detection & Suppression Precautions", expanded=False):
        st.markdown(f"**Prevention Protocol:** {state['prevention']}")
        st.markdown(f"**Detection Strategy:** {state['detection']}")
        st.markdown(f"**Suppression Action:** {state['suppression']}")

    with st.expander("Model Predictions & Parametric Charts Workspace (Staging)", expanded=False):
        st.caption(
            "Workspace reserved for the separately trained & validated XGBoost multi-target prediction suite "
            "(Burning Rate K, Spread Velocity V_f, Peak Temp, P_max/P_0, and Regime Probability Curves)."
        )
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.container(border=True).markdown(
                "**XGBoost Prediction Slot (Pending Integration)**  \n"
                "Will populate trained regression & multi-class fire regime confidence intervals once model artifacts are validated."
            )
        with p_col2:
            st.container(border=True).markdown(
                "**Parametric Sensitivity Charts Slot (Pending Integration)**  \n"
                "Will expand here with Gravity vs. Limiting Oxygen Concentration (LOC) envelopes and feature importance plots."
            )

#https://psi.nasa.gov/physci/repo/data/investigations/PSI-102 if time
#DATASETS LOADED
#need to train using XG BOOST
#reference to ppt's and such (add in data)for precatution along with hard coded data
