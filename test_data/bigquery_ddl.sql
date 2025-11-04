-- bigquery_ddl.sql
-- BigQuery DDL (Data Definition Language) for sample Delta tables
-- These tables match the schema of the sample Delta tables generated

-- ============================================================================
-- CUSTOMERS TABLE
-- ============================================================================

CREATE OR REPLACE TABLE `your-project-id.analytics.customers` (
  customer_id INT64 NOT NULL,
  first_name STRING,
  last_name STRING,
  email STRING,
  phone STRING,
  registration_date DATE,
  country STRING,
  is_active BOOL,
  lifetime_value FLOAT64,
  created_at TIMESTAMP
)
PARTITION BY DATE(registration_date)
CLUSTER BY country, is_active
OPTIONS (
  description = 'Customer information table',
  labels = [("source", "delta_migration"), ("env", "test")]
);

-- Sample query to verify
-- SELECT COUNT(*) as total_customers, country
-- FROM `your-project-id.analytics.customers`
-- GROUP BY country;


-- ============================================================================
-- ORDERS TABLE (with complex types)
-- ============================================================================

CREATE OR REPLACE TABLE `your-project-id.analytics.orders` (
  order_id INT64 NOT NULL,
  customer_id INT64,
  order_date DATE,
  order_amount FLOAT64,
  status STRING,
  payment_method STRING,
  shipping_address STRUCT<
    street STRING,
    city STRING,
    state STRING,
    zip STRING
  >,
  items ARRAY<STRUCT<
    product_id INT64,
    quantity INT64,
    price FLOAT64
  >>,
  created_at TIMESTAMP
)
PARTITION BY DATE(order_date)
CLUSTER BY customer_id, status
OPTIONS (
  description = 'Orders table with nested shipping address and items array',
  labels = [("source", "delta_migration"), ("env", "test")]
);

-- Sample queries to verify
-- SELECT COUNT(*) as total_orders, status
-- FROM `your-project-id.analytics.orders`
-- GROUP BY status;

-- Query nested fields
-- SELECT 
--   order_id,
--   shipping_address.city as city,
--   ARRAY_LENGTH(items) as item_count
-- FROM `your-project-id.analytics.orders`
-- LIMIT 10;


-- ============================================================================
-- PRODUCTS TABLE (with arrays)
-- ============================================================================

