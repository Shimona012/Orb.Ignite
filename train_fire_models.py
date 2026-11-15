"""Standalone NASA PSI microgravity combustion ML + physics-hybrid trainer.

This module is intentionally standalone and separate from the Streamlit UI (`Pages/*`).
It cleans and merges the NASA Physical Sciences Informatics (PSI) datasets under `DATASETS/`,
strictly isolates Train / Validation / Test splits before any imputation, scaling, or encoding,
benchmarks four model tiers (Naive Baseline, Linear/Logistic Baseline, Random Forest, and XGBoost)
with 95% bootstrap confidence intervals, validates droplet cool-flame & extinction predictions
against PSI-117 digitized curves, and packages a unified `OrbIgnitePredictor` implementing:
    1. Burn Duration & Persistence (`burn_duration_s`, stage probabilities)
    2. Droplet Burning Rate Constant (`K_mm2_s`) & Extinction Diameter (`d_ext_mm`)
    3. Flame Regime & Termination Mode (Hot, Cool Flame, Radiative Self-Extinction, Disruption)
    4. Flame Optical Color & Sooting (`Blue`, `Yellow-Blue`, `Yellow`, `Blue-Limit/Dim`)
    5. Solid Enclosure Gas Signatures (`delta_O2_pct`, `delta_CO2_pct`, `delta_CO_ppm`)
    6. Hybrid Physics + ML Inference Engine with 3-Tier Confidence Warnings and Objective
       Life (Crew) vs. Infrastructure (Spacecraft) Harm Metrics.
"""

from __future__ import annotations

import json
import math
import os
import re
import warnings
from datetime import datetime, timezone
from typing import Any

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="y_pred contains classes not in y_true")
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from xgboost import XGBClassifier, XGBRegressor

SIGMA_SB = 5.6704e-8
R_UNIV = 8.314462
RANDOM_STATE = 42

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "DATASETS")
MODELS_DIR = os.path.join(BASE_DIR, "models")


# Physical property lookup enables cross-fuel generalization beyond one-hot fuel names.
FUEL_PROPERTIES: dict[str, dict[str, Any]] = {
    "Heptane": {
        "fuel_phase": "liquid",
        "mw_g_mol": 100.20,
        "boiling_point_K": 371.5,
        "heat_of_combustion_MJ_kg": 44.6,
        "stoich_o2_mass_ratio": 3.52,
        "sooting_propensity": 0.65,
        "cool_flame_capable": 1,
    },
    "Octane": {
        "fuel_phase": "liquid",
        "mw_g_mol": 114.23,
        "boiling_point_K": 398.8,
        "heat_of_combustion_MJ_kg": 44.4,
        "stoich_o2_mass_ratio": 3.51,
        "sooting_propensity": 0.72,
        "cool_flame_capable": 1,
    },
    "Decane": {
        "fuel_phase": "liquid",
        "mw_g_mol": 142.28,
        "boiling_point_K": 447.3,
        "heat_of_combustion_MJ_kg": 44.2,
        "stoich_o2_mass_ratio": 3.49,
        "sooting_propensity": 0.78,
        "cool_flame_capable": 1,
    },
    "Dodecane": {
        "fuel_phase": "liquid",
        "mw_g_mol": 170.33,
        "boiling_point_K": 489.5,
        "heat_of_combustion_MJ_kg": 44.1,
        "stoich_o2_mass_ratio": 3.48,
        "sooting_propensity": 0.82,
        "cool_flame_capable": 1,
    },
    "Methanol": {
        "fuel_phase": "liquid",
        "mw_g_mol": 32.04,
        "boiling_point_K": 337.8,
        "heat_of_combustion_MJ_kg": 19.9,
        "stoich_o2_mass_ratio": 1.50,
        "sooting_propensity": 0.02,
        "cool_flame_capable": 0,
    },
    "Ethane": {
        "fuel_phase": "gas",
        "mw_g_mol": 30.07,
        "boiling_point_K": 184.6,
        "heat_of_combustion_MJ_kg": 47.5,
        "stoich_o2_mass_ratio": 3.73,
        "sooting_propensity": 0.35,
        "cool_flame_capable": 0,
    },
    "Propane": {
        "fuel_phase": "gas",
        "mw_g_mol": 44.10,
        "boiling_point_K": 231.1,
        "heat_of_combustion_MJ_kg": 46.4,
        "stoich_o2_mass_ratio": 3.63,
        "sooting_propensity": 0.52,
        "cool_flame_capable": 1,
    },
    "Butane": {
        "fuel_phase": "gas",
        "mw_g_mol": 58.12,
        "boiling_point_K": 272.6,
        "heat_of_combustion_MJ_kg": 45.7,
        "stoich_o2_mass_ratio": 3.58,
        "sooting_propensity": 0.62,
        "cool_flame_capable": 1,
    },
    "Methane": {
        "fuel_phase": "gas",
        "mw_g_mol": 16.04,
        "boiling_point_K": 111.7,
        "heat_of_combustion_MJ_kg": 50.0,
        "stoich_o2_mass_ratio": 3.99,
        "sooting_propensity": 0.18,
        "cool_flame_capable": 0,
    },
    "Ethylene": {
        "fuel_phase": "gas",
        "mw_g_mol": 28.05,
        "boiling_point_K": 169.4,
        "heat_of_combustion_MJ_kg": 47.2,
        "stoich_o2_mass_ratio": 3.42,
        "sooting_propensity": 0.78,
        "cool_flame_capable": 0,
    },
    "Propylene": {
        "fuel_phase": "gas",
        "mw_g_mol": 42.08,
        "boiling_point_K": 225.5,
        "heat_of_combustion_MJ_kg": 45.8,
        "stoich_o2_mass_ratio": 3.42,
        "sooting_propensity": 0.84,
        "cool_flame_capable": 1,
    },
    "PMMA": {
        "fuel_phase": "solid",
        "mw_g_mol": 100.12,
        "boiling_point_K": 655.0,
        "heat_of_combustion_MJ_kg": 25.2,
        "stoich_o2_mass_ratio": 1.92,
        "sooting_propensity": 0.58,
        "cool_flame_capable": 0,
    },
    "SIBAL": {
        "fuel_phase": "solid",
        "mw_g_mol": 162.14,
        "boiling_point_K": 620.0,
        "heat_of_combustion_MJ_kg": 16.5,
        "stoich_o2_mass_ratio": 1.18,
        "sooting_propensity": 0.35,
        "cool_flame_capable": 0,
    },
    "Cotton-Fiberglass": {
        "fuel_phase": "solid",
        "mw_g_mol": 162.14,
        "boiling_point_K": 610.0,
        "heat_of_combustion_MJ_kg": 16.5,
        "stoich_o2_mass_ratio": 1.18,
        "sooting_propensity": 0.32,
        "cool_flame_capable": 0,
    },
    "Nomex": {
        "fuel_phase": "solid",
        "mw_g_mol": 238.24,
        "boiling_point_K": 710.0,
        "heat_of_combustion_MJ_kg": 20.5,
        "stoich_o2_mass_ratio": 1.75,
        "sooting_propensity": 0.70,
        "cool_flame_capable": 0,
    },
    "Ultem": {
        "fuel_phase": "solid",
        "mw_g_mol": 592.60,
        "boiling_point_K": 790.0,
        "heat_of_combustion_MJ_kg": 24.0,
        "stoich_o2_mass_ratio": 1.85,
        "sooting_propensity": 0.68,
        "cool_flame_capable": 0,
    },
    "Candle": {
        "fuel_phase": "solid",
        "mw_g_mol": 352.00,
        "boiling_point_K": 570.0,
        "heat_of_combustion_MJ_kg": 42.0,
        "stoich_o2_mass_ratio": 3.45,
        "sooting_propensity": 0.60,
        "cool_flame_capable": 1,
    },
}


def read_psi_csv(rel_path: str) -> pd.DataFrame:
    """Load a PSI CSV safely using utf-8-sig with latin1/cp1252 fallback."""
    full_path = os.path.join(DATASET_DIR, rel_path)
    last_err: Exception | None = None
    for enc in ("utf-8-sig", "latin1", "cp1252"):
        try:
            return pd.read_csv(full_path, encoding=enc)
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"Failed to read {full_path}: {last_err}")


def _extract_first_float(val: Any) -> float:
    """Extract first numeric token from noisy entries like '~6' or '\x96'."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return float("nan")
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "-", "\x96", "#div/0!"):
        return float("nan")
    match = re.search(r"[-+]?\d*\.?\d+", s)
    return float(match.group(0)) if match else float("nan")


def _extract_sequence_stats(val: Any) -> tuple[float, float, float]:
    """Parse sequence settings (e.g., '5 4 3 2 1') into (initial, mean, min)."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return float("nan"), float("nan"), float("nan")
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "-", "\x96"):
        return float("nan"), float("nan"), float("nan")
    nums = [float(m) for m in re.findall(r"\d*\.?\d+", s)]
    if not nums:
        return float("nan"), float("nan"), float("nan")
    return nums[0], float(np.mean(nums)), float(np.min(nums))


def _parse_hms_duration(start_str: Any, end_str: Any) -> float:
    """Compute elapsed burn duration in seconds from HH:MM:SS GMT strings."""
    if pd.isna(start_str) or pd.isna(end_str):
        return float("nan")
    s1 = str(start_str).strip()
    s2 = str(end_str).strip()
    m1 = re.search(r"(\d{1,2}):(\d{2}):(\d{2})", s1)
    m2 = re.search(r"(\d{1,2}):(\d{2}):(\d{2})", s2)
    if not (m1 and m2):
        return float("nan")
    t1 = int(m1.group(1)) * 3600 + int(m1.group(2)) * 60 + int(m1.group(3))
    t2 = int(m2.group(1)) * 3600 + int(m2.group(2)) * 60 + int(m2.group(3))
    dt = t2 - t1
    # Only wrap across midnight when ignition is near 23:xx and flame-off is early 00:xx/01:xx.
    if dt < 0:
        if t1 >= 22 * 3600 and t2 <= 2 * 3600:
            dt += 86400
        else:
            return float("nan")
    if dt <= 0 or dt > 1200:
        return float("nan")
    return float(dt)


def _normalize_fuel_name(raw: Any) -> tuple[str, float]:
    """Map dataset fuel labels to canonical name and fuel stream fraction."""
    s = str(raw).strip()
    lower = s.lower()
    frac = 1.0
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
    if pct_match:
        frac = float(pct_match.group(1)) / 100.0

    for key in FUEL_PROPERTIES:
        if key.lower() in lower:
            return key, frac
    if "pmma" in lower or "film" in lower or "acrylic" in lower:
        return "PMMA", frac
    if "sibal" in lower or "cotton" in lower or "kimwipe" in lower:
        return "Cotton-Fiberglass", frac
    if "nomex" in lower:
        return "Nomex", frac
    if "ultem" in lower:
        return "Ultem", frac
    if "candle" in lower or "wax" in lower:
        return "Candle", frac
    return "Heptane", frac


def _enrich_fuel_properties(df: pd.DataFrame, fuel_col: str = "fuel_base") -> pd.DataFrame:
    """Attach thermodynamic & kinetic lookup descriptors for each row's fuel."""
    enriched = df.copy()
    default_props = FUEL_PROPERTIES["Heptane"]
    props_rows = [FUEL_PROPERTIES.get(str(f), default_props) for f in enriched[fuel_col]]
    props_df = pd.DataFrame(props_rows, index=enriched.index)
    for col in props_df.columns:
        enriched[col] = props_df[col]
    return enriched


