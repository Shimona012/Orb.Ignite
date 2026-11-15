# Orb.Ignite — Standalone Microgravity Combustion Model Report

Generated: `2026-11-15T08:00:54.099298+00:00`

## 1. Dataset Audit Summary
- **PSI-69 FLEX:** `273` clean rows (dropped `1` zero-pressure error).
- **PSI-159 CFI-G:** `333` unified rows (`179` Normal + `154` Inverse; `9` Cool Flame).
- **PSI-107 SPICE:** `116` unique burn runs (deduplicated from `469` rows to eliminate leakage).
- **PSI-25 BASS-II:** `122` valid O₂ runs (removed `5` sensor O₂ spike anomalies).

## 2. Held-Out Test Performance (XGBoost vs. Baselines)
| Model Task | N | Metric | Naive Baseline | Linear Baseline | Random Forest | XGBoost (95% CI) | CV5 Mean ± Std |
| :--- | ---: | :--- | ---: | ---: | ---: | :--- | :--- |
| `model1a_persistence` | 716 | Macro-F1 / Bal-Acc | 0.307 / 0.333 | 0.618 / 0.792 | 0.706 / 0.758 | 0.799 / 0.753 (CI F1 [0.6126, 0.928]) | 0.636 ± 0.105 |
| `model1b_burn_duration` | 716 | RMSE / R² | 50.842 / -0.204 | 38.762 / 0.300 | 32.609 / 0.505 | 33.090 / 0.490 (CI R² [0.1521, 0.7093]) | 0.688 ± 0.038 |
| `model2a_burning_rate_K` | 257 | RMSE / R² | 0.130 / -0.001 | 0.074 / 0.677 | 0.072 / 0.693 | 0.075 / 0.668 (CI R² [0.4576, 0.7975]) | 0.646 ± 0.064 |
| `model2b_extinction_diameter` | 209 | RMSE / R² | 1.181 / -0.000 | 0.869 / 0.459 | 0.736 / 0.611 | 0.826 / 0.511 (CI R² [0.1209, 0.7694]) | 0.738 ± 0.050 |
| `model3_fire_regime` | 643 | Macro-F1 / Bal-Acc | 0.179 / 0.250 | 0.601 / 0.750 | 0.719 / 0.779 | 0.833 / 0.821 (CI F1 [0.7382, 0.9034]) | 0.794 ± 0.060 |
| `model4_flame_colour` | 120 | Macro-F1 / Bal-Acc | 0.167 / 0.250 | 0.554 / 0.542 | 0.689 / 0.688 | 0.629 / 0.604 (CI F1 [0.2926, 0.8607]) | 0.871 ± 0.132 |
| `model5a_delta_O2_pct` | 122 | RMSE / R² | 0.468 / -0.014 | 0.380 / 0.331 | 0.305 / 0.568 | 0.300 / 0.581 (CI R² [-0.0615, 0.9002]) | 0.622 ± 0.144 |
| `model5b_delta_CO2_pct` | 121 | RMSE / R² | 0.394 / -0.019 | 0.300 / 0.407 | 0.295 / 0.429 | 0.288 / 0.455 (CI R² [-0.1278, 0.7515]) | 0.661 ± 0.095 |
| `model5c_delta_CO_ppm` | 118 | RMSE / R² | 168.998 / -0.254 | 38354.620 / -64583.214 | 109.997 / 0.469 | 105.165 / 0.514 (CI R² [-0.1392, 0.9613]) | 0.496 ± 0.181 |

## 3. Independent PSI-117 Cool-Flame & Extinction Validation
- Cool Flame `Kavg_CF` MAE (0.5–5.0 atm Dodecane, n=19): **0.0378 mm²/s**
- Hot Flame `d_ext` MAE (C7/C10/C12 at 1 atm, n=15): **0.6654 mm**

