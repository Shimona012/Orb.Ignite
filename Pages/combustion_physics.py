#SI genereated document based on human research but haphazard compilation of NASA microgravity combustion experiments.
#Left to be human-audited and edited for clarity, accuracy, and completeness.
import json
import math
import os
import numpy as np
import pandas as pd
import streamlit as st

SIGMA_SB = 5.6704e-8
R_UNIV = 8.314462

PRESET_OPTIONS = [
    "ISS Microgravity (0g)",
    "Lunar Gateway (0.16g)",
    "Mars Habitat (0.38g)",
    "Earth Lab (1.0g)",
    "Custom",
]

PRESET_CONFIGS = {
    "ISS Microgravity (0g)": {"g": 0.00, "o2": 21.0, "flow": 0.0, "p": 1.00, "area": 1.0},
    "Lunar Gateway (0.16g)": {"g": 0.16, "o2": 23.0, "flow": 2.0, "p": 0.82, "area": 1.0},
    "Mars Habitat (0.38g)": {"g": 0.38, "o2": 25.0, "flow": 5.0, "p": 0.70, "area": 1.0},
    "Earth Lab (1.0g)": {"g": 1.00, "o2": 20.9, "flow": 0.0, "p": 1.00, "area": 1.0},
    "Custom": {"g": 0.00, "o2": 21.0, "flow": 0.0, "p": 1.00, "area": 1.0},
}


def _preset_file_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "Data", "user_presets.json")


def load_custom_preset(email=None):
    p_path = _preset_file_path()
    if os.path.exists(p_path):
        try:
            with open(p_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if email and email in data.get("users", {}):
                return data["users"][email]
            if "guest_default" in data:
                return data["guest_default"]
        except Exception:
            pass
    return {"g": 0.00, "o2": 21.0, "flow": 0.0, "p": 1.00, "area": 1.0}


def save_custom_preset(email=None, cfg=None):
    if cfg is None:
        cfg = {
            "g": float(st.session_state.get("fl_g", st.session_state.get("fp_g", 0.0))),
            "o2": float(st.session_state.get("fl_o2", st.session_state.get("fp_o2", 21.0))),
            "flow": float(st.session_state.get("fl_flow", st.session_state.get("fp_flow", 0.0))),
            "p": float(st.session_state.get("fp_p", 1.0)),
            "area": float(st.session_state.get("fl_area", st.session_state.get("fp_area", 1.0))),
        }
    p_path = _preset_file_path()
    data = {"guest_default": cfg, "users": {}}
    if os.path.exists(p_path):
        try:
            with open(p_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    if "users" not in data:
        data["users"] = {}
    data["guest_default"] = cfg
    target_email = email or st.session_state.get("auth_user")
    if target_email:
        data["users"][target_email] = cfg
    try:
        with open(p_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
    PRESET_CONFIGS["Custom"] = cfg
    return cfg


def ensure_preset_state():
    auth_user = st.session_state.get("auth_user")
    saved_custom = load_custom_preset(auth_user)
    PRESET_CONFIGS["Custom"] = saved_custom

    if "shared_env_preset" not in st.session_state:
        st.session_state["shared_env_preset"] = "ISS Microgravity (0g)"
    preset = st.session_state["shared_env_preset"]
    cfg = PRESET_CONFIGS.get(preset, PRESET_CONFIGS["ISS Microgravity (0g)"])

    for k in ("sidebar_env_preset", "fl_env_preset", "fp_env_preset"):
        if k not in st.session_state:
            st.session_state[k] = preset

    defaults = {
        "fl_g": float(cfg["g"]),
        "fl_o2": float(cfg["o2"]),
        "fl_flow": float(cfg["flow"]),
        "fl_area": float(cfg["area"]),
        "fp_g": float(cfg["g"]),
        "fp_o2": float(cfg["o2"]),
        "fp_flow": float(cfg["flow"]),
        "fp_p": float(cfg.get("p", 1.0)),
        "fp_area": float(cfg["area"]),
    }
    for k, val in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = val


def on_preset_change(source_key):
    new_preset = st.session_state.get(source_key, "ISS Microgravity (0g)")
    st.session_state["shared_env_preset"] = new_preset
    for k in ("sidebar_env_preset", "fl_env_preset", "fp_env_preset"):
        st.session_state[k] = new_preset

    if new_preset in PRESET_CONFIGS:
        cfg = PRESET_CONFIGS[new_preset]
        st.session_state["fl_g"] = float(cfg["g"])
        st.session_state["fl_o2"] = float(cfg["o2"])
        st.session_state["fl_flow"] = float(cfg["flow"])
        st.session_state["fl_area"] = float(cfg["area"])
        st.session_state["fp_g"] = float(cfg["g"])
        st.session_state["fp_o2"] = float(cfg["o2"])
        st.session_state["fp_flow"] = float(cfg["flow"])
        st.session_state["fp_p"] = float(cfg.get("p", 1.0))
        st.session_state["fp_area"] = float(cfg["area"])


def on_slider_change_to_custom(prefix=None):
    st.session_state["shared_env_preset"] = "Custom"
    for k in ("sidebar_env_preset", "fl_env_preset", "fp_env_preset"):
        st.session_state[k] = "Custom"
    save_custom_preset()


def _hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, int(round(rgb[0])))),
        max(0, min(255, int(round(rgb[1])))),
        max(0, min(255, int(round(rgb[2])))),
    )


def _blend_colorscales(scale_a, scale_b, alpha):
    a = max(0.0, min(1.0, float(alpha)))
    stops = [0.0, 0.25, 0.50, 0.78, 1.0]

    def _sample(scale, pos):
        pts = sorted(scale, key=lambda item: item[0])
        if pos <= pts[0][0]:
            return _hex_to_rgb(pts[0][1])
        if pos >= pts[-1][0]:
            return _hex_to_rgb(pts[-1][1])
        for idx in range(len(pts) - 1):
            p0, c0 = pts[idx]
            p1, c1 = pts[idx + 1]
            if p0 <= pos <= p1:
                t = (pos - p0) / max(1e-6, p1 - p0)
                r0, r1 = _hex_to_rgb(c0), _hex_to_rgb(c1)
                return tuple(r0[c] * (1.0 - t) + r1[c] * t for c in range(3))
        return _hex_to_rgb(pts[-1][1])

    blended = []
    for s in stops:
        ca = _sample(scale_a, s)
        cb = _sample(scale_b, s)
        rgb = tuple(ca[c] * (1.0 - a) + cb[c] * a for c in range(3))
        blended.append([s, _rgb_to_hex(rgb)])
    return blended


