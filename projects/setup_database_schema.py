#!/usr/bin/env python3
"""
Setup Database Schema for Silver Fox Integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'minisforum_database_transfer/bulletproof_package/scripts'))

from database_connection import db_manager
import logging

logger = logging.getLogger(__name__)

def create_schema():
    """Create the complete database schema"""
    
    # Read and execute SQL files
    sql_files = [
        'minisforum_database_transfer/bulletproof_package/sql/02_create_tables.sql',
        'minisforum_database_transfer/bulletproof_package/sql/03_initial_dealership_configs.sql',
        'minisforum_database_transfer/bulletproof_package/sql/06_order_processing_tables.sql'
    ]
    
    for sql_file in sql_files:
        try:
            print(f"Executing {sql_file}...")
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Split by statements and execute
            statements = sql_content.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        with db_manager.get_cursor() as cursor:
                            cursor.execute(statement)
                        print(f"OK Executed statement")
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"Warning: {e}")
            
            print(f"OK Completed {sql_file}")
            
        except Exception as e:
            print(f"Error with {sql_file}: {e}")
    
    # Verify schema
    tables = db_manager.execute_query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    print(f"\nOK Database schema created successfully!")
    print(f"Tables created: {', '.join([t['table_name'] for t in tables])}")
    
    return True

if __name__ == "__main__":
    create_schema()