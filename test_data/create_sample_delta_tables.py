#!/usr/bin/env python3
"""
create_sample_delta_tables.py

Creates sample Delta Lake tables with realistic data for testing migration to BigQuery.
Generates parquet files and Delta transaction logs (_delta_log/*.json files).
"""

import json
import os
import sys
from datetime import datetime, timedelta
import random
import string

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import *
    from pyspark.sql.functions import col, lit, current_timestamp
    from delta import configure_spark_with_delta_pip
except ImportError:
    print("ERROR: Required packages not installed!")
    print("\nInstall with:")
    print("  pip install pyspark==3.4.0 delta-spark==2.4.0")
    sys.exit(1)


def create_spark_session():
    """Create Spark session with Delta support"""
    print("Creating Spark session with Delta Lake support...")
    
    builder = SparkSession.builder \
        .appName("DeltaSampleGenerator") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .master("local[*]")
    
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"✓ Spark {spark.version} with Delta Lake ready")
    return spark


def generate_customers_data(spark, num_records=1000):
    """Generate sample customers data"""
    print(f"\nGenerating {num_records} customer records...")
    
    data = []
    for i in range(num_records):
        customer_id = i + 1
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        data.append({
            "customer_id": customer_id,
            "first_name": random.choice(first_names),
            "last_name": random.choice(last_names),
            "email": f"customer{customer_id}@example.com",
            "phone": f"+1-555-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "registration_date": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
            "country": random.choice(["USA", "Canada", "UK", "Germany", "France"]),
            "is_active": random.choice([True, False]),
            "lifetime_value": round(random.uniform(100, 10000), 2),
            "created_at": datetime.now().isoformat()
        })
    
    schema = StructType([
        StructField("customer_id", IntegerType(), False),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("registration_date", StringType(), True),
        StructField("country", StringType(), True),
        StructField("is_active", BooleanType(), True),
        StructField("lifetime_value", DoubleType(), True),
        StructField("created_at", StringType(), True)
    ])
    
    df = spark.createDataFrame(data, schema)
    print(f"✓ Generated customers data with {df.count()} records")
    return df