def get_dynamic_flame_colorscale(exp_key, fuel_type, g, o2_pct, flow_cm_s, is_cool_flame, is_extinguished, mode="optical"):
    fuel_lower = (fuel_type or "").lower()

    if is_extinguished:
        return [
            [0.0, "#111827"],
            [0.35, "#374151"],
            [0.70, "#4B5563"],
            [1.0, "#6B7280"],
        ]

    if is_cool_flame:
        return [
            [0.0, "#090D16"],
            [0.32, "#1E1B4B"],
            [0.65, "#3B82F6"],
            [0.88, "#60A5FA"],
            [1.0, "#BFDBFE"],
        ]

    if mode == "temp":
        thermal_base = [
            [0.0, "#450A0A"],
            [0.25, "#B91C1C"],
            [0.52, "#F97316"],
            [0.78, "#FACC15"],
            [1.0, "#FFFBEB"],
        ]
        thermal_hyper = [
            [0.0, "#7C2D12"],
            [0.25, "#DC2626"],
            [0.55, "#FB923C"],
            [0.82, "#FEF08A"],
            [1.0, "#FFFFFF"],
        ]
        hyper_factor = max(0.0, min(1.0, (o2_pct - 21.0) / 14.0))
        return _blend_colorscales(thermal_base, thermal_hyper, hyper_factor)

    is_clean_alcohol_h2 = (
        "methanol" in fuel_lower
        or "hydrogen" in fuel_lower
        or "h2-air" in fuel_lower
        or exp_key == "SOFBALL"
    )
    is_smoulder_dust = exp_key in ("SAME", "DAFT")

    if is_smoulder_dust and g < 0.45:
        return EXPERIMENT_PROFILES[exp_key]["hot_colorscale"]

    earth_sooting_luminous = [
        [0.0, "#450A0A"],
        [0.22, "#991B1B"],
        [0.48, "#EA580C"],
        [0.75, "#FACC15"],
        [1.0, "#FFFBEB"],
    ]
    earth_clean_alcohol = [
        [0.0, "#1E3A8A"],
        [0.30, "#38BDF8"],
        [0.65, "#F59E0B"],
        [1.0, "#FEF3C7"],
    ]

    microg_clean_blue = [
        [0.0, "#0B192C"],
        [0.32, "#0284C7"],
        [0.66, "#38BDF8"],
        [0.88, "#BAE6FD"],
        [1.0, "#F0F9FF"],
    ]
    microg_soot_shell = [
        [0.0, "#0F172A"],
        [0.26, "#0284C7"],
        [0.56, "#EA580C"],
        [0.82, "#FACC15"],
        [1.0, "#FEF08A"],
    ]

    # Soot formation in 0g increases cleanly with O2 enrichment, flow supply, or heavy hydrocarbons
    is_low_flow_sofie = (exp_key == "SOFIE" and flow_cm_s < 8.0 and o2_pct < 24.0)
    soot_propensity = 0.0 if (is_clean_alcohol_h2 or is_low_flow_sofie) else 0.72
    if not is_clean_alcohol_h2:
        soot_propensity += max(0.0, (o2_pct - 21.0) / 14.0) * 0.28 + max(0.0, (flow_cm_s - 4.0) / 16.0) * 0.20
    else:
        soot_propensity += max(0.0, (o2_pct - 26.0) / 18.0) * 0.35
    soot_propensity = max(0.0, min(1.0, soot_propensity))

    zero_g_scale = _blend_colorscales(microg_clean_blue, microg_soot_shell, soot_propensity)
    high_g_scale = earth_clean_alcohol if is_clean_alcohol_h2 else earth_sooting_luminous

    if g <= 0.04:
        return zero_g_scale
    if g >= 0.45:
        return high_g_scale

    # Smooth partial-gravity transition between 0g spherical diffusion and >=0.45g buoyant plume
    buoyancy_blend = (g - 0.04) / (0.45 - 0.04)
    return _blend_colorscales(zero_g_scale, high_g_scale, buoyancy_blend)

FUEL_TYPES = [
    "n-Heptane / n-Octane (Liquid Droplet — FLEX / FLEX-2)",
    "n-Decane / n-Dodecane (Heavy Alkane Droplet — FLEX-2)",
    "Methanol / Hexanol (Alcohol Droplet — FLEX)",
    "SIBAL Fabric 75% Cotton / 25% Fiberglass (Solid Fabric — Saffire I–VI)",
    "Acrylic / PMMA Thick & Thin Slabs (Solid Polymer — SoFIE)",
    "Ethane / Propane / n-Butane / Methane (Non-Premixed Gas — ACME / CFI-G)",
    "PMMA / PTFE Teflon / Nomex (Thin & Thick Solids — BASS / BASS-II)",
    "Kapton / Teflon / Silicone Wire Insulation (Smouldering Aerosol — SAME)",
    "Lean H₂-Air / CH₄-Air-Ar (Premixed Gas Flame Ball — SOFBALL)",
    "PMMA / Polyethylene Wire / Nomex in Lunar-Mars Gravity (Partial-G Solid — FLARE)",
    "Cabin Dust / Lint / Smoke Particulates (Aerosol Discrimination — DAFT)",
    "PMMA Concurrent Flow Plate (Solid Spread CFD — PSI-62)",
]

