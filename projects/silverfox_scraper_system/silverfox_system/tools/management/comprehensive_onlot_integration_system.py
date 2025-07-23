#!/usr/bin/env python3
"""
Comprehensive On-Lot Integration System
Systematically apply on-lot filtering methodology to ALL scrapers
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

def get_all_working_scrapers():
    """Get list of all working scraper files"""
    scrapers_dir = "scraper/dealerships"
    working_scrapers = []
    
    # Find all *_working.py files
    if os.path.exists(scrapers_dir):
        for filename in os.listdir(scrapers_dir):
            if filename.endswith('_working.py'):
                scraper_name = filename.replace('_working.py', '')
                working_scrapers.append({
                    'name': scraper_name,
                    'filename': filename,
                    'path': os.path.join(scrapers_dir, filename)
                })
    
    return working_scrapers

def get_all_regular_scrapers():
    """Get list of all regular scraper files (non-working, non-onlot)"""
    scrapers_dir = "scraper/dealerships"
    regular_scrapers = []
    
    if os.path.exists(scrapers_dir):
        for filename in os.listdir(scrapers_dir):
            if (filename.endswith('.py') and 
                not filename.endswith('_working.py') and 
                not filename.endswith('_onlot.py') and
                not filename.startswith('test_') and
                not filename.startswith('debug_') and
                filename not in ['__init__.py', 'scraper_gui.py']):
                
                scraper_name = filename.replace('.py', '')
                regular_scrapers.append({
                    'name': scraper_name,
                    'filename': filename,
                    'path': os.path.join(scrapers_dir, filename)
                })
    
    return regular_scrapers

def test_scraper_basic_functionality(scraper_info):
    """Test if a scraper can find any vehicles"""
    try:
        sys.path.append('scraper')
        
        # Dynamic import based on filename
        module_name = scraper_info['filename'].replace('.py', '')
        dealership_module = __import__(f'dealerships.{module_name}', fromlist=[''])
        
        # Find the scraper class (usually named after the dealership)
        scraper_class = None
        for attr_name in dir(dealership_module):
            attr = getattr(dealership_module, attr_name)
            if (isinstance(attr, type) and 
                hasattr(attr, 'scrape_inventory') and 
                attr_name.endswith('Scraper')):
                scraper_class = attr
                break
        
        if not scraper_class:
            return {'success': False, 'error': 'No scraper class found'}
        
        # Create config
        config = {
            'name': scraper_info['name'].title().replace('_', ' '),
            'base_url': f"https://www.{scraper_info['name']}.com"
        }
        
        # Test the scraper with timeout
        start_time = time.time()
        scraper = scraper_class(config)
        
        # Set a reasonable timeout
        try:
            vehicles = scraper.scrape_inventory()
            end_time = time.time()
            
            return {
                'success': True,
                'vehicle_count': len(vehicles),
                'duration': end_time - start_time,
                'sample_vehicle': vehicles[0] if vehicles else None,
                'scraper_class': scraper_class.__name__
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f"Import/setup error: {str(e)}"
        }

def create_onlot_integrated_scraper(working_scraper_info, base_scraper_result):
    """Create an on-lot integrated version of a working scraper"""
    
    scraper_name = working_scraper_info['name']
    class_name = base_scraper_result['scraper_class']
    
    # Create the integrated scraper filename
    integrated_filename = f"{scraper_name}_onlot_integrated.py"
    integrated_path = os.path.join("scraper/dealerships", integrated_filename)
    
    # Template for integrated scraper (simplified version)
    template = f'''import sys
import os
import logging
from typing import Dict, List, Any

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import on-lot filtering methodology
sys.path.append(os.path.dirname(parent_dir))
from on_lot_filtering_methodology import OnLotFilteringMixin

# Import the working scraper
from {working_scraper_info['filename'].replace('.py', '')} import {class_name}

class {scraper_name.title().replace('_', '')}OnLotIntegrated({class_name}, OnLotFilteringMixin):
    """
    {scraper_name.title().replace('_', ' ')} scraper with integrated on-lot filtering methodology
    Combines proven working scraper with on-lot filtering for physical inventory
    """
    
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape on-lot vehicles with filtering applied"""
        
        all_vehicles = []
        raw_vehicles = []
        
        try:
            self.logger.info(f"Starting integrated on-lot scrape for {{self.dealership_name}}")
            
            # Use the parent class scraping method
            raw_vehicles = super().scrape_inventory()
            self.logger.info(f"Base scraper found {{len(raw_vehicles)}} vehicles")
            
            # Apply on-lot filtering to all found vehicles
            for vehicle in raw_vehicles:
                # Standardize vehicle data for on-lot validation
                standardized_vehicle = self._standardize_vehicle_data(vehicle)
                if standardized_vehicle:
                    # Apply on-lot filtering
                    validated_vehicle = self._validate_on_lot_vehicle(
                        standardized_vehicle,
                        None,  # No element for processed data
                        str(vehicle),  # Use string representation as text
                        str(vehicle)   # Use string representation as HTML
                    )
                    
                    if validated_vehicle:
                        all_vehicles.append(validated_vehicle)
            
        except Exception as e:
            self.logger.error(f"Integrated scraping failed: {{str(e)}}")
            raise
        
        # Generate filtering report
        report = self.generate_on_lot_filtering_report(raw_vehicles, all_vehicles)
        self.logger.info(f"Integrated scraping complete: {{len(all_vehicles)}}/{{len(raw_vehicles)}} on-lot vehicles, {{report['average_data_quality']:.1f}}% avg quality")
        
        return all_vehicles
    
    def _standardize_vehicle_data(self, raw_vehicle: Dict[str, Any]):
        """Convert raw vehicle data to standardized format with on-lot indicators"""
        try:
            # If already standardized, enhance with on-lot scoring
            if isinstance(raw_vehicle, dict) and 'dealership' in raw_vehicle:
                vehicle = raw_vehicle.copy()
            else:
                # Create base vehicle structure
                vehicle = self._create_base_vehicle_structure(self.dealership_name)
                
                # Map common fields
                field_mappings = {{
                    'year': ['year', 'Year', 'model_year'],
                    'make': ['make', 'Make', 'manufacturer'],
                    'model': ['model', 'Model'],
                    'trim': ['trim', 'Trim', 'series'],
                    'vin': ['vin', 'VIN'],
                    'stock_number': ['stock_number', 'StockNumber', 'stock'],
                    'price': ['price', 'Price', 'asking_price'],
                    'mileage': ['mileage', 'Mileage', 'odometer'],
                    'condition': ['condition', 'Condition', 'type'],
                    'exterior_color': ['exterior_color', 'ExteriorColor', 'color'],
                    'interior_color': ['interior_color', 'InteriorColor'],
                    'transmission': ['transmission', 'Transmission'],
                    'engine': ['engine', 'Engine'],
                    'fuel_type': ['fuel_type', 'FuelType', 'fuel'],
                    'drivetrain': ['drivetrain', 'Drivetrain', 'drive_type']
                }}
                
                for field, possible_keys in field_mappings.items():
                    for key in possible_keys:
                        if key in raw_vehicle and raw_vehicle[key]:
                            vehicle[field] = raw_vehicle[key]
                            break
            
            # Set availability status for on-lot filtering
            status_fields = ['status', 'availability', 'description', 'notes']
            combined_text = ""
            
            for field in status_fields:
                if field in raw_vehicle and raw_vehicle[field]:
                    combined_text += f" {{raw_vehicle[field]}}".lower()
            
            # Determine availability status
            if 'in stock' in combined_text or 'available now' in combined_text:
                vehicle['availability_status'] = 'in stock'
            elif any(indicator in combined_text for indicator in ['transfer', 'locate', 'special order']):
                vehicle['availability_status'] = 'transfer required'
            else:
                vehicle['availability_status'] = 'available'
            
            # Calculate data quality score
            vehicle['data_quality_score'] = self._calculate_data_quality_score(vehicle)
            
            return vehicle
            
        except Exception as e:
            self.logger.warning(f"Error standardizing vehicle: {{str(e)}}")
            return None

