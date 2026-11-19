import io
import zipfile

import pandas as pd
import requests

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FILES = {
    "ff5": "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
    "mom": "F-F_Momentum_Factor_daily_CSV.zip",
}


def _parse(csv_text: str, prefix: str) -> pd.DataFrame:
    lines = csv_text.splitlines()
    # première ligne dont le premier champ est une date AAAAMMJJ
    start = next(i for i, l in enumerate(lines) if l.split(",")[0].strip().isdigit()
                 and len(l.split(",")[0].strip()) == 8)
    header = [h.strip() for h in lines[start - 1].split(",")]
    header[0] = "obs_date"
    body = [l for l in lines[start:] if l.split(",")[0].strip().isdigit()]
    df = pd.read_csv(io.StringIO("\n".join(body)), names=header)
    df["obs_date"] = pd.to_datetime(df["obs_date"].astype(str), format="%Y%m%d")
    long = df.melt(id_vars="obs_date", var_name="series_id", value_name="value")
    long["series_id"] = prefix + "_" + long["series_id"].str.replace("-", "_").str.strip()
    long["value"] = long["value"] / 100.0  # en pourcentage dans la source
    long["attribute"] = "daily_return"
    return long


def fetch() -> pd.DataFrame:
    frames = []
    for key, fname in FILES.items():
        r = requests.get(BASE + fname, timeout=120)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            csv_name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            frames.append(_parse(z.read(csv_name).decode("latin-1"), key))
    return pd.concat(frames, ignore_index=True)