## 4. Scenario Verification Outputs (No Subjective Labels)
### Scenario A — ISS 0g Heptane Cool-Flame Droplet (d0=3.5mm, 21% O2)
- **Confidence:** `Data-backed (High Confidence)`
- **Duration & Regime:** Predicted to burn for 18.6 s | Regime: `Cool_Flame` | Colour: `Blue-Limit/Dim (500–800 K CH₂O* Chemiluminescence)`
- **Crew Life Metrics:** CO `71.1 ppm`, ΔO₂ `-0.356%` (rem `20.64%`), CH₂O `4.95 mg/m³`, FED `0.0415`
- **Vehicle Infrastructure Metrics:** Heat Flux `2.27 kW/m²`, Peak Temp `580.0 K`, ΔP `3.11 kPa`, Char `10.2 cm` (`0.0105 m²`)

### Scenario B — ISS 0g Methanol Droplet Completion (d0=2.8mm, 25% O2)
- **Confidence:** `Data-backed (High Confidence)`
- **Duration & Regime:** Predicted to burn for 11.3 s | Regime: `Droplet_Disruption` | Colour: `Blue`
- **Crew Life Metrics:** CO `14.0 ppm`, ΔO₂ `-0.213%` (rem `24.79%`), CH₂O `0.35 mg/m³`, FED `0.0028`
- **Vehicle Infrastructure Metrics:** Heat Flux `17.54 kW/m²`, Peak Temp `1524.0 K`, ΔP `1.95 kPa`, Char `9.2 cm` (`0.0085 m²`)

### Scenario C — ISS 0g PMMA Enclosure Burn (BASS-II/SoFIE)
- **Confidence:** `Data-backed (High Confidence)`
- **Duration & Regime:** Predicted to burn for 15.5 s | Regime: `Radiative_Diffusive_Self_Extinction` | Colour: `Yellow`
- **Crew Life Metrics:** CO `12.5 ppm`, ΔO₂ `-0.069%` (rem `21.93%`), CH₂O `0.85 mg/m³`, FED `0.0068`
- **Vehicle Infrastructure Metrics:** Heat Flux `30.98 kW/m²`, Peak Temp `1446.0 K`, ΔP `1.81 kPa`, Char `11.4 cm` (`0.0131 m²`)

### Scenario D — Lunar Base Partial-G (0.16g, 0.6 atm, 34% O2)
- **Confidence:** `Theory-based (Moderate Confidence)` — Theory-backed regime (Trained XGBoost + Physics Active): Partial-gravity/scale coupling combines trained XGBoost estimators with Grashof/Rayleigh/d²-law equations.
- **Duration & Regime:** Predicted to burn for 10.2 s | Regime: `Hot_Sustained` | Colour: `Yellow-Blue`
- **Crew Life Metrics:** CO `11.6 ppm`, ΔO₂ `-0.104%` (rem `33.9%`), CH₂O `0.46 mg/m³`, FED `0.0037`
- **Vehicle Infrastructure Metrics:** Heat Flux `78.53 kW/m²`, Peak Temp `1777.2 K`, ΔP `2.13 kPa`, Char `11.7 cm` (`0.0136 m²`)

### Scenario E — Earth Buoyant Lab (1.0g, 1.0 atm, 21% O2)
- **Confidence:** `Theory-based (Moderate Confidence)` — Theory-backed regime (Trained XGBoost + Physics Active): Partial-gravity/scale coupling combines trained XGBoost estimators with Grashof/Rayleigh/d²-law equations.
- **Duration & Regime:** Predicted to burn for 11.4 s | Regime: `Hot_Sustained` | Colour: `Yellow`
- **Crew Life Metrics:** CO `12.6 ppm`, ΔO₂ `-0.122%` (rem `20.78%`), CH₂O `0.46 mg/m³`, FED `0.0042`
- **Vehicle Infrastructure Metrics:** Heat Flux `52.72 kW/m²`, Peak Temp `1537.4 K`, ΔP `1.71 kPa`, Char `8.7 cm` (`0.0076 m²`)
