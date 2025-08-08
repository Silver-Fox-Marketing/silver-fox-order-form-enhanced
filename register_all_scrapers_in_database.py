#!/usr/bin/env python3
"""
Register All 40 Scrapers in Database for Web GUI Display
This will add all scrapers to the dealership_configs table so they appear in the scraper control center
"""

import psycopg2
from psycopg2.extras import execute_batch
import json
import traceback
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dealership_db', 
    'user': 'postgres',
    'password': ''
}

# All 40 scrapers with their proper display names and URLs
SCRAPER_CONFIGS = [
    {
        'name': 'Audi Ranch Mirage',
        'scraper_file': 'audiranchomirage.py',
        'website_url': 'https://www.audiranchomirage.com',
        'active': True
    },
    {
        'name': 'Auffenberg Hyundai',
        'scraper_file': 'auffenberghyundai.py',
        'website_url': 'https://www.auffenberghyundai.com',
        'active': True
    },
    {
        'name': 'BMW of West St. Louis',
        'scraper_file': 'bmwofweststlouis.py',
        'website_url': 'https://www.bmwofweststlouis.com',
        'active': True
    },
    {
        'name': 'Bommarito Cadillac',
        'scraper_file': 'bommaritocadillac.py',
        'website_url': 'https://www.bommaritocadillac.com',
        'active': True
    },
    {
        'name': 'Bommarito West County',
        'scraper_file': 'bommaritowestcounty.py',
        'website_url': 'https://www.bommaritowestcounty.com',
        'active': True
    },
    {
        'name': 'Columbia BMW',
        'scraper_file': 'columbiabmw.py',
        'website_url': 'https://www.columbiabmw.com',
        'active': True
    },
    {
        'name': 'Columbia Honda',
        'scraper_file': 'columbiahonda.py',
        'website_url': 'https://www.columbiahonda.com',
        'active': True
    },
    {
        'name': 'Dave Sinclair Lincoln South',
        'scraper_file': 'davesinclairlincolnsouth.py',
        'website_url': 'https://www.davesinclairlincoln.com',
        'active': True
    },
    {
        'name': 'Dave Sinclair Lincoln St. Peters',
        'scraper_file': 'davesinclairlincolnstpeters.py',
        'website_url': 'https://www.davesinclairlincolnstpeters.com',
        'active': True
    },
    {
        'name': 'Frank Leta Honda',
        'scraper_file': 'frankletahonda.py',
        'website_url': 'https://www.frankletahonda.com',
        'active': True
    },
    {
        'name': 'Glendale Chrysler Jeep',
        'scraper_file': 'glendalechryslerjeep.py',
        'website_url': 'https://www.glendalechryslerjeep.net',
        'active': True
    },
    {
        'name': 'Honda of Frontenac',
        'scraper_file': 'hondafrontenac.py',
        'website_url': 'https://www.hondaoffrontenac.com',
        'active': True
    },
    {
        'name': 'H&W Kia',
        'scraper_file': 'hwkia.py',
        'website_url': 'https://www.hwkia.com',
        'active': True
    },
    {
        'name': 'Indigo Auto Group',
        'scraper_file': 'indigoautogroup.py',
        'website_url': 'https://www.indigoautogroup.com',
        'active': True
    },
    {
        'name': 'Jaguar Ranch Mirage',
        'scraper_file': 'jaguarranchomirage.py',
        'website_url': 'https://www.jaguarranchomirage.com',
        'active': True
    },
    {
        'name': 'Joe Machens CDJR',
        'scraper_file': 'joemachenscdjr.py',
        'website_url': 'https://www.joemachenscdjr.com',
        'active': True
    },
    {
        'name': 'Joe Machens Hyundai',
        'scraper_file': 'joemachenshyundai.py',
        'website_url': 'https://www.joemachenshyundai.com',
        'active': True
    },
    {
        'name': 'Joe Machens Nissan',
        'scraper_file': 'joemachensnissan.py',
        'website_url': 'https://www.joemachensnissan.com',
        'active': True
    },
    {
        'name': 'Joe Machens Toyota',
        'scraper_file': 'joemachenstoyota.py',
        'website_url': 'https://www.joemachenstoyota.com',
        'active': True
    },
    {
        'name': 'Kia of Columbia',
        'scraper_file': 'kiaofcolumbia.py',
        'website_url': 'https://www.kiaofcolumbia.com',
        'active': True
    },
    {
        'name': 'Land Rover Ranch Mirage',
        'scraper_file': 'landroverranchomirage.py',
        'website_url': 'https://www.landroverranchomirage.com',
        'active': True
    },
    {
        'name': 'Mini of St. Louis',
        'scraper_file': 'miniofstlouis.py',
        'website_url': 'https://www.miniofstlouis.com',
        'active': True
    },
    {
        'name': 'Pappas Toyota',
        'scraper_file': 'pappastoyota.py',
        'website_url': 'https://www.pappastoyota.com',
        'active': True
    },
    {
        'name': 'Porsche St. Louis',
        'scraper_file': 'porschestlouis.py',
        'website_url': 'https://www.porschestlouis.com',
        'active': True
    },
    {
        'name': 'Pundmann Ford',
        'scraper_file': 'pundmannford.py',
        'website_url': 'https://www.pundmannford.com',
        'active': True
    },
    {
        'name': 'Rusty Drewing Cadillac',
        'scraper_file': 'rustydrewingcadillac.py',
        'website_url': 'https://www.rustydrewingcadillac.com',
        'active': True
    },
    {
        'name': 'Rusty Drewing Chevrolet Buick GMC',
        'scraper_file': 'rustydrewingchevroletbuickgmc.py',
        'website_url': 'https://www.rustydrewingchevroletbuickgmc.com',
        'active': True
    },
    {
        'name': 'Serra Honda O\'Fallon',
        'scraper_file': 'serrahondaofallon.py',
        'website_url': 'https://www.serrahondaofallon.com',
        'active': True
    },
    {
        'name': 'South County Autos',
        'scraper_file': 'southcountyautos.py',
        'website_url': 'https://www.southcountyautos.com',
        'active': True
    },
    {
        'name': 'Spirit Lexus',
        'scraper_file': 'spiritlexus.py',
        'website_url': 'https://www.spiritlexus.com',
        'active': True
    },
    {
        'name': 'Stehouwer Auto',
        'scraper_file': 'stehouwerauto.py',
        'website_url': 'https://www.stehouwerauto.com',
        'active': True
    },
    {
        'name': 'Suntrup Buick GMC',
        'scraper_file': 'suntrupbuickgmc.py',
        'website_url': 'https://www.suntrupbuickgmc.com',
        'active': True
    },
    {
        'name': 'Suntrup Ford Kirkwood',
        'scraper_file': 'suntrupfordkirkwood.py',
        'website_url': 'https://www.suntrupfordkirkwood.com',
        'active': True
    },
    {
        'name': 'Suntrup Ford West',
        'scraper_file': 'suntrupfordwest.py',
        'website_url': 'https://www.suntrupfordwest.com',
        'active': True
    },
    {
        'name': 'Suntrup Hyundai South',
        'scraper_file': 'suntruphyundaisouth.py',
        'website_url': 'https://www.suntruphyundaisouth.com',
        'active': True
    },
    {
        'name': 'Suntrup Kia South',
        'scraper_file': 'suntrupkiasouth.py',
        'website_url': 'https://www.suntrupkiasouth.com',
        'active': True
    },
    {
        'name': 'Thoroughbred Ford',
        'scraper_file': 'thoroughbredford.py',
        'website_url': 'https://www.thoroughbredford.com',
        'active': True
    },
    {
        'name': 'Twin City Toyota',
        'scraper_file': 'twincitytoyota.py',
        'website_url': 'https://www.twincitytoyota.com',
        'active': True
    },
    {
        'name': 'West County Volvo Cars',
        'scraper_file': 'wcvolvocars.py',
        'website_url': 'https://www.westcountyvolvocars.com',
        'active': True
    },
    {
        'name': 'Weber Chevrolet',
        'scraper_file': 'weberchev.py',
        'website_url': 'https://www.weberchevrolet.com',
        'active': True
    }
]

