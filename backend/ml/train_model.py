"""
Trains the Random Forest risk classifier and saves it + a SHAP explainer
for use by the FastAPI risk-scoring endpoint.

Run (after generate_dataset.py): python ml/train_model.py
Outputs: ml/model.pkl, ml/explainer.pkl
"""
import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import shap

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "..", "data", "landslide_training_data.csv")
FEATURES = ["rainfall_mm", "soil_moisture_pct", "displacement_mm", "pore_pressure_kpa", "slope_angle_deg"]

df = pd.read_csv(DATA_PATH)
X = df[FEATURES]
y = df["risk_label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_leaf=5,
    class_weight="balanced",
    random_state=42,
)
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test)))

# SHAP explainer for per-prediction factor attribution (used in the citizen/officer UI)
explainer = shap.TreeExplainer(model)

joblib.dump(model, os.path.join(HERE, "model.pkl"))
joblib.dump(explainer, os.path.join(HERE, "explainer.pkl"))
joblib.dump(FEATURES, os.path.join(HERE, "features.pkl"))

print("Saved model.pkl, explainer.pkl, features.pkl")
