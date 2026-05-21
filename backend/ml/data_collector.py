import requests
import pandas as pd
from datetime import datetime, timedelta


def fetch_gdacs_historical(years_back: int = 2) -> pd.DataFrame:
    """
    Fetches real historical disaster data from GDACS.
    Goes back `years_back` years. Free, no API key needed.
    """
    all_events = []

    end_date   = datetime.now()
    start_date = end_date - timedelta(days=365 * years_back)

    # Fetch in 3-month chunks to avoid timeouts
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=90), end_date)

        url = (
            "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
            f"?eventlist=FL,TC,EQ,VO,WF"
            f"&fromDate={current.strftime('%Y-%m-%d')}"
            f"&toDate={chunk_end.strftime('%Y-%m-%d')}"
            f"&alertlevel=green,orange,red"
        )

        try:
            res  = requests.get(url, timeout=20)
            data = res.json()

            for event in data.get("features", []):
                props  = event["properties"]
                coords = event["geometry"]["coordinates"]
                alert  = props.get("alertlevel", "green").lower()

                # FIX: was using current.year / current.month (the chunk start
                # date), so every event in a 90-day window got the same
                # year and month. The time-based train/label split in
                # build_features() depends on accurate per-event dates —
                # with the old code every chunk had identical timestamps,
                # making the split meaningless.
                # Now we parse the event's own fromdate field instead.
                raw_date = props.get("fromdate", "")
                try:
                    evt_dt    = datetime.fromisoformat(
                        raw_date.replace("Z", "+00:00")
                    )
                    evt_year  = evt_dt.year
                    evt_month = evt_dt.month
                except (ValueError, AttributeError):
                    # Fall back to chunk midpoint if field is missing/malformed
                    midpoint  = current + (chunk_end - current) / 2
                    evt_year  = midpoint.year
                    evt_month = midpoint.month

                all_events.append({
                    "lat":      coords[1],
                    "lng":      coords[0],
                    "type":     map_type(props.get("eventtype")),
                    "severity": alert,
                    "year":     evt_year,
                    "month":    evt_month,
                    "fromdate": raw_date,
                })

            print(
                f"Fetched chunk {current.strftime('%Y-%m-%d')} → "
                f"{chunk_end.strftime('%Y-%m-%d')}: "
                f"{len(data.get('features', []))} events"
            )

        except Exception as e:
            print(f"Chunk fetch error: {e}")

        current = chunk_end

    df = pd.DataFrame(all_events)
    print(f"\nTotal historical events collected: {len(df)}")
    return df


def map_type(t: str) -> str:
    return {
        "EQ": "earthquake",
        "FL": "flood",
        "TC": "cyclone",
        "VO": "volcano",
        "WF": "wildfire",
    }.get(t, "other")


def severity_to_label(sev: str) -> int:
    return {
        "green":    0,
        "low":      0,
        "orange":   1,
        "medium":   1,
        "red":      2,
        "critical": 2,
    }.get(sev, 0)


def label_to_risk(label: int) -> dict:
    mapping = {
        0: ("low",      "#22c55e"),
        1: ("high",     "#f97316"),
        2: ("critical", "#ef4444"),
    }
    level, color = mapping.get(label, ("low", "#22c55e"))
    return {"risk_level": level, "color": color}