EXPERIMENT_PROFILES = {
    "FLEX": {
        "code": "FLEX / FLEX-2",
        "title": "Flame Extinguishment Experiment (FLEX & FLEX-2)",
        "category": "Liquid Alkane & Alcohol Droplet Combustion",
        "fuels": ["n-heptane", "n-octane", "n-decane", "n-dodecane", "methanol", "hexanol", "heptane", "octane", "decane", "dodecane", "liquid droplet"],
        "ref_g": 0.0,
        "ref_o2": 21.0,
        "ref_flow": 0.5,
        "ref_p": 1.0,
        "ref_area_m2": 0.25,
        "base_threat": 72.0,
        "tol_g": 0.15,
        "tol_o2": 8.0,
        "tol_flow": 6.0,
        "equation_name": "Classical d² Law, Spalding Transfer Number & Cool-Flame Wave Speed",
        "equation_latex": r"d(t)^2 = d_0^2 - K t, \quad K = \frac{8 k_g}{\rho_l c_{p,g}} \ln(1 + B_T), \quad S_f^2 = 2 L \left(\frac{T_f}{T_f - T_u}\right)^2 \left(\frac{T_f}{T_4}\right)^2 D_f A_4 \exp\left(\frac{T_4 - T_f}{T_f}\right)",
        "hot_colorscale": [
            [0.0, "#140B34"],
            [0.3, "#0B3D91"],
            [0.55, "#FC3D21"],
            [0.82, "#FFB302"],
            [1.0, "#FFF9D2"],
        ],
        "cool_colorscale": [
            [0.0, "#070B19"],
            [0.35, "#1E1B4B"],
            [0.65, "#3B82F6"],
            [0.88, "#60A5FA"],
            [1.0, "#BFDBFE"],
        ],
        "prevention": "Isolate liquid hydrocarbon propellants/solvents; enforce 45-minute cabin hold after suppression before restoring ventilation.",
        "detection": "UV/deep-blue formaldehyde (CH2O*, 350–450 nm) optical spectroscopy; standard visible/IR sensors miss 500–800 K cool flames.",
        "suppression": "He/CO₂/N₂ dilution above radiative extinction threshold; avoid premature O₂ airflow re-introduction that triggers hot reignition.",
    },
    "SAFFIRE": {
        "code": "Saffire I–VI",
        "title": "Spacecraft Fire Safety Demonstration (Saffire I–VI)",
        "category": "Large-Scale Solid Fabric & Composite Enclosure Fire",
        "fuels": ["sibal", "cotton", "fiberglass", "solid fabric", "mixed solids", "saffire"],
        "ref_g": 0.0,
        "ref_o2": 23.5,
        "ref_flow": 20.0,
        "ref_p": 0.85,
        "ref_area_m2": 1.2,
        "base_threat": 82.0,
        "tol_g": 0.2,
        "tol_o2": 10.0,
        "tol_flow": 15.0,
        "equation_name": "Fourier Conduction & Stefan-Boltzmann Surface Radiative Loss",
        "equation_latex": r"q_{\text{cond}}'' = -k_s \frac{dT}{dx}, \quad q_{\text{rad}}'' = \varepsilon \sigma \left(T_s^4 - T_\infty^4\right), \quad \sigma = 5.6704 \times 10^{-8}\ \text{W/m}^2\text{K}^4",
        "hot_colorscale": [
            [0.0, "#1A0F0A"],
            [0.3, "#7C2D12"],
            [0.6, "#EA580C"],
            [0.85, "#FACC15"],
            [1.0, "#FEF08A"],
        ],
        "cool_colorscale": [
            [0.0, "#0F172A"],
            [0.4, "#1D4ED8"],
            [0.75, "#F97316"],
            [1.0, "#FDE047"],
        ],
        "prevention": "Enforce NASA-STD-6001 material width/thickness limits; account for 26–34% O₂ exploration atmosphere acceleration.",
        "detection": "Distributed CO/CO₂ gas sensors + pressure-rise monitoring; smoke obscuration lags behind initial pyrolysis CO spike.",
        "suppression": "Immediate ECLSS ventilation fan shutoff to starve oxygen transport, followed by depressurization venting and post-fire scrubbing.",
    },
    "SOFIE": {
        "code": "SoFIE (MIST / RTLS / GEL / SMuRF)",
        "title": "Solid Fuel Ignition and Extinction (SoFIE)",
        "category": "Thick & Thin Solid Polymer (Acrylic/PMMA) Ignition & Spread",
        "fuels": ["acrylic", "poly(methyl methacrylate)", "sofie", "thick & thin slabs"],
        "ref_g": 0.0,
        "ref_o2": 21.0,
        "ref_flow": 10.0,
        "ref_p": 1.0,
        "ref_area_m2": 0.6,
        "base_threat": 76.0,
        "tol_g": 0.2,
        "tol_o2": 10.0,
        "tol_flow": 12.0,
        "equation_name": "Thermally Thick Solid Thermal Inertia Ignition Delay",
        "equation_latex": r"t_{\text{ig}} = \frac{\pi}{4} k_s \rho_s c_s \left(\frac{T_{\text{ig}} - T_0}{\dot{q}_{\text{rad}}''}\right)^2",
        "hot_colorscale": [
            [0.0, "#09152B"],
            [0.3, "#0284C7"],
            [0.6, "#38BDF8"],
            [0.85, "#E0F2FE"],
            [1.0, "#FFFFFF"],
        ],
        "cool_colorscale": [
            [0.0, "#090D16"],
            [0.45, "#0369A1"],
            [0.8, "#7DD3FC"],
            [1.0, "#F0F9FF"],
        ],
        "prevention": "Maintain high thermal inertia (k_s * rho_s * c_s) on exposed cabin plastics; avoid thin edges and sharp wire insulation corners.",
        "detection": "Subsurface IR thermography (>750 K surface monitoring) and acoustic/optical bubble pyrolysis detection.",
        "suppression": "Reduce oxidizer flow below 5 cm/s radiative quenching threshold; maintain cooling until deep subsurface boiling ceases.",
    },
    "ACME": {
        "code": "ACME / CFI-G / E-FIELD",
        "title": "Advanced Combustion via Microgravity Experiments (ACME)",
        "category": "Non-Premixed Gaseous Diffusion & Hyper-Oxic Cool Flames",
        "fuels": ["ethane", "propane", "n-butane", "methane", "gaseous fuel", "acme", "cfi-g", "e-field"],
        "ref_g": 0.0,
        "ref_o2": 30.0,
        "ref_flow": 8.0,
        "ref_p": 1.0,
        "ref_area_m2": 0.5,
        "base_threat": 78.0,
        "tol_g": 0.2,
        "tol_o2": 25.0,
        "tol_flow": 12.0,
        "equation_name": "Damköhler Number (Residence Time vs. Arrhenius Chemical Time)",
        "equation_latex": r"Da = \frac{\tau_{\text{flow}}}{\tau_{\text{chem}}} = \frac{L / u_\infty}{\left[A \exp\left(-E_a / R T\right)\right]^{-1}}",
        "hot_colorscale": [
            [0.0, "#081C24"],
            [0.35, "#02BFE7"],
            [0.65, "#34D399"],
            [0.88, "#FBBF24"],
            [1.0, "#FFFFFF"],
        ],
        "cool_colorscale": [
            [0.0, "#041019"],
            [0.4, "#0891B2"],
            [0.75, "#2DD4BF"],
            [1.0, "#A7F3D0"],
        ],
        "prevention": "Regulate high-pressure O₂ manifold lines; apply electrostatic field (E-FIELD 10 kV) ion-wind deflection near gas fittings.",
        "detection": "Bandpass CH2O* (390–490 nm blue-green) and OH* (310 nm) chemiluminescence sensors.",
        "suppression": "Drive Damköhler number below critical limit (Da < 1) via high-strain inert jet blow-off or fuel shutoff valve.",
    },
    "BASS": {
        "code": "BASS / BASS-II",
        "title": "Burning and Suppression of Solids (BASS & BASS-II)",
        "category": "Low-Velocity Opposed/Concurrent Solid Polymer Spread",
        "fuels": ["ptfe", "bass", "pmma spheres", "flat cast sheets", "thin & thick solids"],
        "ref_g": 0.0,
        "ref_o2": 21.0,
        "ref_flow": 12.0,
        "ref_p": 1.0,
        "ref_area_m2": 0.4,
        "base_threat": 68.0,
        "tol_g": 0.2,
        "tol_o2": 8.0,
        "tol_flow": 12.0,
        "equation_name": "de Ris Thermally Thin & Thermally Thick Flame Spread Formulations",
        "equation_latex": r"V_{f,\text{thin}} = V_a \frac{\sqrt{2} k_g c_g}{\rho_s c_s L_m} \left(\frac{T_f - T_p}{T_p - T_\infty}\right)^2, \quad V_{f,\text{thick}} = V_a \frac{k_g \rho_g c_g}{k_s \rho_s c_s} \left(\frac{T_f - T_p}{T_p - T_\infty}\right)^2",
        "hot_colorscale": [
            [0.0, "#0B2545"],
            [0.35, "#1D4ED8"],
            [0.65, "#F97316"],
            [0.88, "#FACC15"],
            [1.0, "#FFFFFF"],
        ],
        "cool_colorscale": [
            [0.0, "#0A192F"],
            [0.5, "#1E40AF"],
            [0.85, "#60A5FA"],
            [1.0, "#DBEAFE"],
        ],
        "prevention": "Avoid intermediate cabin drafts (10–20 cm/s) where microgravity oxygen limits are lower than 1g Earth baselines.",
        "detection": "Boundary-layer optical imaging; flame flattens tightly against solid surfaces under low flow.",
        "suppression": "Direct N₂ extinguisher tangential/parallel to polymer surface or drop ventilation < 5 cm/s to induce radiative quenching.",
    },
    "SAME": {
        "code": "SAME / SAME-R",
        "title": "Smoke Aerosol Measurement Experiment (SAME & SAME-R)",
        "category": "Non-Flaming Overheated Wire Insulation & Smouldering Aerosol",
        "fuels": ["kapton", "silicone", "wire insulation", "smouldering", "same", "cellulose", "pyrolyzed"],
        "ref_g": 0.0,
        "ref_o2": 21.0,
        "ref_flow": 3.0,
        "ref_p": 1.0,
        "ref_area_m2": 0.8,
        "base_threat": 74.0,
        "tol_g": 0.2,
        "tol_o2": 8.0,
        "tol_flow": 8.0,
        "equation_name": "Fickian Vapor Diffusion & Monodisperse Brownian Coagulation",
        "equation_latex": r"j_i = -\rho_g D_i \frac{dY_i}{dx}, \quad \frac{dn_p}{dt} = -K_{\text{coag}} n_p^2, \quad d_p(t) = d_{p,0}\left(1 + K_{\text{coag}} n_{p,0} t\right)^{1/3}",
        "hot_colorscale": [
            [0.0, "#1C1917"],
            [0.4, "#57534E"],
            [0.7, "#B45309"],
            [0.9, "#F59E0B"],
            [1.0, "#FDE68A"],
        ],
        "cool_colorscale": [
            [0.0, "#18181B"],
            [0.5, "#52525B"],
            [0.85, "#D97706"],
            [1.0, "#FCD34D"],
        ],
        "prevention": "Current-limiting breakers on Kapton/Teflon wiring harnesses to prevent non-flaming radiative overheat.",
        "detection": "Forward-scattering photoelectric laser detectors calibrated for enlarged microgravity aggregates (d_p > 1.0–2.0 µm).",
        "suppression": "Immediate electrical bus de-energization and localized HEPA/electrostatic particulate filtration.",
    },
    "SOFBALL": {
        "code": "SOFBALL",
        "title": "Structure of Flame Balls at Low Lewis-Number (SOFBALL)",
        "category": "Ultra-Lean Premixed Gas Stationary Flame Balls",
        "fuels": ["lean h2", "h2-air", "ch4-air", "sofball", "flame ball", "hydrogen"],
        "ref_g": 0.0,
        "ref_o2": 20.0,
        "ref_flow": 0.0,
        "ref_p": 1.0,
        "ref_area_m2": 0.35,
        "base_threat": 70.0,
        "tol_g": 0.1,
        "tol_o2": 8.0,
        "tol_flow": 3.0,
        "equation_name": "Lewis Number & Quenching Peclet Number",
        "equation_latex": r"Le = \frac{\alpha_g}{D_i} = \frac{k_g}{\rho_g c_{p,g} D_i} \ll 1, \quad Pe = \frac{u_\infty d_q}{\alpha_g}",
        "hot_colorscale": [
            [0.0, "#050B1A"],
            [0.35, "#1E3A8A"],
            [0.7, "#3B82F6"],
            [0.9, "#93C5FD"],
            [1.0, "#EFF6FF"],
        ],
        "cool_colorscale": [
            [0.0, "#030712"],
            [0.45, "#1D4ED8"],
            [0.8, "#60A5FA"],
            [1.0, "#DBEAFE"],
        ],
        "prevention": "Eliminate stagnant pockets in battery/electrolysis compartments where lean H₂ or CH₄ can accumulate (Le ~ 0.3).",
        "detection": "High-sensitivity IR thermal imaging; flame balls release only ~1 W thermal power and do not flicker or rise.",
        "suppression": "Induce convective air currents (increase Peclet number Pe) or sweep with CO₂/He radiative quenchants.",
    },
    "FLARE": {
        "code": "FLARE / FM2",
        "title": "Flammability Limits at Reduced Gravity (FLARE / JAXA-NASA)",
        "category": "Lunar (0.16g) & Martian (0.38g) Partial-Gravity Solid Spread",
        "fuels": ["lunar", "mars", "partial-g", "polyethylene wire", "flare", "nomex in lunar"],
        "ref_g": 0.16,
        "ref_o2": 23.0,
        "ref_flow": 5.0,
        "ref_p": 0.8,
        "ref_area_m2": 0.7,
        "base_threat": 80.0,
        "tol_g": 0.25,
        "tol_o2": 10.0,
        "tol_flow": 12.0,
        "equation_name": "Grashof & Rayleigh Buoyancy-to-Viscosity Numbers",
        "equation_latex": r"Gr = \frac{g \beta \left(T_s - T_\infty\right) L^3}{\nu_g^2}, \quad Ra = Gr \cdot Pr = \frac{g \beta \left(T_s - T_\infty\right) L^3}{\nu_g \alpha_g}",
        "hot_colorscale": [
            [0.0, "#1E1B4B"],
            [0.35, "#2563EB"],
            [0.65, "#F97316"],
            [0.88, "#FACC15"],
            [1.0, "#FFFFFF"],
        ],
        "cool_colorscale": [
            [0.0, "#0F172A"],
            [0.5, "#3B82F6"],
            [0.85, "#FB923C"],
            [1.0, "#FEF08A"],
        ],
        "prevention": "Certify materials specifically at 0.16g Lunar gravity where minimum limiting oxygen concentration (LOC) is lowest.",
        "detection": "Account for weak buoyant plumes (Gr ~ 10²–10³) that tilt flames at intermediate angles between 0g and 1g.",
        "suppression": "High-momentum inert gas sweep; partial-gravity buoyancy continuously replenishes O₂ unless fully blanketed.",
    },
    "DAFT": {
        "code": "DAFT / DAFT-2",
        "title": "Dust and Aerosol Measurement Feasibility Test (DAFT)",
        "category": "Cabin Particulate vs. Combustion Smoke Discrimination",
        "fuels": ["cabin dust", "lint", "daft", "particulates", "skin flakes"],
        "ref_g": 0.0,
        "ref_o2": 21.0,
        "ref_flow": 10.0,
        "ref_p": 1.0,
        "ref_area_m2": 1.0,
        "base_threat": 44.0,
        "tol_g": 0.2,
        "tol_o2": 8.0,
        "tol_flow": 12.0,
        "equation_name": "Duct Flow Reynolds Number & Polarized Mie Depolarization Ratio",
        "equation_latex": r"Re = \frac{u_\infty L}{\nu_g}, \quad \delta_p = \frac{I_\perp(\theta)}{I_\parallel(\theta)}",
        "hot_colorscale": [
            [0.0, "#1E293B"],
            [0.4, "#64748B"],
            [0.7, "#94A3B8"],
            [0.9, "#CBD5E1"],
            [1.0, "#F8FAFC"],
        ],
        "cool_colorscale": [
            [0.0, "#0F172A"],
            [0.5, "#475569"],
            [0.85, "#94A3B8"],
            [1.0, "#E2E8F0"],
        ],
        "prevention": "Pre-filter cabin return ducts around crew exercise and vacuum maintenance stations.",
        "detection": "Dual-wavelength multi-angle polarized scattering to separate spherical smoke (low δ_p) from jagged dust (high δ_p).",
        "suppression": "Verify true CO/CO₂ combustion signature before discharging halon/water-mist or depressurizing cabin.",
    },
    "PSI62": {
        "code": "PSI-62 CFD",
        "title": "PSI-62 Concurrent Flow Flame Spread & Pyrolysis Modeling",
        "category": "Concurrent Solid PMMA Pyrolysis & Boundary Layer Spread",
        "fuels": ["psi-62", "concurrent flow plate", "concurrent solid"],
        "ref_g": 0.0,
        "ref_o2": 21.0,
        "ref_flow": 15.0,
        "ref_p": 1.0,
        "ref_area_m2": 1.1,
        "base_threat": 84.0,
        "tol_g": 0.2,
        "tol_o2": 10.0,
        "tol_flow": 12.0,
        "equation_name": "Arrhenius Solid Pyrolytic Mass Flux Law",
        "equation_latex": r"\dot{m}_p'' = A_p \exp\left(-\frac{E_p}{R T_s}\right)",
        "hot_colorscale": [
            [0.0, "#0B192C"],
            [0.3, "#1E3E62"],
            [0.6, "#FF6500"],
            [0.85, "#FFB200"],
            [1.0, "#FFFFFF"],
        ],
        "cool_colorscale": [
            [0.0, "#09122C"],
            [0.45, "#1E3E62"],
            [0.8, "#60A5FA"],
            [1.0, "#E2E8F0"],
        ],
        "prevention": "Orient polymeric panels perpendicular or opposed to primary HVAC flow vectors to prevent concurrent flame lengthening.",
        "detection": "Downstream thermal plume arrays positioned along the concurrent wake axis.",
        "suppression": "Reverse or terminate concurrent duct velocity immediately to collapse the downstream pyrolysis preheat tail.",
    },
}


