"""POST /api/predict — sales volume prediction."""

from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np
import joblib
import os

router = APIRouter()

# Lazy-load models on first request
_rf_model = None
_label_encoder = None


def get_models():
    global _rf_model, _label_encoder
    if _rf_model is None:
        model_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        _rf_model = joblib.load(os.path.join(model_dir, "rf_model.pkl"))
        _label_encoder = joblib.load(os.path.join(model_dir, "label_encoder.pkl"))
    return _rf_model, _label_encoder


class PredictRequest(BaseModel):
    price: float
    rating: float
    review_count: int
    is_promoted: int
    category: str


class PredictResponse(BaseModel):
    predicted_sales: int
    range_low: int
    range_high: int
    confidence: str


@router.post("/predict", response_model=PredictResponse)
def predict_sales(req: PredictRequest):
    rf_model, label_encoder = get_models()

    # Encode category
    try:
        cat_enc = label_encoder.transform([req.category])[0]
    except ValueError:
        cat_enc = 0  # Unknown category → default to first

    X = np.array([[
        req.price,
        req.rating,
        req.review_count,
        req.is_promoted,
        int(cat_enc),
    ]])

    pred = rf_model.predict(X)[0]

    # Confidence label based on model R²
    r2 = 0.71
    if r2 >= 0.80:
        confidence = "high"
    elif r2 >= 0.60:
        confidence = "moderate"
    else:
        confidence = "low"

    return PredictResponse(
        predicted_sales=max(0, round(pred)),
        range_low=max(0, round(pred * 0.8)),
        range_high=max(0, round(pred * 1.2)),
        confidence=confidence,
    )