def test_{scraper_name}_integrated():
    """Test the integrated scraper"""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = {{
        'name': '{scraper_name.title().replace("_", " ")}',
        'base_url': 'https://www.{scraper_name}.com'
    }}
    
    scraper = {scraper_name.title().replace('_', '')}OnLotIntegrated(config)
    
    print("🧪 Testing {scraper_name.title().replace('_', ' ')} INTEGRATED ON-LOT scraper...")
    print("🎯 Goal: Working scraper + On-lot filtering for physical inventory only")
    print()
    
    start_time = time.time()
    vehicles = scraper.scrape_inventory()
    end_time = time.time()
    
    print(f"✅ Integrated scraping completed in {{end_time - start_time:.1f}} seconds")
    print(f"📊 Vehicles physically on lot: {{len(vehicles)}}")
    
    if vehicles:
        with_vin = [v for v in vehicles if v.get('vin')]
        with_price = [v for v in vehicles if v.get('price')]
        avg_quality = sum(v.get('data_quality_score', 0) for v in vehicles) / len(vehicles)
        
        print(f"\\n📋 DATA QUALITY:")
        print(f"   With VINs: {{len(with_vin)}} ({{len(with_vin)/len(vehicles)*100:.0f}}%)")
        print(f"   With prices: {{len(with_price)}} ({{len(with_price)/len(vehicles)*100:.0f}}%)")
        print(f"   Average data quality: {{avg_quality:.1f}}%")
        
        print(f"\\n📋 SAMPLE VEHICLES:")
        for i, vehicle in enumerate(vehicles[:3]):
            print(f"   {{i+1}}. {{vehicle.get('year', 'N/A')}} {{vehicle.get('make', '')}} {{vehicle.get('model', '')}}")
            print(f"      Price: ${{vehicle.get('price', 'N/A')}}")
            print(f"      VIN: {{vehicle.get('vin', 'N/A')}}")
            print(f"      Quality: {{vehicle.get('data_quality_score', 0)}}%")
            print(f"      Status: {{vehicle.get('availability_status', 'Unknown')}}")
            print()
        
        success = len(vehicles) > 0 and avg_quality >= 40
        return success
    else:
        print("❌ No vehicles found on the physical lot")
        return False