def detect_experiment_category(fuel_type, g, o2_pct, flow_cm_s, pressure_atm=1.0):
    fuel_lower = (fuel_type or "").lower()
    scores = {}

    for key, prof in EXPERIMENT_PROFILES.items():
        fuel_match = 0.35
        for kw in prof["fuels"]:
            if kw in fuel_lower:
                fuel_match = 1.0
                break

        if key == "FLARE" and 0.05 <= g <= 0.45 and ("pmma" in fuel_lower or "solid" in fuel_lower or "nomex" in fuel_lower or "lunar" in fuel_lower):
            fuel_match = max(fuel_match, 0.95)
        elif key == "PSI62" and flow_cm_s >= 12.0 and "pmma" in fuel_lower and "concurrent" in fuel_lower:
            fuel_match = 1.0

        dg = abs(g - prof["ref_g"]) / max(prof["tol_g"], 0.05)
        do2 = abs(o2_pct - prof["ref_o2"]) / max(prof["tol_o2"], 1.0)
        dflow = abs(flow_cm_s - prof["ref_flow"]) / max(prof["tol_flow"], 1.0)
        dp = abs(pressure_atm - prof["ref_p"]) / 0.5

        env_score = math.exp(-0.22 * (dg**2 + 0.6 * do2**2 + 0.5 * dflow**2 + 0.3 * dp**2))
        total_score = (0.68 * fuel_match + 0.32 * env_score) * 100.0
        scores[key] = min(99.4, max(18.0, total_score))

    best_key = max(scores, key=scores.get)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    surety_pct = round(scores[best_key], 1)

    return best_key, surety_pct, sorted_scores


