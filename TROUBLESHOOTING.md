# Troubleshooting Guide

Common issues and their solutions for Delta to BigQuery migration.

## Table of Contents

1. [Cluster Issues](#cluster-issues)
2. [Permission Issues](#permission-issues)
3. [Delta Table Issues](#delta-table-issues)
4. [BigQuery Issues](#bigquery-issues)
5. [Performance Issues](#performance-issues)
6. [Job Failures](#job-failures)

## Cluster Issues

### Cluster Creation Fails: Quota Exceeded

**Error:**
```
ERROR: (gcloud.dataproc.clusters.create) RESOURCE_EXHAUSTED: Quota 'CPUS' exceeded.
```

**Solution:**
```bash
# Check current quotas
gcloud compute project-info describe --project=${PROJECT_ID}

# Request quota increase at:
# https://console.cloud.google.com/iam-admin/quotas

# Or use a smaller cluster temporarily
WORKER_MACHINE_TYPE="n1-standard-2"
NUM_WORKERS=2
```

### Cluster Already Exists

**Error:**
```
ERROR: Cluster delta-migration-cluster already exists
```

**Solution:**
```bash
# List existing clusters
gcloud dataproc clusters list --region=us-central1

# Delete existing cluster
gcloud dataproc clusters delete delta-migration-cluster \
  --region=us-central1 \
  --quiet

# Or use a different name
CLUSTER_NAME="delta-migration-cluster-$(date +%s)"
```

### Cluster Creation Timeout

**Error:**
```
ERROR: Operation timed out
```

**Solution:**
```bash
# Check cluster status
gcloud dataproc clusters describe CLUSTER_NAME --region=us-central1

# If stuck, delete and recreate
gcloud dataproc clusters delete CLUSTER_NAME --region=us-central1 --async

# Try with longer timeout
gcloud dataproc clusters create ... --request-timeout=1200
```

## Permission Issues

### Permission Denied: GCS Access

**Error:**
```
java.io.IOException: Permission denied: gs://bucket/path
```

**Solution:**
```bash
# Check service account
gcloud dataproc clusters describe CLUSTER_NAME \
  --region=us-central1 \
  --format="value(config.gceClusterConfig.serviceAccount)"

# Grant storage permissions
export SA_EMAIL="SERVICE_ACCOUNT_EMAIL"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${SA_EMAIL} \
  --role=roles/storage.objectViewer

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${SA_EMAIL} \
  --role=roles/storage.objectCreator
```

### Permission Denied: BigQuery

**Error:**
```
Access Denied: BigQuery BigQuery: Permission denied while writing to project
```

**Solution:**
```bash
# Grant BigQuery permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${SA_EMAIL} \
  --role=roles/bigquery.dataEditor

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${SA_EMAIL} \
  --role=roles/bigquery.jobUser
```

### Cannot Create Dataset

**Error:**
```
Dataset not found: project:dataset
```

**Solution:**
```bash
# Create dataset manually
bq mk --dataset \
  --location=us-central1 \
  ${PROJECT_ID}:your_dataset

# Or grant dataset creation permission
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${SA_EMAIL} \
  --role=roles/bigquery.dataOwner
```

## Delta Table Issues

### Delta Table Not Found

**Error:**
```
AnalysisException: [PATH_NOT_FOUND] Path does not exist: gs://bucket/path
```

**Solution:**
```bash
# Verify Delta table structure
gsutil ls gs://bucket/path/

# Should see:
# - Parquet files (*.parquet)
# - _delta_log/ directory

# Check Delta log
gsutil ls gs://bucket/path/_delta_log/

# Should see:
# - 00000000000000000000.json
# - 00000000000000000001.json
# - etc.
```

### Corrupted Delta Log

**Error:**
```
org.apache.spark.sql.delta.DeltaErrors$DeltaIllegalStateException
```

**Solution:**
```bash
# Try to repair Delta table first (on Databricks or local Spark):
# from delta.tables import DeltaTable
# DeltaTable.forPath(spark, "gs://bucket/path").generate("symlink_format_manifest")

# Or copy to new location without _delta_log and recreate
gsutil -m cp -r gs://bucket/old-path/*.parquet gs://bucket/new-path/

# Then create new Delta table from parquet
# df = spark.read.parquet("gs://bucket/new-path")
# df.write.format("delta").save("gs://bucket/new-delta-path")
```

### Unsupported Delta Features

**Error:**
```
Unsupported Delta table feature: changeDataFeed
```

**Solution:**
```bash
# Disable advanced features before migration (in Databricks):
# ALTER TABLE table_name SET TBLPROPERTIES (
#   'delta.enableChangeDataFeed' = 'false'
# )

# Or read specific version
--delta-path "gs://bucket/path@v123"
```

## BigQuery Issues

### Table Already Exists

**Error:**
```
BigQuery error: Already Exists: Table project:dataset.table
```

**Solution:**
```bash
# Use overwrite mode
--mode overwrite

# Or delete table first
bq rm -f -t ${PROJECT_ID}:dataset.table

# Or use append mode
--mode append
```

### Schema Mismatch

**Error:**
```
Provided Schema does not match Table
```

**Solution:**
```bash
# Delete and recreate with overwrite
bq rm -f -t ${PROJECT_ID}:dataset.table

# Then rerun with overwrite mode
--mode overwrite

# Or create table with correct schema manually first
bq mk --table ${PROJECT_ID}:dataset.table schema.json
```

### Row Too Large

**Error:**
```
Row too large: maximum is 100MB
```

**Solution:**
- Split large columns into separate tables
- Compress or truncate large text fields
- Use nested/repeated fields instead of wide tables
- Consider partitioning by date to reduce row size

### Quota Exceeded

**Error:**
```
Exceeded rate limits: too many table update operations
```

**Solution:**
```bash
# Reduce parallelism
--properties=spark.sql.shuffle.partitions=50

# Use parquet method instead of connector
--method parquet

# Wait and retry
sleep 60 && ./submit_job.sh
```

## Performance Issues

### Job Running Very Slow

**Symptoms:**
- Job takes hours instead of minutes
- Executors sitting idle
- Low CPU utilization

**Solution:**
```bash
# 1. Increase cluster size
NUM_WORKERS=10
WORKER_MACHINE_TYPE="n1-highmem-8"

# 2. Adjust Spark configuration
--properties="\
spark:spark.executor.memory=12g,\
spark:spark.executor.cores=4,\
spark:spark.default.parallelism=400,\
spark:spark.sql.shuffle.partitions=400"

# 3. Use parquet method for large datasets
--method parquet
```

### Out of Memory Error

**Error:**
```
java.lang.OutOfMemoryError: Java heap space
```

**Solution:**
```bash
# 1. Use high-memory machines
WORKER_MACHINE_TYPE="n1-highmem-16"

# 2. Increase executor memory
--properties=spark:spark.executor.memory=16g

# 3. Reduce partition size
--properties=spark:spark.sql.files.maxPartitionBytes=134217728  # 128MB

# 4. Use parquet intermediate method
--method parquet
```

### Executor Lost / Node Failure

**Error:**
```
ExecutorLostFailure: Executor lost
```

**Solution:**
```bash
# 1. Don't use preemptible workers for critical jobs
--num-preemptible-workers=0

# 2. Increase executor memory
--properties=spark:spark.executor.memory=12g

# 3. Enable speculation
--properties=spark:spark.speculation=true

# 4. Increase timeout
--properties=spark:spark.network.timeout=800s
```

## Job Failures

### Python Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'google.cloud.bigquery'
```

**Solution:**
```bash
# Ensure initialization action is included
--metadata="PIP_PACKAGES=google-cloud-bigquery==3.11.0" \
--initialization-actions=gs://goog-dataproc-initialization-actions-${REGION}/python/pip-install.sh

# Or install manually after cluster creation
gcloud compute ssh ${CLUSTER_NAME}-m --zone=${ZONE} \
  --command="sudo pip3 install google-cloud-bigquery"
```

### Spark Package Not Found

**Error:**
```
java.lang.ClassNotFoundException: io.delta.sql.DeltaSparkSessionExtension
```

**Solution:**
```bash
# Ensure packages are specified in cluster creation
--properties="spark:spark.jars.packages=io.delta:delta-core_2.12:2.4.0,com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2"

# Or specify when submitting job
gcloud dataproc jobs submit pyspark \
  --jars=gs://path/to/delta-core_2.12-2.4.0.jar \
  ...
```

### Job Timeout

**Error:**
```
Job exceeded maximum time
```

**Solution:**
```bash
# Increase job timeout
gcloud dataproc jobs submit pyspark \
  --max-failures-per-hour=3 \
  ...

# Or split into smaller batches
# Edit config file to process fewer tables per job
```

### Verification Failed

**Warning:**
```
Row count mismatch! Delta: 1000000, BigQuery: 999995
```

**Possible Causes:**
1. Data still loading (eventual consistency)
2. Filters applied during read
3. Duplicate handling differences
4. Null value handling

**Solution:**
```bash
# 1. Wait and recheck
sleep 60
bq query "SELECT COUNT(*) FROM \`project.dataset.table\`"

# 2. Check for duplicates
bq query "
SELECT COUNT(*) as total, COUNT(DISTINCT id) as unique_ids
FROM \`project.dataset.table\`
"

# 3. Compare samples
bq query "SELECT * FROM \`project.dataset.table\` LIMIT 10"

# 4. Rerun with overwrite
--mode overwrite
```

## Debugging Steps

### 1. Check Job Status

```bash
# List recent jobs
gcloud dataproc jobs list --region=us-central1 --limit=10

# Get job details
gcloud dataproc jobs describe JOB_ID --region=us-central1

# View job logs
gcloud dataproc jobs wait JOB_ID --region=us-central1
```

### 2. Check Cluster Health

```bash
# Cluster status
gcloud dataproc clusters describe CLUSTER_NAME --region=us-central1

# SSH into master node
gcloud compute ssh ${CLUSTER_NAME}-m --zone=us-central1-a

# Check Spark logs
tail -f /var/log/spark/*.log
```

### 3. Check Data

```bash
# Verify Delta table
gsutil ls -lh gs://bucket/delta-path/
gsutil ls gs://bucket/delta-path/_delta_log/ | head -5

# Verify BigQuery table
bq show ${PROJECT_ID}:dataset.table
bq head -n 10 ${PROJECT_ID}:dataset.table
```

### 4. Enable Verbose Logging

```bash
# Submit with debug logging
gcloud dataproc jobs submit pyspark \
  --properties=spark:spark.log.level=DEBUG \
  ...
```

## Getting More Help

### Viewing Logs

```bash
# Dataproc job logs
gcloud logging read "resource.type=cloud_dataproc_job" --limit=50

# Cluster logs
gcloud logging read "resource.type=cloud_dataproc_cluster \
  AND resource.labels.cluster_name=${CLUSTER_NAME}" --limit=50

# BigQuery job logs
bq ls -j -a -n 100
```

### Useful Commands

```bash
# Test Delta read
gcloud dataproc jobs submit pyspark \
  --cluster=${CLUSTER_NAME} \
  --region=us-central1 \
  --py-files=- << 'EOF'
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.read.format("delta").load("gs://bucket/path")
print(f"Row count: {df.count()}")
print(f"Schema: {df.schema}")
EOF

# Test BigQuery write
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`project.dataset.table\`"
```

## Contact & Support

If issues persist after trying these solutions:

1. Check the main [README.md](README.md) for more details
2. Review [Cloud Dataproc documentation](https://cloud.google.com/dataproc/docs)
3. Check [BigQuery documentation](https://cloud.google.com/bigquery/docs)
4. Review [Delta Lake documentation](https://docs.delta.io/)

---

**Last Updated:** November 4, 2025
