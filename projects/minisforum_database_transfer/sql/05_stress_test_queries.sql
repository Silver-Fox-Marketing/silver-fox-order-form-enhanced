-- Stress test queries to validate database performance
-- Run these after loading sample data to ensure optimal performance

-- Test 1: Bulk insert performance (simulating daily 195MB import)
EXPLAIN ANALYZE
INSERT INTO raw_vehicle_data (
    vin, stock, type, year, make, model, trim, ext_color, 
    status, price, body_style, fuel_type, msrp, date_in_stock,
    street_address, locality, postal_code, region, country, 
    location, vehicle_url
)
SELECT 
    'TEST' || generate_series || substr(md5(random()::text), 1, 13) as vin,
    'STK' || generate_series as stock,
    CASE WHEN random() < 0.3 THEN 'New' ELSE 'Used' END as type,
    2020 + floor(random() * 5)::int as year,
    (ARRAY['Ford', 'Chevrolet', 'Toyota', 'Honda', 'Nissan'])[floor(random() * 5 + 1)] as make,
    (ARRAY['F-150', 'Silverado', 'Camry', 'Accord', 'Altima'])[floor(random() * 5 + 1)] as model,
    'Trim ' || floor(random() * 10) as trim,
    (ARRAY['Black', 'White', 'Silver', 'Red', 'Blue'])[floor(random() * 5 + 1)] as ext_color,
    (ARRAY['Available', 'In-Transit', 'Sold'])[floor(random() * 3 + 1)] as status,
    15000 + floor(random() * 50000) as price,
    'SUV' as body_style,
    'Gasoline' as fuel_type,
    20000 + floor(random() * 60000) as msrp,
    CURRENT_DATE - (random() * 90)::int as date_in_stock,
    '123 Main St' as street_address,
    'St. Louis' as locality,
    '63101' as postal_code,
    'MO' as region,
    'USA' as country,
    'dealership_' || (floor(random() * 39) + 1) as location,
    'https://example.com/vehicle/' || generate_series as vehicle_url
FROM generate_series(1, 100000);  -- Simulating ~100k records

-- Test 2: Normalization process performance
EXPLAIN ANALYZE
INSERT INTO normalized_vehicle_data (
    raw_data_id, vin, stock, vehicle_condition, year, make, model, 
    trim, status, price, msrp, date_in_stock, location, vehicle_url
)
SELECT 
    r.id,
    r.vin,
    r.stock,
    CASE 
        WHEN r.type IN ('Certified Used', 'Certified Pre-Owned', 'Certified') THEN 'cpo'
        WHEN r.type IN ('Used', 'Pre-Owned', 'pre-owned') THEN 'po'
        WHEN r.type IN ('New', 'new') THEN 'new'
        WHEN r.status IN ('In-transit', 'In-Transit', 'Arriving Soon') THEN 'offlot'
        ELSE 'onlot'
    END as vehicle_condition,
    r.year,
    r.make,
    r.model,
    r.trim,
    r.status,
    r.price,
    r.msrp,
    r.date_in_stock,
    r.location,
    r.vehicle_url
FROM raw_vehicle_data r
WHERE r.vin IS NOT NULL 
    AND r.stock IS NOT NULL
    AND r.import_date = CURRENT_DATE
ON CONFLICT (vin, location) DO UPDATE SET
    stock = EXCLUDED.stock,
    vehicle_condition = EXCLUDED.vehicle_condition,
    price = EXCLUDED.price,
    status = EXCLUDED.status,
    last_seen_date = CURRENT_DATE,
    vin_scan_count = normalized_vehicle_data.vin_scan_count + 1,
    updated_at = CURRENT_TIMESTAMP;

-- Test 3: VIN history tracking performance
EXPLAIN ANALYZE
INSERT INTO vin_history (vin, dealership_name, scan_date, raw_data_id)
SELECT DISTINCT
    r.vin,
    r.location,
    r.import_date,
    r.id
FROM raw_vehicle_data r
WHERE r.import_date = CURRENT_DATE
    AND r.vin IS NOT NULL;

-- Test 4: Complex query performance (typical user query)
EXPLAIN ANALYZE
SELECT 
    n.vin,
    n.stock,
    n.year,
    n.make,
    n.model,
    n.trim,
    n.price,
    n.vehicle_condition,
    d.qr_output_path || n.stock || '.png' as qr_code_path,
    vh.scan_count
FROM normalized_vehicle_data n
JOIN dealership_configs d ON n.location = d.name
LEFT JOIN LATERAL (
    SELECT COUNT(*) as scan_count
    FROM vin_history v
    WHERE v.vin = n.vin
) vh ON true
WHERE n.vehicle_condition IN ('new', 'po', 'cpo', 'onlot')
    AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
    AND d.is_active = true
    AND n.price BETWEEN 20000 AND 50000
ORDER BY n.make, n.model, n.price;

-- Test 5: Duplicate detection performance
EXPLAIN ANALYZE
WITH duplicate_vins AS (
    SELECT 
        vin,
        COUNT(DISTINCT location) as location_count,
        array_agg(DISTINCT location ORDER BY location) as locations
    FROM normalized_vehicle_data
    WHERE last_seen_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY vin
    HAVING COUNT(DISTINCT location) > 1
)
SELECT 
    dv.vin,
    dv.location_count,
    dv.locations,
    n.year,
    n.make,
    n.model,
    n.price
FROM duplicate_vins dv
JOIN normalized_vehicle_data n ON dv.vin = n.vin
WHERE n.last_seen_date = (
    SELECT MAX(last_seen_date) 
    FROM normalized_vehicle_data n2 
    WHERE n2.vin = n.vin
);

-- Test 6: Cleanup old data performance
EXPLAIN ANALYZE
DELETE FROM raw_vehicle_data
WHERE import_date < CURRENT_DATE - INTERVAL '90 days';

-- Performance metrics queries
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Cleanup test data after stress testing
TRUNCATE TABLE vin_history CASCADE;
TRUNCATE TABLE normalized_vehicle_data CASCADE;
TRUNCATE TABLE raw_vehicle_data CASCADE;