def calc_flex_droplet(g, o2_pct, flow_cm_s):
    k_g = 0.045
    rho_l = 684.0
    c_pg = 1350.0
    T_inf = 298.0
    T_b = 371.5
    Y_o2 = (o2_pct / 100.0) * (32.0 / 28.97)
    dH_c = 44.6e6
    r_stoich = 3.52
    L_v = 3.18e5

    B_T = (c_pg * (T_inf - T_b) + (Y_o2 * dH_c / r_stoich)) / L_v
    B_T = max(0.5, B_T)
    K_m2_s = (8.0 * k_g / (rho_l * c_pg)) * math.log(1.0 + B_T)
    K_mm2_s = K_m2_s * 1e6 * (1.0 + 0.025 * flow_cm_s + 0.18 * g)

    T_f = 640.0 if (g < 0.08 and o2_pct <= 23.0 and flow_cm_s < 4.0) else 1680.0
    T_u = 300.0
    T_4 = 15000.0
    D_f = 2.2e-5
    A_4 = 1.0e8
    L_lewis = 1.05
    S_f_sq = 2.0 * L_lewis * ((T_f / (T_f - T_u)) ** 2) * ((T_f / T_4) ** 2) * D_f * A_4 * math.exp((T_4 - T_f) / T_f)
    S_f_cm_s = math.sqrt(max(1e-6, S_f_sq)) * 100.0

    T_3 = -8360.0
    k3_ntc = 1.0e12 * math.exp(-T_3 / max(500.0, min(850.0, T_f)))
    k7_branch = 7.5e11 * math.exp(-1760.0 / max(500.0, T_f))

    d0_mm = 3.2
    t_burn_s = (d0_mm ** 2) / max(0.05, K_mm2_s)

    return {
        "Spalding B_T": round(B_T, 2),
        "Burning Constant K (mm²/s)": round(K_mm2_s, 3),
        "Cool-Flame Wave Speed S_f (cm/s)": round(S_f_cm_s, 2),
        "Droplet Lifetime t_burn (s)": round(t_burn_s, 1),
        "Branching Rate k_7 (s⁻¹)": f"{k7_branch:.2e}",
    }


def calc_saffire_radiation(g, o2_pct, flow_cm_s):
    k_s = 0.19
    T_s = 720.0 + 14.0 * (o2_pct - 21.0) + 2.2 * flow_cm_s
    T_inf = 298.0
    delta_x = 0.004
    eps = 0.92
    q_cond = k_s * (T_s - T_inf) / delta_x
    q_rad = eps * SIGMA_SB * (T_s**4 - T_inf**4)
    v_spread = max(0.0, 1.3 + 0.045 * (flow_cm_s - 10.0) + 0.12 * (o2_pct - 21.0) + 0.8 * g)
    osc_hz = 0.75 + 0.032 * flow_cm_s if g < 0.05 else 0.0
    return {
        "Surface Temp T_s (K)": round(T_s, 1),
        "Conduction Flux q_cond (kW/m²)": round(q_cond / 1000.0, 2),
        "Radiative Loss q_rad (kW/m²)": round(q_rad / 1000.0, 2),
        "Spread Rate V_f (mm/s)": round(v_spread, 2),
        "Flame Oscillation (Hz)": round(osc_hz, 2),
    }


def calc_sofie_ignition(g, o2_pct, flow_cm_s, q_rad_kw=25.0):
    k_s = 0.19
    rho_s = 1190.0
    c_s = 1460.0
    T_ig = 655.0 - 2.5 * (o2_pct - 21.0)
    T_0 = 298.0
    q_net = max(5000.0, (q_rad_kw * 1000.0) * (0.85 + 0.015 * flow_cm_s))
    t_ig = (math.pi / 4.0) * k_s * rho_s * c_s * (((T_ig - T_0) / q_net) ** 2)
    quenched = flow_cm_s < 1.5 and g < 0.05 and o2_pct < 20.0
    return {
        "Thermal Inertia kρc (J²/m⁴K²s)": f"{k_s * rho_s * c_s:.2e}",
        "Ignition Temp T_ig (K)": round(T_ig, 1),
        "Ignition Delay t_ig (s)": round(t_ig, 1),
        "Radiative Quench Risk": "HIGH (<5 cm/s)" if flow_cm_s < 5.0 else "LOW (Anchored)",
        "Extinguished State": "YES" if quenched else "NO",
    }


def calc_acme_damkohler(g, o2_pct, flow_cm_s):
    L_char = 0.015
    u_m_s = max(0.005, (flow_cm_s / 100.0) + 0.12 * g)
    tau_flow = L_char / u_m_s
    T_flame = 620.0 if (o2_pct >= 30.0 and flow_cm_s < 6.0 and g < 0.05) else (1550.0 + 25.0 * (o2_pct - 21.0))
    A_pre = 2.4e9
    E_a = 125000.0
    rate_chem = A_pre * math.exp(-E_a / (R_UNIV * T_flame)) * (o2_pct / 21.0)
    tau_chem = 1.0 / max(1e-6, rate_chem)
    Da = tau_flow / tau_chem
    return {
        "Flow Time τ_flow (s)": round(tau_flow, 3),
        "Chemical Time τ_chem (ms)": round(tau_chem * 1000.0, 3),
        "Damköhler Number Da": round(Da, 2),
        "Flame Temperature (K)": round(T_flame, 0),
        "Stability Regime": "Blow-off Risk (Da < 1)" if Da < 1.0 else ("Cool Diffusion Sphere" if T_flame < 800 else "Stable Diffusion"),
    }


def calc_bass_deris_spread(g, o2_pct, flow_cm_s):
    V_a = max(0.005, (flow_cm_s / 100.0) + 0.15 * math.sqrt(max(0.0, g)))
    k_g, rho_g, c_g = 0.042, 1.18, 1100.0
    k_s, rho_s, c_s = 0.19, 1190.0, 1460.0
    L_m = 0.0015
    T_f = 1650.0 + 32.0 * (o2_pct - 21.0)
    T_p = 650.0
    T_inf = 298.0
    thermal_ratio = ((T_f - T_p) / (T_p - T_inf)) ** 2

    Vf_thin = (math.sqrt(2.0) * k_g * c_g / (rho_s * c_s * L_m)) * thermal_ratio * (0.6 + 0.04 * flow_cm_s)
    Vf_thick = V_a * (k_g * rho_g * c_g / (k_s * rho_s * c_s)) * thermal_ratio * 120.0

    if flow_cm_s < 2.0 and g < 0.04 and o2_pct < 19.5:
        regime = "Radiative Quenching"
    elif flow_cm_s <= 20.0:
        regime = "Oxygen-Supply Peak Spread"
    else:
        regime = "Convective Cooling / Blow-off"

    return {
        "Thin Spread V_f,thin (mm/s)": round(Vf_thin * 1000.0, 2),
        "Thick Spread V_f,thick (mm/s)": round(Vf_thick * 1000.0, 2),
        "Flame Temp T_f (K)": round(T_f, 0),
        "BASS Parabolic Regime": regime,
    }


def calc_same_aerosol(g, o2_pct, flow_cm_s):
    rho_g = 1.2
    D_i = 1.4e-5
    dY_dx = 0.25
    j_i = rho_g * D_i * dY_dx * 1e6
    K_coag = 5.5e-16 * (1.0 + 0.2 * (1.0 - min(1.0, g)))
    n_p0 = 2.0e13
    t_res = max(5.0, 45.0 / max(1.0, flow_cm_s + 10.0 * g))
    d_p0_um = 0.28
    d_p_um = d_p0_um * ((1.0 + K_coag * n_p0 * t_res) ** (1.0 / 3.0))
    return {
        "Vapor Flux j_i (mg/m²s)": round(j_i, 2),
        "Residence Time t_res (s)": round(t_res, 1),
        "Agglomerated Diameter d_p (µm)": round(d_p_um, 2),
        "Ionization Sensor Sensitivity": "Reduced (-50%)" if d_p_um > 0.8 else "Nominal",
    }


