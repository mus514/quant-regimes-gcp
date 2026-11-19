import io
import logging
import os
from datetime import date, datetime, timezone, timedelta
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import storage

log = logging.getLogger(__name__)

BRONZE_COLUMNS = ["source", "series_id", "obs_date", "value", "attribute", "extracted_at"]

def to_bronze_frame(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Force le schéma long normalisé attendu par la couche bronze."""
    out = df.copy()
    out["source"] = source
    out["obs_date"] = pd.to_datetime(out["obs_date"]).dt.date
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out["extracted_at"] = datetime.now(timezone.utc)
    if "attribute" not in out.columns:
        out["attribute"] = "level"
    out = out.dropna(subset=["value"])
    return out[BRONZE_COLUMNS]


def write_parquet(df: pd.DataFrame, bucket: str, source: str, name: str) -> str:
    if df.empty:
        log.warning("No written line for %s/%s", source, name)
        return ""
    schema = pa.schema(
        [
            ('source', pa.string()),
            ('series_id', pa.string()),
            ('obs_date', pa.date32()),
            ('value', pa.float64()),
            ('attribute', pa.string()),
            ('extracted_at', pa.timestamp('us', tz='UTC'))
        ]
    )

    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="snappy")
    path = f"{source}/ingest_date={date.today().isoformat()}/{name}.parquet"

    if os.environ.get("DRY_RUN", "false").lower() == "true":
        local = Path("/tmp/bronze") / path
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(buf.getvalue())
        log.info("DRY_RUN : %s lignes écrites dans %s", len(df), local)

    return str(local)

    storage.Client().bucket(bucket).blob(path).upload_from_string(
        buf.getvalue(), content_type="application/octet-stream"
    )

    uri = f"gs://{bucket}/{path}"
    log.info("Écrit %s lignes dans %s", len(df), uri)
    
    return uri
