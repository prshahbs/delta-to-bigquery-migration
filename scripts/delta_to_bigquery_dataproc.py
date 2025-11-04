# delta_to_bigquery_dataproc.py
"""
Delta to BigQuery Migration Script for Dataproc
Optimized for running on Google Cloud Dataproc clusters
"""

import argparse
import logging
from typing import List, Optional
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import col, to_json, struct
from google.cloud import bigquery
import json
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/delta_migration.log')
    ]
)
logger = logging.getLogger(__name__)


class DataprocDeltaMigrator:
    """Migrates Delta Lake tables from GCS to BigQuery using Dataproc"""
    
    def __init__(
        self,
        gcs_delta_path: str,
        bq_project: str,
        bq_dataset: str,
        bq_table: str,
        temp_bucket: str,
        spark: Optional[SparkSession] = None
    ):
        self.gcs_delta_path = gcs_delta_path
        self.bq_project = bq_project
        self.bq_dataset = bq_dataset
        self.bq_table = bq_table
        self.temp_bucket = temp_bucket
        
        # Use existing Spark session or create new one
        self.spark = spark if spark else self._get_spark_session()
        
        # Initialize BigQuery client (uses Application Default Credentials on Dataproc)
        self.bq_client = bigquery.Client(project=bq_project)
    
    def _get_spark_session(self) -> SparkSession:
        """Get or create Spark session"""
        spark = SparkSession.builder.getOrCreate()
        logger.info(f"Using Spark version: {spark.version}")
        return spark
    
    def read_delta_table(self):
        """Read Delta table from GCS"""
        logger.info(f"Reading Delta table from {self.gcs_delta_path}")
        
        try:
            # Read Delta format
            df = self.spark.read.format("delta").load(self.gcs_delta_path)
            
            row_count = df.count()
            logger.info(f"Successfully read {row_count:,} rows from Delta table")
            logger.info(f"Schema: {df.schema.simpleString()}")
            logger.info(f"Partitions: {df.rdd.getNumPartitions()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading Delta table: {str(e)}")
            raise
    
    def get_delta_table_info(self):
        """Get metadata about the Delta table"""
        logger.info("Retrieving Delta table metadata...")
        
        try:
            delta_table = self.spark.sql(f"DESCRIBE DETAIL delta.`{self.gcs_delta_path}`")
            table_info = delta_table.collect()[0].asDict()
            
            logger.info(f"Delta format version: {table_info.get('format')}")
            logger.info(f"Number of files: {table_info.get('numFiles')}")
            logger.info(f"Size in bytes: {table_info.get('sizeInBytes'):,}")
            logger.info(f"Partition columns: {table_info.get('partitionColumns')}")
            
            return table_info
            
        except Exception as e:
            logger.warning(f"Could not retrieve Delta table metadata: {str(e)}")
            return None
    
    def optimize_dataframe(self, df):
        """Optimize DataFrame for BigQuery write"""
        logger.info("Optimizing DataFrame for BigQuery...")
        
        # Convert complex types to JSON strings
        for field in df.schema.fields:
            field_type = field.dataType.simpleString().lower()
            
            if 'array' in field_type or 'struct' in field_type or 'map' in field_type:
                logger.info(f"Converting complex field '{field.name}' to JSON string")
                df = df.withColumn(field.name, to_json(col(field.name)))
        
        # Repartition for optimal BigQuery write
        # BigQuery works best with fewer, larger files
        optimal_partitions = max(1, df.rdd.getNumPartitions() // 4)
        logger.info(f"Repartitioning to {optimal_partitions} partitions")
        df = df.coalesce(optimal_partitions)
        
        return df
    
    def write_to_bigquery_connector(self, df, mode='overwrite'):
        """Write using Spark BigQuery connector"""
        logger.info(f"Writing to BigQuery using connector method")
        
        try:
            full_table_name = f"{self.bq_project}:{self.bq_dataset}.{self.bq_table}"
            
            # Optimize DataFrame
            df = self.optimize_dataframe(df)
            
            # Write to BigQuery
            df.write \
                .format("bigquery") \
                .option("table", full_table_name) \
                .option("temporaryGcsBucket", self.temp_bucket) \
                .option("writeMethod", "direct") \
                .mode(mode) \
                .save()
            
            logger.info(f"Successfully wrote data to BigQuery table {full_table_name}")
            
        except Exception as e:
            logger.error(f"Error writing to BigQuery: {str(e)}")
            raise
    
    def write_via_parquet_intermediate(self, df, mode='overwrite'):
        """
        Two-step approach: Write to Parquet, then load to BigQuery
        More reliable for very large datasets
        """
        logger.info("Using Parquet intermediate approach")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        parquet_path = f"gs://{self.temp_bucket}/delta_migration/{self.bq_table}_{timestamp}"
        
        try:
            # Step 1: Write optimized Parquet
            logger.info(f"Writing to Parquet: {parquet_path}")
            
            # Optimize DataFrame
            df = self.optimize_dataframe(df)
            
            df.write \
                .format("parquet") \
                .option("compression", "snappy") \
                .mode("overwrite") \
                .save(parquet_path)
            
            logger.info("Parquet write completed")
            
            # Step 2: Load to BigQuery using bq load
            logger.info("Loading Parquet to BigQuery...")
            
            table_ref = f"{self.bq_project}.{self.bq_dataset}.{self.bq_table}"
            
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.PARQUET,
                write_disposition=(
                    bigquery.WriteDisposition.WRITE_TRUNCATE if mode == 'overwrite'
                    else bigquery.WriteDisposition.WRITE_APPEND
                ),
                autodetect=True,
                max_bad_records=0
            )
            
            load_job = self.bq_client.load_table_from_uri(
                f"{parquet_path}/*.parquet",
                table_ref,
                job_config=job_config
            )
            
            # Wait for job completion
            load_job.result()
            
            destination_table = self.bq_client.get_table(table_ref)
            logger.info(f"Loaded {destination_table.num_rows:,} rows to {table_ref}")
            
            return parquet_path
            
        except Exception as e:
            logger.error(f"Error in Parquet intermediate write: {str(e)}")
            raise
    
    def cleanup_temp_files(self, path: str):
        """Clean up temporary files"""
        logger.info(f"Cleaning up temporary files at {path}")
        
        try:
            hadoop_conf = self.spark.sparkContext._jsc.hadoopConfiguration()
            fs = self.spark.sparkContext._jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)
            hadoop_path = self.spark.sparkContext._jvm.org.apache.hadoop.fs.Path(path)
            
            if fs.exists(hadoop_path):
                fs.delete(hadoop_path, True)
                logger.info("Cleanup completed")
            else:
                logger.info("No files to clean up")
                
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")
    
    def verify_migration(self):
        """Verify migration by comparing row counts"""
        logger.info("Verifying migration...")
        
        try:
            # Delta count
            delta_df = self.read_delta_table()
            delta_count = delta_df.count()
            
            # BigQuery count
            query = f"""
                SELECT COUNT(*) as row_count
                FROM `{self.bq_project}.{self.bq_dataset}.{self.bq_table}`
            """
            bq_result = self.bq_client.query(query).result()
            bq_count = list(bq_result)[0]['row_count']
            
            logger.info(f"Delta table rows: {delta_count:,}")
            logger.info(f"BigQuery table rows: {bq_count:,}")
            
            if delta_count == bq_count:
                logger.info("✓ Verification successful: Row counts match!")
                return True
            else:
                diff = abs(delta_count - bq_count)
                logger.warning(f"✗ Row count mismatch! Difference: {diff:,} rows")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return False
    
    def migrate(self, method='parquet', mode='overwrite', verify=True, cleanup=True):
        """
        Execute complete migration
        
        Args:
            method: 'connector' or 'parquet'
            mode: 'overwrite' or 'append'
            verify: Verify after migration
            cleanup: Clean up temporary files
        """
        logger.info("=" * 80)
        logger.info("DELTA TO BIGQUERY MIGRATION - DATAPROC")
        logger.info("=" * 80)
        logger.info(f"Source Delta: {self.gcs_delta_path}")
        logger.info(f"Target BigQuery: {self.bq_project}.{self.bq_dataset}.{self.bq_table}")
        logger.info(f"Method: {method}")
        logger.info(f"Mode: {mode}")
        logger.info(f"Temp Bucket: {self.temp_bucket}")
        
        start_time = datetime.now()
        temp_path = None
        
        try:
            # Get table info
            self.get_delta_table_info()
            
            # Read Delta table
            df = self.read_delta_table()
            
            # Cache DataFrame for reuse
            df.cache()
            
            # Write to BigQuery
            if method == 'connector':
                self.write_to_bigquery_connector(df, mode=mode)
            elif method == 'parquet':
                temp_path = self.write_via_parquet_intermediate(df, mode=mode)
            else:
                raise ValueError(f"Unknown method: {method}. Use 'connector' or 'parquet'")
            
            # Unpersist cache
            df.unpersist()
            
            # Verify
            if verify:
                verification_success = self.verify_migration()
                if not verification_success:
                    logger.warning("Migration completed but verification failed!")
            
            # Cleanup
            if cleanup and temp_path and method == 'parquet':
                self.cleanup_temp_files(temp_path)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info(f"✓ Migration completed successfully in {duration:.2f} seconds")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Migration failed: {str(e)}")
            logger.exception("Full traceback:")
            return False


