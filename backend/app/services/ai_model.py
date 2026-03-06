from pathlib import Path
import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "ai_models" / "rf_ahp_model.pkl"

_model = None


def load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Không tìm thấy model tại: {MODEL_PATH}")
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_scores(laptops):
    model = load_model()

    features = []
    for l in laptops:
        features.append([
            float(l.norm_cpu),
            float(l.norm_ram),
            float(l.norm_gpu),
            float(l.norm_screen),
            float(l.norm_weight),
            float(l.norm_battery),
            float(l.norm_durability),
            float(l.norm_upgradeability),
            float(l.price),
        ])

    X = np.array(features)
    scores = model.predict(X)
    return scores