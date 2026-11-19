import argparse
import logging
import os
import sys

import functions_framework
import pandas as pd
from flask import Request

from common.config import Settings, get_secret
from common.gcs import to_bronze_frame, write_parquet
from sources import boc_valet, fama_french, fred, gsheet, open_meteo, policy_indices, sentiment, statcan, yahoo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ingestion")

SOURCES = ["yahoo", "fred", "boc_valet", "statcan", "fama_french", "policy_indices",
           "open_meteo", "sentiment", "gsheet"]


def run(source: str, s: Settings) -> None:
    start, end = s.effective_start, s.end
    log.info("Source=%s fenêtre=%s→%s", source, start, end)

    if source == "yahoo":
        df = yahoo.fetch(start, end)
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "prices")

    elif source == "fred":
        df = fred.fetch(get_secret(s.project_id, "FRED_API_KEY"), start, end)
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "series")

    elif source == "boc_valet":
        df = boc_valet.fetch(start, end)
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "series")

    elif source == "statcan":
        df = statcan.fetch()
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "series")

    elif source == "fama_french":
        df = fama_french.fetch()  # fichiers complets, toujours full refresh
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "factors")

    elif source == "policy_indices":
        df = policy_indices.fetch()
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "indices")

    elif source == "open_meteo":
        df = open_meteo.fetch(start, end)
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "weather")

    elif source == "sentiment":
        df = sentiment.fetch()
        write_parquet(to_bronze_frame(df, source), s.raw_bucket, source, "sentiment")

    elif source == "gsheet":
        # Les onglets ne sont pas des séries temporelles : écriture Parquet brute par onglet
        import io
        from datetime import date
        from google.cloud import storage
        tabs = gsheet.fetch_tabs(s.sheet_id)
        for name, tab in tabs.items():
            if tab.empty:
                continue
            buf = io.BytesIO()
            tab.astype(str).to_parquet(buf, index=False)
            path = f"gsheet/{name}/ingest_date={date.today().isoformat()}/{name}.parquet"
            storage.Client().bucket(s.raw_bucket).blob(path).upload_from_string(buf.getvalue())
            log.info("Onglet %s : %s lignes → gs://%s/%s", name, len(tab), s.raw_bucket, path)

    else:
        raise ValueError(f"Source inconnue : {source}")


@functions_framework.http
def ingest(request: Request):
    # Point d'entrée HTTP de la Cloud Function.
    # Appels : POST <url>?source=fred                                   (Cloud Scheduler)
    #          POST <url>?source=yahoo&full_refresh=true&lookback_days=90
    #          corps JSON {"source": "fred"} accepté aussi.
    body = request.get_json(silent=True) or {}
    source = request.args.get("source") or body.get("source")
    if source not in SOURCES:
        return {"status": "error", "error": f"source inconnue : {source}", "sources": SOURCES}, 400

    # Surcharges par requête, lues par Settings() à l'instanciation
    for param, env in (("full_refresh", "FULL_REFRESH"), ("lookback_days", "LOOKBACK_DAYS")):
        value = request.args.get(param) or body.get(param)
        if value is not None:
            os.environ[env] = str(value)
        else:
            os.environ.pop(env, None)

    try:
        run(source, Settings())
        return {"status": "ok", "source": source}, 200
    except Exception as exc:
        log.exception("Échec de l'ingestion %s", source)
        return {"status": "error", "source": source, "error": str(exc)}, 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=SOURCES)
    args = parser.parse_args()
    try:
        run(args.source, Settings())
    except Exception:
        log.exception("Échec de l'ingestion %s", args.source)
        sys.exit(1)