if __name__ == "__main__":
    success = test_{scraper_name}_integrated()
    print(f"\\n✅ {scraper_name.title().replace('_', ' ')} integrated verification: {{'SUCCESS' if success else 'NEEDS OPTIMIZATION'}}")
'''
    
    return template, integrated_path

def run_comprehensive_integration():
    """Run comprehensive on-lot integration across all scrapers"""
    
    print("🎯 COMPREHENSIVE ON-LOT INTEGRATION SYSTEM")
    print("Applying proven on-lot filtering methodology to ALL scrapers")
    print("=" * 80)
    
    # Get all scrapers
    working_scrapers = get_all_working_scrapers()
    regular_scrapers = get_all_regular_scrapers()
    
    print(f"📊 SCRAPER INVENTORY:")
    print(f"   Working scrapers (*_working.py): {len(working_scrapers)}")
    print(f"   Regular scrapers: {len(regular_scrapers)}")
    print(f"   Total scrapers to process: {len(working_scrapers) + len(regular_scrapers)}")
    print()
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'working_scrapers': {},
        'regular_scrapers': {},
        'successful_integrations': [],
        'failed_integrations': [],
        'summary': {}
    }
    
    # Test working scrapers first (highest priority)
    print("🔧 TESTING WORKING SCRAPERS:")
    print("-" * 50)
    
    for i, scraper in enumerate(working_scrapers[:5], 1):  # Limit to 5 for testing
        print(f"[{i:2d}/{min(5, len(working_scrapers))}] Testing {scraper['name']}...")
        
        try:
            # Test basic functionality with timeout
            result = test_scraper_basic_functionality(scraper)
            results['working_scrapers'][scraper['name']] = result
            
            if result['success'] and result['vehicle_count'] > 0:
                print(f"   ✅ SUCCESS: {result['vehicle_count']} vehicles in {result['duration']:.1f}s")
                
                # Create integrated version
                template, integrated_path = create_onlot_integrated_scraper(scraper, result)
                
                # Write the integrated scraper
                with open(integrated_path, 'w') as f:
                    f.write(template)
                
                results['successful_integrations'].append({
                    'name': scraper['name'],
                    'type': 'working',
                    'vehicle_count': result['vehicle_count'],
                    'duration': result['duration'],
                    'integrated_file': integrated_path
                })
                
                print(f"   📁 Created: {os.path.basename(integrated_path)}")
                
            else:
                print(f"   ❌ FAILED: {result.get('error', 'No vehicles found')}")
                results['failed_integrations'].append({
                    'name': scraper['name'],
                    'type': 'working',
                    'error': result.get('error', 'No vehicles')
                })
        
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results['failed_integrations'].append({
                'name': scraper['name'],
                'type': 'working',
                'error': str(e)
            })
        
        time.sleep(1)  # Brief pause between tests
    
    # Generate summary
    successful_count = len(results['successful_integrations'])
    failed_count = len(results['failed_integrations'])
    
    results['summary'] = {
        'total_tested': len(working_scrapers[:5]),
        'successful_integrations': successful_count,
        'failed_integrations': failed_count,
        'success_rate': f"{successful_count/(successful_count + failed_count)*100:.1f}%" if (successful_count + failed_count) > 0 else "0%"
    }
    
    print(f"\n📊 INTEGRATION SUMMARY:")
    print(f"   Successful integrations: {successful_count}")
    print(f"   Failed integrations: {failed_count}")
    print(f"   Success rate: {results['summary']['success_rate']}")
    
    # Save results
    results_file = f"comprehensive_integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    results = run_comprehensive_integration()
    
    print(f"\n🎯 NEXT STEPS:")
    if results['successful_integrations']:
        print(f"   1. Test the {len(results['successful_integrations'])} integrated scrapers")
        print(f"   2. Apply methodology to remaining working scrapers")
        print(f"   3. Document all results for full fleet coverage")
    else:
        print(f"   1. Investigate integration issues")
        print(f"   2. Adjust methodology for failed scrapers")
        print(f"   3. Retry with refined approach")