def calc_sofball_lewis_peclet(g, o2_pct, flow_cm_s):
    alpha_g = 2.2e-5
    D_H2 = 7.1e-5
    Le = alpha_g / D_H2
    d_q = 0.008
    u_m_s = (flow_cm_s / 100.0) + 0.08 * g
    Pe = (u_m_s * d_q) / alpha_g
    power_w = 1.15 * (o2_pct / 21.0)
    return {
        "Lewis Number Le": round(Le, 3),
        "Peclet Number Pe": round(Pe, 2),
        "Radiant Power (W)": round(power_w, 2),
        "Flame Ball State": "Stationary Spherical Ball" if (g < 0.05 and flow_cm_s < 2.0) else "Convectively Distorted",
    }


def calc_flare_grashof_rayleigh(g, o2_pct, flow_cm_s):
    beta = 1.0 / 600.0
    T_s = 740.0 + 15.0 * (o2_pct - 21.0)
    T_inf = 298.0
    L = 0.05
    nu_g = 1.6e-5
    alpha_g = 2.2e-5
    g_ms2 = g * 9.80665
    Gr = (g_ms2 * beta * (T_s - T_inf) * (L**3)) / (nu_g**2)
    Ra = Gr * (nu_g / alpha_g)
    u_buoy_cm_s = math.sqrt(max(0.0, g_ms2 * beta * (T_s - T_inf) * L)) * 100.0
    loc_pct = 16.5 if (0.10 <= g <= 0.25) else (17.8 if g < 0.10 else 18.2)
    return {
        "Grashof Number Gr": round(Gr, 1),
        "Rayleigh Number Ra": round(Ra, 1),
        "Buoyant Velocity u_b (cm/s)": round(u_buoy_cm_s, 2),
        "Limiting O₂ Conc. LOC (%)": loc_pct,
    }


def calc_daft_reynolds(g, o2_pct, flow_cm_s):
    L_duct = 0.12
    nu_g = 1.56e-5
    u_m_s = max(0.01, flow_cm_s / 100.0)
    Re = (u_m_s * L_duct) / nu_g
    depol_dust = 0.34
    depol_smoke = 0.06
    return {
        "Duct Reynolds Number Re": round(Re, 1),
        "Dust Depolarization δ_p": depol_dust,
        "Smoke Depolarization δ_p": depol_smoke,
        "Flow Regime": "Laminar Duct Flow" if Re < 2100 else "Transitional / Turbulent",
    }


def calc_psi62_pyrolysis(g, o2_pct, flow_cm_s):
    A_p = 3.2e6
    E_p = 92000.0
    T_s = 685.0 + 11.0 * (o2_pct - 21.0) + 1.8 * flow_cm_s
    m_dot_p = A_p * math.exp(-E_p / (R_UNIV * T_s))
    flame_len_cm = 2.4 + 0.38 * flow_cm_s + 0.15 * (o2_pct - 21.0)
    return {
        "Surface Pyrolysis Temp T_s (K)": round(T_s, 1),
        "Pyrolytic Mass Flux ṁ_p'' (g/m²s)": round(m_dot_p, 2),
        "Concurrent Plume Length (cm)": round(flame_len_cm, 1),
    }


def evaluate_area_scaling(area_m2, g, o2_pct, flow_cm_s, exp_key=None):
    area_val = max(0.05, float(area_m2))
    confinement_factor = (1.0 / max(0.08, area_val)) ** 0.35
    expansion_pyrolysis_factor = area_val ** 0.42

    if area_val < 0.6:
        area_regime = "Spatial Confinement / Contraction"
        area_effect_summary = (
            "Reduced area traps thermal energy, elevates wall radiative feedback and HCl/HF wall adsorption lag, "
            "and promotes hot-to-cool flame shift while driving Exposure Factor EF toward 1.0."
        )
    elif area_val <= 1.8:
        area_regime = "Nominal Compartment Geometry"
        area_effect_summary = (
            "Balanced radiant dissipation and exposed fuel area; baseline flow and diffusion detection timing."
        )
    else:
        area_regime = "Spatial Expansion / Large Scale"
        area_effect_summary = (
            "Expanded surface increases solid pyrolysis flux and operational attack surface; in 0g, spherical "
            "non-buoyant smoke dispersion decouples hazards from ceiling sensors."
        )

    conf_contrib = ((0.6 - area_val) / 0.6) * 0.45 if area_val < 0.6 else 0.0
    exp_contrib = min(0.40, max(0.0, (area_val - 1.2) / 8.8) * 0.40)
    ef_base = 0.38 + (o2_pct - 21.0) * 0.008
    if exp_key in ("SAFFIRE", "SOFIE", "PSI62"):
        ef_base += 0.08
    elif exp_key == "DAFT":
        ef_base -= 0.14
    exposure_factor_EF = round(min(0.98, max(0.15, ef_base + conf_contrib + exp_contrib)), 3)

    adsorption_lag = 6.5 * max(0.0, confinement_factor - 1.0)
    dispersion_lag = (8.0 * expansion_pyrolysis_factor / max(0.5, flow_cm_s + 15.0 * g)) * (1.35 if g < 0.08 else 0.7)
    detection_lag_s = round(max(1.0, 2.5 + adsorption_lag + dispersion_lag), 1)

    return {
        "area_m2": round(area_val, 2),
        "area_regime": area_regime,
        "confinement_factor": round(confinement_factor, 3),
        "expansion_pyrolysis_factor": round(expansion_pyrolysis_factor, 3),
        "exposure_factor_EF": exposure_factor_EF,
        "detection_lag_s": detection_lag_s,
        "area_effect_summary": area_effect_summary,
    }


def calculate_threat_metrics(exp_key, g, o2_pct, flow_cm_s, pressure_atm=1.0, area_m2=1.0, cool_flame=False, base_risk_score=None):
    prof = EXPERIMENT_PROFILES[exp_key]
    area_info = evaluate_area_scaling(area_m2, g, o2_pct, flow_cm_s, exp_key)

    flex_m = calc_flex_droplet(g, o2_pct, flow_cm_s)
    bass_m = calc_bass_deris_spread(g, o2_pct, flow_cm_s)

    o2_contrib = min(30.0, max(-10.0, 1.35 * (o2_pct - 21.0)))
    g_contrib = 8.5 if 0.10 <= g <= 0.38 else (3.0 if g < 0.05 else 0.0)
    flow_contrib = 7.0 if 5.0 <= flow_cm_s <= 25.0 else (-4.0 if flow_cm_s < 1.5 and g < 0.05 else 1.5)
    p_contrib = 2.5 * (pressure_atm - 1.0)
    cool_penalty = 11.5 if cool_flame else 0.0

    rate_contrib = min(
        14.0,
        2.0 * math.log1p(flex_m["Spalding B_T"])
        + 1.4 * flex_m["Burning Constant K (mm²/s)"]
        + 0.35 * bass_m["Thin Spread V_f,thin (mm/s)"],
    )

    conf_penalty = min(16.0, 11.5 * max(0.0, area_info["confinement_factor"] - 1.05))
    exp_penalty = min(16.0, 7.5 * max(0.0, area_info["expansion_pyrolysis_factor"] - 1.25))
    if exp_key in ("SAFFIRE", "SOFIE", "BASS", "PSI62"):
        exp_penalty *= 1.15
    elif exp_key in ("FLEX", "ACME", "SAME"):
        conf_penalty *= 1.15

    raw_physics_score = (
        0.55 * prof["base_threat"]
        + 0.45 * 45.0
        + 0.45 * o2_contrib
        + g_contrib
        + flow_contrib
        + p_contrib
        + cool_penalty
        + 0.5 * rate_contrib
        + conf_penalty
        + exp_penalty
    )

    if base_risk_score is not None:
        anchored_base = float(base_risk_score) * 100.0
        threat_score = 0.58 * anchored_base + 0.42 * raw_physics_score
    else:
        threat_score = raw_physics_score

    threat_score = round(min(99.5, max(5.0, threat_score)), 1)

    if threat_score >= 80.0:
        threat_tier = "CRITICAL"
    elif threat_score >= 65.0:
        threat_tier = "HIGH"
    elif threat_score >= 45.0:
        threat_tier = "MODERATE"
    else:
        threat_tier = "LOW"

    s_norm = threat_score / 100.0
    F_t = min(0.95, max(0.02, 0.12 + 0.75 * (s_norm ** 1.4)))
    f_t = max(0.01, 0.85 * s_norm * (1.0 - s_norm * 0.45))
    hazard_rate_h = round(f_t / max(0.05, 1.0 - F_t), 3)
    aro = round(0.15 + 1.85 * (s_norm ** 1.2) * (1.0 + 0.25 * max(0.0, float(area_m2) - 1.0)), 3)
    ale_norm = round(area_info["exposure_factor_EF"] * aro, 3)

    return {
        "threat_score": threat_score,
        "threat_tier": threat_tier,
        "hazard_rate_h": hazard_rate_h,
        "exposure_factor_EF": area_info["exposure_factor_EF"],
        "aro_index": aro,
        "ale_norm": ale_norm,
        "detection_lag_s": area_info["detection_lag_s"],
        "area_scaling": area_info,
    }


