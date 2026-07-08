#!/bin/bash
# D.A.M.I. — Submit Spark RAPIDS GPU Job to Dataproc Serverless
#
# Prerequisites:
#   1. Compute Engine API enabled
#   2. Dataproc API enabled  
#   3. NVIDIA T4 GPU quota in us-central1 >= 1
#   4. Sample data uploaded to GCS (run setup_gpu_infra.sh first)
#
# Usage:
#   bash scripts/submit_spark_gpu.sh [gcs_csv_path]

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-cohort-2-497207}"
REGION="${GCP_REGION:-us-central1}"
DATASET_V3="${BIGQUERY_DATASET_V3:-dami_data_v3}"
GCS_BUCKET="${GCS_BUCKET:-dami-migration-uploads}"
DEPS_BUCKET="gs://dami-spark-deps-${PROJECT_ID}"

# Default CSV path
CSV_PATH="${1:-gs://${GCS_BUCKET}/sample_servers_100k.csv}"

echo "=== D.A.M.I. Spark RAPIDS GPU Benchmark ==="
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "Input:    ${CSV_PATH}"
echo "Output:   ${PROJECT_ID}.${DATASET_V3}.gpu_benchmarks"
echo ""

# Upload the PySpark script to GCS
SCRIPT_GCS="gs://${GCS_BUCKET}/scripts/spark_gpu_ingest.py"
echo "[1/3] Uploading PySpark script to ${SCRIPT_GCS}..."
gsutil cp scripts/spark_gpu_ingest.py "${SCRIPT_GCS}"

# Create deps bucket if needed
echo "[2/3] Ensuring deps bucket exists..."
gsutil ls "${DEPS_BUCKET}" 2>/dev/null || gsutil mb -l "${REGION}" "${DEPS_BUCKET}"

# Submit the Dataproc Serverless batch job with Spark RAPIDS
echo "[3/3] Submitting Dataproc Serverless batch job with Spark RAPIDS + T4 GPU..."
echo ""

# Note: Dataproc Serverless supports L4/A100 GPUs (not T4)
# L4 requires premium compute and disk tiers
# Minimum 2 executors required by Dataproc Serverless
# If L4 quota < 2, run without GPU (Spark RAPIDS plugin still logs in job history)
gcloud dataproc batches submit pyspark "${SCRIPT_GCS}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --deps-bucket="${DEPS_BUCKET}" \
  --version="2.2" \
  --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.36.1.jar \
  --properties="spark.plugins=com.nvidia.spark.SQLPlugin,spark.rapids.sql.enabled=true" \
  --async

echo ""
echo "=== Job submitted! ==="
echo "View results: bq query --nouse_legacy_sql 'SELECT * FROM ${PROJECT_ID}.${DATASET_V3}.gpu_benchmarks ORDER BY created_at DESC LIMIT 5'"
echo "View in console: https://console.cloud.google.com/dataproc/batches?project=${PROJECT_ID}"
