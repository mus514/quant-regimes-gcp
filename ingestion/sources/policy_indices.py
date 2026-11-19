import io

import pandas as pd
import requests

# URL à vérifier une fois, puis figer dans config/series_catalog.yaml
EPU_US_DAILY = "https://www.policyuncertainty.com/media/All_Daily_Policy_Data.csv"
EPU_CANADA = "https://www.policyuncertainty.com/media/Canada_Policy_Uncertainty_Data.xlsx"
GPR_DAILY = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"
GISTEMP = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"


def _get(url: str) -> bytes:
    r = requests.get(url, timeout=120, headers={"User-Agent": "quant-regimes/1.0"})
    r.raise_for_status()
    return r.content


def fetch_epu_us_daily() -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(_get(EPU_US_DAILY)))
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.dropna(subset=["year", "month", "day"])
    df["obs_date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=df["day"]))
    col = [c for c in df.columns if "policy" in c and "index" in c][0]
    return pd.DataFrame({"series_id": "EPU_US_DAILY", "obs_date": df["obs_date"],
                         "value": df[col], "attribute": "level"})


def fetch_epu_canada_monthly() -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(_get(EPU_CANADA)))
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.dropna(subset=["year", "month"])
    df["obs_date"] = pd.to_datetime(dict(year=df["year"].astype(int), month=df["month"].astype(int), day=1)) \
        + pd.offsets.MonthEnd(0)
    col = [c for c in df.columns if c not in ("year", "month", "obs_date")][0]
    return pd.DataFrame({"series_id": "EPU_CANADA", "obs_date": df["obs_date"],
                         "value": df[col], "attribute": "level"})


def fetch_gpr_daily() -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(_get(GPR_DAILY)))
    df.columns = [str(c).strip() for c in df.columns]
    date_col = [c for c in df.columns if c.lower() in ("date", "day")][0]
    keep = [c for c in ("GPRD", "GPRD_ACT", "GPRD_THREAT") if c in df.columns]
    long = df[[date_col] + keep].melt(id_vars=date_col, var_name="series_id", value_name="value")
    long = long.rename(columns={date_col: "obs_date"})
    long["attribute"] = "level"
    return long


def fetch_gistemp_monthly() -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(_get(GISTEMP)), skiprows=1)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    long = df[["Year"] + months].melt(id_vars="Year", var_name="m", value_name="value")
    long = long[pd.to_numeric(long["value"], errors="coerce").notna()]
    long["obs_date"] = pd.to_datetime(long["Year"].astype(str) + "-" + long["m"], format="%Y-%b") \
        + pd.offsets.MonthEnd(0)
    return pd.DataFrame({"series_id": "GISTEMP_GLOBAL_ANOMALY", "obs_date": long["obs_date"],
                         "value": long["value"].astype(float), "attribute": "level"})


def fetch() -> pd.DataFrame:
    frames = []
    for fn in (fetch_epu_us_daily, fetch_epu_canada_monthly, fetch_gpr_daily, fetch_gistemp_monthly):
        try:
            frames.append(fn())
        except Exception as exc:  # une source académique en panne ne doit pas bloquer les autres
            print(f"[policy_indices] {fn.__name__} ignorée : {exc}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()