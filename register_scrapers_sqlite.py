#!/usr/bin/env python3
"""
Register All 40 Scrapers in SQLite Database for Web GUI Display
This will add all scrapers to the dealership_configs table so they appear in the scraper control center
"""

import sqlite3
import json
import traceback
from datetime import datetime

# Database path - using the order_processing.db
DB_PATH = r"C:\Users\Workstation_1\Documents\Tools\ClaudeCode\projects\database_system\data\order_processing.db"

# All 40 scrapers with their proper display names and URLs
SCRAPER_CONFIGS = [
    {
        'name': 'Audi Ranch Mirage',
        'scraper_file': 'audiranchomirage.py',
        'website_url': 'https://www.audiranchomirage.com',
        'active': 1
    },
    {
        'name': 'Auffenberg Hyundai',
        'scraper_file': 'auffenberghyundai.py',
        'website_url': 'https://www.auffenberghyundai.com',
        'active': 1
    },
    {
        'name': 'BMW of West St. Louis',
        'scraper_file': 'bmwofweststlouis.py',
        'website_url': 'https://www.bmwofweststlouis.com',
        'active': 1
    },
    {
        'name': 'Bommarito Cadillac',
        'scraper_file': 'bommaritocadillac.py',
        'website_url': 'https://www.bommaritocadillac.com',
        'active': 1
    },
    {
        'name': 'Bommarito West County',
        'scraper_file': 'bommaritowestcounty.py',
        'website_url': 'https://www.bommaritowestcounty.com',
        'active': 1
    },
    {
        'name': 'Columbia BMW',
        'scraper_file': 'columbiabmw.py',
        'website_url': 'https://www.columbiabmw.com',
        'active': 1
    },
    {
        'name': 'Columbia Honda',
        'scraper_file': 'columbiahonda.py',
        'website_url': 'https://www.columbiahonda.com',
        'active': 1
    },
    {
        'name': 'Dave Sinclair Lincoln South',
        'scraper_file': 'davesinclairlincolnsouth.py',
        'website_url': 'https://www.davesinclairlincoln.com',
        'active': 1
    },
    {
        'name': 'Dave Sinclair Lincoln St. Peters',
        'scraper_file': 'davesinclairlincolnstpeters.py',
        'website_url': 'https://www.davesinclairlincolnstpeters.com',
        'active': 1
    },
    {
        'name': 'Frank Leta Honda',
        'scraper_file': 'frankletahonda.py',
        'website_url': 'https://www.frankletahonda.com',
        'active': 1
    },
    {
        'name': 'Glendale Chrysler Jeep',
        'scraper_file': 'glendalechryslerjeep.py',
        'website_url': 'https://www.glendalechryslerjeep.net',
        'active': 1
    },
    {
        'name': 'Honda of Frontenac',
        'scraper_file': 'hondafrontenac.py',
        'website_url': 'https://www.hondaoffrontenac.com',
        'active': 1
    },
    {
        'name': 'H&W Kia',
        'scraper_file': 'hwkia.py',
        'website_url': 'https://www.hwkia.com',
        'active': 1
    },
    {
        'name': 'Indigo Auto Group',
        'scraper_file': 'indigoautogroup.py',
        'website_url': 'https://www.indigoautogroup.com',
        'active': 1
    },
    {
        'name': 'Jaguar Ranch Mirage',
        'scraper_file': 'jaguarranchomirage.py',
        'website_url': 'https://www.jaguarranchomirage.com',
        'active': 1
    },
    {
        'name': 'Joe Machens CDJR',
        'scraper_file': 'joemachenscdjr.py',
        'website_url': 'https://www.joemachenscdjr.com',
        'active': 1
    },
    {
        'name': 'Joe Machens Hyundai',
        'scraper_file': 'joemachenshyundai.py',
        'website_url': 'https://www.joemachenshyundai.com',
        'active': 1
    },
    {
        'name': 'Joe Machens Nissan',
        'scraper_file': 'joemachensnissan.py',
        'website_url': 'https://www.joemachensnissan.com',
        'active': 1
    },
    {
        'name': 'Joe Machens Toyota',
        'scraper_file': 'joemachenstoyota.py',
        'website_url': 'https://www.joemachenstoyota.com',
        'active': 1
    },
    {
        'name': 'Kia of Columbia',
        'scraper_file': 'kiaofcolumbia.py',
        'website_url': 'https://www.kiaofcolumbia.com',
        'active': 1
    },
    {
        'name': 'Land Rover Ranch Mirage',
        'scraper_file': 'landroverranchomirage.py',
        'website_url': 'https://www.landroverranchomirage.com',
        'active': 1
    },
    {
        'name': 'Mini of St. Louis',
        'scraper_file': 'miniofstlouis.py',
        'website_url': 'https://www.miniofstlouis.com',
        'active': 1
    },
    {
        'name': 'Pappas Toyota',
        'scraper_file': 'pappastoyota.py',
        'website_url': 'https://www.pappastoyota.com',
        'active': 1
    },
    {
        'name': 'Porsche St. Louis',
        'scraper_file': 'porschestlouis.py',
        'website_url': 'https://www.porschestlouis.com',
        'active': 1
    },
    {
        'name': 'Pundmann Ford',
        'scraper_file': 'pundmannford.py',
        'website_url': 'https://www.pundmannford.com',
        'active': 1
    },
    {
        'name': 'Rusty Drewing Cadillac',
        'scraper_file': 'rustydrewingcadillac.py',
        'website_url': 'https://www.rustydrewingcadillac.com',
        'active': 1
    },
    {
        'name': 'Rusty Drewing Chevrolet Buick GMC',
        'scraper_file': 'rustydrewingchevroletbuickgmc.py',
        'website_url': 'https://www.rustydrewingchevroletbuickgmc.com',
        'active': 1
    },
    {
        'name': 'Serra Honda O\'Fallon',
        'scraper_file': 'serrahondaofallon.py',
        'website_url': 'https://www.serrahondaofallon.com',
        'active': 1
    },
    {
        'name': 'South County Autos',
        'scraper_file': 'southcountyautos.py',
        'website_url': 'https://www.southcountyautos.com',
        'active': 1
    },
    {
        'name': 'Spirit Lexus',
        'scraper_file': 'spiritlexus.py',
        'website_url': 'https://www.spiritlexus.com',
        'active': 1
    },
    {
        'name': 'Stehouwer Auto',
        'scraper_file': 'stehouwerauto.py',
        'website_url': 'https://www.stehouwerauto.com',
        'active': 1
    },
    {
        'name': 'Suntrup Buick GMC',
        'scraper_file': 'suntrupbuickgmc.py',
        'website_url': 'https://www.suntrupbuickgmc.com',
        'active': 1
    },
    {
        'name': 'Suntrup Ford Kirkwood',
        'scraper_file': 'suntrupfordkirkwood.py',
        'website_url': 'https://www.suntrupfordkirkwood.com',
        'active': 1
    },
    {
        'name': 'Suntrup Ford West',
        'scraper_file': 'suntrupfordwest.py',
        'website_url': 'https://www.suntrupfordwest.com',
        'active': 1
    },
    {
        'name': 'Suntrup Hyundai South',
        'scraper_file': 'suntruphyundaisouth.py',
        'website_url': 'https://www.suntruphyundaisouth.com',
        'active': 1
    },
    {
        'name': 'Suntrup Kia South',
        'scraper_file': 'suntrupkiasouth.py',
        'website_url': 'https://www.suntrupkiasouth.com',
        'active': 1
    },
    {
        'name': 'Thoroughbred Ford',
        'scraper_file': 'thoroughbredford.py',
        'website_url': 'https://www.thoroughbredford.com',
        'active': 1
    },
    {
        'name': 'Twin City Toyota',
        'scraper_file': 'twincitytoyota.py',
        'website_url': 'https://www.twincitytoyota.com',
        'active': 1
    },
    {
        'name': 'West County Volvo Cars',
        'scraper_file': 'wcvolvocars.py',
        'website_url': 'https://www.westcountyvolvocars.com',
        'active': 1
    },
    {
        'name': 'Weber Chevrolet',
        'scraper_file': 'weberchev.py',
        'website_url': 'https://www.weberchevrolet.com',
        'active': 1
    }
]

