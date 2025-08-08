#!/usr/bin/env python3
"""
Scraper Integration Script for Bulletproof Package
Integrates all 39 scrapers from vehicle_scraper18 folder into bulletproof system
Preserves existing scraping logic, only adds error handling and database integration
"""

import os
import shutil
import sys
from pathlib import Path
import psycopg2
from datetime import datetime
import json

class ScraperIntegrator:
    def __init__(self):
        self.source_path = Path("C:/Users/Workstation_1/Documents/Tools/ClaudeCode/projects/shared_resources/Project reference for scraper/vehicle_scraper 18")
        self.dest_path = Path("C:/Users/Workstation_1/Documents/Tools/ClaudeCode/bulletproof_package")
        self.scrapers_dest = self.dest_path / "scrapers"
        
        # Database connection info (from bulletproof system)
        self.db_config = {
            'host': 'localhost',
            'database': 'vehicle_inventory',
            'user': 'postgres',
            'password': 'password'
        }
        
        # List of all 39 scrapers to integrate
        self.scraper_list = [
            'joemachensnissan', 'joemachenscdjr', 'joemachenshyundai', 'kiaofcolumbia',
            'porschestlouis', 'auffenberghyundai', 'hondafrontenac', 'bommaritocadillac',
            'pappastoyota', 'twincitytoyota', 'serrahondaofallon', 'southcountyautos',
            'glendalechryslerjeep', 'davesinclairlincolnsouth', 'suntrupkiasouth', 'columbiabmw',
            'rustydrewingcadillac', 'rustydrewingchevroletbuickgmc', 'pundmannford', 'stehouwerauto',
            'bmwofweststlouis', 'bommaritowestcounty', 'hwkia', 'wcvolvocars',
            'joemachenstoyota', 'suntruphyundaisouth', 'landroverranchomirage', 'jaguarranchomirage',
            'indigoautogroup', 'miniofstlouis', 'suntrupfordkirkwood', 'thoroughbredford',
            'spiritlexus', 'frankletahonda', 'columbiahonda', 'davesinclairlincolnstpeters',
            'weberchev', 'suntrupbuickgmc', 'suntrupfordwest'
        ]

    def setup_directories(self):
        """Create necessary directories for scrapers"""
        print("Setting up directory structure...")
        
        # Create scrapers directory
        self.scrapers_dest.mkdir(exist_ok=True)
        
        # Create logs directory
        (self.scrapers_dest / "logs").mkdir(exist_ok=True)
        
        # Create config directory
        (self.scrapers_dest / "config").mkdir(exist_ok=True)
        
        print(f"✓ Directory structure created at {self.scrapers_dest}")

    def copy_helper_classes(self):
        """Copy helper and interface classes with database integration"""
        print("Copying and modifying helper classes...")
        
        # Copy original helper_class.py as base
        source_helper = self.source_path / "scrapers" / "helper_class.py"
        dest_helper = self.scrapers_dest / "helper_class.py"
        
        if source_helper.exists():
            shutil.copy2(source_helper, dest_helper)
            print("✓ Helper class copied")
        
        # Copy original interface_class.py as base
        source_interface = self.source_path / "scrapers" / "interface_class.py"
        dest_interface = self.scrapers_dest / "interface_class.py"
        
        if source_interface.exists():
            shutil.copy2(source_interface, dest_interface)
            print("✓ Interface class copied")
            
        # Create enhanced helper class with database integration
        self.create_enhanced_helper_class()

    def create_enhanced_helper_class(self):
        """Create enhanced helper class with database integration"""
        enhanced_helper_content = '''import json
import os
import re
import requests
import sys
import random
import csv
import time
from bs4 import BeautifulSoup
import datetime
import psycopg2
from psycopg2 import sql
import traceback

class DatabaseHelper:
    """Database integration helper for scrapers"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            
    def insert_vehicle_data(self, vehicle_data):
        """Insert vehicle data into raw_data table"""
        try:
            if not self.connection:
                if not self.connect():
                    return False
                    
            cursor = self.connection.cursor()
            
            # Insert into raw_data table (matching existing structure)
            insert_query = """
                INSERT INTO raw_data (
                    vin, stock, v_type, year, make, model, trim, ext_color,
                    status, price, body, fuel_type, msrp, date_in_stock,
                    street_addr, locality, postal_code, region, country,
                    location, vehicle_url, import_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Add import timestamp
            vehicle_data_with_timestamp = list(vehicle_data) + [datetime.datetime.now()]
            
            cursor.execute(insert_query, vehicle_data_with_timestamp)
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Database insert error: {e}")
            if self.connection:
                self.connection.rollback()
            return False

class EnhancedHelper:
    """Enhanced helper class combining original functionality with database integration"""
    
    def __init__(self, db_config=None):
        # Initialize database helper if config provided
        if db_config:
            self.db_helper = DatabaseHelper(db_config)
        else:
            self.db_helper = None
            
    def read_txt_file(self, filename):
        with open(filename) as infile:
            ids = [row.replace('\\n', '').replace('\\r', '') for row in infile]
        return ids

    def writing_output_file(self, sub_list, output_file):
        """Write to both CSV file and database"""
        
        # Original CSV writing functionality (preserved)
        if self.is_file_exist(output_file):
            csv_data = self.reading_csv(output_file)
        else:
            csv_data = [["vin", "stock", "v_type", "year", "make", "model", "trim", "ext_color",
                        "status", "price", "body", "fuel_type", "msrp", "date_in_stock",
                        "street_addr", "locality", "postal_code", "region", "country",
                        "location", "vehicle_url"]]
            
        csv_data.append(sub_list)
        self.writing_csv(csv_data, output_file)
        
        # Database writing functionality (new)
        if self.db_helper:
            success = self.db_helper.insert_vehicle_data(sub_list)
            if success:
                print("✓ Vehicle data saved to database")
            else:
                print("✗ Failed to save vehicle data to database")

    def get_url_response(self, url, is_json=False):
        print("Processing URL: ", url)
        count = 0
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
        
        while 1:
            try:
                if not is_json:
                    return requests.get(url, headers=headers, timeout=30).text
                return requests.get(url, headers=headers, timeout=30).json()
            except Exception as error:
                print('Error in getting URL response: ', error)
            
            count += 1
            if count > 3:
                return False
            time.sleep(3)

    def make_soup_url(self, url):
        return BeautifulSoup(self.get_url_response(url), 'html.parser')

    def reading_csv(self, csv_filename):
        f = open(csv_filename, 'r', encoding='utf-8', errors='replace')
        csv_data = []
        reader = csv.reader(f)
        for row in reader:
            csv_data.append(row)
        f.close()
        return csv_data

    def writing_csv(self, data, csv_filename):
        myFile = open(csv_filename, 'w', newline='', encoding='utf-8', errors='replace')
        with myFile:
            writer = csv.writer(myFile, quoting=csv.QUOTE_ALL)
            writer.writerows(data)
        return csv_filename

    def checking_folder_existence(self, dest_dir):
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
            print("Directory", dest_dir, "Created")
        return dest_dir

    def write_json_file(self, data, filename):
        while 1:
            try:
                with open(filename, 'w', encoding='utf-8') as outfile:
                    json.dump(data, outfile, indent=4)
                break
            except Exception as error:
                print("Error in writing Json file: ", error)
                time.sleep(1)

    def read_json_file(self, filename):
        data = {}
        with open(filename, encoding='utf-8') as json_data:
            data = json.load(json_data)
        return data

    def is_file_exist(self, filename):
        if os.path.exists(filename):
            return True
        else:
            return False

    def json_exist_data(self, fileName):
        json_data = []
        if self.is_file_exist(fileName):
            json_data = self.read_json_file(fileName)
        return json_data

    def downloading_image_file(self, image_url, image_filename):
        if self.is_file_exist(image_filename):
            return True
        
        print('Downloading File: ', image_filename, ' : ', image_url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        response = requests.request("GET", image_url, headers=headers, data={}).content
        with open(image_filename, 'wb') as handler:
            handler.write(response)

    def write_random_file(self, text, file_name):
        file = open(file_name, "w", encoding='utf-8')
        file.write(str(text))
        file.close()

    def read_random_file(self, file_name):
        f = open(file_name, "r", encoding='utf-8')
        return f.read()

# Backward compatibility - create Helper class that uses EnhancedHelper
class Helper(EnhancedHelper):
    """Backward compatible Helper class"""
    pass
'''
        
        # Write enhanced helper class
        enhanced_helper_path = self.scrapers_dest / "enhanced_helper_class.py"
        with open(enhanced_helper_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_helper_content)
        
        print("✓ Enhanced helper class created with database integration")

    def copy_and_wrap_scraper(self, scraper_name):
        """Copy individual scraper and wrap with error handling"""
        print(f"Processing scraper: {scraper_name}")
        
        source_file = self.source_path / "scrapers" / f"{scraper_name}.py"
        dest_file = self.scrapers_dest / f"{scraper_name}.py"
        
        if not source_file.exists():
            print(f"✗ Source file not found: {source_file}")
            return False
            
        # Read original scraper content
        with open(source_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Create wrapped version with error handling
        wrapped_content = self.create_wrapped_scraper(original_content, scraper_name)
        
        # Write wrapped scraper
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(wrapped_content)
            
        print(f"✓ Scraper {scraper_name} integrated with error handling")
        return True

    def create_wrapped_scraper(self, original_content, scraper_name):
        """Create error-wrapped version of scraper while preserving logic"""
        
        # Replace helper import to use enhanced version
        wrapped_content = original_content.replace(
            "from . helper_class import *",
            "from enhanced_helper_class import *\nimport traceback\nimport sys\nimport os"
        )
        
        # Add database configuration
        db_config_inject = f'''
# Database configuration for bulletproof system
DB_CONFIG = {{
    'host': 'localhost', 
    'database': 'vehicle_inventory',
    'user': 'postgres',
    'password': 'password'
}}
'''
        
        # Find class definition and inject database config
        class_match = f"class {scraper_name.upper()}():"
        if class_match in wrapped_content:
            wrapped_content = wrapped_content.replace(
                class_match,
                db_config_inject + class_match
            )
        
        # Modify __init__ method to use enhanced helper with database
        init_pattern = "self.helper = Helper()"
        enhanced_init = "self.helper = EnhancedHelper(DB_CONFIG)"
        wrapped_content = wrapped_content.replace(init_pattern, enhanced_init)
        
        # Wrap main scraping method with comprehensive error handling
        main_method_name = f"start_scraping_{scraper_name.lower()}"
        
        if f"def {main_method_name}(self):" in wrapped_content:
            # Find the method and wrap it
            method_start = wrapped_content.find(f"def {main_method_name}(self):")
            if method_start != -1:
                # Add error handling wrapper
                error_wrapper = f'''
    def {main_method_name}_with_error_handling(self):
        """Error-wrapped version of original scraping method"""
        scraper_name = "{scraper_name}"
        start_time = datetime.datetime.now()
        
        print(f"Starting scraper: {{scraper_name}} at {{start_time}}")
        
        try:
            # Call original scraping method
            result = self.{main_method_name}_original()
            
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            print(f"✓ Scraper {{scraper_name}} completed successfully in {{duration}}")
            
            # Log success
            self.log_scraper_result(scraper_name, "SUCCESS", str(duration), "")
            return result
            
        except Exception as e:
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            print(f"✗ Scraper {{scraper_name}} failed after {{duration}}")
            print(f"Error: {{error_msg}}")
            print(f"Traceback: {{error_trace}}")
            
            # Log failure
            self.log_scraper_result(scraper_name, "FAILED", str(duration), error_msg)
            
            # Continue processing other scrapers - don't crash the system
            return None
    
    def log_scraper_result(self, scraper_name, status, duration, error_msg):
        """Log scraper execution results"""
        try:
            log_entry = {{
                "scraper": scraper_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": status,
                "duration": duration,
                "error": error_msg
            }}
            
            log_file = f"./scrapers/logs/{{scraper_name}}_log.json"
            
            # Read existing logs
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            
            # Add new log entry
            logs.append(log_entry)
            
            # Keep only last 100 entries
            logs = logs[-100:]
            
            # Write back to file
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as log_error:
            print(f"Failed to log scraper result: {{log_error}}")

    def {main_method_name}(self):
        """Public method - calls error-wrapped version"""
        return self.{main_method_name}_with_error_handling()
'''
                
                # Rename original method
                wrapped_content = wrapped_content.replace(
                    f"def {main_method_name}(self):",
                    f"def {main_method_name}_original(self):"
                )
                
                # Find a good place to insert error wrapper (after class definition)
                class_def_end = wrapped_content.find(f"def {main_method_name}_original(self):")
                if class_def_end != -1:
                    # Insert error wrapper before original method
                    wrapped_content = (
                        wrapped_content[:class_def_end] + 
                        error_wrapper + 
                        wrapped_content[class_def_end:]
                    )
        
        return wrapped_content

    def create_master_runner(self):
        """Create master runner script for all scrapers"""
        runner_content = '''#!/usr/bin/env python3
"""
Master Scraper Runner for Bulletproof Package
Runs all integrated scrapers with error handling and monitoring
"""

import sys
import os
import json
import datetime
from pathlib import Path

# Add scrapers directory to path
sys.path.append(str(Path(__file__).parent / "scrapers"))

class ScraperRunner:
    def __init__(self):
        self.scrapers_dir = Path(__file__).parent / "scrapers"
        self.results = {}
        
        # List of all integrated scrapers
        self.scraper_modules = [
            "joemachensnissan", "joemachenscdjr", "joemachenshyundai", "kiaofcolumbia",
            "porschestlouis", "auffenberghyundai", "hondafrontenac", "bommaritocadillac", 
            "pappastoyota", "twincitytoyota", "serrahondaofallon", "southcountyautos",
            "glendalechryslerjeep", "davesinclairlincolnsouth", "suntrupkiasouth", "columbiabmw",
            "rustydrewingcadillac", "rustydrewingchevroletbuickgmc", "pundmannford", "stehouwerauto",
            "bmwofweststlouis", "bommaritowestcounty", "hwkia", "wcvolvocars",
            "joemachenstoyota", "suntruphyundaisouth", "landroverranchomirage", "jaguarranchomirage", 
            "indigoautogroup", "miniofstlouis", "suntrupfordkirkwood", "thoroughbredford",
            "spiritlexus", "frankletahonda", "columbiahonda", "davesinclairlincolnstpeters",
            "weberchev", "suntrupbuickgmc", "suntrupfordwest"
        ]
    
    def run_single_scraper(self, scraper_name):
        """Run a single scraper with error isolation"""
        print(f"\\n{'='*60}")
        print(f"Running scraper: {scraper_name}")
        print(f"{'='*60}")
        
        try:
            # Import scraper module
            module = __import__(scraper_name)
            
            # Get class (uppercase scraper name)
            scraper_class = getattr(module, scraper_name.upper())
            
            # Create data folders
            data_folder = f"./output_data/{datetime.datetime.now().strftime('%Y-%m-%d')}/"
            os.makedirs(data_folder, exist_ok=True)
            
            output_file = f"{data_folder}{scraper_name}_data.csv"
            
            # Initialize and run scraper
            scraper_instance = scraper_class(data_folder, output_file)
            
            # Call the main scraping method
            method_name = f"start_scraping_{scraper_name}"
            scraping_method = getattr(scraper_instance, method_name)
            
            result = scraping_method()
            
            self.results[scraper_name] = {
                "status": "SUCCESS",
                "timestamp": datetime.datetime.now().isoformat(),
                "output_file": output_file
            }
            
            print(f"✓ {scraper_name} completed successfully")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ {scraper_name} failed: {error_msg}")
            
            self.results[scraper_name] = {
                "status": "FAILED", 
                "timestamp": datetime.datetime.now().isoformat(),
                "error": error_msg
            }
            return False
    
    def run_all_scrapers(self):
        """Run all scrapers sequentially"""
        print(f"Starting batch run of {len(self.scraper_modules)} scrapers...")
        print(f"Start time: {datetime.datetime.now()}")
        
        successful = 0
        failed = 0
        
        for scraper_name in self.scraper_modules:
            try:
                if self.run_single_scraper(scraper_name):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Critical error running {scraper_name}: {e}")
                failed += 1
                
        print(f"\\n{'='*60}")
        print(f"BATCH RUN COMPLETE")
        print(f"{'='*60}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(self.scraper_modules)}")
        print(f"End time: {datetime.datetime.now()}")
        
        # Save results summary
        results_file = f"./scrapers/logs/batch_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"Results saved to: {results_file}")
    
    def run_selected_scrapers(self, scraper_names):
        """Run only selected scrapers"""
        print(f"Running selected scrapers: {', '.join(scraper_names)}")
        
        for scraper_name in scraper_names:
            if scraper_name in self.scraper_modules:
                self.run_single_scraper(scraper_name)
            else:
                print(f"✗ Unknown scraper: {scraper_name}")

def main():
    runner = ScraperRunner()
    
    if len(sys.argv) == 1:
        # Run all scrapers
        runner.run_all_scrapers()
    elif sys.argv[1] == "list":
        # List available scrapers  
        print("Available scrapers:")
        for scraper in runner.scraper_modules:
            print(f"  - {scraper}")
    else:
        # Run specific scrapers
        selected_scrapers = sys.argv[1:]
        runner.run_selected_scrapers(selected_scrapers)

if __name__ == "__main__":
    main()
'''
        
        runner_path = self.dest_path / "run_scrapers.py"
        with open(runner_path, 'w', encoding='utf-8') as f:
            f.write(runner_content)
            
        print("✓ Master scraper runner created")

    def integrate_all_scrapers(self):
        """Main integration method"""
        print("Starting scraper integration process...")
        print(f"Source: {self.source_path}")
        print(f"Destination: {self.dest_path}")
        print(f"Scrapers to integrate: {len(self.scraper_list)}")
        
        # Setup directory structure
        self.setup_directories()
        
        # Copy and enhance helper classes
        self.copy_helper_classes()
        
        # Process each scraper
        successful = 0
        failed = 0
        
        for scraper_name in self.scraper_list:
            try:
                if self.copy_and_wrap_scraper(scraper_name):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ Failed to integrate {scraper_name}: {e}")
                failed += 1
        
        # Create master runner
        self.create_master_runner()
        
        # Create __init__.py files for package structure
        (self.scrapers_dest / "__init__.py").touch()
        
        print(f"\n{'='*60}")
        print(f"INTEGRATION COMPLETE")
        print(f"{'='*60}")
        print(f"Successfully integrated: {successful}")
        print(f"Failed: {failed}")
        print(f"Total scrapers: {len(self.scraper_list)}")
        print(f"\nTo run scrapers:")
        print(f"  python run_scrapers.py                    # Run all scrapers")
        print(f"  python run_scrapers.py list               # List available scrapers")
        print(f"  python run_scrapers.py columbiahonda      # Run specific scraper")

def main():
    integrator = ScraperIntegrator()
    integrator.integrate_all_scrapers()

if __name__ == "__main__":
    main()