def batch_migrate(config_file: str, method='parquet', mode='overwrite'):
    """Migrate multiple tables from config file"""
    logger.info(f"Loading batch configuration from {config_file}")
    
    with open(config_file, 'r') as f:
        tables = json.load(f)
    
    logger.info(f"Found {len(tables)} tables to migrate")
    
    # Get Spark session once
    spark = SparkSession.builder.getOrCreate()
    
    results = []
    
    for idx, table_config in enumerate(tables, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing table {idx}/{len(tables)}: {table_config['bq_table']}")
        logger.info(f"{'='*80}")
        
        try:
            migrator = DataprocDeltaMigrator(
                gcs_delta_path=table_config['gcs_delta_path'],
                bq_project=table_config['bq_project'],
                bq_dataset=table_config['bq_dataset'],
                bq_table=table_config['bq_table'],
                temp_bucket=table_config['temp_bucket'],
                spark=spark
            )
            
            success = migrator.migrate(method=method, mode=mode)
            
            results.append({
                'table': table_config['bq_table'],
                'status': 'SUCCESS' if success else 'FAILED'
            })
            
        except Exception as e:
            logger.error(f"Failed to migrate {table_config['bq_table']}: {str(e)}")
            results.append({
                'table': table_config['bq_table'],
                'status': 'FAILED',
                'error': str(e)
            })
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("BATCH MIGRATION SUMMARY")
    logger.info("=" * 80)
    
    for result in results:
        symbol = "✓" if result['status'] == 'SUCCESS' else "✗"
        logger.info(f"{symbol} {result['table']}: {result['status']}")
        if 'error' in result:
            logger.info(f"  Error: {result['error']}")
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    logger.info(f"\nCompleted: {success_count}/{len(results)} tables migrated successfully")
    
    spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Migrate Delta tables to BigQuery on Dataproc'
    )
    
    parser.add_argument('--delta-path', help='GCS path to Delta table')
    parser.add_argument('--bq-project', help='BigQuery project ID')
    parser.add_argument('--bq-dataset', help='BigQuery dataset')
    parser.add_argument('--bq-table', help='BigQuery table name')
    parser.add_argument('--temp-bucket', help='GCS temp bucket')
    parser.add_argument(
        '--method',
        choices=['connector', 'parquet'],
        default='parquet',
        help='Migration method'
    )
    parser.add_argument(
        '--mode',
        choices=['overwrite', 'append'],
        default='overwrite',
        help='Write mode'
    )
    parser.add_argument('--config-file', help='JSON config for batch migration')
    parser.add_argument('--no-verify', action='store_true', help='Skip verification')
    parser.add_argument('--no-cleanup', action='store_true', help='Keep temp files')
    
    args = parser.parse_args()
    
    if args.config_file:
        batch_migrate(args.config_file, method=args.method, mode=args.mode)
    else:
        if not all([args.delta_path, args.bq_project, args.bq_dataset, 
                   args.bq_table, args.temp_bucket]):
            parser.error("Single table migration requires: delta-path, bq-project, "
                        "bq-dataset, bq-table, temp-bucket")
        
        migrator = DataprocDeltaMigrator(
            gcs_delta_path=args.delta_path,
            bq_project=args.bq_project,
            bq_dataset=args.bq_dataset,
            bq_table=args.bq_table,
            temp_bucket=args.temp_bucket
        )
        
        migrator.migrate(
            method=args.method,
            mode=args.mode,
            verify=not args.no_verify,
            cleanup=not args.no_cleanup
        )