def generate_orders_data(spark, num_records=5000):
    """Generate sample orders data"""
    print(f"\nGenerating {num_records} order records...")
    
    data = []
    for i in range(num_records):
        order_id = i + 1
        customer_id = random.randint(1, 1000)
        
        data.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d"),
            "order_amount": round(random.uniform(10, 1000), 2),
            "status": random.choice(["pending", "processing", "shipped", "delivered", "cancelled"]),
            "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
            "shipping_address": {
                "street": f"{random.randint(100, 9999)} Main St",
                "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                "zip": f"{random.randint(10000, 99999)}"
            },
            "items": [
                {
                    "product_id": random.randint(1, 100),
                    "quantity": random.randint(1, 5),
                    "price": round(random.uniform(10, 200), 2)
                }
                for _ in range(random.randint(1, 3))
            ],
            "created_at": datetime.now().isoformat()
        })
    
    schema = StructType([
        StructField("order_id", IntegerType(), False),
        StructField("customer_id", IntegerType(), True),
        StructField("order_date", StringType(), True),
        StructField("order_amount", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("payment_method", StringType(), True),
        StructField("shipping_address", StructType([
            StructField("street", StringType(), True),
            StructField("city", StringType(), True),
            StructField("state", StringType(), True),
            StructField("zip", StringType(), True)
        ]), True),
        StructField("items", ArrayType(StructType([
            StructField("product_id", IntegerType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("price", DoubleType(), True)
        ])), True),
        StructField("created_at", StringType(), True)
    ])
    
    df = spark.createDataFrame(data, schema)
    print(f"✓ Generated orders data with {df.count()} records")
    return df


def generate_products_data(spark, num_records=500):
    """Generate sample products data"""
    print(f"\nGenerating {num_records} product records...")
    
    categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
    brands = ["BrandA", "BrandB", "BrandC", "BrandD", "BrandE"]
    
    data = []
    for i in range(num_records):
        product_id = i + 1
        
        data.append({
            "product_id": product_id,
            "product_name": f"Product {product_id}",
            "category": random.choice(categories),
            "brand": random.choice(brands),
            "price": round(random.uniform(9.99, 999.99), 2),
            "cost": round(random.uniform(5.0, 500.0), 2),
            "stock_quantity": random.randint(0, 1000),
            "description": f"High quality product number {product_id} with excellent features",
            "rating": round(random.uniform(1.0, 5.0), 1),
            "review_count": random.randint(0, 500),
            "is_available": random.choice([True, False]),
            "tags": random.sample(["new", "sale", "featured", "popular", "clearance"], k=random.randint(0, 3)),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
    
    schema = StructType([
        StructField("product_id", IntegerType(), False),
        StructField("product_name", StringType(), True),
        StructField("category", StringType(), True),
        StructField("brand", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("cost", DoubleType(), True),
        StructField("stock_quantity", IntegerType(), True),
        StructField("description", StringType(), True),
        StructField("rating", DoubleType(), True),
        StructField("review_count", IntegerType(), True),
        StructField("is_available", BooleanType(), True),
        StructField("tags", ArrayType(StringType()), True),
        StructField("created_at", StringType(), True),
        StructField("updated_at", StringType(), True)
    ])
    
    df = spark.createDataFrame(data, schema)
    print(f"✓ Generated products data with {df.count()} records")
    return df


def save_as_delta(df, path, table_name):
    """Save DataFrame as Delta table"""
    print(f"\nSaving {table_name} to Delta format at {path}")
    
    # Write as Delta
    df.write.format("delta").mode("overwrite").save(path)
    
    # Verify Delta structure
    delta_log_path = os.path.join(path, "_delta_log")
    if os.path.exists(delta_log_path):
        log_files = os.listdir(delta_log_path)
        json_files = [f for f in log_files if f.endswith('.json')]
        print(f"✓ Delta table saved successfully")
        print(f"  - Parquet files: {len([f for f in os.listdir(path) if f.endswith('.parquet')])} files")
        print(f"  - Transaction logs: {len(json_files)} JSON files")
        print(f"  - Location: {path}")
    else:
        print(f"⚠ Warning: Delta log not found at {delta_log_path}")


def create_sample_tables(output_dir="./sample_delta_tables"):
    """Main function to create all sample tables"""
    print("=" * 70)
    print("DELTA LAKE SAMPLE DATA GENERATOR")
    print("=" * 70)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Generate and save customers table
        customers_df = generate_customers_data(spark, num_records=1000)
        save_as_delta(customers_df, f"{output_dir}/customers", "customers")
        
        # Generate and save orders table
        orders_df = generate_orders_data(spark, num_records=5000)
        save_as_delta(orders_df, f"{output_dir}/orders", "orders")
        
        # Generate and save products table
        products_df = generate_products_data(spark, num_records=500)
        save_as_delta(products_df, f"{output_dir}/products", "products")
        
        print("\n" + "=" * 70)
        print("✓ ALL SAMPLE TABLES CREATED SUCCESSFULLY!")
        print("=" * 70)
        
        print("\nSummary:")
        print(f"  Customers: {customers_df.count()} records")
        print(f"  Orders: {orders_df.count()} records")
        print(f"  Products: {products_df.count()} records")
        
        print(f"\nDelta tables saved to: {output_dir}/")
        print("\nNext steps:")
        print("1. Upload to GCS:")
        print(f"   gsutil -m cp -r {output_dir}/* gs://YOUR-BUCKET/delta-tables/")
        print("\n2. Create BigQuery tables:")
        print("   Use the DDL scripts in bigquery_ddl.sql")
        print("\n3. Run migration:")
        print("   Update migration config and run the migration script")
        
    finally:
        spark.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample Delta tables for testing")
    parser.add_argument(
        "--output-dir",
        default="./sample_delta_tables",
        help="Output directory for Delta tables (default: ./sample_delta_tables)"
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=1000,
        help="Number of customer records (default: 1000)"
    )
    parser.add_argument(
        "--orders",
        type=int,
        default=5000,
        help="Number of order records (default: 5000)"
    )
    parser.add_argument(
        "--products",
        type=int,
        default=500,
        help="Number of product records (default: 500)"
    )
    
    args = parser.parse_args()
    
    print(f"Configuration:")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Customers: {args.customers}")
    print(f"  Orders: {args.orders}")
    print(f"  Products: {args.products}")
    print()
    
    create_sample_tables(args.output_dir)
