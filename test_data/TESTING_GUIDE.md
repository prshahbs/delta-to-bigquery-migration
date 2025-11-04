# Testing Guide - Sample Data Generation and Migration

Complete guide for testing the Delta to BigQuery migration with sample data.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Generate Sample Data](#generate-sample-data)
3. [Upload to GCS](#upload-to-gcs)
4. [Create BigQuery Tables](#create-bigquery-tables)
5. [Run Migration Test](#run-migration-test)
6. [Verify Results](#verify-results)
7. [Cleanup](#cleanup)

## Prerequisites

### Local Environment Setup

Install required Python packages:

```bash
pip install pyspark==3.4.0 delta-spark==2.4.0
```

Or use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pyspark==3.4.0 delta-spark==2.4.0
```

### GCP Setup

```bash
# Set your project
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET="your-test-bucket"

gcloud config set project ${PROJECT_ID}

# Create test bucket if needed
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET}

# Create BigQuery dataset
bq mk --dataset --location=${REGION} ${PROJECT_ID}:analytics
```

## Generate Sample Data

### Step 1: Run the Generator Script

```bash
cd test_data

# Generate sample tables (default sizes)
python create_sample_delta_tables.py

# Or with custom sizes
python create_sample_delta_tables.py \
  --output-dir ./my_delta_tables \
  --customers 2000 \
  --orders 10000 \
  --products 1000
```

**Expected Output:**
```
======================================================================
DELTA LAKE SAMPLE DATA GENERATOR
======================================================================

Output directory: ./sample_delta_tables

Creating Spark session with Delta Lake support...
✓ Spark 3.4.0 with Delta Lake ready

Generating 1000 customer records...
✓ Generated customers data with 1000 records

Saving customers to Delta format at ./sample_delta_tables/customers
✓ Delta table saved successfully
  - Parquet files: 1 files
  - Transaction logs: 1 JSON files
  - Location: ./sample_delta_tables/customers

[... similar output for orders and products ...]

======================================================================
✓ ALL SAMPLE TABLES CREATED SUCCESSFULLY!
======================================================================

Summary:
  Customers: 1000 records
  Orders: 5000 records
  Products: 500 records
```

### Step 2: Verify Local Delta Structure

```bash
# Check directory structure
ls -R sample_delta_tables/

# Expected structure:
# sample_delta_tables/
# ├── customers/
# │   ├── _delta_log/
# │   │   └── 00000000000000000000.json
# │   └── part-00000-*.snappy.parquet
# ├── orders/
# │   ├── _delta_log/
# │   │   └── 00000000000000000000.json
# │   └── part-00000-*.snappy.parquet
# └── products/
#     ├── _delta_log/
#     │   └── 00000000000000000000.json
#     └── part-00000-*.snappy.parquet
```

### Step 3: Inspect Delta Logs

```bash
# View Delta transaction log
cat sample_delta_tables/customers/_delta_log/00000000000000000000.json | python -m json.tool

# You should see Delta protocol info and file metadata
```

## Upload to GCS

### Option 1: Upload All Tables

```bash
# Upload all Delta tables to GCS
gsutil -m cp -r sample_delta_tables/* gs://${BUCKET}/delta-tables/

# Verify upload
gsutil ls gs://${BUCKET}/delta-tables/
gsutil ls gs://${BUCKET}/delta-tables/customers/_delta_log/
```

### Option 2: Upload Individual Tables

```bash
# Upload customers table
gsutil -m cp -r sample_delta_tables/customers gs://${BUCKET}/delta-tables/

# Upload orders table
gsutil -m cp -r sample_delta_tables/orders gs://${BUCKET}/delta-tables/

# Upload products table
gsutil -m cp -r sample_delta_tables/products gs://${BUCKET}/delta-tables/
```

### Verify GCS Structure

```bash
# Check all files are uploaded
gsutil ls -r gs://${BUCKET}/delta-tables/

# Expected output should include:
# gs://${BUCKET}/delta-tables/customers/
# gs://${BUCKET}/delta-tables/customers/_delta_log/
# gs://${BUCKET}/delta-tables/customers/_delta_log/00000000000000000000.json
# gs://${BUCKET}/delta-tables/customers/part-*.snappy.parquet
# ... (similar for orders and products)
```

## Create BigQuery Tables

### Option 1: Using bq Command (Recommended)

```bash
# Navigate to test_data directory
cd test_data

# Edit the SQL file to replace project ID
sed -i "s/your-project-id/${PROJECT_ID}/g" bigquery_ddl.sql

# Execute DDL
bq query --use_legacy_sql=false < bigquery_ddl.sql
```

### Option 2: Using BigQuery Console

1. Go to [BigQuery Console](https://console.cloud.google.com/bigquery)
2. Click "Compose New Query"
3. Copy contents from `bigquery_ddl.sql`
4. Replace `your-project-id` with your actual project ID
5. Click "Run"

### Option 3: Create Tables Manually

```bash
# Create customers table
bq mk --table \
  ${PROJECT_ID}:analytics.customers \
  customer_id:INTEGER,first_name:STRING,last_name:STRING,email:STRING,phone:STRING,registration_date:DATE,country:STRING,is_active:BOOLEAN,lifetime_value:FLOAT,created_at:TIMESTAMP

# Create orders table
bq mk --table \
  ${PROJECT_ID}:analytics.orders \
  order_id:INTEGER,customer_id:INTEGER,order_date:DATE,order_amount:FLOAT,status:STRING,payment_method:STRING,shipping_address:STRING,items:STRING,created_at:TIMESTAMP

# Create products table
bq mk --table \
  ${PROJECT_ID}:analytics.products \
  product_id:INTEGER,product_name:STRING,category:STRING,brand:STRING,price:FLOAT,cost:FLOAT,stock_quantity:INTEGER,description:STRING,rating:FLOAT,review_count:INTEGER,is_available:BOOLEAN,tags:STRING,created_at:TIMESTAMP,updated_at:TIMESTAMP
```

### Verify Tables Created

```bash
# List tables in dataset
bq ls ${PROJECT_ID}:analytics

# Show table schema
bq show ${PROJECT_ID}:analytics.customers
bq show ${PROJECT_ID}:analytics.orders
bq show ${PROJECT_ID}:analytics.products
```

## Run Migration Test

### Step 1: Update Migration Config

```bash
cd ..  # Back to root directory

# Create test migration config
cat > config/test_migration_config.json << EOF
[
  {
    "gcs_delta_path": "gs://${BUCKET}/delta-tables/customers",
    "bq_project": "${PROJECT_ID}",
    "bq_dataset": "analytics",
    "bq_table": "customers",
    "temp_bucket": "${BUCKET}-temp"
  },
  {
    "gcs_delta_path": "gs://${BUCKET}/delta-tables/orders",
    "bq_project": "${PROJECT_ID}",
    "bq_dataset": "analytics",
    "bq_table": "orders",
    "temp_bucket": "${BUCKET}-temp"
  },
  {
    "gcs_delta_path": "gs://${BUCKET}/delta-tables/products",
    "bq_project": "${PROJECT_ID}",
    "bq_dataset": "analytics",
    "bq_table": "products",
    "temp_bucket": "${BUCKET}-temp"
  }
]
EOF
```

### Step 2: Update Workflow Script

```bash
# Edit the workflow script
nano scripts/full_migration_workflow.sh

# Update these variables:
# PROJECT_ID="your-project-id"
# BUCKET="your-test-bucket"
# TEMP_BUCKET="your-test-bucket-temp"
# CONFIG_FILE="config/test_migration_config.json"
```

### Step 3: Run Migration

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run complete workflow
./scripts/full_migration_workflow.sh
```

### Alternative: Run Step-by-Step

```bash
# 1. Create cluster
./scripts/setup_dataproc.sh

# 2. Test single table first
# Edit submit_single_job.sh with one table
nano scripts/submit_single_job.sh
./scripts/submit_single_job.sh

# 3. If successful, run batch migration
./scripts/submit_batch_job.sh

# 4. Cleanup
gcloud dataproc clusters delete delta-migration-cluster --region=${REGION} --quiet
```

## Verify Results

### Check Row Counts

```bash
# Check all tables
bq query --use_legacy_sql=false "
SELECT 
  'customers' as table_name, 
  COUNT(*) as row_count 
FROM \`${PROJECT_ID}.analytics.customers\`
UNION ALL
SELECT 
  'orders' as table_name, 
  COUNT(*) as row_count 
FROM \`${PROJECT_ID}.analytics.orders\`
UNION ALL
SELECT 
  'products' as table_name, 
  COUNT(*) as row_count 
FROM \`${PROJECT_ID}.analytics.products\`
"
```

**Expected Output:**
```
+------------+-----------+
| table_name | row_count |
+------------+-----------+
| customers  |      1000 |
| orders     |      5000 |
| products   |    500    |
+------------+-----------+
```

### Verify Data Quality

```bash
# Check customers table
bq query --use_legacy_sql=false "
SELECT 
  customer_id,
  first_name,
  last_name,
  email,
  country,
  is_active,
  lifetime_value
FROM \`${PROJECT_ID}.analytics.customers\`
LIMIT 5
"

# Check orders with nested data
bq query --use_legacy_sql=false "
SELECT 
  order_id,
  customer_id,
  order_amount,
  status,
  shipping_address,
  items
FROM \`${PROJECT_ID}.analytics.orders\`
LIMIT 5
"

# Check products with arrays
bq query --use_legacy_sql=false "
SELECT 
  product_id,
  product_name,
  category,
  price,
  rating,
  tags
FROM \`${PROJECT_ID}.analytics.products\`
LIMIT 5
"
```

### Run Analytics Queries

```bash
# Customer order summary
bq query --use_legacy_sql=false "
SELECT 
  c.country,
  COUNT(DISTINCT c.customer_id) as customers,
  COUNT(o.order_id) as total_orders,
  SUM(o.order_amount) as total_revenue,
  AVG(o.order_amount) as avg_order_value
FROM \`${PROJECT_ID}.analytics.customers\` c
LEFT JOIN \`${PROJECT_ID}.analytics.orders\` o
  ON c.customer_id = o.customer_id
GROUP BY c.country
ORDER BY total_revenue DESC
"

# Product category performance
bq query --use_legacy_sql=false "
SELECT 
  category,
  COUNT(*) as product_count,
  AVG(price) as avg_price,
  AVG(rating) as avg_rating,
  SUM(stock_quantity) as total_stock
FROM \`${PROJECT_ID}.analytics.products\`
GROUP BY category
ORDER BY product_count DESC
"
```

### Check Table Metadata

```bash
# Get table info
bq show --format=prettyjson ${PROJECT_ID}:analytics.customers
bq show --format=prettyjson ${PROJECT_ID}:analytics.orders
bq show --format=prettyjson ${PROJECT_ID}:analytics.products
```

## Cleanup

### Remove Test Data from GCS

```bash
# Delete Delta tables from GCS
gsutil -m rm -r gs://${BUCKET}/delta-tables/

# Delete temp files
gsutil -m rm -r gs://${BUCKET}-temp/delta_migration/
```

### Drop BigQuery Tables

```bash
# Delete specific tables
bq rm -f -t ${PROJECT_ID}:analytics.customers
bq rm -f -t ${PROJECT_ID}:analytics.orders
bq rm -f -t ${PROJECT_ID}:analytics.products

# Or delete entire dataset
bq rm -r -f -d ${PROJECT_ID}:analytics
```

### Remove Local Files

```bash
# Delete local Delta tables
rm -rf test_data/sample_delta_tables/

# Keep the generator script for future use
```

### Delete Dataproc Cluster (if still running)

```bash
# List clusters
gcloud dataproc clusters list --region=${REGION}

# Delete cluster
gcloud dataproc clusters delete delta-migration-cluster \
  --region=${REGION} \
  --quiet
```

## Troubleshooting Test Migration

### Issue: Sample Data Generation Fails

```bash
# Check Python packages
pip list | grep -E "pyspark|delta"

# Reinstall if needed
pip install --upgrade pyspark==3.4.0 delta-spark==2.4.0

# Check Java is installed (required by Spark)
java -version
# If not installed: sudo apt-get install openjdk-11-jdk
```

### Issue: Upload to GCS Fails

```bash
# Check authentication
gcloud auth list

# Check bucket permissions
gsutil iam get gs://${BUCKET}

# Try creating bucket if it doesn't exist
gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET}
```

### Issue: BigQuery Table Creation Fails

```bash
# Check dataset exists
bq ls ${PROJECT_ID}:

# Create dataset if missing
bq mk --dataset --location=${REGION} ${PROJECT_ID}:analytics

# Check permissions
gcloud projects get-iam-policy ${PROJECT_ID}
```

### Issue: Migration Fails to Read Delta

```bash
# Verify Delta structure in GCS
gsutil ls gs://${BUCKET}/delta-tables/customers/_delta_log/

# Check for JSON files
gsutil cat gs://${BUCKET}/delta-tables/customers/_delta_log/00000000000000000000.json

# If missing, regenerate and re-upload
```

## Next Steps

After successful test:

1. **Scale Up**: Generate larger datasets for performance testing
2. **Production Setup**: Use real Delta tables from your data lake
3. **Automation**: Set up scheduled migrations with Cloud Scheduler
4. **Monitoring**: Add alerting and monitoring
5. **Optimization**: Tune cluster size based on test results

## Example: Complete Test Run

```bash
#!/bin/bash
# complete_test_run.sh - Run complete test from start to finish

export PROJECT_ID="my-project"
export REGION="us-central1"
export BUCKET="my-test-bucket"

echo "Step 1: Generate sample data"
python test_data/create_sample_delta_tables.py

echo "Step 2: Upload to GCS"
gsutil -m cp -r sample_delta_tables/* gs://${BUCKET}/delta-tables/

echo "Step 3: Create BigQuery tables"
sed "s/your-project-id/${PROJECT_ID}/g" test_data/bigquery_ddl.sql | \
  bq query --use_legacy_sql=false

echo "Step 4: Run migration"
./scripts/full_migration_workflow.sh

echo "Step 5: Verify"
bq query --use_legacy_sql=false "
SELECT 'customers' as table_name, COUNT(*) as row_count 
FROM \`${PROJECT_ID}.analytics.customers\`
UNION ALL
SELECT 'orders' as table_name, COUNT(*) as row_count 
FROM \`${PROJECT_ID}.analytics.orders\`
UNION ALL
SELECT 'products' as table_name, COUNT(*) as row_count 
FROM \`${PROJECT_ID}.analytics.products\`
"

echo "✓ Test complete!"
```

---

**Last Updated:** November 4, 2025
