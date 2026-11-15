#3D movable real-time flame 
#SI used for debugging logic,mock calculations, to be replaced with NASA FLEX-2 data and equations and other relevant datasets
import streamlit as st
import numpy as np
import plotly.graph_objects as go
try:
    from Pages import combustion_physics
except ImportError:
    import combustion_physics


def compute_field(g, o2_pct, flow, morph=None):
    #Doing a 4x4x4 grid of points to represent the flame in 3D space, with the shape and color of the flame changing based on the input parameters.
    #0g : sphere ; 1g: tear drop [Considered experimental data from NASA FLEX-2]
    #To be optimized into detecting different experimental categories before predicting and changing colours based on that
    n_points = 32
    xy_axis = np.linspace(-2.2, 2.2, n_points)
    z_axis = np.linspace(-1.5, 4.2, n_points)
    X, Y, Z = np.meshgrid(xy_axis, xy_axis, z_axis)
    buoyancy_stretch = morph["buoyancy_stretch"] if morph else (1.0 + (1.8 * g))
    #hotness of flamer proportional to oxygen 
    size_factor = morph["size_factor"] if morph else ((o2_pct / 21.0) * 0.9)
    #airflow pushes the flame in the direction of flow, creating a teardrop shape
    #Taking X axis as the direction of flow.
    x_drift = morph["x_drift"] if morph else ((flow / 20.0) * 0.6)
    X_shifted = X - x_drift
    # Points above the center (Z > 0) stretch upward more than points below (Z < 0)
    Z_modified = np.where(Z > 0, Z / buoyancy_stretch, Z * 1.2)
    radial_pinch = 1.0 + 0.28 * g * np.clip(Z / max(1.0, buoyancy_stretch), 0.0, 1.5)
    Radius = ((X_shifted * radial_pinch)**2) + ((Y * radial_pinch)**2) + (Z_modified**2)
    #Thermal Gradient using Gaussian decay (Asymptotic tail : value decreases as we move towards 0;  Unlike sharp or linear cutoffs, the drop-off starts slow near the peak, accelerates in the middle, and then flattens out smoothly at greater distances)
    temp_scale = morph["temp_scale"] if morph else (0.4 + 0.6 * ((o2_pct - 15.0) / 20.0))
    intensity = 1000.0 * temp_scale * np.exp(-Radius / (size_factor ** 2))
    return X, Y, Z, intensity

#Need to debug the movement, consider different cases, and give colour accurate representations from the NASA experiment observations.
DYNAMIC_FLAME_SCALE = [
    [0.0, "#0B3D91"],
    [0.35, "#02BFE7"],
    [0.6, "#FC3D21"],
    [0.85, "#FFB302"],
    [1.0, "#FFFFFF"]
]


def render():
    combustion_physics.ensure_preset_state()
    st.subheader("3D Flame Morphing Lab")

    col1, col2 = st.columns([1, 2.5])
    with col1:
        fuel_type = st.selectbox(
            "Fuel / Material Type",
            combustion_physics.FUEL_TYPES,
            index=0,
            key="fl_fuel_type"
        )
        scenario_preset = st.selectbox(
            "Environment Preset",
            combustion_physics.PRESET_OPTIONS,
            key="fl_env_preset",
            on_change=combustion_physics.on_preset_change,
            args=("fl_env_preset",),
        )

        gravity = st.slider(
            "Gravity Level (g)",
            0.0,
            1.0,
            step=0.01,
            key="fl_g",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fl",),
        )
        oxygen = st.slider(
            "Oxygen Concentration (% O₂)",
            15.0,
            35.0,
            step=0.1,
            key="fl_o2",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fl",),
        )
        ventilation = st.slider(
            "Cabin Airflow / Ventilation (cm/s)",
            0.0,
            20.0,
            step=0.5,
            key="fl_flow",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fl",),
        )
        area_m2 = st.slider(
            "Enclosure / Sample Area (m²)",
            0.1,
            10.0,
            step=0.1,
            key="fl_area",
            on_change=combustion_physics.on_slider_change_to_custom,
            args=("fl",),
        )
        colorscheme = st.selectbox("Color Palette", ["Dynamic (Experiment Optical)", "Dynamic (Temp)", "Hot", "Inferno", "Turbo", "Plasma"], key="fl_colorscheme")
        if scenario_preset == "Custom":
            if st.button("Save Custom Preset", key="fl_save_custom", use_container_width=True):
                combustion_physics.save_custom_preset()
                st.success("Custom preset profile saved.")

        state = combustion_physics.evaluate_combustion_state(fuel_type, gravity, oxygen, ventilation, area_m2=area_m2)
        st.markdown(
            f"**Detected Suite:** `{state['code']}`  \n"
            f"**Category Surety:** `{state['surety_pct']}%`  \n"
            f"**Threat Level:** `{state['threat']['threat_score']}/100 ({state['threat']['threat_tier']})`  \n"
            f"**Area Regime:** {state['area_scaling']['area_regime']}  \n"
            f"**Regime:** {state['regime_label']}"
        )
        st.caption(state["optical_regime_desc"])

    with col2:
        X, Y, Z, intensity = compute_field(gravity, oxygen, ventilation, state["morphology_params"])
        if colorscheme == "Dynamic (Experiment Optical)":
            active_scale = state["colorscale"]
        elif colorscheme == "Dynamic (Temp)":
            active_scale = state["temp_colorscale"]
        else:
            active_scale = colorscheme
        fig = go.Figure(data=go.Isosurface(
            x=X.flatten(),
            y=Y.flatten(),
            z=Z.flatten(),
            value=intensity.flatten(),
            isomin=150 if state["is_cool_flame"] else 200,
            isomax=900,
            surface_count=4,
            colorscale=active_scale,
            caps=dict(x_show=False, y_show=False, z_show=False),
            opacity=0.65,
            colorbar=dict(
                title=dict(
                    text="Thermal Intensity (A.U.)",
                    font=dict(color="#E9EEF6")
                ),
                tickfont=dict(color="#E9EEF6")
            )
        ))
        fig.update_layout(
            height=500,
            uirevision="flame_cam",
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#0B0D17",
            scene=dict(
                aspectmode="data",
                xaxis=dict(backgroundcolor="#0B0D17", gridcolor="#1C2A44", showbackground=True),
                yaxis=dict(backgroundcolor="#0B0D17", gridcolor="#1C2A44", showbackground=True),
                zaxis=dict(backgroundcolor="#0B0D17", gridcolor="#1C2A44", showbackground=True),
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander(f"View Governing Equation — {state['equation_name']} ({state['surety_pct']}% Surety)", expanded=False):
            st.latex(state["equation_latex"])
            metric_items = list(state["metrics"].items())
            for row_start in range(0, len(metric_items), 4):
                row_items = metric_items[row_start:row_start + 4]
                m_cols = st.columns(len(row_items))
                for idx, (k, v) in enumerate(row_items):
                    m_cols[idx].metric(k, str(v))