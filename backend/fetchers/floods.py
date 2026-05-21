import requests

def get_floods():
    floods = []

    # Source 1: GloFAS (Global Flood Awareness System) - no key needed
    try:
        url = "https://ffgs.dhigroup.com/api/v2/events?type=flood&limit=50"
        # Fallback: use ReliefWeb API which is free and reliable
        url = "https://api.reliefweb.int/v1/disasters?appname=disastermap&filter[field]=type.name&filter[value]=Flood&limit=20&fields[include][]=name&fields[include][]=date&fields[include][]=country&fields[include][]=status"
        res = requests.get(url, timeout=10)
        data = res.json()

        for item in data.get("data", []):
            fields = item.get("fields", {})
            country = fields.get("country", [{}])
            location = country[0] if country else {}

            # ReliefWeb gives country-level, not coordinates
            # We use approximate country centroids
            lat, lng = get_country_coords(location.get("name", ""))

            if lat is None:
                continue

            floods.append({
                "id": str(item.get("id")),
                "type": "flood",
                "title": fields.get("name", "Flood Event"),
                "magnitude": None,
                "severity": get_flood_severity(fields.get("status", "")),
                "lat": lat,
                "lng": lng,
                "time": fields.get("date", {}).get("created"),
                "url": f"https://reliefweb.int/disaster/{item.get('id')}"
            })
    except Exception as e:
        print(f"ReliefWeb flood fetch error: {e}")

    # Source 2: GDACS floods specifically (more precise coords)
    try:
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=FL"
        res = requests.get(url, timeout=10)
        data = res.json()

        for event in data.get("features", []):
            props = event["properties"]
            coords = event["geometry"]["coordinates"]
            floods.append({
                "id": f"gdacs-fl-{props.get('eventid')}",
                "type": "flood",
                "title": props.get("name", "Flood Alert"),
                "magnitude": None,
                "severity": props.get("alertlevel", "low").lower(),
                "lat": coords[1],
                "lng": coords[0],
                "time": None,
                "url": props.get("url", {}).get("report", "")
            })
    except Exception as e:
        print(f"GDACS flood fetch error: {e}")

    print(f"Fetched {len(floods)} flood alerts")
    return floods


def get_flood_severity(status):
    if status == "alert":
        return "critical"
    if status == "ongoing":
        return "high"
    return "medium"


# Approximate centroids for common countries
# (used when API only gives country name, not coordinates)
COUNTRY_COORDS = {
    "Bangladesh": (23.6850, 90.3563),
    "India": (20.5937, 78.9629),
    "Pakistan": (30.3753, 69.3451),
    "Nigeria": (9.0820, 8.6753),
    "China": (35.8617, 104.1954),
    "Indonesia": (-0.7893, 113.9213),
    "Philippines": (12.8797, 121.7740),
    "Brazil": (-14.2350, -51.9253),
    "Ethiopia": (9.1450, 40.4897),
    "Somalia": (5.1521, 46.1996),
    "Sudan": (12.8628, 30.2176),
    "Mozambique": (-18.6657, 35.5296),
    "Myanmar": (21.9162, 95.9560),
    "Afghanistan": (33.9391, 67.7100),
    "Kenya": (-0.0236, 37.9062),
    "South Sudan": (6.8770, 31.3070),
    "Democratic Republic of the Congo": (-4.0383, 21.7587),
    "Nepal": (28.3949, 84.1240),
    "Vietnam": (14.0583, 108.2772),
    "Thailand": (15.8700, 100.9925),
}

def get_country_coords(country_name):
    coords = COUNTRY_COORDS.get(country_name)
    if coords:
        return coords[0], coords[1]
    return None, None