def register_scrapers_in_database():
    """Register all scrapers in the SQLite database"""
    
    conn = None
    cursor = None
    
    try:
        print(f"Connecting to SQLite database: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if dealership_configs table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='dealership_configs'
        """)
        
        if not cursor.fetchone():
            print("Creating dealership_configs table...")
            cursor.execute("""
                CREATE TABLE dealership_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    scraper_file TEXT,
                    website_url TEXT,
                    active INTEGER DEFAULT 1,
                    config_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Table created successfully")
        
        # Check current dealerships
        print("\nChecking current dealerships in database...")
        cursor.execute("SELECT name FROM dealership_configs ORDER BY name")
        current_dealerships = [row[0] for row in cursor.fetchall()]
        print(f"Current dealerships ({len(current_dealerships)}): {', '.join(current_dealerships[:5]) if current_dealerships else 'None'}...")
        
        # Insert or update dealerships
        inserted = 0
        updated = 0
        
        for config in SCRAPER_CONFIGS:
            if config['name'] in current_dealerships:
                # Update existing
                cursor.execute("""
                    UPDATE dealership_configs 
                    SET scraper_file = ?, website_url = ?, active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (config['scraper_file'], config['website_url'], config['active'], config['name']))
                updated += 1
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO dealership_configs 
                    (name, scraper_file, website_url, active, config_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    config['name'],
                    config['scraper_file'],
                    config['website_url'],
                    config['active'],
                    json.dumps({
                        'max_retries': 3,
                        'timeout': 30,
                        'rate_limit': 1.0
                    })
                ))
                inserted += 1
        
        # Commit changes
        conn.commit()
        
        print(f"\nInserted {inserted} new dealerships")
        print(f"Updated {updated} existing dealerships")
        
        # Verify final count
        cursor.execute("SELECT COUNT(*) FROM dealership_configs WHERE active = 1")
        active_count = cursor.fetchone()[0]
        
        print(f"\nSUCCESS: Database now has {active_count} active dealerships")
        print("All 40 scrapers are now registered and should appear in the web GUI")
        
        # List all dealerships for verification
        cursor.execute("SELECT name FROM dealership_configs WHERE active = 1 ORDER BY name")
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
    print("Registering All 40 Scrapers in SQLite Database")
    print("=" * 50)
    register_scrapers_in_database()