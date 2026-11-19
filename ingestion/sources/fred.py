import pandas as pd
import requests

SERIES = [
    # taux et courbe
    "DTB3", "DGS2", "DGS10", "DGS30", "T10Y2Y", "DFF", "T10YIE", "DTWEXBGS",
    # volatilité et crédit
    "VIXCLS", "BAMLH0A0HYM2", "BAMLC0A0CM", "STLFSI4",
    # macro mensuel
    "CPIAUCSL", "UNRATE", "INDPRO", "CFNAI", "UMCSENT",
]
URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch(api_key: str, start: str, end: str) -> pd.DataFrame:
    frames = []
    for sid in SERIES:
        params = {
            "series_id": sid, "api_key": api_key, "file_type": "json",
            "observation_start": start, "observation_end": end,
        }
        r = requests.get(URL, params=params, timeout=60)
        r.raise_for_status()
        obs = pd.DataFrame(r.json()["observations"])
        if obs.empty:
            continue
        obs = obs[obs["value"] != "."]
        frames.append(pd.DataFrame({
            "series_id": sid,
            "obs_date": obs["date"],
            "value": obs["value"].astype(float),
            "attribute": "level",
        }))
    return pd.concat(frames, ignore_index=True)