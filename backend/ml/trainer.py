import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

from ml.data_collector import fetch_gdacs_historical, severity_to_label

MODEL_PATH = "ml/disaster_model.pkl"
DATA_PATH  = "ml/historical_data.csv"


def build_features(df: pd.DataFrame, recent_months: int = 6) -> pd.DataFrame:
    GRID = 4.0

    df = df.copy()
    df["month"] = pd.to_numeric(df["month"], errors="coerce").fillna(6).astype(int)
    df["year"]  = pd.to_numeric(df["year"],  errors="coerce").fillna(2023).astype(int)

    df["cell_lat"] = (df["lat"] / GRID).round() * GRID
    df["cell_lng"] = (df["lng"] / GRID).round() * GRID

    type_map = {
        "earthquake": 0, "flood": 1, "cyclone": 2,
        "wildfire": 3,   "volcano": 4, "other": 5,
    }
    df["type_code"] = df["type"].map(type_map).fillna(5)
    df["label"]     = df["severity"].apply(severity_to_label)

    max_year  = int(df["year"].max())
    max_month = int(df[df["year"] == max_year]["month"].max())

    cutoff_year  = max_year
    cutoff_month = max_month - recent_months
    while cutoff_month <= 0:
        cutoff_month += 12
        cutoff_year  -= 1

    def is_recent(row):
        if row["year"] > cutoff_year:
            return True
        if row["year"] == cutoff_year and row["month"] >= cutoff_month:
            return True
        return False

    df["is_recent"] = df.apply(is_recent, axis=1)

    past_df   = df[~df["is_recent"]]
    recent_df = df[ df["is_recent"]]

    print(
        f"Time split → past: {len(past_df)} events | "
        f"recent: {len(recent_df)} events "
        f"(cutoff {cutoff_year}-{cutoff_month:02d})"
    )

    past_stats = past_df.groupby(["cell_lat", "cell_lng"]).agg(
        total_events   = ("label",     "count"),
        avg_severity   = ("label",     "mean"),
        eq_count       = ("type_code", lambda x: (x == 0).sum()),
        flood_count    = ("type_code", lambda x: (x == 1).sum()),
        cyclone_count  = ("type_code", lambda x: (x == 2).sum()),
        wildfire_count = ("type_code", lambda x: (x == 3).sum()),
        volcano_count  = ("type_code", lambda x: (x == 4).sum()),
        avg_month      = ("month",     "mean"),
    ).reset_index()

    recent_labels = recent_df.groupby(["cell_lat", "cell_lng"]).agg(
        recent_max_sev = ("label", "max"),
        recent_count   = ("label", "count"),
    ).reset_index()

    merged = (
        past_stats
        .merge(recent_labels, on=["cell_lat", "cell_lng"], how="inner")
        .reset_index(drop=True)
    )

    # Use recent event COUNT to drive labels — GDACS skews heavily green so
    # severity alone produces only one class. Frequency is a better signal.
    def count_to_label(count):
        if count >=8: return 2   # critical
        if count >= 3:  return 1   # high
        return 0                   # low

    merged["risk_label"] = merged["recent_count"].apply(count_to_label)

    print(
        f"Past regions: {len(past_stats)} | "
        f"Recent regions: {len(recent_labels)} | "
        f"Merged (training rows): {len(merged)}"
    )
    print(f"Label distribution: {dict(merged['risk_label'].value_counts().sort_index())}")
    return merged


def train_model(recent_months: int = 6):

    print("=" * 50)
    print("FETCHING REAL HISTORICAL DATA...")
    print("=" * 50)

    df = fetch_gdacs_historical(years_back=6)

    if df.empty:
        print("No data fetched.")
        return None

    df.to_csv(DATA_PATH, index=False)
    print(f"Saved {len(df)} events to {DATA_PATH}")

    features_df = build_features(df, recent_months=recent_months)
    print(f"Built features for {len(features_df)} regions")

    FEATURE_COLS = [
        "cell_lat",
        "cell_lng",
        "total_events",
        "avg_severity",
        "eq_count",
        "flood_count",
        "cyclone_count",
        "wildfire_count",
        "volcano_count",
        "avg_month",
    ]

    X = features_df[FEATURE_COLS].values
    y = features_df["risk_label"].values

    unique_classes = np.unique(y)
    print(f"Unique risk classes in data: {unique_classes}")

    if len(unique_classes) < 2:
        print("Still only one class — forcing by percentile of total_events...")
        events = features_df["total_events"].values
        p66 = np.percentile(events, 66)
        p33 = np.percentile(events, 33)
        y = np.where(events >= p66, 2, np.where(events >= p33, 1, 0))
        print(f"Forced label distribution: {np.unique(y, return_counts=True)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y if len(np.unique(y)) > 1 else None,
    )

    print(f"\nTraining on {len(X_train)} regions")
    print(f"Testing  on {len(X_test)} regions")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)

    y_pred   = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("\n" + "=" * 50)
    print(f"MODEL ACCURACY: {accuracy * 100:.2f}%")
    print("=" * 50)

    present_classes = sorted(np.unique(y_test).tolist())
    all_names       = {0: "Low Risk", 1: "High Risk", 2: "Critical Risk"}
    present_names   = [all_names[c] for c in present_classes]

    report = classification_report(
        y_test, y_pred,
        labels=present_classes,
        target_names=present_names,
        output_dict=True,
        zero_division=0,
    )

    print(classification_report(
        y_test, y_pred,
        labels=present_classes,
        target_names=present_names,
        zero_division=0,
    ))

    print("\nRunning Cross Validation...")
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"CV scores: {cv_scores}")
    print(f"Average CV accuracy: {cv_scores.mean():.3f}")

    joblib.dump(
        {
            "model":        model,
            "feature_cols": FEATURE_COLS,
            "accuracy":     round(accuracy * 100, 2),
            "cv_accuracy":  round(cv_scores.mean() * 100, 2),
            "report":       report,
            "trained_on":   len(X_train),
            "tested_on":    len(X_test),
            "regions":      len(features_df),
        },
        MODEL_PATH,
    )
    print(f"\nModel saved to {MODEL_PATH}")

    return {
        "accuracy":    round(accuracy * 100, 2),
        "cv_accuracy": round(cv_scores.mean() * 100, 2),
        "report":      report,
        "trained_on":  len(X_train),
        "tested_on":   len(X_test),
        "regions":     len(features_df),
    }


def load_model() -> dict | None:
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None