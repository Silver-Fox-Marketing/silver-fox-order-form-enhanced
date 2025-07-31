#!/usr/bin/env python3
"""
Create Core Database Tables for Silver Fox Integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
import logging

logger = logging.getLogger(__name__)

def create_core_tables():
    """Create essential tables for the system"""
    
    tables = [
        # Raw vehicle data table
        """
        CREATE TABLE IF NOT EXISTS raw_vehicle_data (
            id SERIAL PRIMARY KEY,
            vin VARCHAR(17),
            stock VARCHAR(50),
            type VARCHAR(50),
            year INTEGER,
            make VARCHAR(100),
            model VARCHAR(100),
            trim VARCHAR(200),
            ext_color VARCHAR(100),
            status VARCHAR(50),
            price DECIMAL(10, 2),
            body_style VARCHAR(50),
            fuel_type VARCHAR(50),
            msrp DECIMAL(10, 2),
            date_in_stock DATE,
            street_address VARCHAR(255),
            locality VARCHAR(100),
            postal_code VARCHAR(20),
            region VARCHAR(100),
            country VARCHAR(100),
            location VARCHAR(100),
            vehicle_url TEXT,
            import_date DATE DEFAULT CURRENT_DATE,
            import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Normalized vehicle data table
        """
        CREATE TABLE IF NOT EXISTS normalized_vehicle_data (
            id SERIAL PRIMARY KEY,
            raw_data_id INTEGER,
            vin VARCHAR(17) NOT NULL,
            stock VARCHAR(50) NOT NULL,
            vehicle_condition VARCHAR(10) CHECK (vehicle_condition IN ('new', 'po', 'cpo', 'offlot', 'onlot')),
            year INTEGER,
            make VARCHAR(100),
            model VARCHAR(100),
            trim VARCHAR(200),
            status VARCHAR(50),
            price DECIMAL(10, 2),
            msrp DECIMAL(10, 2),
            date_in_stock DATE,
            location VARCHAR(100),
            vehicle_url TEXT,
            vin_scan_count INTEGER DEFAULT 1,
            last_seen_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(vin, location)
        )
        """,
        
        # VIN history table
        """
        CREATE TABLE IF NOT EXISTS vin_history (
            id SERIAL PRIMARY KEY,
            vin VARCHAR(17) NOT NULL,
            dealership_name VARCHAR(100) NOT NULL,
            scan_date DATE NOT NULL,
            raw_data_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Dealership configs table
        """
        CREATE TABLE IF NOT EXISTS dealership_configs (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            filtering_rules JSONB DEFAULT '{}',
            output_rules JSONB DEFAULT '{}',
            qr_output_path TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Order processing jobs table
        """
        CREATE TABLE IF NOT EXISTS order_processing_jobs (
            id SERIAL PRIMARY KEY,
            dealership_name VARCHAR(100) NOT NULL,
            job_type VARCHAR(50) NOT NULL DEFAULT 'standard',
            vehicle_count INTEGER DEFAULT 0,
            final_vehicle_count INTEGER,
            export_file TEXT,
            status VARCHAR(20) DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            notes TEXT,
            created_by VARCHAR(100) DEFAULT 'system'
        )
        """,
        
        # QR file tracking table
        """
        CREATE TABLE IF NOT EXISTS qr_file_tracking (
            id SERIAL PRIMARY KEY,
            vin VARCHAR(17) NOT NULL,
            dealership_name VARCHAR(100) NOT NULL,
            qr_file_path TEXT NOT NULL,
            file_exists BOOLEAN DEFAULT false,
            file_size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            job_id INTEGER,
            UNIQUE(vin, dealership_name)
        )
        """,
        
        # Export history table
        """
        CREATE TABLE IF NOT EXISTS export_history (
            id SERIAL PRIMARY KEY,
            export_type VARCHAR(50) NOT NULL,
            dealership_name VARCHAR(100),
            file_path TEXT NOT NULL,
            record_count INTEGER DEFAULT 0,
            file_size INTEGER,
            export_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            job_id INTEGER,
            exported_by VARCHAR(100) DEFAULT 'system',
            notes TEXT
        )
        """
    ]
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_raw_vin ON raw_vehicle_data(vin)",
        "CREATE INDEX IF NOT EXISTS idx_raw_stock ON raw_vehicle_data(stock)",
        "CREATE INDEX IF NOT EXISTS idx_raw_location ON raw_vehicle_data(location)",
        "CREATE INDEX IF NOT EXISTS idx_norm_vin ON normalized_vehicle_data(vin)",
        "CREATE INDEX IF NOT EXISTS idx_norm_stock ON normalized_vehicle_data(stock)",
        "CREATE INDEX IF NOT EXISTS idx_norm_location ON normalized_vehicle_data(location)",
        "CREATE INDEX IF NOT EXISTS idx_norm_condition ON normalized_vehicle_data(vehicle_condition)",
        "CREATE INDEX IF NOT EXISTS idx_history_vin ON vin_history(vin)",
        "CREATE INDEX IF NOT EXISTS idx_config_name ON dealership_configs(name)",
        "CREATE INDEX IF NOT EXISTS idx_order_jobs_status ON order_processing_jobs(status)",
        "CREATE INDEX IF NOT EXISTS idx_qr_tracking_vin ON qr_file_tracking(vin)"
    ]
    
    # Execute table creation
    for i, table_sql in enumerate(tables, 1):
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(table_sql)
            print(f"OK Created table {i}/{len(tables)}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"Error creating table {i}: {e}")
    
    # Execute index creation
    for i, index_sql in enumerate(indexes, 1):
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(index_sql)
            print(f"OK Created index {i}/{len(indexes)}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"Error creating index {i}: {e}")
    
    # Insert sample dealership configs
    sample_configs = [
        ("BMW of West St. Louis", '{"exclude_conditions": ["unknown"]}', '{"sort_by": ["make", "model", "year"]}', "C:/qr_codes/bmw_west_st_louis/"),
        ("Suntrup Ford West", '{"exclude_conditions": ["unknown"]}', '{"sort_by": ["make", "model", "year"]}', "C:/qr_codes/suntrup_ford_west/"),
        ("Columbia Honda", '{"exclude_conditions": ["unknown"]}', '{"sort_by": ["make", "model", "year"]}', "C:/qr_codes/columbia_honda/"),
        ("Joe Machens Toyota", '{"exclude_conditions": ["unknown"]}', '{"sort_by": ["make", "model", "year"]}', "C:/qr_codes/joe_machens_toyota/"),
        ("Dave Sinclair Lincoln South", '{"exclude_conditions": ["unknown"]}', '{"sort_by": ["make", "model", "year"]}', "C:/qr_codes/dave_sinclair_lincoln_south/"),
    ]
    
    for name, filtering, output, qr_path in sample_configs:
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO dealership_configs (name, filtering_rules, output_rules, qr_output_path)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        filtering_rules = EXCLUDED.filtering_rules,
                        output_rules = EXCLUDED.output_rules,
                        qr_output_path = EXCLUDED.qr_output_path
                """, (name, filtering, output, qr_path))
            print(f"OK Added config for {name}")
        except Exception as e:
            print(f"Error adding config for {name}: {e}")
    
    # Verify tables
    tables_result = db_manager.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    print(f"\nOK Database setup complete!")
    print(f"Tables: {', '.join([t['table_name'] for t in tables_result])}")
    
    return True

if __name__ == "__main__":
    create_core_tables()