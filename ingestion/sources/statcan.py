import pandas as pd
import requests

# vecteurs StatCan : à valider sur https://www150.statcan.gc.ca avant mise en production
VECTORS = {
    "v41690973": "cpi_canada_all_items",
    "v2062815": "unemployment_rate_canada",
    "v65201210": "gdp_monthly_canada",
}
URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"


def fetch(latest_n: int = 600) -> pd.DataFrame:
    payload = [{"vectorId": int(v[1:]), "latestN": latest_n} for v in VECTORS]
    r = requests.post(URL, json=payload, timeout=120)
    r.raise_for_status()
    rows = []
    for item in r.json():
        if item.get("status") != "SUCCESS":
            continue
        vid = f"v{item['object']['vectorId']}"
        for dp in item["object"]["vectorDataPoint"]:
            rows.append({
                "series_id": vid,
                "obs_date": dp["refPer"],
                "value": dp["value"],
                "attribute": "level",
            })
    df = pd.DataFrame(rows)
    # refPer est le 1er du mois : on ramène à la fin de mois pour la convention du projet
    df["obs_date"] = pd.to_datetime(df["obs_date"]) + pd.offsets.MonthEnd(0)
    return df