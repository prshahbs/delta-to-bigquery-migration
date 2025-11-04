#!/bin/bash
# submit_batch_job.sh - Submit batch migration job for multiple tables

set -e

# ============================================================================
# CONFIGURATION - Edit these values
# ============================================================================

PROJECT_ID="your-project-id"
REGION="us-central1"
CLUSTER_NAME="delta-migration-cluster"
BUCKET="your-bucket"

# Migration settings
METHOD="parquet"  # Options: 'parquet' or 'connector'
MODE="overwrite"  # Options: 'overwrite' or 'append'

# Path to config file (local)
CONFIG_FILE="config/migration_config.json"

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

echo "============================================"
echo "Submitting Batch Migration Job"
echo "============================================"
echo "Project: ${PROJECT_ID}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Config: ${CONFIG_FILE}"
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

# Check if config file exists
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "ERROR: Config file not found: ${CONFIG_FILE}"
    exit 1
fi

# Count tables in config
TABLE_COUNT=$(python3 -c "import json; print(len(json.load(open('${CONFIG_FILE}'))))")
echo "Found ${TABLE_COUNT} tables to migrate"
echo ""

# Upload files to GCS
echo "Uploading files to GCS..."
gsutil cp scripts/delta_to_bigquery_dataproc.py gs://${BUCKET}/scripts/
gsutil cp ${CONFIG_FILE} gs://${BUCKET}/config/migration_config.json
echo "✓ Files uploaded"
echo ""

# Submit batch job with more resources
echo "Submitting batch job to Dataproc..."
gcloud dataproc jobs submit pyspark \
  gs://${BUCKET}/scripts/delta_to_bigquery_dataproc.py \
  --cluster=${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --properties=spark.executor.memory=8g,spark.executor.cores=4 \
  -- \
  --config-file gs://${BUCKET}/config/migration_config.json \
  --method ${METHOD} \
  --mode ${MODE}

JOB_STATUS=$?

if [ $JOB_STATUS -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✓ Batch job completed successfully!"
    echo "============================================"
    echo ""
    echo "Check your BigQuery tables:"
    echo "  bq ls ${PROJECT_ID}:your_dataset"
else
    echo ""
    echo "============================================"
    echo "✗ Batch job failed with exit code ${JOB_STATUS}"
    echo "============================================"
    echo ""
    echo "Check logs with:"
    echo "  gcloud dataproc jobs list --region=${REGION} --filter='status.state=ERROR'"
    exit 1
fi