def register_scrapers_in_database():
    """Register all scrapers in the database"""
    
    conn = None
    cursor = None
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check current dealerships
        print("\nChecking current dealerships in database...")
        cursor.execute("SELECT name FROM dealership_configs ORDER BY name")
        current_dealerships = [row[0] for row in cursor.fetchall()]
        print(f"Current dealerships ({len(current_dealerships)}): {', '.join(current_dealerships[:5])}...")
        
        # Prepare insert data
        insert_data = []
        update_data = []
        
        for config in SCRAPER_CONFIGS:
            if config['name'] in current_dealerships:
                # Update existing
                update_data.append((
                    config['scraper_file'],
                    config['website_url'],
                    config['active'],
                    datetime.now(),
                    config['name']
                ))
            else:
                # Insert new
                insert_data.append((
                    config['name'],
                    config['scraper_file'],
                    config['website_url'],
                    config['active'],
                    json.dumps({
                        'max_retries': 3,
                        'timeout': 30,
                        'rate_limit': 1.0
                    }),
                    datetime.now(),
                    datetime.now()
                ))
        
        # Insert new dealerships
        if insert_data:
            print(f"\nInserting {len(insert_data)} new dealerships...")
            insert_query = """
                INSERT INTO dealership_configs 
                (name, scraper_file, website_url, active, config_json, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            execute_batch(cursor, insert_query, insert_data)
            print(f"Successfully inserted {len(insert_data)} dealerships")
        
        # Update existing dealerships
        if update_data:
            print(f"\nUpdating {len(update_data)} existing dealerships...")
            update_query = """
                UPDATE dealership_configs 
                SET scraper_file = %s, website_url = %s, active = %s, updated_at = %s
                WHERE name = %s
            """
            execute_batch(cursor, update_query, update_data)
            print(f"Successfully updated {len(update_data)} dealerships")
        
        # Commit changes
        conn.commit()
        
        # Verify final count
        cursor.execute("SELECT COUNT(*) FROM dealership_configs WHERE active = true")
        active_count = cursor.fetchone()[0]
        
        print(f"\nSUCCESS: Database now has {active_count} active dealerships")
        print("All 40 scrapers are now registered and should appear in the web GUI")
        
        # List all dealerships for verification
        cursor.execute("SELECT name FROM dealership_configs WHERE active = true ORDER BY name")
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
    print("Registering All 40 Scrapers in Database")
    print("=" * 50)
    register_scrapers_in_database()