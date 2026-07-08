#!/bin/bash
# D.A.M.I. — One-time GPU Infrastructure Setup
#
# This script:
# 1. Enables required APIs
# 2. Creates GCS bucket for Spark deps
# 3. Uploads sample 100K server data to GCS
# 4. Creates dami_data_v3 dataset (if not exists)
#
# Usage:
#   bash scripts/setup_gpu_infra.sh

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-cohort-2-497207}"
REGION="${GCP_REGION:-us-central1}"
GCS_BUCKET="${GCS_BUCKET:-dami-migration-uploads}"
DEPS_BUCKET="dami-spark-deps-${PROJECT_ID}"

echo "=== D.A.M.I. GPU Infrastructure Setup ==="
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"
echo ""

# 1. Enable required APIs
echo "[1/5] Enabling required APIs..."
gcloud services enable compute.googleapis.com --project="${PROJECT_ID}" --quiet 2>/dev/null || true
gcloud services enable dataproc.googleapis.com --project="${PROJECT_ID}" --quiet 2>/dev/null || true
echo "  APIs enabled."

# 2. Create Spark deps bucket
echo "[2/5] Creating Spark deps bucket..."
gsutil ls "gs://${DEPS_BUCKET}" 2>/dev/null || gsutil mb -l "${REGION}" -p "${PROJECT_ID}" "gs://${DEPS_BUCKET}"
echo "  Deps bucket ready: gs://${DEPS_BUCKET}"

# 3. Upload sample data to GCS
echo "[3/5] Uploading sample server data to GCS..."
if [ -f "data/seed/sample_servers_100k.csv" ]; then
    gsutil cp data/seed/sample_servers_100k.csv "gs://${GCS_BUCKET}/sample_servers_100k.csv"
    echo "  Uploaded: gs://${GCS_BUCKET}/sample_servers_100k.csv"
else
    echo "  WARNING: data/seed/sample_servers_100k.csv not found."
    echo "  Run: python scripts/generate_100k_servers.py first"
fi

# 4. Also upload the original sample
echo "[4/5] Uploading original sample RVTools data..."
if [ -f "data/seed/sample_rvtools.csv" ]; then
    gsutil cp data/seed/sample_rvtools.csv "gs://${GCS_BUCKET}/sample_rvtools.csv"
    echo "  Uploaded: gs://${GCS_BUCKET}/sample_rvtools.csv"
fi

# 5. Create dami_data_v3 dataset
echo "[5/5] Creating dami_data_v3 BigQuery dataset..."
bq mk --dataset --location=US "${PROJECT_ID}:dami_data_v3" 2>/dev/null || echo "  Dataset already exists."

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Check T4 GPU quota: https://console.cloud.google.com/iam-admin/quotas?project=${PROJECT_ID}"
echo "     Filter: 'NVIDIA_T4_GPUS' in region '${REGION}'"
echo "  2. Run benchmark: bash scripts/submit_spark_gpu.sh"
echo "  3. View results: bq query 'SELECT * FROM ${PROJECT_ID}.dami_data_v3.gpu_benchmarks'"
