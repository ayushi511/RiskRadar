import requests

def get_earthquakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        alerts = []
        for feature in data["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            alerts.append({
                "id": feature["id"],
                "type": "earthquake",
                "title": props["title"],
                "magnitude": props["mag"],
                "severity": get_severity(props["mag"]),
                "lat": coords[1],
                "lng": coords[0],
                "time": props["time"],
                "url": props["url"]
            })
        return alerts
    except Exception as e:
        print(f"Earthquake fetch error: {e}")
        return []

def get_severity(mag):
    if mag is None:
        return "low"
    if mag >= 6:
        return "critical"
    if mag >= 4:
        return "high"
    if mag >= 2:
        return "medium"
    return "low"