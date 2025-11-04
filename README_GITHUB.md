# Delta to BigQuery Migration Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Spark 3.4+](https://img.shields.io/badge/spark-3.4+-orange.svg)](https://spark.apache.org/)

A production-ready solution for migrating Delta Lake tables from Google Cloud Storage to BigQuery using Dataproc.

## 🌟 Features

- ✅ **Complete Migration Solution** - Scripts, documentation, and test data included
- ✅ **Production Ready** - Error handling, logging, verification, and cleanup
- ✅ **Two Migration Methods** - Direct connector and Parquet intermediate
- ✅ **Batch Processing** - Migrate multiple tables at once
- ✅ **Test Data Generator** - Create sample Delta tables for testing
- ✅ **Schema Mapping** - Automatic type conversion from Delta to BigQuery
- ✅ **Complex Types Support** - Handles STRUCT, ARRAY, and nested types
- ✅ **Well Documented** - 70+ KB of guides and documentation

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Delta Lake tables in Google Cloud Storage
- Python 3.8+ (for local testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/delta-to-bigquery-migration.git
cd delta-to-bigquery-migration

# Make scripts executable
chmod +x scripts/*.sh
```

### Test with Sample Data (5 minutes)

```bash
# 1. Generate sample Delta tables
cd test_data
pip install -r requirements_test.txt
python create_sample_delta_tables.py

# 2. Upload to GCS
export BUCKET="your-test-bucket"
gsutil -m cp -r sample_delta_tables/* gs://${BUCKET}/delta-tables/

# 3. Create BigQuery tables
export PROJECT_ID="your-project-id"
sed "s/your-project-id/${PROJECT_ID}/g" bigquery_ddl.sql | \
  bq query --use_legacy_sql=false

# 4. Run migration
cd ..
./scripts/full_migration_workflow.sh

# 5. Verify
bq query "SELECT COUNT(*) FROM \`${PROJECT_ID}.analytics.customers\`"
```

### Production Migration

```bash
# 1. Edit configuration
nano scripts/full_migration_workflow.sh
# Update PROJECT_ID, BUCKET, REGION

# 2. Update table config
nano config/migration_config.json
# Add your Delta table paths

# 3. Run migration
./scripts/full_migration_workflow.sh
```

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Complete documentation (this file) |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute getting started guide |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |
| [test_data/TESTING_GUIDE.md](test_data/TESTING_GUIDE.md) | Detailed testing instructions |
| [test_data/QUICK_TEST_REFERENCE.md](test_data/QUICK_TEST_REFERENCE.md) | Quick command reference |

## 📁 Project Structure

```
delta-to-bigquery-migration/
├── README.md                          # Main documentation
├── QUICKSTART.md                      # Quick start guide
├── TROUBLESHOOTING.md                 # Troubleshooting guide
├── LICENSE                            # MIT License
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Git ignore patterns
│
├── config/
│   └── migration_config.json         # Batch migration configuration
│
├── scripts/
│   ├── delta_to_bigquery_dataproc.py # Main migration script
│   ├── setup_dataproc.sh             # Cluster creation
│   ├── submit_single_job.sh          # Single table migration
│   ├── submit_batch_job.sh           # Batch migration
│   └── full_migration_workflow.sh    # Complete workflow (recommended)
│
└── test_data/
    ├── create_sample_delta_tables.py # Sample data generator
    ├── bigquery_ddl.sql              # BigQuery DDL
    ├── TESTING_GUIDE.md              # Testing documentation
    ├── QUICK_TEST_REFERENCE.md       # Quick reference
    └── requirements_test.txt         # Test dependencies
```

## 🎯 Use Cases

- Migrate data from Databricks/Spark to BigQuery
- Move Delta Lake tables to Google Cloud
- One-time data lake migration
- Scheduled incremental loads
- Cross-platform data consolidation

## 💰 Cost Estimates

| Data Size | Workers | Time | Estimated Cost |
|-----------|---------|------|----------------|
| < 100GB   | 2       | ~10 min | ~$1-2 |
| 100GB-1TB | 5       | ~1-2 hrs | ~$10-20 |
| 1TB-10TB  | 10-20   | ~4-8 hrs | ~$100-300 |

*Costs include Dataproc cluster and BigQuery storage*

## 🔧 Configuration

### Single Table Migration

Edit `scripts/submit_single_job.sh`:

```bash
DELTA_PATH="gs://bucket/delta-tables/customers"
BQ_DATASET="analytics"
BQ_TABLE="customers"
METHOD="parquet"  # or "connector"
MODE="overwrite"  # or "append"
```

### Batch Migration

Edit `config/migration_config.json`:

```json
[
  {
    "gcs_delta_path": "gs://bucket/delta-tables/table1",
    "bq_project": "project-id",
    "bq_dataset": "dataset",
    "bq_table": "table1",
    "temp_bucket": "temp-bucket"
  }
]
```

## 🧪 Sample Data

The included test data generator creates:

- **Customers** (1,000 records) - Basic fields
- **Orders** (5,000 records) - Nested STRUCT + ARRAY
- **Products** (500 records) - ARRAY of tags

Perfect for testing schema mapping and complex types!

## 🛠️ Migration Methods

### Method 1: Parquet Intermediate (Recommended)

Best for large datasets and production workloads.

```bash
--method parquet
```

**How it works:**
1. Read Delta table from GCS
2. Write optimized Parquet to temp location
3. Load Parquet into BigQuery
4. Clean up temp files

### Method 2: Direct Connector

Best for smaller datasets (< 500GB).

```bash
--method connector
```

**How it works:**
1. Read Delta table from GCS
2. Write directly to BigQuery using Spark connector

## 📊 What Gets Migrated

- ✅ All Delta Lake data (parquet files)
- ✅ Transaction history (_delta_log)
- ✅ Schema and data types
- ✅ Nested structures (STRUCT)
- ✅ Arrays (ARRAY)
- ✅ Partitions (converted to BigQuery partitions)

## ⚙️ Architecture

```
┌─────────────────┐
│  Delta Tables   │
│  in GCS         │
│ (parquet + log) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dataproc      │
│   (Spark)       │
│   + Migration   │
│   Script        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   BigQuery      │
│   Tables        │
└─────────────────┘
```

## 🔐 Security

- Uses Google Cloud IAM for authentication
- Service account credentials supported
- No data leaves Google Cloud (GCS → Dataproc → BigQuery)
- Temporary files cleaned up automatically

## 🚨 Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

**Quick fixes:**

```bash
# Permission issues
gcloud auth login
gcloud auth application-default login

# Cluster issues
gcloud compute project-info describe --project=${PROJECT_ID}

# Delta not found
gsutil ls gs://bucket/delta-tables/table/_delta_log/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Apache Spark and Delta Lake communities
- Google Cloud Dataproc and BigQuery teams
- All contributors and users

## 📧 Support

- 📚 Check the [documentation](README.md)
- 🐛 Report issues on [GitHub Issues](https://github.com/YOUR-USERNAME/delta-to-bigquery-migration/issues)
- 💬 Discussion on [GitHub Discussions](https://github.com/YOUR-USERNAME/delta-to-bigquery-migration/discussions)

## ⭐ Star History

If this project helped you, please consider giving it a star!

---

**Made with ❤️ for the data engineering community**