# ==============================================================================
# Dataset Loaders & Cleaning Pipelines
# ==============================================================================


def load_flex_dataset() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load and clean PSI-69 FLEX droplet combustion data (274 raw -> 273 clean rows)."""
    raw = read_psi_csv("PSI-69_Experimental table_FLEX.csv")
    df = pd.DataFrame(index=raw.index)
    df["fuel_base"] = raw["Fuel"].astype(str).str.strip().apply(lambda x: _normalize_fuel_name(x)[0])
    df["experiment_family"] = "FLEX"
    df["X_fuel_stream"] = 1.0
    df["pressure_atm"] = pd.to_numeric(raw["Ambient pressure; mmHg"], errors="coerce") / 760.0
    df["X_O2"] = pd.to_numeric(raw["O initial ambient composition; mole fraction"], errors="coerce")
    df["X_N2"] = pd.to_numeric(raw["N initial ambient composition; mole fraction"], errors="coerce")
    # PSI-69 CSV stripped the subscript '2' from CO2; range 0-0.70 confirms CO2 diluent.
    df["X_CO2"] = pd.to_numeric(raw["CO initial ambient composition; mole fraction"], errors="coerce")
    df["X_He"] = pd.to_numeric(raw["He initial ambient composition; mole fraction"], errors="coerce")
    df["char_scale_mm"] = raw["Droplet initial diameter; mm"].apply(_extract_first_float)
    df["d_ext_mm"] = raw["Visible flame extinction diameter; mm"].apply(_extract_first_float)
    df["K_mm2_s"] = pd.to_numeric(raw["Burning rate; mm"], errors="coerce")
    df["burn_duration_s"] = raw["Burn time; s"].apply(_extract_first_float)
    df["test_end"] = raw["Test end"].astype(str).str.strip()
    df["flow_cm_s"] = 0.2
    df["fuel_flow_mg_s"] = 0.0

    # Completion means droplet burned completely out, so visible extinction diameter is 0.0 mm.
    comp_mask = (df["test_end"] == "Completion") & df["d_ext_mm"].isna()
    df.loc[comp_mask, "d_ext_mm"] = 0.0

    dropped_zero_p = int((df["pressure_atm"] <= 0.01).sum())
    df = df[df["pressure_atm"] > 0.01].copy().reset_index(drop=True)

    df = _enrich_fuel_properties(df)
    df["o2_partial_pressure_atm"] = df["X_O2"] * df["pressure_atm"]
    df["inert_diluent_sum"] = df["X_CO2"].fillna(0.0) + df["X_He"].fillna(0.0)

    audit = {
        "raw_rows": int(len(raw)),
        "clean_rows": int(len(df)),
        "dropped_zero_pressure_rows": dropped_zero_p,
        "missing_counts": {k: int(v) for k, v in df.isna().sum().to_dict().items() if v > 0},
    }
    return df, audit


def load_cfig_datasets() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load and unify PSI-159 CFI-G Normal (179 rows) and Inverse (154 valid rows) tables."""
    raw_n = read_psi_csv("PSI-159_Experimental table_CFI-G_Normal Flames.csv")
    raw_i = read_psi_csv("PSI-159_Experimental table_CFI-G_Inverse Flames.csv")
    # Inverse CSV contains trailing empty spreadsheet rows after test 154.
    raw_i = raw_i[raw_i["Fuel"].notna()].copy().reset_index(drop=True)

    records: list[dict[str, Any]] = []

    for _, row in raw_n.iterrows():
        fuel_name, xf_fallback = _normalize_fuel_name(row["Fuel"])
        xf = pd.to_numeric(row["Xf"], errors="coerce")
        if pd.isna(xf):
            xf = xf_fallback
        hot = str(row["Hot ignition"]).strip().lower()
        btime = _extract_first_float(row["burn time (sec)"])
        if hot == "no" and pd.isna(btime):
            btime = 0.0
        peak_c = _extract_first_float(row["Peak burner T (C )"])
        peak_k = peak_c + 273.15 if not math.isnan(peak_c) else float("nan")
        cool_str = str(row.get("Cool flame?", "")).lower()
        comm_str = str(row.get("Comments", "")).lower()
        is_cool = ("yes" in cool_str) or ("direct cool" in comm_str)
        records.append(
            {
                "experiment_family": "CFIG_Normal",
                "fuel_base": fuel_name,
                "X_fuel_stream": float(xf),
                "X_O2": pd.to_numeric(row[" XO2 before test"], errors="coerce"),
                "X_CO2": 0.0,
                "X_He": 0.0,
                "pressure_atm": pd.to_numeric(row["approx p (bar)"], errors="coerce") * 0.986923,
                "fuel_flow_mg_s": pd.to_numeric(row["mHC (mg/s)"], errors="coerce"),
                "flow_cm_s": 2.5,
                "char_scale_mm": 3.2,
                "Tad_K": _extract_first_float(row["Tad (K)"]),
                "Zst": _extract_first_float(row["Zst"]),
                "hot_ignition": hot,
                "burn_duration_s": btime,
                "termination": str(row["Self-ext or flow term"]).strip(),
                "peak_temp_K": peak_k,
                "is_cool_flame": int(is_cool),
                "flame_colour": None,
            }
        )

    def _clean_color(c: Any) -> str | None:
        if pd.isna(c):
            return None
        cl = str(c).strip().lower()
        if cl in ("blue", "blue "):
            return "Blue"
        if "yellow-blue" in cl:
            return "Yellow-Blue"
        if "yellow" in cl:
            return "Yellow"
        if "limit" in cl:
            return "Blue-Limit/Dim"
        return None

    for _, row in raw_i.iterrows():
        fuel_name, _ = _normalize_fuel_name(row["Fuel"])
        xf = _extract_first_float(row["Xf  before test"])
        if math.isnan(xf):
            xf = 1.0
        hot = str(row["Hot ignition"]).strip().lower()
        btime = _extract_first_float(row["burn time (sec)"])
        if hot == "no" and pd.isna(btime):
            btime = 0.0
        peak_k = _extract_first_float(row["Peak burner temp (K)"])
        records.append(
            {
                "experiment_family": "CFIG_Inverse",
                "fuel_base": fuel_name,
                "X_fuel_stream": float(xf),
                "X_O2": pd.to_numeric(row["XO2"], errors="coerce"),
                "X_CO2": 0.0,
                "X_He": 0.0,
                "pressure_atm": pd.to_numeric(row["approx p (bar)"], errors="coerce") * 0.986923,
                "fuel_flow_mg_s": pd.to_numeric(row["HC burnrate (mg/s)"], errors="coerce"),
                "flow_cm_s": 2.5,
                "char_scale_mm": 3.2,
                "Tad_K": _extract_first_float(row["Tad (K)"]),
                "Zst": _extract_first_float(row["Zst"]),
                "hot_ignition": hot,
                "burn_duration_s": btime,
                "termination": str(row["Self -ext or flow term"]).strip(),
                "peak_temp_K": peak_k,
                "is_cool_flame": 0,
                "flame_colour": _clean_color(row["Color"]),
            }
        )

    df = pd.DataFrame(records)
    df = _enrich_fuel_properties(df)
    df["o2_partial_pressure_atm"] = df["X_O2"] * df["pressure_atm"]
    df["inert_diluent_sum"] = 0.0

    audit = {
        "normal_rows": int(len(raw_n)),
        "inverse_valid_rows": int(len(raw_i)),
        "combined_rows": int(len(df)),
        "cool_flame_rows": int(df["is_cool_flame"].sum()),
        "colour_labeled_rows": int(df["flame_colour"].notna().sum()),
    }
    return df, audit


