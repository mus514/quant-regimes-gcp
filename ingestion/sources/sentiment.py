import pandas as pd
import requests

FEAR_GREED = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cnn.com/markets/fear-and-greed",
    "Origin": "https://www.cnn.com",
}

EXPECTED_COLUMNS = ["series_id", "obs_date", "value", "attribute"]


def fetch_fear_greed(timeout: float | tuple[float, float] = (5.0, 20.0)) -> pd.DataFrame:
    with requests.Session() as session:
        resp = session.get(FEAR_GREED, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()

    hist = payload.get("fear_and_greed_historical", {}).get("data") or []
    if not hist:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    df = pd.DataFrame(hist)
    if not {"x", "y"}.issubset(df.columns):
        raise ValueError(f"Unexpected payload structure; columns={list(df.columns)}")

    out = pd.DataFrame({
        "series_id": "CNN_FEAR_GREED",
        "obs_date": pd.to_datetime(df["x"], unit="ms", utc=True).dt.date,
        "value": pd.to_numeric(df["y"], errors="coerce"),
        "attribute": "level",
    }).dropna(subset=["obs_date", "value"])

    return out[EXPECTED_COLUMNS].reset_index(drop=True)


def fetch() -> pd.DataFrame:
    try:
        return fetch_fear_greed()
    except Exception as exc:
        print(f"[sentiment] Fear & Greed ignoré : {exc}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)