CREATE OR REPLACE TABLE `your-project-id.analytics.products` (
  product_id INT64 NOT NULL,
  product_name STRING,
  category STRING,
  brand STRING,
  price FLOAT64,
  cost FLOAT64,
  stock_quantity INT64,
  description STRING,
  rating FLOAT64,
  review_count INT64,
  is_available BOOL,
  tags ARRAY<STRING>,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
CLUSTER BY category, brand, is_available
OPTIONS (
  description = 'Product catalog with tags array',
  labels = [("source", "delta_migration"), ("env", "test")]
);

-- Sample query to verify
-- SELECT 
--   category,
--   COUNT(*) as product_count,
--   AVG(price) as avg_price,
--   AVG(rating) as avg_rating
-- FROM `your-project-id.analytics.products`
-- GROUP BY category
-- ORDER BY product_count DESC;


-- ============================================================================
-- ALTERNATIVE: If migration script converts complex types to JSON strings
-- ============================================================================

-- Use this version if the migration script converts nested types to JSON

CREATE OR REPLACE TABLE `your-project-id.analytics.orders_json` (
  order_id INT64 NOT NULL,
  customer_id INT64,
  order_date DATE,
  order_amount FLOAT64,
  status STRING,
  payment_method STRING,
  shipping_address STRING,  -- JSON string
  items STRING,             -- JSON string
  created_at TIMESTAMP
)
PARTITION BY DATE(order_date)
CLUSTER BY customer_id, status
OPTIONS (
  description = 'Orders table with JSON strings (alternative schema)',
  labels = [("source", "delta_migration"), ("env", "test")]
);

-- Query JSON fields
-- SELECT 
--   order_id,
--   JSON_EXTRACT_SCALAR(shipping_address, '$.city') as city,
--   JSON_EXTRACT(items, '$') as items_json
-- FROM `your-project-id.analytics.orders_json`
-- LIMIT 10;


-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- Customer order summary view
CREATE OR REPLACE VIEW `your-project-id.analytics.customer_order_summary` AS
SELECT 
  c.customer_id,
  c.first_name,
  c.last_name,
  c.email,
  c.country,
  COUNT(o.order_id) as total_orders,
  SUM(o.order_amount) as total_spent,
  AVG(o.order_amount) as avg_order_value,
  MAX(o.order_date) as last_order_date
FROM `your-project-id.analytics.customers` c
LEFT JOIN `your-project-id.analytics.orders` o
  ON c.customer_id = o.customer_id
GROUP BY 
  c.customer_id,
  c.first_name,
  c.last_name,
  c.email,
  c.country;


-- Product performance view
CREATE OR REPLACE VIEW `your-project-id.analytics.product_performance` AS
SELECT 
  p.product_id,
  p.product_name,
  p.category,
  p.brand,
  p.price,
  p.rating,
  p.review_count,
  p.stock_quantity,
  p.is_available
FROM `your-project-id.analytics.products` p
WHERE p.is_available = TRUE
ORDER BY p.rating DESC, p.review_count DESC;


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count all records
-- SELECT 
--   'customers' as table_name, 
--   COUNT(*) as row_count 
-- FROM `your-project-id.analytics.customers`
-- UNION ALL
-- SELECT 
--   'orders' as table_name, 
--   COUNT(*) as row_count 
-- FROM `your-project-id.analytics.orders`
-- UNION ALL
-- SELECT 
--   'products' as table_name, 
--   COUNT(*) as row_count 
-- FROM `your-project-id.analytics.products`;


-- Check data quality
-- SELECT 
--   COUNT(*) as total_customers,
--   COUNT(DISTINCT customer_id) as unique_customers,
--   COUNT(DISTINCT email) as unique_emails,
--   COUNTIF(is_active) as active_customers,
--   COUNTIF(NOT is_active) as inactive_customers
-- FROM `your-project-id.analytics.customers`;


-- ============================================================================
-- GRANT PERMISSIONS (optional)
-- ============================================================================

-- Grant read access to a specific user
-- GRANT `roles/bigquery.dataViewer` 
-- ON TABLE `your-project-id.analytics.customers`
-- TO "user:someone@example.com";

-- Grant read access to a service account
-- GRANT `roles/bigquery.dataViewer` 
-- ON TABLE `your-project-id.analytics.customers`
-- TO "serviceAccount:migration-sa@your-project-id.iam.gserviceaccount.com";


-- ============================================================================
-- TABLE DESCRIPTIONS
-- ============================================================================

/*
TABLE: customers
- Primary key: customer_id
- Partitioned by: registration_date (for efficient date-range queries)
- Clustered by: country, is_active (for efficient filtering)
- Row count: ~1,000 records

TABLE: orders
- Primary key: order_id
- Foreign key: customer_id (references customers)
- Partitioned by: order_date
- Clustered by: customer_id, status
- Complex types: nested STRUCT for address, ARRAY of STRUCT for items
- Row count: ~5,000 records

TABLE: products
- Primary key: product_id
- Clustered by: category, brand, is_available
- Complex types: ARRAY of strings for tags
- Row count: ~500 records

VIEWS:
- customer_order_summary: Aggregates customer orders
- product_performance: Shows top-rated available products
*/


-- ============================================================================
-- COST OPTIMIZATION TIPS
-- ============================================================================

/*
1. PARTITIONING:
   - All tables are partitioned by date columns
   - Always filter by partition column in WHERE clause
   - Example: WHERE order_date >= '2025-01-01'

2. CLUSTERING:
   - Tables are clustered by frequently filtered columns
   - Benefits queries with WHERE, GROUP BY, JOIN on these columns

3. QUERY OPTIMIZATION:
   - Use SELECT with specific columns, not SELECT *
   - Use partitioning and clustering filters
   - Limit result size when testing

4. STORAGE:
   - Enable table expiration if data is temporary
   - Use time-partitioning with automatic expiration
   - Compress large text fields

Example optimized query:
SELECT customer_id, order_amount, status
FROM `your-project-id.analytics.orders`
WHERE order_date >= '2025-01-01'  -- Uses partition pruning
  AND status = 'delivered'         -- Uses clustering
LIMIT 1000;
*/