def load_spice_dataset() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load PSI-107 SPICE and deduplicate repeated run timestamps to prevent data leakage."""
    raw = read_psi_csv("PSI-107_Experimental table_Spice.csv")
    work = pd.DataFrame()
    work["gmt_date"] = raw["GMT date"]
    work["gmt_ign"] = raw["GMT ignition"].astype(str).str.strip()
    work["gmt_off"] = raw["GMT  Flame Off "].astype(str).str.strip()
    work["fuel_raw"] = raw["Fuel"].astype(str).str.strip()
    work["burn_duration_s"] = [
        _parse_hms_duration(s, e) for s, e in zip(work["gmt_ign"], work["gmt_off"])
    ]
    work["char_scale_mm"] = pd.to_numeric(raw["Nozzle (mm)"], errors="coerce")
    work["fuel_flow_mg_s"] = pd.to_numeric(raw["Fuel Rate (mg/s)"], errors="coerce")
    work["flow_cm_s"] = pd.to_numeric(raw["Air Rate (cm/s)"], errors="coerce")

    # Multiple camera/rate rows share the exact same burn run; aggregate by run key.
    dedup = (
        work.dropna(subset=["burn_duration_s"])
        .groupby(["gmt_date", "gmt_ign", "gmt_off", "fuel_raw"], as_index=False)
        .agg(
            burn_duration_s=("burn_duration_s", "mean"),
            char_scale_mm=("char_scale_mm", "mean"),
            fuel_flow_mg_s=("fuel_flow_mg_s", "mean"),
            flow_cm_s=("flow_cm_s", "mean"),
        )
    )
    parsed_fuels = dedup["fuel_raw"].apply(_normalize_fuel_name)
    dedup["fuel_base"] = parsed_fuels.apply(lambda x: x[0])
    dedup["X_fuel_stream"] = parsed_fuels.apply(lambda x: x[1])
    dedup["experiment_family"] = "SPICE"
    dedup["X_O2"] = 0.21
    dedup["X_CO2"] = 0.0
    dedup["X_He"] = 0.0
    dedup["pressure_atm"] = 1.0
    dedup = _enrich_fuel_properties(dedup)
    dedup["o2_partial_pressure_atm"] = dedup["X_O2"] * dedup["pressure_atm"]
    dedup["inert_diluent_sum"] = 0.0

    audit = {
        "raw_rows": int(len(raw)),
        "deduplicated_runs": int(len(dedup)),
    }
    return dedup, audit


def _parse_bass2_material(desc: Any) -> tuple[str, str, float, float, int]:
    """Extract material class, geometry, thickness/diameter (mm), width (mm), and one-sided flag."""
    s = str(desc).strip()
    lower = s.lower()

    if "nomex" in lower:
        mat = "Nomex"
    elif "ultem" in lower:
        mat = "Ultem"
    elif "sibal" in lower or "cotton" in lower or "kimwipe" in lower:
        mat = "Cotton-Fiberglass"
    elif "candle" in lower or "wax" in lower:
        mat = "Candle"
    else:
        mat = "PMMA"

    if "rod" in lower or "cyl" in lower or "candle" in lower:
        geom = "rod"
    elif "sphere" in lower:
        geom = "sphere"
    elif "slab" in lower or "sided" in lower or re.search(r"\b[1-5]\s*mm\b", lower):
        geom = "slab"
    elif "sibal" in lower:
        geom = "fabric"
    else:
        geom = "film"

    thick_mm = 0.25
    m_frac_in = re.search(r"(\d+)\s*/\s*(\d+)\s*(?:\"|in|black|clear|blac|rod)?", lower)
    m_dec_in = re.search(r'(\d+(?:\.\d+)?)\s*"', lower)
    m_um = re.search(r"(\d+(?:\.\d+)?)\s*(?:micron|um)", lower)
    m_mm = re.search(r"(\d+(?:\.\d+)?)\s*mm\b", lower)
    m_cm = re.search(r"(\d+(?:\.\d+)?)\s*cm\b", lower)

    if geom == "rod" and m_frac_in:
        thick_mm = (float(m_frac_in.group(1)) / float(m_frac_in.group(2))) * 25.4
    elif geom == "rod" and m_dec_in:
        thick_mm = float(m_dec_in.group(1)) * 25.4
    elif geom == "sphere" and m_cm:
        thick_mm = float(m_cm.group(1)) * 10.0
    elif m_um:
        thick_mm = float(m_um.group(1)) / 1000.0
    elif m_mm:
        thick_mm = float(m_mm.group(1))
    elif mat == "Cotton-Fiberglass":
        thick_mm = 0.35

    width_mm = 20.0
    if m_cm:
        width_mm = float(m_cm.group(1)) * 10.0
    elif geom == "rod":
        width_mm = thick_mm

    is_one_sided = 1 if ("1 sided" in lower or "top side" in lower) else 0
    return mat, geom, thick_mm, width_mm, is_one_sided


def load_bass2_dataset() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load and clean PSI-25 BASS-II solid combustion gas delta signatures."""
    raw = read_psi_csv("PSI-25_Experimental table_BASS-II.csv")
    df = pd.DataFrame(index=raw.index)
    parsed = raw["Fuel Sample Material"].apply(_parse_bass2_material)
    df["fuel_base"] = parsed.apply(lambda x: x[0])
    df["geometry"] = parsed.apply(lambda x: x[1])
    df["thickness_mm"] = parsed.apply(lambda x: x[2])
    df["width_mm"] = parsed.apply(lambda x: x[3])
    df["is_one_sided"] = parsed.apply(lambda x: x[4])
    df["flow_restrictor"] = pd.to_numeric(raw["Flow restrictor"], errors="coerce")

    air_stats = raw["Air display"].apply(_extract_sequence_stats)
    df["air_flow_init"] = air_stats.apply(lambda x: x[0])
    df["air_flow_mean"] = air_stats.apply(lambda x: x[1])
    df["air_flow_min"] = air_stats.apply(lambda x: x[2])

    fan_stats = raw["Fan display"].apply(_extract_sequence_stats)
    df["fan_init"] = fan_stats.apply(lambda x: x[0])

    df["total_frames"] = raw["Total Frames Shot"].apply(_extract_first_float)
    df["init_O2_pct"] = pd.to_numeric(raw["Calibrated  initial O2 % by vol "], errors="coerce")
    df["final_O2_pct"] = pd.to_numeric(raw["Calibrated final O2 % by vol"], errors="coerce")
    df["init_CO2_pct"] = pd.to_numeric(raw["Initial CO2 % by vol"], errors="coerce")
    df["final_CO2_pct"] = pd.to_numeric(raw["Final CO2 % by vol"], errors="coerce")
    df["init_CO_ppm"] = pd.to_numeric(raw["Initial CO (ppm)"], errors="coerce")
    df["final_CO_ppm"] = pd.to_numeric(raw["Final CO (ppm)"], errors="coerce")

    # Remove documented O2 sensor gain/zero glitches (spikes > init+0.5 or impossible <10% dropouts).
    glitch_mask = (df["final_O2_pct"] > (df["init_O2_pct"] + 0.5)) | (df["final_O2_pct"] < 10.0)
    dropped_glitches = int(glitch_mask.sum())
    df = df[~glitch_mask].copy().reset_index(drop=True)

    df["delta_O2_pct"] = np.where(
        df["final_O2_pct"].notna() & df["init_O2_pct"].notna(),
        np.maximum(0.0, df["init_O2_pct"] - df["final_O2_pct"]),
        np.nan,
    )
    df["delta_CO2_pct"] = np.where(
        df["final_CO2_pct"].notna() & df["init_CO2_pct"].notna(),
        np.maximum(0.0, df["final_CO2_pct"] - df["init_CO2_pct"]),
        np.nan,
    )
    df["delta_CO_ppm"] = np.where(
        df["final_CO_ppm"].notna() & df["init_CO_ppm"].notna(),
        np.maximum(0.0, df["final_CO_ppm"] - df["init_CO_ppm"]),
        np.nan,
    )

    df = _enrich_fuel_properties(df)
    df["sample_cross_section_mm2"] = df["thickness_mm"] * df["width_mm"]
    audit = {
        "raw_rows": int(len(raw)),
        "dropped_o2_sensor_glitches": dropped_glitches,
        "valid_O2_rows": int(df["delta_O2_pct"].notna().sum()),
        "valid_CO2_rows": int(df["delta_CO2_pct"].notna().sum()),
        "valid_CO_rows": int(df["delta_CO_ppm"].notna().sum()),
    }
    return df, audit


def load_psi117_cool_flame_curves() -> dict[str, pd.DataFrame]:
    """Load digitized PSI-117 cool-flame burning rate & extinction curves."""
    kavg_raw = read_psi_csv("PSI-117/PSI-117_Analyzed Data_MST_2024_Kavg.csv")
    kavg_exp = kavg_raw[["Pressure", "Kavg_CF"]].dropna().copy()
    kavg_exp.columns = ["pressure_atm", "K_mm2_s"]
    kavg_exp["fuel_base"] = "Dodecane"
    kavg_exp["source"] = "Expt_MST_2024"

    dext_raw = read_psi_csv("PSI-117/PSI-117_Analyzed Data_MST_2024_Dext.csv")
    dext_cool_exp = dext_raw[["Pressure.1", "Dext_cool_Expt"]].dropna().copy()
    dext_cool_exp.columns = ["pressure_atm", "d_ext_cool_mm"]
    dext_cool_exp["fuel_base"] = "Dodecane"

    alk_raw = read_psi_csv("PSI-117/PSI-117_Analyzed Data_PROCI_2023_Alkane_Extinction_Diameter_1atm.csv")
    alk_rows: list[dict[str, Any]] = []
    block_map = [
        ("Heptane", "Do", "Dext_HF", "Dext_CF"),
        ("Decane", "Do.2", "Dext_HF.2", "Dext_CF.2"),
        ("Dodecane", "Do.4", "Dext_HF.4", "Dext_CF.4"),
    ]
    for fuel_name, c_do, c_hf, c_cf in block_map:
        sub = alk_raw[[c_do, c_hf, c_cf]].dropna()
        for _, r in sub.iterrows():
            alk_rows.append(
                {
                    "fuel_base": fuel_name,
                    "pressure_atm": 1.0,
                    "X_O2": 0.21,
                    "X_N2": 0.79,
                    "X_CO2": 0.0,
                    "X_He": 0.0,
                    "char_scale_mm": float(r[c_do]),
                    "d_ext_hot_mm": float(r[c_hf]),
                    "d_ext_cool_mm": float(r[c_cf]),
                }
            )
    alk_df = pd.DataFrame(alk_rows)

    c12_p_raw = read_psi_csv("PSI-117/PSI-117_Analyzed Data_PROCI_2023_C12_Extinction_Diameter_vs_pressure.csv")
    c12_p_df = c12_p_raw[["P (atm).1", "Dext_CF_EXPT"]].dropna().copy()
    c12_p_df.columns = ["pressure_atm", "d_ext_cool_mm"]
    c12_p_df["fuel_base"] = "Dodecane"

    return {
        "kavg_cool": kavg_exp,
        "dext_cool_mst": dext_cool_exp,
        "alkane_dext_1atm": alk_df,
        "c12_dext_pressure": c12_p_df,
    }


# ==============================================================================
# ML Best-Practices Splitting, Preprocessing & Evaluation Helpers
# ==============================================================================


def make_preprocessor(num_cols: list[str], cat_cols: list[str]) -> ColumnTransformer:
    """Create leakage-free ColumnTransformer fit strictly on training data."""
    num_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    cat_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [
            ("num", num_pipe, num_cols),
            ("cat", cat_pipe, cat_cols),
        ],
        remainder="drop",
    )


