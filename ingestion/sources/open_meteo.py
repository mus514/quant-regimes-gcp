import pandas as pd
import requests

CITIES = {
    "montreal": (45.50, -73.57),
    "toronto": (43.65, -79.38),
    "new_york": (40.71, -74.01),
    "chicago": (41.88, -87.63),
    "houston": (29.76, -95.37),
}
URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY = "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"


def fetch(start: str, end: str) -> pd.DataFrame:
    frames = []
    for city, (lat, lon) in CITIES.items():
        params = {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
                  "daily": DAILY, "timezone": "America/Toronto"}
        r = requests.get(URL, params=params, timeout=120)
        r.raise_for_status()
        d = r.json()["daily"]
        df = pd.DataFrame(d).rename(columns={"time": "obs_date"})
        long = df.melt(id_vars="obs_date", var_name="attribute", value_name="value")
        long["series_id"] = f"WEATHER_{city.upper()}"
        frames.append(long)
    return pd.concat(frames, ignore_index=True)