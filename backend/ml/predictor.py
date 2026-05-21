import os
import pandas as pd
import numpy as np

from ml.trainer import load_model, build_features, DATA_PATH
from ml.data_collector import label_to_risk


def predict_risk_zones() -> list:
    """
    Loads the trained model + historical CSV, predicts risk for every region,
    and returns zone dicts ready for the map frontend.
    """
    bundle = load_model()
    if not bundle:
        print("No trained model found — run GET /api/ml/train first")
        return []

    model        = bundle["model"]
    feature_cols = bundle["feature_cols"]
    accuracy     = bundle["accuracy"]

    if not os.path.exists(DATA_PATH):
        print(f"Historical data not found at {DATA_PATH}")
        return []

    df          = pd.read_csv(DATA_PATH)
    features_df = build_features(df)   # reset_index(drop=True) done inside

    X             = features_df[feature_cols].values
    predictions   = model.predict(X)
    probabilities = model.predict_proba(X)

    zones = []

    # FIX: was `for i, row in features_df.iterrows()` then `predictions[i]`.
    # iterrows() yields the DataFrame index as i. After groupby + merge the
    # index is reset to 0…N by build_features(), but using the DataFrame index
    # to address a numpy array is fragile — if the index ever drifts the wrong
    # prediction ends up on the wrong region with no error raised.
    # enumerate() binds the loop counter directly to the numpy arrays (always
    # 0-based), making the alignment explicit and safe.
    for idx, (_, row) in enumerate(features_df.iterrows()):
        pred       = int(predictions[idx])
        confidence = round(float(probabilities[idx].max()) * 100, 1)
        risk       = label_to_risk(pred)

        # Skip low-risk low-confidence zones to reduce map clutter
        if pred == 0 and confidence < 50:
            continue

        zones.append({
            "lat":            float(row["cell_lat"]),
            "lng":            float(row["cell_lng"]),
            "risk_level":     risk["risk_level"],
            "color":          risk["color"],
            "confidence":     confidence,
            "score":          confidence,          # alias so map popup works for both zone types
            "model_accuracy": accuracy,
            "total_events":   int(row["total_events"]),
            "count":          int(row["total_events"]),  # alias for popup count field
            "types":          _get_types(row),
            "radius_km":      550,
        })

    zones.sort(key=lambda z: z["confidence"], reverse=True)
    print(f"Generated {len(zones)} ML-predicted risk zones")
    return zones


def get_model_stats() -> dict:
    bundle = load_model()
    if not bundle:
        return {"trained": False}
    return {
        "trained":     True,
        "accuracy":    bundle["accuracy"],
        "cv_accuracy": bundle.get("cv_accuracy"),
        "trained_on":  bundle["trained_on"],
        "tested_on":   bundle["tested_on"],
        "regions":     bundle.get("regions", "?"),
        "report":      bundle["report"],
    }


def _get_types(row) -> list:
    types = []
    if row.get("eq_count",       0) > 0: types.append("earthquake")
    if row.get("flood_count",    0) > 0: types.append("flood")
    if row.get("cyclone_count",  0) > 0: types.append("cyclone")
    if row.get("wildfire_count", 0) > 0: types.append("wildfire")
    if row.get("volcano_count",  0) > 0: types.append("volcano")
    return types