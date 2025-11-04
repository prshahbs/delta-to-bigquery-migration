# Quick Test Reference Card

## 🚀 Quick Test (5 Commands)

```bash
# 1. Generate sample Delta tables
cd test_data
pip install -r requirements_test.txt
python create_sample_delta_tables.py

# 2. Upload to GCS
export PROJECT_ID="your-project"
export BUCKET="your-bucket"
gsutil -m cp -r sample_delta_tables/* gs://${BUCKET}/delta-tables/

# 3. Create BigQuery tables
sed "s/your-project-id/${PROJECT_ID}/g" bigquery_ddl.sql | bq query --use_legacy_sql=false

# 4. Run migration
cd ..
./scripts/full_migration_workflow.sh

# 5. Verify
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`${PROJECT_ID}.analytics.customers\`"
```

## 📊 Sample Data Overview

| Table     | Records | Features                           |
|-----------|---------|----------------------------------- |
| customers | 1,000   | Basic fields, partitioned by date |
| orders    | 5,000   | Nested STRUCT + ARRAY              |
| products  | 500     | ARRAY of tags                      |

## 🔍 Quick Verification Queries

```sql
-- Row counts
SELECT 'customers', COUNT(*) FROM `project.analytics.customers`
UNION ALL
SELECT 'orders', COUNT(*) FROM `project.analytics.orders`
UNION ALL
SELECT 'products', COUNT(*) FROM `project.analytics.products`;

-- Sample data
SELECT * FROM `project.analytics.customers` LIMIT 5;
SELECT * FROM `project.analytics.orders` LIMIT 5;
SELECT * FROM `project.analytics.products` LIMIT 5;
```

## 📁 Delta Structure

```
sample_delta_tables/
├── customers/
│   ├── _delta_log/
│   │   └── 00000000000000000000.json  ← Transaction log
│   └── part-*.parquet                  ← Data files
├── orders/
└── products/
```

## 🎯 Key Files

| File                              | Purpose                      |
|-----------------------------------|------------------------------|
| `create_sample_delta_tables.py`  | Generate test data           |
| `bigquery_ddl.sql`                | Create BQ tables             |
| `TESTING_GUIDE.md`                | Complete testing guide       |
| `requirements_test.txt`           | Python dependencies          |

## ⚡ Troubleshooting

**Delta generation fails:**
```bash
pip install --upgrade pyspark==3.4.0 delta-spark==2.4.0
```

**Upload fails:**
```bash
gcloud auth login
gsutil mb gs://${BUCKET}
```

**BQ table creation fails:**
```bash
bq mk --dataset ${PROJECT_ID}:analytics
```

**Migration fails:**
```bash
# Check Delta structure
gsutil ls gs://${BUCKET}/delta-tables/customers/_delta_log/

# Check BQ tables exist
bq ls ${PROJECT_ID}:analytics
```

## 🧹 Cleanup

```bash
# Remove from GCS
gsutil -m rm -r gs://${BUCKET}/delta-tables/

# Remove from BigQuery
bq rm -r -f -d ${PROJECT_ID}:analytics

# Remove local files
rm -rf test_data/sample_delta_tables/
```

## 💡 Customization

```bash
# Generate more data
python create_sample_delta_tables.py \
  --customers 10000 \
  --orders 50000 \
  --products 5000

# Change output directory
python create_sample_delta_tables.py \
  --output-dir /path/to/custom/location
```

## 📈 Expected Times

| Action          | Time     |
|-----------------|----------|
| Generate data   | 1-2 min  |
| Upload to GCS   | 30 sec   |
| Create BQ tables| 10 sec   |
| Run migration   | 5-10 min |
| Total           | ~10 min  |

---

For detailed instructions, see **TESTING_GUIDE.md**