def evaluate_combustion_state(fuel_type, g, o2_pct, flow_cm_s, pressure_atm=1.0, area_m2=1.0):
    exp_key, surety_pct, sorted_scores = detect_experiment_category(
        fuel_type, g, o2_pct, flow_cm_s, pressure_atm
    )
    prof = EXPERIMENT_PROFILES[exp_key]

    if exp_key == "FLEX":
        metrics = calc_flex_droplet(g, o2_pct, flow_cm_s)
    elif exp_key == "SAFFIRE":
        metrics = calc_saffire_radiation(g, o2_pct, flow_cm_s)
    elif exp_key == "SOFIE":
        metrics = calc_sofie_ignition(g, o2_pct, flow_cm_s)
    elif exp_key == "ACME":
        metrics = calc_acme_damkohler(g, o2_pct, flow_cm_s)
    elif exp_key == "BASS":
        metrics = calc_bass_deris_spread(g, o2_pct, flow_cm_s)
    elif exp_key == "SAME":
        metrics = calc_same_aerosol(g, o2_pct, flow_cm_s)
    elif exp_key == "SOFBALL":
        metrics = calc_sofball_lewis_peclet(g, o2_pct, flow_cm_s)
    elif exp_key == "FLARE":
        metrics = calc_flare_grashof_rayleigh(g, o2_pct, flow_cm_s)
    elif exp_key == "DAFT":
        metrics = calc_daft_reynolds(g, o2_pct, flow_cm_s)
    else:
        metrics = calc_psi62_pyrolysis(g, o2_pct, flow_cm_s)

    is_cool_flame = False
    if exp_key in ("FLEX", "ACME") and g < 0.08 and flow_cm_s < 5.0 and o2_pct <= 24.0:
        is_cool_flame = True
    elif exp_key == "ACME" and o2_pct >= 30.0 and flow_cm_s < 6.0 and g < 0.06:
        is_cool_flame = True
    elif exp_key == "SOFIE" and g < 0.05 and flow_cm_s < 3.0:
        is_cool_flame = True
    elif area_m2 < 0.35 and g < 0.08 and exp_key in ("FLEX", "ACME", "SOFIE", "BASS"):
        is_cool_flame = True

    is_extinguished = False
    if exp_key in ("SOFIE", "BASS") and g < 0.04 and flow_cm_s < 1.0 and o2_pct < 18.5:
        is_extinguished = True

    threat = calculate_threat_metrics(
        exp_key, g, o2_pct, flow_cm_s, pressure_atm=pressure_atm, area_m2=area_m2, cool_flame=is_cool_flame
    )
    area_scaling = threat["area_scaling"]
    metrics["Threat Score (0-100)"] = f"{threat['threat_score']} ({threat['threat_tier']})"
    metrics["Exposure Factor EF"] = threat["exposure_factor_EF"]

    buoyancy_stretch = 1.0 + (1.8 * g)
    size_factor = (o2_pct / 21.0) * 0.9
    x_drift = (flow_cm_s / 20.0) * 0.6
    temp_scale = 0.4 + 0.6 * ((o2_pct - 15.0) / 20.0)

    if exp_key == "SOFBALL":
        buoyancy_stretch = 1.0 + (0.65 * g)
        x_drift = (flow_cm_s / 20.0) * 0.25
        size_factor *= 0.78
    elif exp_key in ("SAFFIRE", "PSI62"):
        buoyancy_stretch = 1.15 + (2.0 * g) + (flow_cm_s / 25.0) * 0.45
        x_drift = (flow_cm_s / 20.0) * 0.85
        size_factor *= 1.12
    elif exp_key == "FLARE":
        lunar_boost = 1.18 if 0.10 <= g <= 0.25 else 1.0
        size_factor *= lunar_boost
        temp_scale *= lunar_boost
    elif exp_key in ("SAME", "DAFT"):
        buoyancy_stretch = 1.0 + (0.9 * g)
        size_factor *= 1.15
        temp_scale *= 0.68

    if area_m2 < 0.6:
        temp_scale *= 1.0 + 0.22 * (area_scaling["confinement_factor"] - 1.0)
        size_factor *= max(0.65, 0.95 - 0.18 * (1.0 - float(area_m2)))
    elif area_m2 > 1.0:
        size_factor *= min(1.35, 1.0 + 0.12 * (area_scaling["expansion_pyrolysis_factor"] - 1.0))
        temp_scale *= min(1.25, 1.0 + 0.08 * (area_scaling["expansion_pyrolysis_factor"] - 1.0))

    if is_cool_flame:
        temp_scale *= 0.62
        size_factor *= 0.85
    if is_extinguished:
        temp_scale *= 0.35
        size_factor *= 0.55

    colorscale = get_dynamic_flame_colorscale(
        exp_key, fuel_type, g, o2_pct, flow_cm_s, is_cool_flame, is_extinguished, mode="optical"
    )
    temp_colorscale = get_dynamic_flame_colorscale(
        exp_key, fuel_type, g, o2_pct, flow_cm_s, is_cool_flame, is_extinguished, mode="temp"
    )

    if is_extinguished:
        regime_label = "Radiative Quenching / Near-Extinction"
        optical_regime_desc = (
            f"Radiative Extinction Regime ({g:.2f}g): Heat losses exceed heat release under oxygen starvation/low flow, yielding a dim residual smoke plume."
        )
    elif is_cool_flame:
        regime_label = "Low-Temperature Cool Flame (500–800 K, CH₂O* UV/Blue)"
        optical_regime_desc = (
            f"Microgravity Cool Flame Regime ({g:.2f}g): Buoyancy absence stabilizes ~600 K spherical formaldehyde (CH₂O*) UV/blue chemiluminescence."
        )
    elif g >= 0.45:
        regime_label = "Earth Buoyant Stretched Teardrop Flame" if g >= 0.85 else "High-Gravity Buoyant Teardrop Flame"
        if "methanol" in (fuel_type or "").lower() or "hydrogen" in (fuel_type or "").lower() or exp_key == "SOFBALL":
            optical_regime_desc = (
                f"Earth/High-G Clean Fuel Buoyancy ({g:.2f}g): Upward natural convection produces a pale-blue base with warm amber-yellow tip."
            )
        else:
            optical_regime_desc = (
                f"Earth/High-G Buoyant Soot-Luminous Regime ({g:.2f}g): Strong upward natural convection creates a stretched teardrop plume with incandescent yellow-orange soot emission."
            )
    elif g >= 0.08:
        regime_label = "Partial-Gravity Mixed Buoyant-Diffusive Plume"
        optical_regime_desc = (
            f"Partial-Gravity Transition ({g:.2f}g): Weak buoyant convection tilts and elongates the plume from a blue reaction base toward luminous amber-orange soot."
        )
    elif g < 0.05 and flow_cm_s < 2.0:
        regime_label = "Microgravity Diffusion Sphere (Zero Buoyancy)"
        optical_regime_desc = (
            f"Microgravity Diffusion-Dominated Regime ({g:.2f}g): Absence of buoyancy yields a spherical reaction zone governed by molecular diffusion and soot/O₂ chemistry."
        )
    else:
        regime_label = "Forced-Flow Microgravity Stretched Flame"
        optical_regime_desc = (
            f"Microgravity Forced-Convection Regime ({g:.2f}g, {flow_cm_s:.1f} cm/s): Cabin airflow replaces buoyancy to transport O₂ and elongate the flame downstream."
        )

    return {
        "exp_key": exp_key,
        "code": prof["code"],
        "title": prof["title"],
        "category": prof["category"],
        "surety_pct": surety_pct,
        "equation_name": prof["equation_name"],
        "equation_latex": prof["equation_latex"],
        "metrics": metrics,
        "colorscale": colorscale,
        "temp_colorscale": temp_colorscale,
        "optical_regime_desc": optical_regime_desc,
        "is_cool_flame": is_cool_flame,
        "is_extinguished": is_extinguished,
        "regime_label": regime_label,
        "prevention": prof["prevention"],
        "detection": prof["detection"],
        "suppression": prof["suppression"],
        "threat": threat,
        "area_scaling": area_scaling,
        "morphology_params": {
            "buoyancy_stretch": buoyancy_stretch,
            "size_factor": max(0.35, size_factor),
            "x_drift": x_drift,
            "temp_scale": max(0.25, temp_scale),
        },
        "runner_up": sorted_scores[1] if len(sorted_scores) > 1 else None,
    }


