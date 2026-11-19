import pandas as pd
import yfinance as yf

TICKERS = [
    "SPY", "XIU.TO", "EFA", "EEM", "TLT", "XBB.TO", "HYG", "GLD", "DBC", "VNQ",
    "^VIX", "^MOVE", "CL=F", "GC=F", "HG=F", "KRBN",
]

def fetch(start: str, end: str) -> pd.DataFrame:
    raw = yf.download(TICKERS, start=start, end=end, auto_adjust=False,
                      group_by="ticker", threads=True, progress=False)
    frames = []
    for t in TICKERS:
        if t not in raw.columns.get_level_values(0):
            continue
        sub = raw[t].dropna(how="all").reset_index().rename(columns={"Date": "obs_date"})
        long = sub.melt(id_vars="obs_date", var_name="attribute", value_name="value")
        long["attribute"] = long["attribute"].str.lower().str.replace(" ", "_")
        long["series_id"] = t
        frames.append(long)
    return pd.concat(frames, ignore_index=True)