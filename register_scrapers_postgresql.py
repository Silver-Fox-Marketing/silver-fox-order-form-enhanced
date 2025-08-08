#!/usr/bin/env python3
"""
Register All 40 Scrapers in PostgreSQL Database for Web GUI Display
This will add all scrapers to the dealership_configs table so they appear in the scraper control center
"""

import psycopg2
from psycopg2.extras import execute_batch
import json
import traceback
from datetime import datetime
import os

# Try to get password from environment variable first
db_password = os.environ.get('DEALERSHIP_DB_PASSWORD', '')

# Database configuration for PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dealership_db', 
    'user': 'postgres',
    'password': db_password,
    'port': 5432
}

# All 40 scrapers with their proper display names
SCRAPER_CONFIGS = [
    {
        'name': 'Audi Ranch Mirage',
        'scraper_file': 'audiranchomirage.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Audi_Ranch_Mirage',
        'is_active': True
    },
    {
        'name': 'Auffenberg Hyundai',
        'scraper_file': 'auffenberghyundai.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Auffenberg_Hyundai',
        'is_active': True
    },
    {
        'name': 'BMW of West St. Louis',
        'scraper_file': 'bmwofweststlouis.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\BMW_of_West_St._Louis',
        'is_active': True
    },
    {
        'name': 'Bommarito Cadillac',
        'scraper_file': 'bommaritocadillac.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Bommarito_Cadillac',
        'is_active': True
    },
    {
        'name': 'Bommarito West County',
        'scraper_file': 'bommaritowestcounty.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Bommarito_West_County',
        'is_active': True
    },
    {
        'name': 'Columbia BMW',
        'scraper_file': 'columbiabmw.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Columbia_BMW',
        'is_active': True
    },
    {
        'name': 'Columbia Honda',
        'scraper_file': 'columbiahonda.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Columbia_Honda',
        'is_active': True
    },
    {
        'name': 'Dave Sinclair Lincoln South',
        'scraper_file': 'davesinclairlincolnsouth.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Dave_Sinclair_Lincoln_South',
        'is_active': True
    },
    {
        'name': 'Dave Sinclair Lincoln St. Peters',
        'scraper_file': 'davesinclairlincolnstpeters.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Dave_Sinclair_Lincoln_St._Peters',
        'is_active': True
    },
    {
        'name': 'Frank Leta Honda',
        'scraper_file': 'frankletahonda.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Frank_Leta_Honda',
        'is_active': True
    },
    {
        'name': 'Glendale Chrysler Jeep',
        'scraper_file': 'glendalechryslerjeep.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Glendale_Chrysler_Jeep',
        'is_active': True
    },
    {
        'name': 'Honda of Frontenac',
        'scraper_file': 'hondafrontenac.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Honda_of_Frontenac',
        'is_active': True
    },
    {
        'name': 'H&W Kia',
        'scraper_file': 'hwkia.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\H&W_Kia',
        'is_active': True
    },
    {
        'name': 'Indigo Auto Group',
        'scraper_file': 'indigoautogroup.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Indigo_Auto_Group',
        'is_active': True
    },
    {
        'name': 'Jaguar Ranch Mirage',
        'scraper_file': 'jaguarranchomirage.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Jaguar_Ranch_Mirage',
        'is_active': True
    },
    {
        'name': 'Joe Machens CDJR',
        'scraper_file': 'joemachenscdjr.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Joe_Machens_CDJR',
        'is_active': True
    },
    {
        'name': 'Joe Machens Hyundai',
        'scraper_file': 'joemachenshyundai.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Joe_Machens_Hyundai',
        'is_active': True
    },
    {
        'name': 'Joe Machens Nissan',
        'scraper_file': 'joemachensnissan.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Joe_Machens_Nissan',
        'is_active': True
    },
    {
        'name': 'Joe Machens Toyota',
        'scraper_file': 'joemachenstoyota.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Joe_Machens_Toyota',
        'is_active': True
    },
    {
        'name': 'Kia of Columbia',
        'scraper_file': 'kiaofcolumbia.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Kia_of_Columbia',
        'is_active': True
    },
    {
        'name': 'Land Rover Ranch Mirage',
        'scraper_file': 'landroverranchomirage.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Land_Rover_Ranch_Mirage',
        'is_active': True
    },
    {
        'name': 'Mini of St. Louis',
        'scraper_file': 'miniofstlouis.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Mini_of_St._Louis',
        'is_active': True
    },
    {
        'name': 'Pappas Toyota',
        'scraper_file': 'pappastoyota.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Pappas_Toyota',
        'is_active': True
    },
    {
        'name': 'Porsche St. Louis',
        'scraper_file': 'porschestlouis.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Porsche_St._Louis',
        'is_active': True
    },
    {
        'name': 'Pundmann Ford',
        'scraper_file': 'pundmannford.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Pundmann_Ford',
        'is_active': True
    },
    {
        'name': 'Rusty Drewing Cadillac',
        'scraper_file': 'rustydrewingcadillac.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Rusty_Drewing_Cadillac',
        'is_active': True
    },
    {
        'name': 'Rusty Drewing Chevrolet Buick GMC',
        'scraper_file': 'rustydrewingchevroletbuickgmc.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Rusty_Drewing_Chevrolet_Buick_GMC',
        'is_active': True
    },
    {
        'name': 'Serra Honda O\'Fallon',
        'scraper_file': 'serrahondaofallon.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Serra_Honda_O\'Fallon',
        'is_active': True
    },
    {
        'name': 'South County Autos',
        'scraper_file': 'southcountyautos.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\South_County_Autos',
        'is_active': True
    },
    {
        'name': 'Spirit Lexus',
        'scraper_file': 'spiritlexus.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Spirit_Lexus',
        'is_active': True
    },
    {
        'name': 'Stehouwer Auto',
        'scraper_file': 'stehouwerauto.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Stehouwer_Auto',
        'is_active': True
    },
    {
        'name': 'Suntrup Buick GMC',
        'scraper_file': 'suntrupbuickgmc.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Suntrup_Buick_GMC',
        'is_active': True
    },
    {
        'name': 'Suntrup Ford Kirkwood',
        'scraper_file': 'suntrupfordkirkwood.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Suntrup_Ford_Kirkwood',
        'is_active': True
    },
    {
        'name': 'Suntrup Ford West',
        'scraper_file': 'suntrupfordwest.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Suntrup_Ford_West',
        'is_active': True
    },
    {
        'name': 'Suntrup Hyundai South',
        'scraper_file': 'suntruphyundaisouth.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Suntrup_Hyundai_South',
        'is_active': True
    },
    {
        'name': 'Suntrup Kia South',
        'scraper_file': 'suntrupkiasouth.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Suntrup_Kia_South',
        'is_active': True
    },
    {
        'name': 'Thoroughbred Ford',
        'scraper_file': 'thoroughbredford.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Thoroughbred_Ford',
        'is_active': True
    },
    {
        'name': 'Twin City Toyota',
        'scraper_file': 'twincitytoyota.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Twin_City_Toyota',
        'is_active': True
    },
    {
        'name': 'West County Volvo Cars',
        'scraper_file': 'wcvolvocars.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\West_County_Volvo_Cars',
        'is_active': True
    },
    {
        'name': 'Weber Chevrolet',
        'scraper_file': 'weberchev.py',
        'filtering_rules': {'min_price': 0, 'max_price': 999999},
        'output_rules': {'format': 'csv'},
        'qr_output_path': 'C:\\dealership_database\\qr_codes\\Weber_Chevrolet',
        'is_active': True
    }
]

