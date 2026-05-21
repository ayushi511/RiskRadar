import requests

def get_gdacs_events():
    url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=FL,TC,EQ,VO,WF"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        alerts = []
        for event in data.get("features", []):
            props = event["properties"]
            coords = event["geometry"]["coordinates"]
            alerts.append({
                "id": str(props.get("eventid")),
                "type": map_type(props.get("eventtype")),
                "title": props.get("name", "Unknown Event"),
                "magnitude": None,
                "severity": props.get("alertlevel", "low").lower(),
                "lat": coords[1],
                "lng": coords[0],
                "time": None,
                "url": props.get("url", {}).get("report", "")
            })
        return alerts
    except Exception as e:
        print(f"GDACS fetch error: {e}")
        return []

def map_type(t):
    mapping = {
        "EQ": "earthquake",
        "FL": "flood",
        "TC": "cyclone",
        "VO": "volcano",
        "WF": "wildfire"
    }
    return mapping.get(t, "other")