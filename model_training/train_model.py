# Standalone Model Training Pipeline for Orb.Ignite Microgravity Combustion
# Trained independently from primary Streamlit UI runtime
import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "DATASETS")
EXPERIMENTS_FILE = os.path.join(BASE_DIR, "Data", "experiments.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def load_harmonized_dataset():
    records = []
    if os.path.exists(EXPERIMENTS_FILE):
        with open(EXPERIMENTS_FILE, "r", encoding="utf-8") as f:
            raw_exps = json.load(f)
            for r in raw_exps:
                records.append({
                    "mission": r.get("mission", "Unknown"),
                    "fuel_category": r.get("fuel_category", "Gas"),
                    "fuel_name": r.get("fuel_name", "Methane"),
                    "gravity_g": float(r.get("gravity_g", 0.0)),
                    "oxygen_pct": float(r.get("oxygen_pct", 21.0)),
                    "pressure_atm": float(r.get("pressure_atm", 1.0)),
                    "burn_duration_s": float(r.get("burn_duration_s", 0.0)),
                    "cool_flame_observed": 1 if r.get("cool_flame_observed") else 0,
                    "safety_risk_level": r.get("safety_risk_level", "LOW"),
                })

    df = pd.DataFrame(records)
    return df


def train_models():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = load_harmonized_dataset()
    print(f"Loaded {len(df)} flight and ground experimental records for training.")

    le_mission = LabelEncoder()
    le_fuel_cat = LabelEncoder()
    le_risk = LabelEncoder()

    df["mission_enc"] = le_mission.fit_transform(df["mission"])
    df["fuel_cat_enc"] = le_fuel_cat.fit_transform(df["fuel_category"])
    df["risk_enc"] = le_risk.fit_transform(df["safety_risk_level"])

    feature_cols = ["gravity_g", "oxygen_pct", "pressure_atm", "mission_enc", "fuel_cat_enc"]
    X = df[feature_cols]

    y_burn = df["burn_duration_s"]
    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(X, y_burn, test_size=0.25, random_state=42)

    regressor = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        random_state=42,
    )
    regressor.fit(X_train_b, y_train_b)
    pred_b = regressor.predict(X_test_b)
    rmse_b = np.sqrt(mean_squared_error(y_test_b, pred_b))
    r2_b = r2_score(y_test_b, pred_b) if len(y_test_b) > 1 else 1.0
    print(f"Burn Duration Regressor -> RMSE: {rmse_b:.3f} s, R2: {r2_b:.3f}")

    y_cool = df["cool_flame_observed"]
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cool, test_size=0.25, random_state=42)

    clf_cool = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
    )
    clf_cool.fit(X_train_c, y_train_c)
    pred_c = clf_cool.predict(X_test_c)
    acc_c = accuracy_score(y_test_c, pred_c)
    print(f"Cool Flame Classifier -> Accuracy: {acc_c * 100:.2f}%")

    y_risk = df["risk_enc"]
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_risk, test_size=0.25, random_state=42)

    clf_risk = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
    )
    clf_risk.fit(X_train_r, y_train_r)
    pred_r = clf_risk.predict(X_test_r)
    acc_r = accuracy_score(y_test_r, pred_r)
    print(f"Risk Tier Classifier -> Accuracy: {acc_r * 100:.2f}%")

    regressor.save_model(os.path.join(OUTPUT_DIR, "burn_duration_xgb.json"))
    clf_cool.save_model(os.path.join(OUTPUT_DIR, "cool_flame_xgb.json"))
    clf_risk.save_model(os.path.join(OUTPUT_DIR, "safety_risk_xgb.json"))

    meta = {
        "features": feature_cols,
        "mission_classes": le_mission.classes_.tolist(),
        "fuel_cat_classes": le_fuel_cat.classes_.tolist(),
        "risk_classes": le_risk.classes_.tolist(),
        "metrics": {
            "burn_duration_rmse": float(rmse_b),
            "burn_duration_r2": float(r2_b),
            "cool_flame_accuracy": float(acc_c),
            "safety_risk_accuracy": float(acc_r),
        },
    }
    with open(os.path.join(OUTPUT_DIR, "model_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("Model training successfully completed. Artifacts saved to model_training/artifacts.")


if __name__ == "__main__":
    train_models()
