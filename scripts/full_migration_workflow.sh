#!/bin/bash
# full_migration_workflow.sh - Complete end-to-end migration workflow
# This script creates cluster, runs migration, and cleans up

set -e

# ============================================================================
# CONFIGURATION - Edit these values for your environment
# ============================================================================

PROJECT_ID="your-project-id"
REGION="us-central1"
CLUSTER_NAME="delta-migration-$(date +%Y%m%d-%H%M%S)"
BUCKET="your-bucket"
TEMP_BUCKET="your-temp-bucket"

# Cluster configuration
MASTER_MACHINE_TYPE="n1-standard-4"
WORKER_MACHINE_TYPE="n1-highmem-4"
NUM_WORKERS=3
WORKER_BOOT_DISK_SIZE=500

# Migration configuration
CONFIG_FILE="config/migration_config.json"
METHOD="parquet"
MODE="overwrite"

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

START_TIME=$(date +%s)

echo "============================================"
echo "Delta to BigQuery Migration Workflow"
echo "============================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Config: ${CONFIG_FILE}"
echo "============================================"
echo ""

# Function to cleanup on error
cleanup_on_error() {
    echo ""
    echo "ERROR: Migration failed!"
    echo "Cleaning up cluster..."
    gcloud dataproc clusters delete ${CLUSTER_NAME} \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --quiet || true
    exit 1
}

trap cleanup_on_error ERR

# Step 1: Create Dataproc cluster
echo "[1/4] Creating Dataproc cluster..."
echo "This may take 2-5 minutes..."
echo ""

gcloud dataproc clusters create ${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --master-machine-type=${MASTER_MACHINE_TYPE} \
  --num-workers=${NUM_WORKERS} \
  --worker-machine-type=${WORKER_MACHINE_TYPE} \
  --worker-boot-disk-size=${WORKER_BOOT_DISK_SIZE} \
  --image-version=2.1-debian11 \
  --scopes=cloud-platform \
  --properties="spark:spark.jars.packages=io.delta:delta-core_2.12:2.4.0,com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2,spark:spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension,spark:spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog,spark:spark.executor.memory=8g,spark:spark.driver.memory=4g,spark:spark.dynamicAllocation.enabled=true" \
  --metadata="PIP_PACKAGES=google-cloud-bigquery==3.11.0" \
  --initialization-actions=gs://goog-dataproc-initialization-actions-${REGION}/python/pip-install.sh

echo "✓ Cluster created successfully"
echo ""

# Step 2: Upload migration scripts
echo "[2/4] Uploading migration scripts to GCS..."
gsutil cp scripts/delta_to_bigquery_dataproc.py gs://${BUCKET}/scripts/
gsutil cp ${CONFIG_FILE} gs://${BUCKET}/config/migration_config.json
echo "✓ Scripts uploaded"
echo ""

# Step 3: Submit migration job
echo "[3/4] Submitting migration job..."
echo "This may take several minutes to hours depending on data size..."
echo ""

gcloud dataproc jobs submit pyspark \
  gs://${BUCKET}/scripts/delta_to_bigquery_dataproc.py \
  --cluster=${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --max-failures-per-hour=1 \
  -- \
  --config-file gs://${BUCKET}/config/migration_config.json \
  --method ${METHOD} \
  --mode ${MODE}

JOB_STATUS=$?
echo ""

# Step 4: Cleanup cluster
echo "[4/4] Cleaning up cluster..."
gcloud dataproc clusters delete ${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --quiet

echo "✓ Cluster deleted"
echo ""

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# Final status
if [ $JOB_STATUS -eq 0 ]; then
    echo "============================================"
    echo "✓ Migration completed successfully!"
    echo "============================================"
    echo "Total time: ${MINUTES}m ${SECONDS}s"
    echo ""
    echo "Your data is now available in BigQuery."
    echo "Check tables with:"
    echo "  bq ls ${PROJECT_ID}:your_dataset"
    echo ""
else
    echo "============================================"
    echo "✗ Migration failed with exit code ${JOB_STATUS}"
    echo "============================================"
    echo "Total time: ${MINUTES}m ${SECONDS}s"
    echo ""
    echo "Check logs for details"
    exit 1
fi
