#!/bin/bash
# setup_dataproc.sh - Script to create Dataproc cluster for Delta migration

set -e

# ============================================================================
# CONFIGURATION - Edit these values for your environment
# ============================================================================

PROJECT_ID="your-project-id"
REGION="us-central1"
CLUSTER_NAME="delta-migration-cluster"
BUCKET_NAME="your-bucket"
TEMP_BUCKET="your-temp-bucket"

# Cluster configuration
MASTER_MACHINE_TYPE="n1-standard-4"
WORKER_MACHINE_TYPE="n1-standard-4"
NUM_WORKERS=3
WORKER_BOOT_DISK_SIZE=500

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

echo "============================================"
echo "Creating Dataproc Cluster"
echo "============================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Workers: ${NUM_WORKERS}"
echo "============================================"

# Check if cluster already exists
if gcloud dataproc clusters describe ${CLUSTER_NAME} \
   --region=${REGION} \
   --project=${PROJECT_ID} &>/dev/null; then
    echo "ERROR: Cluster ${CLUSTER_NAME} already exists!"
    echo "Delete it first with:"
    echo "  gcloud dataproc clusters delete ${CLUSTER_NAME} --region=${REGION} --quiet"
    exit 1
fi

# Create Dataproc cluster
echo "Creating cluster..."
gcloud dataproc clusters create ${CLUSTER_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --master-machine-type=${MASTER_MACHINE_TYPE} \
  --master-boot-disk-size=100 \
  --num-workers=${NUM_WORKERS} \
  --worker-machine-type=${WORKER_MACHINE_TYPE} \
  --worker-boot-disk-size=${WORKER_BOOT_DISK_SIZE} \
  --image-version=2.1-debian11 \
  --optional-components=JUPYTER \
  --enable-component-gateway \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --properties="spark:spark.jars.packages=io.delta:delta-core_2.12:2.4.0,com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2" \
  --properties="spark:spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" \
  --properties="spark:spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" \
  --properties="spark:spark.executor.memory=8g" \
  --properties="spark:spark.driver.memory=4g" \
  --properties="spark:spark.dynamicAllocation.enabled=true" \
  --metadata="PIP_PACKAGES=google-cloud-bigquery==3.11.0 google-cloud-storage==2.10.0" \
  --initialization-actions=gs://goog-dataproc-initialization-actions-${REGION}/python/pip-install.sh

echo ""
echo "============================================"
echo "Cluster ${CLUSTER_NAME} created successfully!"
echo "============================================"
echo ""
echo "Cluster details:"
gcloud dataproc clusters describe ${CLUSTER_NAME} --region=${REGION} --project=${PROJECT_ID}
echo ""
echo "Next steps:"
echo "1. Upload your migration script:"
echo "   gsutil cp scripts/delta_to_bigquery_dataproc.py gs://${BUCKET_NAME}/scripts/"
echo ""
echo "2. Submit a job:"
echo "   ./scripts/submit_single_job.sh"
echo "   OR"
echo "   ./scripts/submit_batch_job.sh"
echo ""
echo "3. Delete cluster when done:"
echo "   gcloud dataproc clusters delete ${CLUSTER_NAME} --region=${REGION} --quiet"
echo ""