def match_catalog_record(exp_record, area_m2=None):
    mission = (exp_record.get("mission") or "").upper()
    fuel_name = exp_record.get("fuel_name") or ""
    g = float(exp_record.get("gravity_g", 0.0))
    o2 = float(exp_record.get("oxygen_pct", 21.0))
    p = float(exp_record.get("pressure_atm", 1.0))
    flow = float(exp_record.get("flow_cm_s", 5.0))

    if "FLEX" in mission:
        key = "FLEX"
    elif "SAFFIRE" in mission:
        key = "SAFFIRE"
    elif "SOFIE" in mission:
        key = "SOFIE"
    elif "ACME" in mission:
        key = "ACME"
    elif "BASS" in mission:
        key = "BASS"
    elif "SAME" in mission:
        key = "SAME"
    elif "DAFT" in mission:
        key = "DAFT"
    elif "FLARE" in mission:
        key = "FLARE"
    elif "SOFBALL" in mission:
        key = "SOFBALL"
    else:
        key, _, _ = detect_experiment_category(fuel_name, g, o2, flow, p)

    _, surety_pct, _ = detect_experiment_category(fuel_name, g, o2, flow, p)
    surety_pct = max(surety_pct, 92.5)
    prof = EXPERIMENT_PROFILES[key]

    resolved_area = float(area_m2) if area_m2 is not None else float(exp_record.get("area_m2") or prof["ref_area_m2"])
    threat = calculate_threat_metrics(
        key,
        g,
        o2,
        flow,
        pressure_atm=p,
        area_m2=resolved_area,
        cool_flame=bool(exp_record.get("cool_flame_observed")),
        base_risk_score=exp_record.get("risk_score"),
    )
    area_info = threat["area_scaling"]

    return {
        "exp_key": key,
        "code": prof["code"],
        "equation_name": prof["equation_name"],
        "equation_latex": prof["equation_latex"],
        "surety_pct": round(surety_pct, 1),
        "threat_score": threat["threat_score"],
        "threat_tier": threat["threat_tier"],
        "hazard_rate_h": threat["hazard_rate_h"],
        "ale_norm": threat["ale_norm"],
        "area_regime": area_info["area_regime"],
        "area_effect_summary": area_info["area_effect_summary"],
        "exposure_factor_EF": threat["exposure_factor_EF"],
        "detection_lag_s": threat["detection_lag_s"],
    }


@st.cache_data
def get_cached_mission_catalog_info(experiments_data, area_m2=1.0):
    cached = {}
    for idx, exp in enumerate(experiments_data or []):
        exp_id = str(exp.get("id") or f"EXP-{idx}")
        matched = match_catalog_record(exp, area_m2=area_m2)
        exp_key = matched.get("exp_key", "FLEX")
        prof = EXPERIMENT_PROFILES.get(exp_key, EXPERIMENT_PROFILES["FLEX"])

        g = float(exp.get("gravity_g", 0.0))
        o2 = float(exp.get("oxygen_pct", 21.0))
        p = float(exp.get("pressure_atm", 1.0))
        flow = float(exp.get("flow_cm_s", prof.get("ref_flow", 5.0)))
        burn_s = float(exp.get("burn_duration_s", 0.0))

        flex_m = calc_flex_droplet(g, o2, flow)
        saf_m = calc_saffire_radiation(g, o2, flow)
        p_ratio = round(1.0 + (0.045 * (o2 / 21.0) * (float(area_m2) ** 0.5) * (1.0 / max(0.3, p))), 3)

        ntrs_raw = str(exp.get("ntrs_document_id") or "").strip()
        ntrs_link = str(exp.get("ntrs_link") or "").strip()
        if not ntrs_link and ntrs_raw:
            ntrs_num = ntrs_raw.replace("NASA-NTRS-", "").replace("NTRS-", "").strip()
            ntrs_link = (
                f"https://ntrs.nasa.gov/citations/{ntrs_num}"
                if ntrs_num.isdigit()
                else f"https://ntrs.nasa.gov/search?q={ntrs_raw}"
            )

        investigator = exp.get("investigator") or "NASA Glenn / Principal Investigator Team"
        hardware_facility = exp.get("hardware_facility") or exp.get("platform") or "ISS / Cygnus Test Facility"
        three_pillars = exp.get("three_pillars_focus") or "Prevention, Detection & Extinction"
        detection_challenge = exp.get("detection_challenge") or prof["detection"]
        extinction_mech = exp.get("extinction_mechanism") or prof["suppression"]
        safety_insight = exp.get("spacecraft_safety_insight") or prof["prevention"]

        hover_html = (
            f"<b>{exp.get('mission', '')} | {hardware_facility}</b><br/>"
            f"<b>PI:</b> {investigator}<br/>"
            f"<b>Env:</b> {g:.2f}g | {o2:.1f}% O₂ | {p:.2f} atm | Burn: {burn_s:.1f}s<br/>"
            f"<b>Pillar:</b> {three_pillars} | <b>Threat:</b> {matched['threat_score']}/100 ({matched['threat_tier']})"
        )

        cached[exp_id] = {
            "id": exp_id,
            "name": exp.get("name", ""),
            "mission": exp.get("mission", ""),
            "year": exp.get("year", ""),
            "platform": exp.get("platform", ""),
            "hardware_facility": hardware_facility,
            "investigator": investigator,
            "fuel_name": exp.get("fuel_name", ""),
            "fuel_category": exp.get("fuel_category", ""),
            "gravity_g": g,
            "oxygen_pct": o2,
            "pressure_atm": p,
            "burn_duration_s": burn_s,
            "safety_risk_level": exp.get("safety_risk_level", ""),
            "cool_flame_observed": bool(exp.get("cool_flame_observed")),
            "three_pillars_focus": three_pillars,
            "key_phenomenon": exp.get("key_phenomenon", ""),
            "detection_challenge": detection_challenge,
            "extinction_mechanism": extinction_mech,
            "spacecraft_safety_insight": safety_insight,
            "ntrs_document_id": ntrs_raw,
            "ntrs_link": ntrs_link,
            "exp_key": exp_key,
            "full_name": prof["title"],
            "equation_name": matched["equation_name"],
            "equation_latex": matched["equation_latex"],
            "equation_desc": f"{prof['equation_name']} — calibrated against {prof['code']} flight envelope.",
            "threat_score": matched["threat_score"],
            "threat_tier": matched["threat_tier"],
            "burn_rate_mm_s2": flex_m["Burning Constant K (mm²/s)"],
            "spread_rate_mm_s": saf_m["Spread Rate V_f (mm/s)"],
            "q_rad_kw_m2": saf_m["Radiative Loss q_rad (kW/m²)"],
            "p_ratio": p_ratio,
            "hover_summary_html": hover_html,
        }
    return cached
