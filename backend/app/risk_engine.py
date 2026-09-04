"""
Loads the trained RandomForest + SHAP explainer and exposes a single
predict_risk() function used by the ingestion endpoint.
"""
import os
import joblib
import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
ML_DIR = os.path.join(HERE, "..", "ml")

_model = None
_explainer = None
_features = None


def _load():
    global _model, _explainer, _features
    if _model is None:
        _model = joblib.load(os.path.join(ML_DIR, "model.pkl"))
        _explainer = joblib.load(os.path.join(ML_DIR, "explainer.pkl"))
        _features = joblib.load(os.path.join(ML_DIR, "features.pkl"))
    return _model, _explainer, _features


def predict_risk(rainfall_mm, soil_moisture_pct, displacement_mm, pore_pressure_kpa, slope_angle_deg):
    """
    Returns: (risk_label: str, probability: float, top_factors: list[dict])
    top_factors = the features pushing this specific prediction toward its
    predicted class, ranked by |SHAP value|, for the explainability panel.
    """
    model, explainer, features = _load()

    row = pd.DataFrame([{
        "rainfall_mm": rainfall_mm,
        "soil_moisture_pct": soil_moisture_pct,
        "displacement_mm": displacement_mm,
        "pore_pressure_kpa": pore_pressure_kpa,
        "slope_angle_deg": slope_angle_deg,
    }])[features]

    pred_label = model.predict(row)[0]
    proba = model.predict_proba(row)[0]
    classes = list(model.classes_)
    probability = float(proba[classes.index(pred_label)])

    shap_values = explainer.shap_values(row)
    class_idx = classes.index(pred_label)

    # shap_values shape differs across shap versions (list-per-class vs 3D array) — handle both
    if isinstance(shap_values, list):
        contribs = shap_values[class_idx][0]
    else:
        contribs = shap_values[0, :, class_idx]

    factor_impacts = sorted(
        zip(features, contribs),
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    top_factors = [
        {"factor": f, "impact": round(float(v), 4)} for f, v in factor_impacts[:3]
    ]

    return pred_label, probability, top_factors
