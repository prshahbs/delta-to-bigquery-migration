#!/bin/bash
# submit_single_job.sh - Submit single table migration job to Dataproc

set -e

# ============================================================================
# CONFIGURATION - Edit these values for your migration
# ============================================================================

PROJECT_ID="your-project-id"
REGION="us-central1"
CLUSTER_NAME="delta-migration-cluster"
BUCKET="your-bucket"
TEMP_BUCKET="your-temp-bucket"

# Table configuration
DELTA_PATH="gs://${BUCKET}/delta-tables/customers"
BQ_DATASET="analytics"
BQ_TABLE="customers"

# Migration settings
METHOD="parquet"  # Options: 'parquet' or 'connector'
MODE="overwrite"  # Options: 'overwrite' or 'append'

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

echo "============================================"
echo "Submitting Delta to BigQuery Migration Job"
echo "============================================"
echo "Project: ${PROJECT_ID}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Source: ${DELTA_PATH}"
echo "Target: ${PROJECT_ID}.${BQ_DATASET}.${BQ_TABLE}"
echo "Method: ${METHOD}"
echo "Mode: ${MODE}"
echo "============================================"
echo ""

# Check if cluster exists
if ! gcloud dataproc clusters describe ${CLUSTER_NAME} \
     --region=${REGION} \
     --project=${PROJECT_ID} &>/dev/null; then
    echo "ERROR: Cluster ${CLUSTER_NAME} does not exist!"
    echo "Create it first with: ./scripts/setup_dataproc.sh"
    exit 1
fi

# Upload script to GCS
echo "Uploading migration script to GCS..."
gsutil cp scripts/delta_to_bigquery_dataproc.py gs://${BUCKET}/scripts/
echo "✓ Script uploaded"
echo ""

# Submit job
echo "Submitting job to Dataproc..."
gcloud dataproc jobs submit pyspark \
  gs://${BUCKET}/scripts/delta_to_bigquery_dataproc.py \
  --cluster=${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  -- \
  --delta-path ${DELTA_PATH} \
  --bq-project ${PROJECT_ID} \
  --bq-dataset ${BQ_DATASET} \
  --bq-table ${BQ_TABLE} \
  --temp-bucket ${TEMP_BUCKET} \
  --method ${METHOD} \
  --mode ${MODE}

JOB_STATUS=$?

if [ $JOB_STATUS -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✓ Job completed successfully!"
    echo "============================================"
    echo ""
    echo "Verify your data in BigQuery:"
    echo "  bq query --use_legacy_sql=false \"SELECT COUNT(*) FROM \\\`${PROJECT_ID}.${BQ_DATASET}.${BQ_TABLE}\\\`\""
else
    echo ""
    echo "============================================"
    echo "✗ Job failed with exit code ${JOB_STATUS}"
    echo "============================================"
    echo ""
    echo "Check logs with:"
    echo "  gcloud dataproc jobs list --region=${REGION} --filter='status.state=ERROR'"
    exit 1
fi
