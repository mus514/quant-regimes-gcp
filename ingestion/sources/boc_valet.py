import pandas as pd
import requests

SERIES = [
    "V39079",                 # taux cible
    "BD.CDN.2YR.DQ.YLD", "BD.CDN.5YR.DQ.YLD", "BD.CDN.10YR.DQ.YLD", "BD.CDN.LONG.DQ.YLD",
    "FXUSDCAD", "FXEURCAD",
]
URL = "https://www.bankofcanada.ca/valet/observations/{series}/json"


def fetch(start: str, end: str) -> pd.DataFrame:
    url = URL.format(series=",".join(SERIES))
    r = requests.get(url, params={"start_date": start, "end_date": end}, timeout=60)
    r.raise_for_status()
    rows = []
    for obs in r.json()["observations"]:
        d = obs["d"]
        for sid in SERIES:
            v = obs.get(sid, {}).get("v")
            if v not in (None, ""):
                rows.append({"series_id": sid, "obs_date": d, "value": float(v), "attribute": "level"})
    return pd.DataFrame(rows)