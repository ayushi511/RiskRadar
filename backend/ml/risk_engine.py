import numpy as np
from collections import defaultdict

# Severity weights
SEV_WEIGHTS = {
    "critical": 4.0, "red": 4.0,
    "high": 3.0,     "orange": 3.0,
    "medium": 2.0,   "green": 2.0,
    "low": 1.0
}

# Type weights — some disasters are more dangerous than others
TYPE_WEIGHTS = {
    "earthquake": 1.4,
    "cyclone":    1.3,
    "flood":      1.2,
    "volcano":    1.1,
    "wildfire":   1.0,
    "other":      0.8
}

def compute_risk_zones(alerts: list, grid_size: float = 8.0) -> list:
    """
    Divides the world into a grid.
    Each cell gets a risk score based on alerts inside it.
    Returns a list of zones with lat/lng center and risk level.
    """
    grid = defaultdict(lambda: {"score": 0.0, "count": 0, "types": set()})

    for alert in alerts:
        lat = alert.get("lat")
        lng = alert.get("lng")
        if lat is None or lng is None:
            continue

        # Snap to grid cell
        cell_lat = round(lat / grid_size) * grid_size
        cell_lng = round(lng / grid_size) * grid_size
        key = (cell_lat, cell_lng)

        sev    = alert.get("severity", "low")
        atype  = alert.get("type", "other")

        sev_w  = SEV_WEIGHTS.get(sev, 1.0)
        type_w = TYPE_WEIGHTS.get(atype, 1.0)

        grid[key]["score"] += sev_w * type_w
        grid[key]["count"] += 1
        grid[key]["types"].add(atype)

    # Normalize scores to 0-100
    if not grid:
        return []

    max_score = max(cell["score"] for cell in grid.values()) or 1.0
    zones = []

    for (cell_lat, cell_lng), data in grid.items():
        normalized = (data["score"] / max_score) * 100

        if normalized >= 60:
            level = "critical"
            color = "#ef4444"
        elif normalized >= 35:
            level = "high"
            color = "#f97316"
        elif normalized >= 15:
            level = "medium"
            color = "#f59e0b"
        else:
            level = "low"
            color = "#22c55e"

        zones.append({
            "lat":        cell_lat,
            "lng":        cell_lng,
            "score":      round(normalized, 1),
            "risk_level": level,
            "color":      color,
            "count":      data["count"],
            "types":      list(data["types"]),
            "radius_km":  grid_size * 60  # approx km for the circle on map
        })

    # Only return zones with actual activity
    zones = [z for z in zones if z["count"] > 0]
    zones.sort(key=lambda z: z["score"], reverse=True)
    return zones