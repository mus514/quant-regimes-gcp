#!/usr/bin/env bash
set -euo pipeline

export PROJECT_ID="quant-regimes-dev"
export REGION="northamerica-northeast1"
export RAW_BUCKET="${PROJECT_ID}-lake-raw"
export ART_BUCKET="${PROJECT_ID}-artifacts"
export SA_INGEST="sa-ingestion"
export SA_DATAFORM="sa-dataform"

gcloud projects create "$PROJECT_ID" --name="Quant Regimes" || true
gcloud config set project "$PROJECT_ID"

gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com secretmanager.googleapis.com \
  bigquery.googleapis.com bigqueryconnection.googleapis.com dataform.googleapis.com \
  dataproc.googleapis.com storage.googleapis.com sheets.googleapis.com drive.googleapis.com

gcloud storage buckets create "gs://${RAW_BUCKET}" --location="$REGION" --uniform-bucket-level-access
gcloud storage buckets create "gs://${ART_BUCKET}" --location="$REGION" --uniform-bucket-level-access


for ds in bronze silver gold ops; do
  bq --location="$REGION" mk --dataset "${PROJECT_ID}:${ds}" || true
done

gcloud artifacts repositories create ingestion --repository-format=docker --location="$REGION" || true

gcloud iam service-accounts create "$SA_INGEST" --display-name="Ingestion Cloud Run Jobs" || true
gcloud iam service-accounts create "$SA_DATAFORM" --display-name="Dataform executions" || true

SA_INGEST_EMAIL="${SA_INGEST}@${PROJECT_ID}.iam.gserviceaccount.com"
SA_DATAFORM_EMAIL="${SA_DATAFORM}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud storage buckets add-iam-policy-binding "gs://${RAW_BUCKET}" --member="serviceAccount:${SA_INGEST_EMAIL}" --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${SA_INGEST_EMAIL}" --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${SA_DATAFORM_EMAIL}" --role="roles/bigquery.dataEditor"
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${SA_DATAFORM_EMAIL}" --role="roles/bigquery.jobUser"
gcloud storage buckets add-iam-policy-binding "gs://${RAW_BUCKET}" --member="serviceAccount:${SA_DATAFORM_EMAIL}" --role="roles/storage.objectViewer"

echo -n "Your_Key" | gcloud secrets create FRED_API_KEY --data-file=- || true
echo "Bootstrap done. Share the GSheet with ${SA_INGEST_EMAIL} (viewer)."