def register_scrapers_in_database():
    """Register all scrapers in the PostgreSQL database"""
    
    conn = None
    cursor = None
    
    try:
        print(f"Connecting to PostgreSQL database...")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Database: {DB_CONFIG['database']}")
        print(f"User: {DB_CONFIG['user']}")
        print(f"Password provided: {'Yes' if DB_CONFIG['password'] else 'No'}")
        
        if not DB_CONFIG['password']:
            print("\nPlease set the database password using:")
            print("set DEALERSHIP_DB_PASSWORD=your_password")
            print("Then run this script again.")
            return
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check current dealerships
        print("\nChecking current dealerships in database...")
        cursor.execute("SELECT name FROM dealership_configs ORDER BY name")
        current_dealerships = [row[0] for row in cursor.fetchall()]
        print(f"Current dealerships ({len(current_dealerships)}): {', '.join(current_dealerships[:5]) if current_dealerships else 'None'}...")
        
        # Prepare insert data
        insert_data = []
        update_data = []
        
        for config in SCRAPER_CONFIGS:
            # Create QR output directory
            os.makedirs(config['qr_output_path'], exist_ok=True)
            
            if config['name'] in current_dealerships:
                # Update existing
                update_data.append((
                    json.dumps(config['filtering_rules']),
                    json.dumps(config['output_rules']),
                    config['qr_output_path'],
                    config['is_active'],
                    datetime.now(),
                    config['name']
                ))
            else:
                # Insert new
                insert_data.append((
                    config['name'],
                    json.dumps(config['filtering_rules']),
                    json.dumps(config['output_rules']),
                    config['qr_output_path'],
                    config['is_active'],
                    datetime.now()
                ))
        
        # Insert new dealerships
        if insert_data:
            print(f"\nInserting {len(insert_data)} new dealerships...")
            insert_query = """
                INSERT INTO dealership_configs 
                (name, filtering_rules, output_rules, qr_output_path, is_active, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            execute_batch(cursor, insert_query, insert_data)
            print(f"Successfully inserted {len(insert_data)} dealerships")
        
        # Update existing dealerships
        if update_data:
            print(f"\nUpdating {len(update_data)} existing dealerships...")
            update_query = """
                UPDATE dealership_configs 
                SET filtering_rules = %s, output_rules = %s, qr_output_path = %s, 
                    is_active = %s, updated_at = %s
                WHERE name = %s
            """
            execute_batch(cursor, update_query, update_data)
            print(f"Successfully updated {len(update_data)} dealerships")
        
        # Commit changes
        conn.commit()
        
        # Verify final count
        cursor.execute("SELECT COUNT(*) FROM dealership_configs WHERE is_active = true")
        active_count = cursor.fetchone()[0]
        
        print(f"\nSUCCESS: Database now has {active_count} active dealerships")
        print("All 40 scrapers are now registered and should appear in the web GUI")
        
        # List all dealerships for verification
        cursor.execute("SELECT name FROM dealership_configs WHERE is_active = true ORDER BY name")
        all_dealerships = [row[0] for row in cursor.fetchall()]
        print(f"\nActive dealerships:")
        for i, name in enumerate(all_dealerships, 1):
            print(f"{i:2d}. {name}")
        
    except Exception as e:
        print(f"\nERROR: Failed to register scrapers: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Registering All 40 Scrapers in PostgreSQL Database")
    print("=" * 50)
    register_scrapers_in_database()