# Quick Start Guide

Get started with Delta to BigQuery migration in 5 minutes!

## Prerequisites Checklist

- [ ] Google Cloud Project with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] Delta tables stored in GCS (with parquet and _delta_log/*.bin files)
- [ ] BigQuery dataset created (or will be auto-created)

## Step 1: Setup (2 minutes)

```bash
# Extract files
unzip delta-to-bigquery-migration.zip
cd delta-to-bigquery-migration

# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
gcloud services enable dataproc.googleapis.com bigquery.googleapis.com storage-api.googleapis.com

# Create buckets
export BUCKET="my-migration-bucket"
export TEMP_BUCKET="my-temp-bucket"
gsutil mb -l us-central1 gs://${BUCKET}
gsutil mb -l us-central1 gs://${TEMP_BUCKET}
```

## Step 2: Configure (1 minute)

### Option A: Single Table Migration

Edit `scripts/submit_single_job.sh`:

```bash
PROJECT_ID="your-project-id"
BUCKET="my-migration-bucket"
TEMP_BUCKET="my-temp-bucket"

DELTA_PATH="gs://my-bucket/delta-tables/customers"
BQ_DATASET="analytics"
BQ_TABLE="customers"
```

### Option B: Batch Migration (Multiple Tables)

Edit `config/migration_config.json`:

```json
[
  {
    "gcs_delta_path": "gs://my-bucket/delta-tables/table1",
    "bq_project": "my-project",
    "bq_dataset": "my_dataset",
    "bq_table": "table1",
    "temp_bucket": "my-temp-bucket"
  }
]
```

## Step 3: Run Migration (1 command!)

### Automated (Recommended)

Runs everything: creates cluster, migrates data, cleans up

```bash
# Edit configuration first
nano scripts/full_migration_workflow.sh

# Run
chmod +x scripts/*.sh
./scripts/full_migration_workflow.sh
```

### Manual

Step-by-step control:

```bash
# 1. Create cluster
chmod +x scripts/setup_dataproc.sh
./scripts/setup_dataproc.sh

# 2. Run migration
chmod +x scripts/submit_single_job.sh
./scripts/submit_single_job.sh

# 3. Delete cluster
gcloud dataproc clusters delete delta-migration-cluster --region=us-central1 --quiet
```

## Step 4: Verify

```bash
# Check BigQuery table
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) as row_count FROM \`${PROJECT_ID}.analytics.customers\`"

# View table schema
bq show ${PROJECT_ID}:analytics.customers
```

## Common First-Time Issues

### Issue: Permission Denied

```bash
# Solution: Grant permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=user:your-email@example.com \
  --role=roles/dataproc.admin

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=user:your-email@example.com \
  --role=roles/bigquery.admin
```

### Issue: Cluster Creation Fails

```bash
# Solution: Check quotas
gcloud compute project-info describe --project=${PROJECT_ID}

# Request quota increase if needed
# https://console.cloud.google.com/iam-admin/quotas
```

### Issue: Delta Table Not Found

```bash
# Solution: Verify Delta structure
gsutil ls gs://your-bucket/delta-tables/table_name/
gsutil ls gs://your-bucket/delta-tables/table_name/_delta_log/

# Should see:
# - *.parquet files
# - _delta_log/ directory
# - _delta_log/*.json files
```

## Example: Complete First Migration

```bash
# 1. Set variables
export PROJECT_ID="my-gcp-project"
export BUCKET="my-data-bucket"
export TEMP_BUCKET="my-temp-bucket"

# 2. Configure single job
cat > scripts/submit_single_job.sh << 'EOF'
#!/bin/bash
set -e

PROJECT_ID="my-gcp-project"
REGION="us-central1"
CLUSTER_NAME="delta-migration-cluster"
BUCKET="my-data-bucket"
TEMP_BUCKET="my-temp-bucket"

DELTA_PATH="gs://my-data-bucket/delta-tables/sales"
BQ_DATASET="analytics"
BQ_TABLE="sales"
METHOD="parquet"
MODE="overwrite"

# Upload and submit
gsutil cp scripts/delta_to_bigquery_dataproc.py gs://${BUCKET}/scripts/

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
EOF

# 3. Make executable
chmod +x scripts/*.sh

# 4. Create cluster
./scripts/setup_dataproc.sh

# 5. Run migration
./scripts/submit_single_job.sh

# 6. Cleanup
gcloud dataproc clusters delete delta-migration-cluster --region=us-central1 --quiet

# 7. Verify
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`${PROJECT_ID}.analytics.sales\`"
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [Troubleshooting](README.md#troubleshooting) for common issues
- Review [Best Practices](README.md#best-practices) for production use
- Explore [Cost Optimization](README.md#cost-optimization) tips

## Getting Help

1. Check the logs:
   ```bash
   gcloud dataproc jobs list --region=us-central1
   gcloud dataproc jobs describe JOB_ID --region=us-central1
   ```

2. Review the full README.md for detailed troubleshooting

3. Common solutions:
   - Permission issues → Check IAM roles
   - Cluster issues → Check quotas
   - Data issues → Verify Delta structure
   - Job failures → Check logs

## Time Estimates

| Data Size | Cluster Size | Estimated Time |
|-----------|--------------|----------------|
| < 10GB    | 2 workers    | 5-10 minutes   |
| 10-100GB  | 3 workers    | 15-30 minutes  |
| 100GB-1TB | 5 workers    | 30-120 minutes |
| > 1TB     | 10+ workers  | 2-8 hours      |

*Times include cluster creation (~3 min) and data transfer*

---

**Pro Tip**: Start with a small subset of data to test the pipeline before running full migration!