def split_train_val_test(
    df: pd.DataFrame,
    target_col: str,
    is_classification: bool,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split DataFrame into 70% Train / 15% Val / 15% Test BEFORE featurization."""
    strat_arg = None
    if is_classification:
        vc = df[target_col].value_counts()
        if vc.min() >= 4:
            strat_arg = df[target_col]
    else:
        try:
            bins = pd.qcut(df[target_col], q=min(5, df[target_col].nunique()), duplicates="drop")
            if bins.value_counts().min() >= 4:
                strat_arg = bins
        except Exception:
            strat_arg = None

    df_trainval, df_test = train_test_split(
        df, test_size=0.15, random_state=random_state, stratify=strat_arg
    )

    strat_tv = None
    if is_classification and df_trainval[target_col].value_counts().min() >= 3:
        strat_tv = df_trainval[target_col]

    df_train, df_val = train_test_split(
        df_trainval,
        test_size=0.15 / 0.85,
        random_state=random_state,
        stratify=strat_tv,
    )
    return df_train.copy(), df_val.copy(), df_test.copy()


def bootstrap_reg_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 500
) -> dict[str, Any]:
    """Compute MAE, RMSE, R2 and 95% bootstrap confidence intervals."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(yt, yp))
    rmse = float(root_mean_squared_error(yt, yp))
    r2 = float(r2_score(yt, yp)) if np.std(yt) > 1e-9 else 0.0

    rng = np.random.default_rng(RANDOM_STATE)
    n = len(yt)
    maes, rmses, r2s = [], [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yb, pb = yt[idx], yp[idx]
        maes.append(mean_absolute_error(yb, pb))
        rmses.append(root_mean_squared_error(yb, pb))
        r2s.append(r2_score(yb, pb) if np.std(yb) > 1e-9 else 0.0)

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "mae_ci95": [round(float(np.percentile(maes, 2.5)), 4), round(float(np.percentile(maes, 97.5)), 4)],
        "rmse_ci95": [round(float(np.percentile(rmses, 2.5)), 4), round(float(np.percentile(rmses, 97.5)), 4)],
        "r2_ci95": [round(float(np.percentile(r2s, 2.5)), 4), round(float(np.percentile(r2s, 97.5)), 4)],
    }


def bootstrap_clf_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None,
    labels: list[Any],
    n_boot: int = 500,
) -> dict[str, Any]:
    """Compute Macro-F1, Balanced Accuracy, Log-Loss, and 95% bootstrap CIs."""
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    mf1 = float(f1_score(yt, yp, average="macro", zero_division=0))
    wf1 = float(f1_score(yt, yp, average="weighted", zero_division=0))
    bal_acc = float(balanced_accuracy_score(yt, yp))
    cm = confusion_matrix(yt, yp, labels=range(len(labels))).tolist()

    ll = None
    if y_proba is not None:
        try:
            ll = round(float(log_loss(yt, y_proba, labels=list(range(len(labels))))), 4)
        except Exception:
            ll = None

    rng = np.random.default_rng(RANDOM_STATE)
    n = len(yt)
    mf1s, bals = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        mf1s.append(f1_score(yt[idx], yp[idx], average="macro", zero_division=0))
        bals.append(balanced_accuracy_score(yt[idx], yp[idx]))

    return {
        "macro_f1": round(mf1, 4),
        "weighted_f1": round(wf1, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "log_loss": ll,
        "macro_f1_ci95": [round(float(np.percentile(mf1s, 2.5)), 4), round(float(np.percentile(mf1s, 97.5)), 4)],
        "balanced_acc_ci95": [round(float(np.percentile(bals, 2.5)), 4), round(float(np.percentile(bals, 97.5)), 4)],
        "confusion_matrix": cm,
        "class_names": [str(c) for c in labels],
    }


def train_and_compare_regressors(
    task_name: str,
    df: pd.DataFrame,
    num_cols: list[str],
    cat_cols: list[str],
    target_col: str,
    log_target: bool = False,
    clip_min: float | None = 0.0,
) -> dict[str, Any]:
    """Train Naive, Ridge, RandomForest, and tuned XGBRegressor with zero data leakage."""
    clean = df[df[target_col].notna()].copy().reset_index(drop=True)
    df_tr, df_val, df_te = split_train_val_test(clean, target_col, is_classification=False)

    X_tr, X_val, X_te = df_tr[num_cols + cat_cols], df_val[num_cols + cat_cols], df_te[num_cols + cat_cols]
    y_tr_raw = df_tr[target_col].to_numpy(dtype=float)
    y_val_raw = df_val[target_col].to_numpy(dtype=float)
    y_te_raw = df_te[target_col].to_numpy(dtype=float)

    y_tr = np.log1p(np.maximum(0.0, y_tr_raw)) if log_target else y_tr_raw
    y_val = np.log1p(np.maximum(0.0, y_val_raw)) if log_target else y_val_raw

    def _inv(arr: np.ndarray) -> np.ndarray:
        out = np.expm1(np.clip(arr, -1.0, 12.0)) if log_target else arr
        if clip_min is not None:
            out = np.maximum(clip_min, out)
        return out

    prep = make_preprocessor(num_cols, cat_cols)
    X_tr_p = prep.fit_transform(X_tr)
    X_val_p = prep.transform(X_val)
    X_te_p = prep.transform(X_te)

    candidates: dict[str, Any] = {
        "Naive_Baseline": DummyRegressor(strategy="mean").fit(X_tr_p, y_tr),
        "Linear_Baseline": Ridge(alpha=5.0).fit(X_tr_p, y_tr),
        "RandomForest": RandomForestRegressor(
            n_estimators=300, max_depth=10, min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=1
        ).fit(X_tr_p, y_tr),
    }

    best_xgb = None
    best_xgb_val_rmse = float("inf")
    best_params = {}
    for md in (2, 3, 4, 6):
        for lr in (0.03, 0.06):
            for n_est in (120, 220, 320):
                for mcw in (1, 4):
                    model = XGBRegressor(
                        max_depth=md,
                        learning_rate=lr,
                        n_estimators=n_est,
                        min_child_weight=mcw,
                        subsample=0.85,
                        colsample_bytree=0.85,
                        reg_alpha=0.2,
                        reg_lambda=2.0,
                        random_state=RANDOM_STATE,
                        n_jobs=1,
                    )
                    model.fit(X_tr_p, y_tr)
                    val_rmse = root_mean_squared_error(y_val_raw, _inv(model.predict(X_val_p)))
                    if val_rmse < best_xgb_val_rmse:
                        best_xgb_val_rmse = val_rmse
                        best_xgb = model
                        best_params = {
                            "max_depth": md,
                            "learning_rate": lr,
                            "n_estimators": n_est,
                            "min_child_weight": mcw,
                        }
    candidates["XGBoost"] = best_xgb

    comparison = {}
    for name, mdl in candidates.items():
        val_pred = _inv(mdl.predict(X_val_p))
        test_pred = _inv(mdl.predict(X_te_p))
        val_metrics = bootstrap_reg_metrics(y_val_raw, val_pred, n_boot=200)
        test_metrics = bootstrap_reg_metrics(y_te_raw, test_pred, n_boot=500)
        comparison[name] = {"val": val_metrics, "test": test_metrics}

    # Refit the final regularized XGBoost pipeline on Train+Val (zero Test leakage).
    df_tv = pd.concat([df_tr, df_val], axis=0).reset_index(drop=True)
    y_tv_raw = df_tv[target_col].to_numpy(dtype=float)
    y_tv = np.log1p(np.maximum(0.0, y_tv_raw)) if log_target else y_tv_raw

    cv_pipe = Pipeline(
        [
            ("prep", make_preprocessor(num_cols, cat_cols)),
            (
                "xgb",
                XGBRegressor(
                    **best_params,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    reg_alpha=0.2,
                    reg_lambda=2.0,
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                ),
            ),
        ]
    )
    cv_r2 = cross_val_score(cv_pipe, df_tv[num_cols + cat_cols], y_tv, cv=5, scoring="r2")

    final_prep = make_preprocessor(num_cols, cat_cols)
    X_tv_p = final_prep.fit_transform(df_tv[num_cols + cat_cols])
    final_xgb = XGBRegressor(
        **best_params,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.2,
        reg_lambda=2.0,
        random_state=RANDOM_STATE,
        n_jobs=1,
    ).fit(X_tv_p, y_tv)

    # Evaluate final Train+Val XGBoost on untouched Test split for honest generalization report.
    final_test_pred = _inv(final_xgb.predict(final_prep.transform(X_te)))
    final_test_metrics = bootstrap_reg_metrics(y_te_raw, final_test_pred, n_boot=500)

    return {
        "task_name": task_name,
        "n_total": int(len(clean)),
        "split_sizes": {"train": len(df_tr), "val": len(df_val), "test": len(df_te)},
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "log_target": log_target,
        "clip_min": clip_min,
        "best_xgb_params": best_params,
        "cv5_trainval_r2_mean": round(float(np.mean(cv_r2)), 4),
        "cv5_trainval_r2_std": round(float(np.std(cv_r2)), 4),
        "benchmark_comparison": comparison,
        "final_test_metrics": final_test_metrics,
        "preprocessor": final_prep,
        "model": final_xgb,
    }


def train_and_compare_classifiers(
    task_name: str,
    df: pd.DataFrame,
    num_cols: list[str],
    cat_cols: list[str],
    target_col: str,
) -> dict[str, Any]:
    """Train Naive, Logistic, RandomForest, and tuned XGBClassifier with zero data leakage."""
    clean = df[df[target_col].notna()].copy().reset_index(drop=True)
    le = LabelEncoder()
    clean["_y_enc"] = le.fit_transform(clean[target_col].astype(str))
    classes = list(le.classes_)

    df_tr, df_val, df_te = split_train_val_test(clean, "_y_enc", is_classification=True)
    X_tr, X_val, X_te = df_tr[num_cols + cat_cols], df_val[num_cols + cat_cols], df_te[num_cols + cat_cols]
    y_tr = df_tr["_y_enc"].to_numpy(dtype=int)
    y_val = df_val["_y_enc"].to_numpy(dtype=int)
    y_te = df_te["_y_enc"].to_numpy(dtype=int)

    prep = make_preprocessor(num_cols, cat_cols)
    X_tr_p = prep.fit_transform(X_tr)
    X_val_p = prep.transform(X_val)
    X_te_p = prep.transform(X_te)

    candidates: dict[str, Any] = {
        "Naive_Baseline": DummyClassifier(strategy="most_frequent").fit(X_tr_p, y_tr),
        "Linear_Baseline": LogisticRegression(
            max_iter=1500, class_weight="balanced", random_state=RANDOM_STATE
        ).fit(X_tr_p, y_tr),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=10, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1
        ).fit(X_tr_p, y_tr),
    }

    best_xgb = None
    best_val_f1 = -1.0
    best_params = {}
    for md in (3, 4, 6):
        for lr in (0.04, 0.08):
            for n_est in (180, 300):
                model = XGBClassifier(
                    max_depth=md,
                    learning_rate=lr,
                    n_estimators=n_est,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    reg_lambda=1.5,
                    eval_metric="mlogloss",
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                )
                model.fit(X_tr_p, y_tr)
                mf1 = f1_score(y_val, model.predict(X_val_p), average="macro", zero_division=0)
                if mf1 > best_val_f1:
                    best_val_f1 = mf1
                    best_xgb = model
                    best_params = {"max_depth": md, "learning_rate": lr, "n_estimators": n_est}
    candidates["XGBoost"] = best_xgb

    comparison = {}
    for name, mdl in candidates.items():
        vp = mdl.predict(X_val_p)
        vprob = mdl.predict_proba(X_val_p) if hasattr(mdl, "predict_proba") else None
        tp = mdl.predict(X_te_p)
        tprob = mdl.predict_proba(X_te_p) if hasattr(mdl, "predict_proba") else None
        comparison[name] = {
            "val": bootstrap_clf_metrics(y_val, vp, vprob, classes, n_boot=200),
            "test": bootstrap_clf_metrics(y_te, tp, tprob, classes, n_boot=500),
        }

    df_tv = pd.concat([df_tr, df_val], axis=0).reset_index(drop=True)
    y_tv = df_tv["_y_enc"].to_numpy(dtype=int)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_pipe = Pipeline(
        [
            ("prep", make_preprocessor(num_cols, cat_cols)),
            (
                "xgb",
                XGBClassifier(
                    **best_params,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    reg_lambda=1.5,
                    eval_metric="mlogloss",
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                ),
            ),
        ]
    )
    cv_f1 = cross_val_score(cv_pipe, df_tv[num_cols + cat_cols], y_tv, cv=skf, scoring="f1_macro")

    final_prep = make_preprocessor(num_cols, cat_cols)
    X_tv_p = final_prep.fit_transform(df_tv[num_cols + cat_cols])
    final_xgb = XGBClassifier(
        **best_params,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.5,
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=1,
    ).fit(X_tv_p, y_tv)

    X_te_final_p = final_prep.transform(X_te)
    final_te_pred = final_xgb.predict(X_te_final_p)
    final_te_prob = final_xgb.predict_proba(X_te_final_p)
    final_test_metrics = bootstrap_clf_metrics(y_te, final_te_pred, final_te_prob, classes, n_boot=500)

    return {
        "task_name": task_name,
        "n_total": int(len(clean)),
        "class_distribution": {str(k): int(v) for k, v in clean[target_col].value_counts().to_dict().items()},
        "split_sizes": {"train": len(df_tr), "val": len(df_val), "test": len(df_te)},
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "classes": classes,
        "best_xgb_params": best_params,
        "cv5_trainval_macro_f1_mean": round(float(np.mean(cv_f1)), 4),
        "cv5_trainval_macro_f1_std": round(float(np.std(cv_f1)), 4),
        "benchmark_comparison": comparison,
        "final_test_metrics": final_test_metrics,
        "preprocessor": final_prep,
        "model": final_xgb,
        "label_encoder": le,
    }


# ==============================================================================
# Dataset Assembly for Models 1 - 5
# ==============================================================================


