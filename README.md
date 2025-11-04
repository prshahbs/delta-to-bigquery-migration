# Delta to BigQuery Migration Tool

A comprehensive solution for migrating Delta Lake tables from Google Cloud Storage to BigQuery using Google Cloud Dataproc.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Migration Methods](#migration-methods)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Cost Optimization](#cost-optimization)

## Overview

This tool enables seamless migration of Delta Lake tables stored in Google Cloud Storage to BigQuery using Apache Spark on Dataproc. It supports:

- ✅ Reading Delta Lake format (parquet + transaction logs)
- ✅ Automatic schema mapping from Delta to BigQuery
- ✅ Batch migration of multiple tables
- ✅ Two migration methods (direct connector and parquet intermediate)
- ✅ Data verification and validation
- ✅ Comprehensive logging and error handling
- ✅ Support for complex data types
- ✅ Incremental and full load modes

## Architecture

```
┌─────────────────┐
│   Delta Tables  │
│   in GCS        │
│ (parquet + bin) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dataproc      │
│   Cluster       │
│  (Apache Spark) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   BigQuery      │
│   Tables        │
└─────────────────┘
```

### Migration Flow

1. **Read**: Spark reads Delta format from GCS (parquet files + _delta_log/*.bin)
2. **Transform**: Optimize DataFrame and convert complex types
3. **Write**: Load data into BigQuery using selected method
4. **Verify**: Compare row counts between source and destination
5. **Cleanup**: Remove temporary files

## Prerequisites

### Google Cloud Platform

- **GCP Project** with billing enabled
- **IAM Permissions**:
  - `dataproc.clusters.create`
  - `dataproc.jobs.create`
  - `bigquery.datasets.create`
  - `bigquery.tables.create`
  - `storage.buckets.create`
  - `storage.objects.create`

### APIs to Enable

```bash
gcloud services enable dataproc.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable compute.googleapis.com
```

### Required Resources

1. **GCS Bucket** for Delta tables
2. **GCS Bucket** for temporary files
3. **BigQuery Dataset** (will be created if doesn't exist)
4. **Service Account** (optional, for authentication)

### Software Requirements

- Google Cloud SDK (`gcloud` CLI)
- Python 3.8+ (for local testing)
- Bash shell

## Installation

### Step 1: Clone or Extract Files

```bash
# Extract the zip file
unzip delta-to-bigquery-migration.zip
cd delta-to-bigquery-migration
```

### Step 2: Set Up Google Cloud SDK

```bash
# Install gcloud SDK (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Step 3: Create Required GCS Buckets

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET_NAME="your-migration-bucket"
export TEMP_BUCKET="your-temp-bucket"

# Create buckets
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME}
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${TEMP_BUCKET}

# Create directories
gsutil mkdir gs://${BUCKET_NAME}/scripts/
gsutil mkdir gs://${BUCKET_NAME}/config/
gsutil mkdir gs://${BUCKET_NAME}/logs/
```

### Step 4: Create BigQuery Dataset

```bash
bq --project_id=${PROJECT_ID} mk --dataset --location=${REGION} your_dataset
```

### Step 5: Upload Scripts to GCS

```bash
# Upload Python script
gsutil cp scripts/delta_to_bigquery_dataproc.py gs://${BUCKET_NAME}/scripts/

# Upload configuration (after editing)
gsutil cp config/migration_config.json gs://${BUCKET_NAME}/config/
```

## Configuration

### 1. Edit Project Settings

Edit `scripts/setup_dataproc.sh`:

```bash
# Configuration
PROJECT_ID="your-project-id"              # Your GCP project ID
REGION="us-central1"                       # GCP region
CLUSTER_NAME="delta-migration-cluster"     # Dataproc cluster name
BUCKET_NAME="your-migration-bucket"        # Your GCS bucket
TEMP_BUCKET="your-temp-bucket"             # Temp bucket for intermediate files
```

### 2. Configure Tables for Migration

Edit `config/migration_config.json`:

```json
[
  {
    "gcs_delta_path": "gs://your-bucket/delta-tables/table1",
    "bq_project": "your-project-id",
    "bq_dataset": "your_dataset",
    "bq_table": "table1",
    "temp_bucket": "your-temp-bucket"
  },
  {
    "gcs_delta_path": "gs://your-bucket/delta-tables/table2",
    "bq_project": "your-project-id",
    "bq_dataset": "your_dataset",
    "bq_table": "table2",
    "temp_bucket": "your-temp-bucket"
  }
]
```

### 3. Adjust Cluster Configuration

For large datasets, modify cluster settings in `scripts/setup_dataproc.sh`:

```bash
# For small datasets (< 100GB)
MASTER_MACHINE_TYPE="n1-standard-4"
WORKER_MACHINE_TYPE="n1-standard-4"
NUM_WORKERS=2

# For medium datasets (100GB - 1TB)
MASTER_MACHINE_TYPE="n1-standard-8"
WORKER_MACHINE_TYPE="n1-highmem-8"
NUM_WORKERS=5

# For large datasets (> 1TB)
MASTER_MACHINE_TYPE="n1-standard-16"
WORKER_MACHINE_TYPE="n1-highmem-16"
NUM_WORKERS=10
```

## Usage

### Option 1: Full Automated Workflow (Recommended)

Run the complete workflow that creates cluster, runs migration, and cleans up:

```bash
# Make script executable
chmod +x scripts/full_migration_workflow.sh

# Edit configuration in the script
nano scripts/full_migration_workflow.sh

# Run migration
./scripts/full_migration_workflow.sh
```

### Option 2: Manual Step-by-Step

#### Step 1: Create Dataproc Cluster

```bash
chmod +x scripts/setup_dataproc.sh
./scripts/setup_dataproc.sh
```

#### Step 2: Submit Single Table Migration

```bash
chmod +x scripts/submit_single_job.sh

# Edit the script with your table details
nano scripts/submit_single_job.sh

# Submit job
./scripts/submit_single_job.sh
```

#### Step 3: Submit Batch Migration

```bash
chmod +x scripts/submit_batch_job.sh

# Make sure migration_config.json is uploaded to GCS
gsutil cp config/migration_config.json gs://${BUCKET_NAME}/config/

# Submit batch job
./scripts/submit_batch_job.sh
```

#### Step 4: Monitor Job

```bash
# List jobs
gcloud dataproc jobs list --region=us-central1

# Get job details
gcloud dataproc jobs describe JOB_ID --region=us-central1

# View logs
gcloud dataproc jobs wait JOB_ID --region=us-central1
```

#### Step 5: Cleanup Cluster

```bash
gcloud dataproc clusters delete delta-migration-cluster \
  --region=us-central1 \
  --quiet
```

### Option 3: Using gcloud Command Directly

```bash
# Upload script
gsutil cp scripts/delta_to_bigquery_dataproc.py gs://${BUCKET_NAME}/scripts/

# Submit job to existing cluster
gcloud dataproc jobs submit pyspark \
  gs://${BUCKET_NAME}/scripts/delta_to_bigquery_dataproc.py \
  --cluster=delta-migration-cluster \
  --region=us-central1 \
  --project=${PROJECT_ID} \
  -- \
  --delta-path gs://${BUCKET_NAME}/delta-tables/customers \
  --bq-project ${PROJECT_ID} \
  --bq-dataset analytics \
  --bq-table customers \
  --temp-bucket ${TEMP_BUCKET} \
  --method parquet \
  --mode overwrite
```

## Migration Methods

### Method 1: Parquet Intermediate (Recommended)

**Best for**: Large datasets, production workloads

**How it works**:
1. Reads Delta table from GCS
2. Writes optimized Parquet files to temp location
3. Loads Parquet into BigQuery using native loader
4. Cleans up temp files

**Advantages**:
- More reliable for large datasets
- Better performance for datasets > 1TB
- Easier to debug (can inspect intermediate files)
- Less memory pressure on Spark

**Usage**:
```bash
--method parquet
```

### Method 2: Direct Connector

**Best for**: Small to medium datasets (< 500GB), quick migrations

**How it works**:
1. Reads Delta table from GCS
2. Writes directly to BigQuery using Spark connector

**Advantages**:
- Faster for small datasets
- No intermediate storage needed
- Simpler architecture

**Usage**:
```bash
--method connector
```

## Command Line Arguments

```bash
# Required arguments for single table migration
--delta-path         # GCS path to Delta table (e.g., gs://bucket/delta-tables/table1)
--bq-project         # BigQuery project ID
--bq-dataset         # BigQuery dataset name
--bq-table           # BigQuery table name
--temp-bucket        # GCS bucket for temporary files (without gs:// prefix)

# Optional arguments
--method             # Migration method: 'connector' or 'parquet' (default: parquet)
--mode               # Write mode: 'overwrite' or 'append' (default: overwrite)
--config-file        # JSON file for batch migration
--no-verify          # Skip verification after migration
--no-cleanup         # Keep temporary files (for debugging)
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied

**Error**: `Permission denied: gs://bucket/path`

**Solution**:
```bash
# Check service account permissions
gcloud projects get-iam-policy ${PROJECT_ID}

# Grant required permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:YOUR_SA@PROJECT.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:YOUR_SA@PROJECT.iam.gserviceaccount.com \
  --role=roles/bigquery.dataEditor
```

#### 2. Delta Table Not Found

**Error**: `AnalysisException: [PATH_NOT_FOUND]`

**Solution**:
```bash
# Verify Delta table exists
gsutil ls gs://bucket/path/to/delta/
gsutil ls gs://bucket/path/to/delta/_delta_log/

# Check Delta log files
gsutil ls gs://bucket/path/to/delta/_delta_log/*.json
```

#### 3. Out of Memory

**Error**: `java.lang.OutOfMemoryError`

**Solution**:
- Increase worker memory: Use `n1-highmem-*` machine types
- Increase number of workers
- Use `parquet` method instead of `connector`
- Reduce partition size in DataFrame

#### 4. Job Timeout

**Error**: Job exceeds maximum time

**Solution**:
```bash
# Submit with longer timeout
gcloud dataproc jobs submit pyspark \
  ... \
  --max-failures-per-hour=3 \
  --properties=spark.executor.heartbeatInterval=60s,spark.network.timeout=600s
```

#### 5. Schema Mismatch

**Error**: `Schema mismatch between source and target`

**Solution**:
- Use `--mode overwrite` to recreate table
- Manually create BigQuery table with correct schema
- Check for unsupported data types

### Viewing Logs

```bash
# View job logs
gcloud dataproc jobs describe JOB_ID --region=us-central1

# View driver logs
gcloud logging read "resource.type=cloud_dataproc_cluster AND resource.labels.cluster_name=CLUSTER_NAME" \
  --limit 100 \
  --format json

# SSH into master node
gcloud compute ssh CLUSTER_NAME-m --zone=us-central1-a

# View Spark logs on master
tail -f /var/log/spark/spark-*-org.apache.spark.deploy.master.Master-*.out
```

## Best Practices

### 1. Data Validation

Always verify your migration:

```bash
# The script automatically verifies, but you can also manually check
bq query --use_legacy_sql=false "
SELECT COUNT(*) as row_count 
FROM \`project.dataset.table\`
"
```

### 2. Incremental Loads

For ongoing sync, use append mode with filtering:

```python
# Modify script to add timestamp filter
df = spark.read.format("delta").load("gs://bucket/delta/") \
    .filter("_commit_timestamp > '2025-11-03 00:00:00'")
```

### 3. Partitioning

Preserve partitioning for query performance:

```python
# If Delta table is partitioned by date
df.write \
    .format("bigquery") \
    .option("partitionField", "date") \
    .option("partitionType", "DAY") \
    .save()
```

### 4. Cost Optimization

- Use preemptible workers (add `--num-preemptible-workers=N`)
- Delete cluster when not in use
- Use lifecycle policies on temp buckets
- Enable cluster autoscaling

### 5. Monitoring

Set up Cloud Monitoring alerts:

```bash
# Alert on job failures
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Dataproc Job Failure" \
  --condition-display-name="Job Failed" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=60s
```

## Cost Optimization

### Cluster Sizing Guidelines

| Data Size | Workers | Machine Type | Estimated Cost/Hour |
|-----------|---------|--------------|---------------------|
| < 100GB   | 2       | n1-standard-4 | ~$1.20 |
| 100GB-500GB | 5     | n1-standard-8 | ~$4.80 |
| 500GB-1TB | 10      | n1-highmem-8 | ~$11.20 |
| > 1TB     | 15-20   | n1-highmem-16 | ~$25-35 |

### Cost-Saving Tips

1. **Use Preemptible Workers**
```bash
--num-preemptible-workers=10
# Saves ~80% on worker costs
```

2. **Enable Autoscaling**
```bash
--enable-component-gateway \
--autoscaling-policy=YOUR_POLICY
```

3. **Set Idle Timeout**
```bash
--max-idle=30m  # Delete cluster after 30 min idle
```

4. **Use Regional Resources**
```bash
# Keep data, Dataproc, and BigQuery in same region
# Avoid cross-region data transfer charges
```

## Performance Tuning

### Spark Configuration

For better performance, adjust in `setup_dataproc.sh`:

```bash
--properties="
spark:spark.executor.memory=8g,
spark:spark.executor.cores=4,
spark:spark.driver.memory=4g,
spark:spark.default.parallelism=200,
spark:spark.sql.shuffle.partitions=200,
spark:spark.dynamicAllocation.enabled=true,
spark:spark.dynamicAllocation.minExecutors=2,
spark:spark.dynamicAllocation.maxExecutors=20
"
```

### DataFrame Optimization

The script automatically optimizes DataFrames:
- Converts complex types to JSON
- Coalesces partitions for BigQuery write
- Caches DataFrames when reused

## Support and Contributions

### Getting Help

- Check [Troubleshooting](#troubleshooting) section
- Review Dataproc logs
- Check BigQuery job history

### Reporting Issues

When reporting issues, include:
- Error messages and stack traces
- Dataproc job ID
- Delta table schema and size
- Cluster configuration

## License

This project is provided as-is for use with Google Cloud Platform services.

## Changelog

### Version 1.0.0 (2025-11-04)
- Initial release
- Support for Delta to BigQuery migration
- Two migration methods (connector and parquet)
- Batch migration support
- Automatic verification
- Comprehensive logging

---

**Last Updated**: November 4, 2025
**Maintained by**: Your Team
**Contact**: your-email@example.com
