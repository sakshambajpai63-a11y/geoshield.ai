"""
Generates a synthetic-but-realistic landslide risk dataset.

There's no public real-time sensor feed for NER slopes, so for the hackathon
we simulate readings using threshold ranges consistent with published
guidance (GSI / NDMA / Sikkim SDMA rainfall-threshold studies referenced in
your PPT). Label a reading Danger/Warning/Watch/Safe using a weighted rule,
then add noise — this gives the RandomForest real signal to learn instead of
pure randomness, while still being clearly disclosed as simulated data.

Run: python ml/generate_dataset.py
Output: ml/data/landslide_training_data.csv (in ../data)
"""
import numpy as np
import pandas as pd
import os

np.random.seed(42)
N = 6000

rainfall_mm = np.random.gamma(shape=2.0, scale=25, size=N)          # 0–250mm/24h, right-skewed
soil_moisture_pct = np.clip(np.random.normal(45, 18, N), 5, 100)
displacement_mm = np.random.exponential(scale=3.0, size=N)          # cumulative slope displacement
pore_pressure_kpa = np.clip(np.random.normal(30, 15, N), 0, 100)
slope_angle_deg = np.clip(np.random.normal(32, 10, N), 5, 75)

# Weighted risk score reflecting known trigger factors (rainfall + pore pressure
# dominate per Sikkim SDMA / Harilal et al. rainfall-threshold literature).
score = (
    0.35 * (rainfall_mm / 250)
    + 0.20 * (soil_moisture_pct / 100)
    + 0.20 * (displacement_mm / 20)
    + 0.15 * (pore_pressure_kpa / 100)
    + 0.10 * (slope_angle_deg / 75)
)
score += np.random.normal(0, 0.04, N)  # sensor/measurement noise
score = np.clip(score, 0, 1)

# Bin by quantile (not fixed cutoffs) so class proportions stay realistic
# (Danger rarest, Safe most common) regardless of the raw score's range.
labels = pd.qcut(
    score,
    q=[0, 0.55, 0.85, 0.95, 1.0],
    labels=["Safe", "Watch", "Warning", "Danger"],
)

df = pd.DataFrame({
    "rainfall_mm": rainfall_mm.round(1),
    "soil_moisture_pct": soil_moisture_pct.round(1),
    "displacement_mm": displacement_mm.round(2),
    "pore_pressure_kpa": pore_pressure_kpa.round(1),
    "slope_angle_deg": slope_angle_deg.round(1),
    "risk_label": labels,
})

out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "landslide_training_data.csv")
df.to_csv(out_path, index=False)

print(f"Wrote {len(df)} rows to {out_path}")
print(df["risk_label"].value_counts())