def build_model1_duration_dataset(
    flex_df: pd.DataFrame, cfig_df: pd.DataFrame, spice_df: pd.DataFrame
) -> pd.DataFrame:
    """Assemble cross-experiment burn duration & persistence dataset."""
    cols = [
        "experiment_family",
        "fuel_base",
        "fuel_phase",
        "X_O2",
        "X_fuel_stream",
        "X_CO2",
        "X_He",
        "pressure_atm",
        "o2_partial_pressure_atm",
        "inert_diluent_sum",
        "char_scale_mm",
        "flow_cm_s",
        "fuel_flow_mg_s",
        "mw_g_mol",
        "boiling_point_K",
        "heat_of_combustion_MJ_kg",
        "stoich_o2_mass_ratio",
        "sooting_propensity",
        "cool_flame_capable",
        "burn_duration_s",
    ]
    flex_sub = flex_df[cols].copy()
    flex_sub["persistence_stage"] = np.where(
        flex_sub["burn_duration_s"] < 2.0, "Brief_Flash", "Sustained_Burn"
    )

    cfig_sub = cfig_df[cols + ["hot_ignition"]].copy()

    def _cfig_stage(row: pd.Series) -> str:
        hot = str(row["hot_ignition"]).lower()
        dur = float(row["burn_duration_s"]) if pd.notna(row["burn_duration_s"]) else 0.0
        if hot == "no" or dur <= 0.1:
            return "No_Sustained_Burn"
        if hot == "flash" or dur < 2.0:
            return "Brief_Flash"
        return "Sustained_Burn"

    cfig_sub["persistence_stage"] = cfig_sub.apply(_cfig_stage, axis=1)
    cfig_sub = cfig_sub.drop(columns=["hot_ignition"])

    spice_sub = spice_df[cols].copy()
    spice_sub["persistence_stage"] = np.where(
        spice_sub["burn_duration_s"] < 2.0, "Brief_Flash", "Sustained_Burn"
    )

    combined = pd.concat([flex_sub, cfig_sub, spice_sub], axis=0).reset_index(drop=True)
    combined = combined[combined["burn_duration_s"].notna()].copy().reset_index(drop=True)
    return combined


