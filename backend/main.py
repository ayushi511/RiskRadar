from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from ml.risk_engine import compute_risk_zones
from ml.trainer import train_model
from ml.predictor import predict_risk_zones, get_model_stats

app = FastAPI(
    title="Disaster Monitoring & Risk Prediction API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

cache = {
    "alerts": [],
    "last_updated": None
}


def refresh_data():
    print("=" * 50)
    print("Refreshing disaster data...")
    print("=" * 50)

    from fetchers.earthquakes import get_earthquakes
    from fetchers.fires import get_gdacs_events
    from fetchers.floods import get_floods

    earthquakes = get_earthquakes()
    gdacs       = get_gdacs_events()
    floods      = get_floods()

    cache["alerts"]       = earthquakes + gdacs + floods
    cache["last_updated"] = datetime.utcnow().isoformat()

    print(f"Loaded {len(cache['alerts'])} total alerts")


refresh_data()

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, trigger="interval", minutes=5)
scheduler.start()


# ── Basic ──────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {
        "message": "Disaster Monitoring API Running",
        "status": "active",
        "last_updated": cache["last_updated"]
    }


# ── Live alerts ────────────────────────────────────────────────────────────────

@app.get("/api/alerts")
def get_alerts():
    return {
        "alerts": cache["alerts"],
        "count": len(cache["alerts"]),
        "last_updated": cache["last_updated"]
    }


# ── Risk zones ─────────────────────────────────────────────────────────────────
#
# FIX: was calling compute_risk_zones() (heuristic grid scorer).
# The frontend map.html toggleRiskZones() fetches /api/risk-zones, so the ML
# model was never reached despite the button being labelled "AI Risk Zones".
# Now serves ML predictions. The heuristic is kept at /api/risk-zones/heuristic
# in case you want to compare the two.

@app.get("/api/risk-zones")
def get_risk_zones():
    zones = predict_risk_zones()
    stats = get_model_stats()
    return {
        "zones": zones,
        "total": len(zones),
        "model": stats,
        "last_updated": cache["last_updated"]
    }


@app.get("/api/risk-zones/heuristic")
def get_heuristic_risk_zones():
    zones = compute_risk_zones(cache["alerts"])
    return {
        "zones": zones,
        "total": len(zones),
        "last_updated": cache["last_updated"]
    }


# ── Stats ──────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    alerts = cache["alerts"]
    return {
        "total_alerts": len(alerts),
        "earthquakes":  sum(1 for a in alerts if a["type"] == "earthquake"),
        "floods":       sum(1 for a in alerts if a["type"] == "flood"),
        "wildfires":    sum(1 for a in alerts if a["type"] == "wildfire"),
        "cyclones":     sum(1 for a in alerts if a["type"] == "cyclone"),
        "critical_alerts": sum(1 for a in alerts if a.get("severity") == "critical")
    }


# ── ML ─────────────────────────────────────────────────────────────────────────

@app.get("/api/ml/train")
def trigger_training():
    try:
        print("=" * 50)
        print("Starting ML Model Training...")
        print("=" * 50)

        result = train_model()

        if result:
            return {
                "status": "success",
                "message": "Model trained successfully",
                "metrics": result
            }

        return {
            "status": "error",
            "message": "Training returned no result"
        }

    except Exception as e:
        import traceback
        detail = traceback.format_exc()
        print(detail)
        return {
            "status": "error",
            "message": str(e),
            "detail": detail
        }


@app.get("/api/ml/risk-zones")
def get_ml_risk_zones():
    try:
        zones = predict_risk_zones()
        stats = get_model_stats()
        return {
            "status": "success",
            "zones": zones,
            "total": len(zones),
            "model": stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/ml/stats")
def get_ml_stats():
    try:
        return {"status": "success", "model": get_model_stats()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "api": "running",
        "alerts_loaded": len(cache["alerts"]),
        "last_updated": cache["last_updated"]
    }