def build_model3_regime_dataset(
    flex_df: pd.DataFrame, cfig_df: pd.DataFrame, psi117: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Assemble 4-class Flame Regime dataset from FLEX, CFI-G, and PSI-117 cool-flame curves."""
    rows: list[dict[str, Any]] = []

    def _to_row(src: pd.Series, regime: str) -> dict[str, Any]:
        return {
            "experiment_family": src["experiment_family"],
            "fuel_base": src["fuel_base"],
            "fuel_phase": src["fuel_phase"],
            "X_O2": src["X_O2"],
            "X_fuel_stream": src["X_fuel_stream"],
            "X_CO2": src["X_CO2"],
            "X_He": src["X_He"],
            "pressure_atm": src["pressure_atm"],
            "o2_partial_pressure_atm": src["o2_partial_pressure_atm"],
            "inert_diluent_sum": src["inert_diluent_sum"],
            "char_scale_mm": src["char_scale_mm"],
            "flow_cm_s": src["flow_cm_s"],
            "fuel_flow_mg_s": src["fuel_flow_mg_s"],
            "mw_g_mol": src["mw_g_mol"],
            "boiling_point_K": src["boiling_point_K"],
            "heat_of_combustion_MJ_kg": src["heat_of_combustion_MJ_kg"],
            "stoich_o2_mass_ratio": src["stoich_o2_mass_ratio"],
            "sooting_propensity": src["sooting_propensity"],
            "cool_flame_capable": src["cool_flame_capable"],
            "fire_regime": regime,
        }

    for _, r in flex_df.iterrows():
        tend = r["test_end"]
        if tend == "Completion":
            reg = "Hot_Sustained"
        elif tend == "Disruption":
            reg = "Droplet_Disruption"
        else:
            reg = "Radiative_Diffusive_Self_Extinction"
        rows.append(_to_row(r, reg))

    for _, r in cfig_df.iterrows():
        if int(r["is_cool_flame"]) == 1:
            reg = "Cool_Flame"
        elif str(r["hot_ignition"]).lower() == "yes" and (
            r["termination"] == "FT" or (pd.notna(r["burn_duration_s"]) and float(r["burn_duration_s"]) >= 20.0)
        ):
            reg = "Hot_Sustained"
        else:
            reg = "Radiative_Diffusive_Self_Extinction"
        rows.append(_to_row(r, reg))

    # Add genuine PSI-117 experimental cool-flame stabilization records across C7, C10, C12.
    cf_points: list[dict[str, Any]] = []
    for _, r in psi117["alkane_dext_1atm"].iterrows():
        if float(r["d_ext_cool_mm"]) > 0.0:
            cf_points.append(
                {
                    "experiment_family": "FLEX",
                    "fuel_base": r["fuel_base"],
                    "X_O2": 0.21,
                    "X_fuel_stream": 1.0,
                    "X_CO2": 0.0,
                    "X_He": 0.0,
                    "pressure_atm": float(r["pressure_atm"]),
                    "char_scale_mm": float(r["char_scale_mm"]),
                    "flow_cm_s": 0.2,
                    "fuel_flow_mg_s": 0.0,
                    "fire_regime": "Cool_Flame",
                }
            )
    for _, r in psi117["c12_dext_pressure"].iterrows():
        cf_points.append(
            {
                "experiment_family": "FLEX",
                "fuel_base": "Dodecane",
                "X_O2": 0.21,
                "X_fuel_stream": 1.0,
                "X_CO2": 0.0,
                "X_He": 0.0,
                "pressure_atm": float(r["pressure_atm"]),
                "char_scale_mm": 4.2,
                "flow_cm_s": 0.2,
                "fuel_flow_mg_s": 0.0,
                "fire_regime": "Cool_Flame",
            }
        )
    for _, r in psi117["kavg_cool"].iterrows():
        cf_points.append(
            {
                "experiment_family": "FLEX",
                "fuel_base": "Dodecane",
                "X_O2": 0.21,
                "X_fuel_stream": 1.0,
                "X_CO2": 0.0,
                "X_He": 0.0,
                "pressure_atm": float(r["pressure_atm"]),
                "char_scale_mm": 4.0,
                "flow_cm_s": 0.2,
                "fuel_flow_mg_s": 0.0,
                "fire_regime": "Cool_Flame",
            }
        )

    if cf_points:
        cf_df = pd.DataFrame(cf_points)
        cf_df = _enrich_fuel_properties(cf_df)
        cf_df["o2_partial_pressure_atm"] = cf_df["X_O2"] * cf_df["pressure_atm"]
        cf_df["inert_diluent_sum"] = 0.0
        for _, r in cf_df.iterrows():
            rows.append(_to_row(r, "Cool_Flame"))

    return pd.DataFrame(rows).reset_index(drop=True)


# ==============================================================================
# Model 6: Hybrid Physics + ML Inference, Confidence Tiers & Harm Quantification
# ==============================================================================


class OrbIgnitePredictor:
    """Unified Hybrid ML + Microgravity Combustion Physics Predictor (Model 6)."""

    def __init__(self, artifacts: dict[str, Any], psi117_benchmarks: dict[str, Any]) -> None:
        self.artifacts = artifacts
        self.psi117_benchmarks = psi117_benchmarks

    def _build_feature_row(
        self,
        fuel: str,
        gravity_g: float,
        o2_pct: float,
        pressure_atm: float,
        flow_cm_s: float,
        char_scale_mm: float,
        co2_frac: float,
        he_frac: float,
        fuel_flow_mg_s: float,
        experiment_family: str,
    ) -> pd.DataFrame:
        fuel_base, _ = _normalize_fuel_name(fuel)
        props = FUEL_PROPERTIES.get(fuel_base, FUEL_PROPERTIES["Heptane"])
        x_o2 = max(0.01, float(o2_pct) / 100.0)
        x_n2 = max(0.0, 1.0 - x_o2 - float(co2_frac) - float(he_frac))
        row = {
            "experiment_family": experiment_family,
            "fuel_base": fuel_base,
            "fuel_phase": props["fuel_phase"],
            "X_O2": x_o2,
            "X_N2": x_n2,
            "X_CO2": float(co2_frac),
            "X_He": float(he_frac),
            "X_fuel_stream": 1.0,
            "pressure_atm": float(pressure_atm),
            "o2_partial_pressure_atm": x_o2 * float(pressure_atm),
            "inert_diluent_sum": float(co2_frac) + float(he_frac),
            "char_scale_mm": float(char_scale_mm),
            "d0_mm": float(char_scale_mm),
            "flow_cm_s": float(flow_cm_s),
            "fuel_flow_mg_s": float(fuel_flow_mg_s),
            "mw_g_mol": props["mw_g_mol"],
            "boiling_point_K": props["boiling_point_K"],
            "heat_of_combustion_MJ_kg": props["heat_of_combustion_MJ_kg"],
            "stoich_o2_mass_ratio": props["stoich_o2_mass_ratio"],
            "sooting_propensity": props["sooting_propensity"],
            "cool_flame_capable": props["cool_flame_capable"],
            "Zst": round(1.0 / (1.0 + props["stoich_o2_mass_ratio"] * 4.29 * (0.21 / x_o2)), 4),
            "Tad_K": 1850.0 + 38.0 * (o2_pct - 21.0) - 450.0 * co2_frac,
        }
        return pd.DataFrame([row])

    def _classify_confidence(
        self, fuel_base: str, gravity_g: float, o2_pct: float, pressure_atm: float, flow_cm_s: float, area_m2: float
    ) -> tuple[str, str | None]:
        """Assign 3-tier confidence level and explicit NASA provenance warning."""
        
        if (
            o2_pct > 50.0
            or o2_pct < 10.0
            or pressure_atm > 4.0
            or pressure_atm < 0.20
            or gravity_g > 1.5
            or flow_cm_s > 50.0
            or area_m2 > 12.0
        ):
            return (
                "Extrapolated (Low Confidence)",
                "Extrapolated regime (Trained XGBoost + Physics Active): Selected parameters extend beyond standard NASA PSI chamber bounds; values combine trained XGBoost estimators with physics-based scaling.",
            )

        if (
            gravity_g > 0.05
            or area_m2 > 2.5
            or area_m2 < 0.35
            or o2_pct > 40.0
            or o2_pct < 12.0
            or pressure_atm > 3.0
            or pressure_atm < 0.35
            or flow_cm_s > 25.0
        ):
            return (
                "Theory-based (Moderate Confidence)",
                "Theory-backed regime (Trained XGBoost + Physics Active): Partial-gravity/scale coupling combines trained XGBoost estimators with Grashof/Rayleigh/d²-law equations.",
            )

        return ("Data-backed (High Confidence)", None)

    def _predict_clf(self, bundle_key: str, X_row: pd.DataFrame) -> tuple[str, dict[str, float]]:
        b = self.artifacts[bundle_key]
        Xp = b["preprocessor"].transform(X_row[b["num_cols"] + b["cat_cols"]])
        probs = b["model"].predict_proba(Xp)[0]
        classes = b["classes"]
        prob_dict = {str(cls): round(float(p), 4) for cls, p in zip(classes, probs)}
        best_cls = classes[int(np.argmax(probs))]
        return str(best_cls), prob_dict

    def _predict_reg(self, bundle_key: str, X_row: pd.DataFrame) -> float:
        b = self.artifacts[bundle_key]
        Xp = b["preprocessor"].transform(X_row[b["num_cols"] + b["cat_cols"]])
        raw = float(b["model"].predict(Xp)[0])
        val = math.expm1(raw) if b["log_target"] else raw
        if b["clip_min"] is not None:
            val = max(float(b["clip_min"]), val)
        return val

    def predict(
        self,
        fuel: str = "Heptane",
        gravity_g: float = 0.0,
        o2_pct: float = 21.0,
        pressure_atm: float = 1.0,
        flow_cm_s: float = 0.5,
        area_m2: float = 1.0,
        char_scale_mm: float = 3.5,
        co2_frac: float = 0.0,
        he_frac: float = 0.0,
        fuel_flow_mg_s: float = 1.5,
        solid_thickness_mm: float = 0.3,
        solid_width_mm: float = 20.0,
    ) -> dict[str, Any]:
        """Run end-to-end 6-model hybrid inference + objective life/infrastructure harm calculation."""
        fuel_base, _ = _normalize_fuel_name(fuel)
        props = FUEL_PROPERTIES.get(fuel_base, FUEL_PROPERTIES["Heptane"])
        phase = props["fuel_phase"]

        if phase == "liquid":
            exp_fam = "FLEX"
            eff_fuel_flow = 0.0
        elif phase == "gas":
            exp_fam = "CFIG_Inverse"
            eff_fuel_flow = max(0.3, float(fuel_flow_mg_s))
        else:
            exp_fam = "SPICE"
            eff_fuel_flow = 0.0

        X_row = self._build_feature_row(
            fuel=fuel_base,
            gravity_g=gravity_g,
            o2_pct=o2_pct,
            pressure_atm=pressure_atm,
            flow_cm_s=flow_cm_s,
            char_scale_mm=char_scale_mm,
            co2_frac=co2_frac,
            he_frac=he_frac,
            fuel_flow_mg_s=eff_fuel_flow,
            experiment_family=exp_fam,
        )

        # Model 1: Persistence & Burn Duration (never outputs binary "exists: yes/no").
        stage_pred, stage_probs = self._predict_clf("model1a_persistence", X_row)
        ml_dur_s = self._predict_reg("model1b_burn_duration", X_row)

        # Model 2: Droplet K & d_ext + theoretical Grashof/forced-convection coupling.
        k_ml = self._predict_reg("model2a_burning_rate_K", X_row)
        dext_ml = min(float(char_scale_mm), max(0.0, self._predict_reg("model2b_extinction_diameter", X_row)))

        # Buoyancy (Grashof) & ventilation coupling when moving from 0g -> partial/Earth gravity.
        buoyancy_vel_factor = 1.0 + 0.32 * math.sqrt(max(0.0, gravity_g)) + 0.025 * max(0.0, flow_cm_s)
        k_coupled = round(max(0.08, k_ml * buoyancy_vel_factor), 3)
        d2_lifetime_s = max(0.0, (char_scale_mm**2 - dext_ml**2) / max(0.08, k_coupled))

        # Model 3: Flame Regime & Cool Flame Risk.
        regime_ml, regime_probs = self._predict_clf("model3_fire_regime", X_row)
        # Enforce chemistry constraint: C1-C2 alcohols/gases and PMMA lack RO2 isomerization cool flames.
        if props["cool_flame_capable"] == 0 or gravity_g >= 0.35:
            regime_probs["Cool_Flame"] = 0.0 if props["cool_flame_capable"] == 0 else min(regime_probs.get("Cool_Flame", 0.0), 0.04)
            tot_p = sum(regime_probs.values())
            if tot_p > 0:
                regime_probs = {k: round(v / tot_p, 4) for k, v in regime_probs.items()}
            regime_ml = max(regime_probs, key=regime_probs.get)

        p_cool = regime_probs.get("Cool_Flame", 0.0)
        if props["cool_flame_capable"] == 1 and phase == "liquid" and gravity_g < 0.08 and char_scale_mm >= 3.0:
            p_cool = max(p_cool, 0.42 if o2_pct <= 24.0 else 0.28)
            regime_probs["Cool_Flame"] = round(p_cool, 4)

        if p_cool >= 0.38 and gravity_g < 0.25 and props["cool_flame_capable"] == 1:
            fire_regime = "Cool_Flame"
        elif gravity_g >= 0.45 and ml_dur_s >= 2.0:
            fire_regime = "Hot_Sustained"
        else:
            fire_regime = regime_ml

        # Cool flames sustain longer at lower K (~0.38 mm2/s vs ~0.60 hot K).
        if fire_regime == "Cool_Flame":
            cool_k = min(k_coupled, 0.42 + 0.02 * (pressure_atm - 1.0))
            k_coupled = round(max(0.28, cool_k), 3)
            d2_lifetime_s = max(d2_lifetime_s, (char_scale_mm**2 - min(dext_ml, 1.3)**2) / k_coupled)

        # Blend ML duration with physics scaling & stage probability.
        if stage_pred == "No_Sustained_Burn" and o2_pct < 17.5 and gravity_g < 0.05:
            pred_duration_s = 0.0
        elif phase == "liquid":
            pred_duration_s = round(max(0.0, 0.55 * ml_dur_s + 0.45 * d2_lifetime_s), 2)
        elif phase == "solid":
            # Solid samples (BASS-II / SoFIE) burn longer with thickness and O2 supply than SPICE gas pulses.
            v_f_mm_s = max(0.3, (0.8 + 0.08 * (o2_pct - 18.0) + 0.05 * flow_cm_s + 0.6 * gravity_g) / max(0.3, solid_thickness_mm**0.45))
            sample_len_mm = max(25.0, float(solid_width_mm) * 2.5)
            solid_phys_s = sample_len_mm / v_f_mm_s
            pred_duration_s = round(max(0.0, (0.35 * ml_dur_s + 0.65 * solid_phys_s) * max(0.7, area_m2**0.25)), 2)
        else:
            area_boost = max(0.6, min(2.2, float(area_m2) ** 0.35))
            o2_scale = max(0.3, o2_pct / 21.0)
            pred_duration_s = round(max(0.0, ml_dur_s * o2_scale * area_boost / max(0.85, buoyancy_vel_factor)), 2)

        if pred_duration_s <= 0.1:
            duration_statement = "Predicted not to sustain ignition (0.0 s — quenched immediately)"
        elif pred_duration_s < 2.0:
            duration_statement = f"Predicted brief ignition flash lasting {pred_duration_s:.1f} s"
        else:
            duration_statement = f"Predicted to burn for {pred_duration_s:.1f} s"

        # Model 4: Flame Color & Sooting coupled cleanly with gravity buoyancy.
        colour_ml, colour_probs = self._predict_clf("model4_flame_colour", X_row)
        if fire_regime == "Cool_Flame":
            flame_colour = "Blue-Limit/Dim (500–800 K CH₂O* Chemiluminescence)"
        elif fire_regime == "Radiative_Diffusive_Self_Extinction" and pred_duration_s < 2.0:
            flame_colour = "Blue-Limit/Dim"
        elif gravity_g >= 0.45:
            flame_colour = "Yellow-Blue" if props["sooting_propensity"] < 0.25 else "Yellow"
        elif gravity_g >= 0.10:
            flame_colour = "Yellow-Blue" if props["sooting_propensity"] >= 0.35 else "Blue"
        else:
            flame_colour = colour_ml

        # Model 5: Gas Signatures (BASS-II XGBoost regressors + stoichiometry/volume scaling).
        bass_row = pd.DataFrame(
            [
                {
                    "fuel_base": fuel_base if phase == "solid" else "PMMA",
                    "geometry": "film" if solid_thickness_mm < 1.0 else "slab",
                    "thickness_mm": float(solid_thickness_mm),
                    "width_mm": float(solid_width_mm),
                    "is_one_sided": 0,
                    "flow_restrictor": 2 if flow_cm_s >= 5.0 else 0,
                    "air_flow_init": float(flow_cm_s),
                    "air_flow_mean": float(flow_cm_s),
                    "air_flow_min": float(max(0.0, flow_cm_s * 0.6)),
                    "fan_init": 55.0,
                    "init_O2_pct": float(o2_pct),
                    "mw_g_mol": props["mw_g_mol"],
                    "heat_of_combustion_MJ_kg": props["heat_of_combustion_MJ_kg"],
                    "stoich_o2_mass_ratio": props["stoich_o2_mass_ratio"],
                    "sooting_propensity": props["sooting_propensity"],
                    "sample_cross_section_mm2": float(solid_thickness_mm) * float(solid_width_mm),
                }
            ]
        )
        d_o2_base = self._predict_reg("model5a_delta_O2_pct", bass_row)
        d_co2_base = self._predict_reg("model5b_delta_CO2_pct", bass_row)
        d_co_base = self._predict_reg("model5c_delta_CO_ppm", bass_row)

        # Scale from BASS-II tunnel to active compartment area & burn duration.
        confinement_scale = (1.0 / max(0.15, float(area_m2))) ** 0.55
        duration_factor = min(3.5, max(0.15, pred_duration_s / 18.0))
        cool_incomplete_mult = 2.8 if fire_regime == "Cool_Flame" else 1.0

        delta_o2_pct = round(min(o2_pct - 5.0, d_o2_base * confinement_scale * duration_factor), 3)
        delta_co2_pct = round(d_co2_base * confinement_scale * duration_factor, 3)
        delta_co_ppm = round(d_co_base * confinement_scale * duration_factor * cool_incomplete_mult, 1)

        # Confidence tier & warning.
        confidence_tier, warning_msg = self._classify_confidence(
            fuel_base, gravity_g, o2_pct, pressure_atm, flow_cm_s, area_m2
        )

        # Objective Crew Life Damage Metrics (NASA SMACs & Purser FED — zero subjective labels).
        final_o2_pct = round(max(0.0, o2_pct - delta_o2_pct), 2)
        ch2o_mg_m3 = round(
            (4.8 if fire_regime == "Cool_Flame" else 0.55 * (1.0 + props["sooting_propensity"]))
            * confinement_scale
            * min(2.0, duration_factor),
            2,
        )
        smac_co_1hr = 55.0
        co_gen_rate_ppm_s = max(0.05, delta_co_ppm / max(1.0, pred_duration_s))
        time_to_co_smac_s = round(smac_co_1hr / co_gen_rate_ppm_s, 1) if co_gen_rate_ppm_s > 0.05 else None
        # Simplified Purser FED over predicted burn duration (35,000 ppm*min CO incapacitation scale).
        co_dose_ppm_min = delta_co_ppm * (pred_duration_s / 60.0) * 0.5
        hypovent_factor = math.exp(0.1903 * max(0.0, delta_co2_pct))
        fed_co = (co_dose_ppm_min / 35000.0) * hypovent_factor
        fed_o2 = max(0.0, (20.9 - final_o2_pct) / 25.0) * min(1.0, pred_duration_s / 120.0)
        fed_total = round(min(2.0, fed_co + fed_o2 + 0.008 * ch2o_mg_m3), 4)

        life_damage = {
            "co_concentration_ppm": delta_co_ppm,
            "nasa_smac_1hr_co_ppm": smac_co_1hr,
            "nasa_smac_24hr_co_ppm": 15.0,
            "o2_consumed_pct_vol": delta_o2_pct,
            "ambient_o2_remaining_pct": final_o2_pct,
            "hypoxia_threshold_o2_pct": 15.0,
            "co2_added_pct_vol": delta_co2_pct,
            "toxic_formaldehyde_ch2o_mg_m3": ch2o_mg_m3,
            "nasa_smac_ch2o_mg_m3": 0.5,
            "fractional_effective_dose_fed": fed_total,
            "time_to_crew_co_smac_s": time_to_co_smac_s,
        }

        # Objective Spacecraft Infrastructure Damage Metrics (no subjective labels).
        if pred_duration_s <= 0.1:
            peak_temp_K = 298.0
            rad_flux_kw_m2 = 0.0
        elif fire_regime == "Cool_Flame":
            peak_temp_K = round(580.0 + 4.0 * (o2_pct - 21.0) + 12.0 * (pressure_atm - 1.0), 1)
            rad_flux_kw_m2 = round(max(1.2, 0.38 * SIGMA_SB * ((peak_temp_K**4) - (298.0**4)) / 1000.0), 2)
        else:
            peak_temp_K = round(1420.0 + 26.0 * (o2_pct - 21.0) + 120.0 * gravity_g - 220.0 * co2_frac, 1)
            emissivity = min(0.95, 0.25 + 0.55 * props["sooting_propensity"] + 0.15 * min(1.0, gravity_g))
            rad_flux_kw_m2 = round(
                min(95.0, max(3.5, emissivity * SIGMA_SB * ((peak_temp_K**4) - (298.0**4)) / 1000.0 * 0.22)), 2
            )

        # Isochoric compartment pressure rise estimate dP/P0 proportional to energy release.
        energy_release_kJ = (
            props["heat_of_combustion_MJ_kg"]
            * 1000.0
            * max(0.0005, (delta_o2_pct / 100.0) * 1.2 * max(0.2, area_m2) * 0.5 / max(1.0, props["stoich_o2_mass_ratio"]))
        )
        pressure_rise_kPa = round(min(85.0, (0.287 * energy_release_kJ) / max(0.4, float(area_m2) * 2.5)), 2)
        damaged_area_m2 = round(
            min(float(area_m2), (0.002 + 0.00045 * pred_duration_s * (1.0 + 0.1 * flow_cm_s)) * (o2_pct / 21.0)), 4
        )
        char_length_cm = round(math.sqrt(max(0.0, damaged_area_m2)) * 100.0, 1)

        cool_reignition = {
            "cool_flame_active_or_probable": bool(fire_regime == "Cool_Flame" or p_cool >= 0.30),
            "cool_flame_probability": round(float(p_cool), 3),
            "eclss_o2_sustained_hazard": bool(props["cool_flame_capable"] == 1 and o2_pct >= 18.0 and gravity_g < 0.25),
            "estimated_hot_reignition_window_s": (
                round(max(8.0, 45.0 / max(0.6, o2_pct / 21.0) - 0.8 * flow_cm_s), 1)
                if (fire_regime == "Cool_Flame" or p_cool >= 0.30)
                else None
            ),
            "mechanism_note": (
                "Continuous ECLSS O₂ supply sustains invisible 500–800 K formaldehyde-producing combustion and enables hot flame reignition upon airflow resumption."
                if (fire_regime == "Cool_Flame" or p_cool >= 0.30)
                else "Direct hot oxidation kinetics dominate without metastable cool-flame plateau."
            ),
        }

        infra_damage = {
            "radiative_heat_flux_kw_m2": rad_flux_kw_m2,
            "avionics_damage_flux_threshold_kw_m2": 12.5,
            "peak_flame_temp_K": peak_temp_K,
            "aluminum_6061_melt_K": 933.0,
            "cabin_pressure_rise_kPa": pressure_rise_kPa,
            "pressure_ratio_Pmax_P0": round(1.0 + pressure_rise_kPa / max(20.0, pressure_atm * 101.325), 4),
            "damaged_area_m2": damaged_area_m2,
            "char_length_cm": char_length_cm,
            "cool_flame_reignition_risk": cool_reignition,
        }

        return {
            "inputs": {
                "fuel": fuel_base,
                "phase": phase,
                "gravity_g": gravity_g,
                "o2_pct": o2_pct,
                "pressure_atm": pressure_atm,
                "flow_cm_s": flow_cm_s,
                "area_m2": area_m2,
                "char_scale_mm": char_scale_mm,
            },
            "confidence_tier": confidence_tier,
            "warning": warning_msg,
            "duration_and_persistence": {
                "burn_duration_s": pred_duration_s,
                "duration_statement": duration_statement,
                "persistence_stage": stage_pred,
                "stage_probabilities": stage_probs,
            },
            "droplet_kinetics": {
                "burning_rate_K_mm2_s": k_coupled,
                "extinction_diameter_mm": round(dext_ml, 3),
                "d2_law_lifetime_s": round(d2_lifetime_s, 2),
            },
            "regime_and_optics": {
                "fire_regime": fire_regime,
                "regime_probabilities": regime_probs,
                "flame_colour": flame_colour,
                "colour_probabilities": colour_probs,
            },
            "gas_signatures": {
                "delta_O2_pct": delta_o2_pct,
                "delta_CO2_pct": delta_co2_pct,
                "delta_CO_ppm": delta_co_ppm,
            },
            "life_damage_crew": life_damage,
            "infrastructure_damage_vehicle": infra_damage,
        }


# ==============================================================================
# Validation Against PSI-117 Curves & End-to-End Pipeline Execution
# ==============================================================================


def validate_against_psi117(
    predictor_artifacts: dict[str, Any], psi117: dict[str, pd.DataFrame]
) -> dict[str, Any]:
    """Cross-check trained FLEX droplet models against independent PSI-117 digitized curves."""
    temp_pred = OrbIgnitePredictor(predictor_artifacts, psi117)

    # 1. Check Cool-Flame Burning Rate Kavg (Dodecane across 0.5-5.0 atm)
    k_errs = []
    for _, r in psi117["kavg_cool"].iterrows():
        out = temp_pred.predict(
            fuel="Dodecane",
            gravity_g=0.0,
            o2_pct=21.0,
            pressure_atm=float(r["pressure_atm"]),
            char_scale_mm=4.0,
        )
        k_errs.append(abs(out["droplet_kinetics"]["burning_rate_K_mm2_s"] - float(r["K_mm2_s"])))

    # 2. Check Hot Extinction Diameter across C7, C10, C12 at 1 atm
    d_errs = []
    for _, r in psi117["alkane_dext_1atm"].iterrows():
        out = temp_pred.predict(
            fuel=str(r["fuel_base"]),
            gravity_g=0.0,
            o2_pct=21.0,
            pressure_atm=1.0,
            char_scale_mm=float(r["char_scale_mm"]),
        )
        d_errs.append(abs(out["droplet_kinetics"]["extinction_diameter_mm"] - float(r["d_ext_hot_mm"])))

    return {
        "psi117_cool_K_samples": int(len(k_errs)),
        "psi117_cool_K_mae_mm2_s": round(float(np.mean(k_errs)), 4),
        "psi117_alkane_hot_dext_samples": int(len(d_errs)),
        "psi117_alkane_hot_dext_mae_mm": round(float(np.mean(d_errs)), 4),
    }


def _strip_models_for_json(bundle_dict: dict[str, Any]) -> dict[str, Any]:
    """Remove non-JSON-serializable estimator objects from a task report."""
    excluded = {"preprocessor", "model", "label_encoder"}
    return {k: v for k, v in bundle_dict.items() if k not in excluded}


def write_markdown_report(report: dict[str, Any], out_path: str) -> None:
    """Write a concise human-readable training & validation summary markdown file."""
    lines = [
        "# Orb.Ignite — Standalone Microgravity Combustion Model Report",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        "",
        "## 1. Dataset Audit Summary",
        f"- **PSI-69 FLEX:** `{report['data_audit']['flex']['clean_rows']}` clean rows (dropped `{report['data_audit']['flex']['dropped_zero_pressure_rows']}` zero-pressure error).",
        f"- **PSI-159 CFI-G:** `{report['data_audit']['cfig']['combined_rows']}` unified rows (`{report['data_audit']['cfig']['normal_rows']}` Normal + `{report['data_audit']['cfig']['inverse_valid_rows']}` Inverse; `{report['data_audit']['cfig']['cool_flame_rows']}` Cool Flame).",
        f"- **PSI-107 SPICE:** `{report['data_audit']['spice']['deduplicated_runs']}` unique burn runs (deduplicated from `{report['data_audit']['spice']['raw_rows']}` rows to eliminate leakage).",
        f"- **PSI-25 BASS-II:** `{report['data_audit']['bass2']['valid_O2_rows']}` valid O₂ runs (removed `{report['data_audit']['bass2']['dropped_o2_sensor_glitches']}` sensor O₂ spike anomalies).",
        "",
        "## 2. Held-Out Test Performance (XGBoost vs. Baselines)",
        "| Model Task | N | Metric | Naive Baseline | Linear Baseline | Random Forest | XGBoost (95% CI) | CV5 Mean ± Std |",
        "| :--- | ---: | :--- | ---: | ---: | ---: | :--- | :--- |",
    ]

    for key, info in report["models"].items():
        cmp_data = info["benchmark_comparison"]
        if "mae" in info["final_test_metrics"]:
            metric_name = "RMSE / R²"
            def _fmt(m: dict[str, Any]) -> str:
                return f"{m['rmse']:.3f} / {m['r2']:.3f}"
            naive_s = _fmt(cmp_data["Naive_Baseline"]["test"])
            lin_s = _fmt(cmp_data["Linear_Baseline"]["test"])
            rf_s = _fmt(cmp_data["RandomForest"]["test"])
            ft = info["final_test_metrics"]
            xgb_s = f"{ft['rmse']:.3f} / {ft['r2']:.3f} (CI R² {ft['r2_ci95']})"
            cv_s = f"{info['cv5_trainval_r2_mean']:.3f} ± {info['cv5_trainval_r2_std']:.3f}"
        else:
            metric_name = "Macro-F1 / Bal-Acc"
            def _fmt_c(m: dict[str, Any]) -> str:
                return f"{m['macro_f1']:.3f} / {m['balanced_accuracy']:.3f}"
            naive_s = _fmt_c(cmp_data["Naive_Baseline"]["test"])
            lin_s = _fmt_c(cmp_data["Linear_Baseline"]["test"])
            rf_s = _fmt_c(cmp_data["RandomForest"]["test"])
            ft = info["final_test_metrics"]
            xgb_s = f"{ft['macro_f1']:.3f} / {ft['balanced_accuracy']:.3f} (CI F1 {ft['macro_f1_ci95']})"
            cv_s = f"{info['cv5_trainval_macro_f1_mean']:.3f} ± {info['cv5_trainval_macro_f1_std']:.3f}"
        lines.append(
            f"| `{key}` | {info['n_total']} | {metric_name} | {naive_s} | {lin_s} | {rf_s} | {xgb_s} | {cv_s} |"
        )

    lines.extend(
        [
            "",
            "## 3. Independent PSI-117 Cool-Flame & Extinction Validation",
            f"- Cool Flame `Kavg_CF` MAE (0.5–5.0 atm Dodecane, n={report['psi117_validation']['psi117_cool_K_samples']}): **{report['psi117_validation']['psi117_cool_K_mae_mm2_s']} mm²/s**",
            f"- Hot Flame `d_ext` MAE (C7/C10/C12 at 1 atm, n={report['psi117_validation']['psi117_alkane_hot_dext_samples']}): **{report['psi117_validation']['psi117_alkane_hot_dext_mae_mm']} mm**",
            "",
            "## 4. Scenario Verification Outputs (No Subjective Labels)",
        ]
    )

    for sc_name, sc in report["scenario_benchmarks"].items():
        dur = sc["duration_and_persistence"]
        reg = sc["regime_and_optics"]
        life = sc["life_damage_crew"]
        inf = sc["infrastructure_damage_vehicle"]
        lines.extend(
            [
                f"### {sc_name}",
                f"- **Confidence:** `{sc['confidence_tier']}`" + (f" — {sc['warning']}" if sc["warning"] else ""),
                f"- **Duration & Regime:** {dur['duration_statement']} | Regime: `{reg['fire_regime']}` | Colour: `{reg['flame_colour']}`",
                f"- **Crew Life Metrics:** CO `{life['co_concentration_ppm']} ppm`, ΔO₂ `-{life['o2_consumed_pct_vol']}%` (rem `{life['ambient_o2_remaining_pct']}%`), CH₂O `{life['toxic_formaldehyde_ch2o_mg_m3']} mg/m³`, FED `{life['fractional_effective_dose_fed']}`",
                f"- **Vehicle Infrastructure Metrics:** Heat Flux `{inf['radiative_heat_flux_kw_m2']} kW/m²`, Peak Temp `{inf['peak_flame_temp_K']} K`, ΔP `{inf['cabin_pressure_rise_kPa']} kPa`, Char `{inf['char_length_cm']} cm` (`{inf['damaged_area_m2']} m²`)",
                "",
            ]
        )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    """Execute full standalone training, evaluation, and packaging workflow."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("=== Loading & Cleaning NASA PSI Datasets ===")
    flex_df, flex_audit = load_flex_dataset()
    cfig_df, cfig_audit = load_cfig_datasets()
    spice_df, spice_audit = load_spice_dataset()
    bass2_df, bass2_audit = load_bass2_dataset()
    psi117 = load_psi117_cool_flame_curves()
    print(f"FLEX: {flex_audit}")
    print(f"CFIG: {cfig_audit}")
    print(f"SPICE: {spice_audit}")
    print(f"BASS-II: {bass2_audit}")

    common_num = [
        "X_O2",
        "X_fuel_stream",
        "X_CO2",
        "X_He",
        "pressure_atm",
        "o2_partial_pressure_atm",
        "inert_diluent_sum",
        "char_scale_mm",
        "flow_cm_s",
        "fuel_flow_mg_s",
        "mw_g_mol",
        "boiling_point_K",
        "heat_of_combustion_MJ_kg",
        "stoich_o2_mass_ratio",
        "sooting_propensity",
        "cool_flame_capable",
    ]
    common_cat = ["experiment_family", "fuel_base", "fuel_phase"]

    # Model 1A & 1B: Persistence Stage & Continuous Burn Duration (seconds).
    m1_df = build_model1_duration_dataset(flex_df, cfig_df, spice_df)
    print(f"\n=== Training Model 1A (Persistence Stage, n={len(m1_df)}) ===")
    m1a = train_and_compare_classifiers(
        "Model 1A: Burn Persistence Stage", m1_df, common_num, common_cat, "persistence_stage"
    )
    print("Model 1A Test:", m1a["final_test_metrics"])

    print(f"\n=== Training Model 1B (Burn Duration s, n={len(m1_df)}) ===")
    m1b = train_and_compare_regressors(
        "Model 1B: Burn Duration (s)", m1_df, common_num, common_cat, "burn_duration_s", log_target=True
    )
    print("Model 1B Test:", m1b["final_test_metrics"])

    # Model 2A & 2B: Droplet Burning Rate Constant K & Extinction Diameter d_ext (FLEX).
    flex_num = [
        "pressure_atm",
        "X_O2",
        "X_N2",
        "X_CO2",
        "X_He",
        "o2_partial_pressure_atm",
        "inert_diluent_sum",
        "char_scale_mm",
        "mw_g_mol",
        "boiling_point_K",
        "heat_of_combustion_MJ_kg",
        "stoich_o2_mass_ratio",
        "sooting_propensity",
    ]
    flex_cat = ["fuel_base"]
    print("\n=== Training Model 2A (Droplet Burning Rate K mm2/s) ===")
    m2a = train_and_compare_regressors(
        "Model 2A: Droplet Burning Rate K (mm2/s)", flex_df, flex_num, flex_cat, "K_mm2_s", log_target=False, clip_min=0.05
    )
    print("Model 2A Test:", m2a["final_test_metrics"])

    print("\n=== Training Model 2B (Visible Extinction Diameter mm) ===")
    m2b = train_and_compare_regressors(
        "Model 2B: Extinction Diameter d_ext (mm)", flex_df, flex_num, flex_cat, "d_ext_mm", log_target=False, clip_min=0.0
    )
    print("Model 2B Test:", m2b["final_test_metrics"])

    # Model 3: Flame Regime & Termination Mode (with PSI-117 & CFI-G Cool Flames).
    m3_df = build_model3_regime_dataset(flex_df, cfig_df, psi117)
    print(f"\n=== Training Model 3 (Flame Regime & Cool Flame Classifier, n={len(m3_df)}) ===")
    m3 = train_and_compare_classifiers(
        "Model 3: Flame Regime & Termination Mode", m3_df, common_num, common_cat, "fire_regime"
    )
    print("Model 3 Test:", m3["final_test_metrics"])

    # Model 4: Optical Flame Color & Sooting Classifier (CFI-G Inverse).
    cfig_col_df = cfig_df[cfig_df["flame_colour"].notna()].copy().reset_index(drop=True)
    col_num = [
        "X_O2",
        "X_fuel_stream",
        "pressure_atm",
        "o2_partial_pressure_atm",
        "fuel_flow_mg_s",
        "Tad_K",
        "Zst",
        "mw_g_mol",
        "heat_of_combustion_MJ_kg",
        "stoich_o2_mass_ratio",
        "sooting_propensity",
    ]
    col_cat = ["fuel_base"]
    print(f"\n=== Training Model 4 (Flame Colour & Sooting, n={len(cfig_col_df)}) ===")
    m4 = train_and_compare_classifiers(
        "Model 4: Flame Optical Colour & Sooting", cfig_col_df, col_num, col_cat, "flame_colour"
    )
    print("Model 4 Test:", m4["final_test_metrics"])

    # Model 5: BASS-II Solid Burn Gas Deltas (delta O2 %, delta CO2 %, delta CO ppm).
    bass_num = [
        "thickness_mm",
        "width_mm",
        "is_one_sided",
        "flow_restrictor",
        "air_flow_init",
        "air_flow_mean",
        "air_flow_min",
        "fan_init",
        "init_O2_pct",
        "mw_g_mol",
        "heat_of_combustion_MJ_kg",
        "stoich_o2_mass_ratio",
        "sooting_propensity",
        "sample_cross_section_mm2",
    ]
    bass_cat = ["fuel_base", "geometry"]
    print("\n=== Training Model 5A/5B/5C (BASS-II Gas Signatures) ===")
    m5a = train_and_compare_regressors(
        "Model 5A: Solid Burn Delta O2 (%)", bass2_df, bass_num, bass_cat, "delta_O2_pct", log_target=True
    )
    m5b = train_and_compare_regressors(
        "Model 5B: Solid Burn Delta CO2 (%)", bass2_df, bass_num, bass_cat, "delta_CO2_pct", log_target=True
    )
    m5c = train_and_compare_regressors(
        "Model 5C: Solid Burn Delta CO (ppm)", bass2_df, bass_num, bass_cat, "delta_CO_ppm", log_target=True
    )
    print("Model 5A Test:", m5a["final_test_metrics"])
    print("Model 5B Test:", m5b["final_test_metrics"])
    print("Model 5C Test:", m5c["final_test_metrics"])

    artifacts = {
        "model1a_persistence": m1a,
        "model1b_burn_duration": m1b,
        "model2a_burning_rate_K": m2a,
        "model2b_extinction_diameter": m2b,
        "model3_fire_regime": m3,
        "model4_flame_colour": m4,
        "model5a_delta_O2_pct": m5a,
        "model5b_delta_CO2_pct": m5b,
        "model5c_delta_CO_ppm": m5c,
    }

    psi117_val = validate_against_psi117(artifacts, psi117)
    print("\n=== PSI-117 Independent Cool/Hot Curve Validation ===", psi117_val)

    predictor = OrbIgnitePredictor(artifacts, psi117)
    scenarios = {
        "Scenario A — ISS 0g Heptane Cool-Flame Droplet (d0=3.5mm, 21% O2)": predictor.predict(
            fuel="Heptane", gravity_g=0.0, o2_pct=21.0, pressure_atm=1.0, flow_cm_s=0.2, area_m2=1.0, char_scale_mm=3.5
        ),
        "Scenario B — ISS 0g Methanol Droplet Completion (d0=2.8mm, 25% O2)": predictor.predict(
            fuel="Methanol", gravity_g=0.0, o2_pct=25.0, pressure_atm=1.0, flow_cm_s=0.2, area_m2=1.0, char_scale_mm=2.8
        ),
        "Scenario C — ISS 0g PMMA Enclosure Burn (BASS-II/SoFIE)": predictor.predict(
            fuel="PMMA", gravity_g=0.0, o2_pct=22.0, pressure_atm=1.0, flow_cm_s=5.0, area_m2=0.8, char_scale_mm=2.0, solid_thickness_mm=0.3
        ),
        "Scenario D — Lunar Base Partial-G (0.16g, 0.6 atm, 34% O2)": predictor.predict(
            fuel="Heptane", gravity_g=0.16, o2_pct=34.0, pressure_atm=0.60, flow_cm_s=4.0, area_m2=1.2, char_scale_mm=3.0
        ),
        "Scenario E — Earth Buoyant Lab (1.0g, 1.0 atm, 21% O2)": predictor.predict(
            fuel="Heptane", gravity_g=1.0, o2_pct=20.9, pressure_atm=1.0, flow_cm_s=1.0, area_m2=1.5, char_scale_mm=3.0
        ),
    }

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_audit": {
            "flex": flex_audit,
            "cfig": cfig_audit,
            "spice": spice_audit,
            "bass2": bass2_audit,
        },
        "models": {k: _strip_models_for_json(v) for k, v in artifacts.items()},
        "psi117_validation": psi117_val,
        "scenario_benchmarks": scenarios,
    }

    bundle_path = os.path.join(MODELS_DIR, "orb_ignite_fire_models.joblib")
    json_path = os.path.join(MODELS_DIR, "training_evaluation_report.json")
    md_path = os.path.join(MODELS_DIR, "MODEL_TRAINING_REPORT.md")

    joblib.dump({"artifacts": artifacts, "psi117": psi117, "fuel_properties": FUEL_PROPERTIES}, bundle_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    write_markdown_report(report, md_path)

    print(f"\nSaved model bundle -> {bundle_path}")
    print(f"Saved metrics JSON -> {json_path}")
    print(f"Saved Markdown report -> {md_path}")


if __name__ == "__main__":
    main()
