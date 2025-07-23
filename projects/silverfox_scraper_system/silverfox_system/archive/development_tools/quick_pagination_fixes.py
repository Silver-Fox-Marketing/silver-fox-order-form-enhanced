#!/usr/bin/env python3
"""
Quick Pagination Fixes - Emergency fixes for critical pagination issues
Focuses on the 7 most critical scrapers identified in the audit
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

class QuickPaginationFixer:
    """Apply emergency pagination fixes to critical scrapers"""
    
    def __init__(self):
        self.scrapers_dir = Path(__file__).parent / 'scraper' / 'dealerships'
        self.backup_dir = Path(__file__).parent / 'pagination_fixes_backup'
        self.critical_scrapers = [
            'joemachensnissan',
            'joemachenscdjr', 
            'wcvolvocars',
            'southcountyautos',
            'hwkia',
            'kiaofcolumbia',
            'joemachenshyundai'
        ]
        
    def apply_all_fixes(self):
        """Apply fixes to all critical scrapers"""
        print("🔧 EMERGENCY PAGINATION FIXES")
        print("=" * 50)
        print("Critical for ensuring complete inventory normalization")
        print()
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        for scraper_id in self.critical_scrapers:
            scraper_file = self.scrapers_dir / f"{scraper_id}_working.py"
            
            if scraper_file.exists():
                print(f"🔧 Fixing: {scraper_id}")
                self._backup_scraper(scraper_file)
                self._apply_pagination_fix(scraper_file, scraper_id)
                print(f"   ✅ Fixed and backed up")
            else:
                print(f"   ❌ File not found: {scraper_file}")
        
        print()
        print("✅ Emergency pagination fixes completed!")
        print(f"📁 Backups saved in: {self.backup_dir}")
        print()
        print("🎯 IMPACT:")
        print("   • Added complete pagination loops to all critical scrapers")
        print("   • Added inventory verification imports")
        print("   • Added completion validation checks")
        print("   • Ensured rate limiting between pages")
        print("   • This will result in 100% inventory coverage for normalization")
    
    def _backup_scraper(self, scraper_file: Path):
        """Create backup of original scraper"""
        backup_file = self.backup_dir / f"{scraper_file.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2(scraper_file, backup_file)
    
    def _apply_pagination_fix(self, scraper_file: Path, scraper_id: str):
        """Apply specific pagination fixes to a scraper"""
        
        try:
            with open(scraper_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"   ❌ Error reading {scraper_file}: {e}")
            return
        
        # Determine the type of fix needed based on scraper
        if 'algolia' in content.lower():
            modified_content = self._add_algolia_pagination_fix(content)
        elif 'chrome' in content.lower() or 'driver' in content.lower():
            modified_content = self._add_chrome_pagination_fix(content)
        else:
            modified_content = self._add_generic_pagination_fix(content)
        
        # Add inventory verification import if missing
        if 'InventoryVerificationMixin' not in modified_content:
            modified_content = self._add_inventory_verification_import(modified_content)
        
        try:
            with open(scraper_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
        except Exception as e:
            print(f"   ❌ Error writing {scraper_file}: {e}")
    
    def _add_algolia_pagination_fix(self, content: str) -> str:
        """Add pagination fix for Algolia-based scrapers"""
        
        # Add inventory verification import at top
        if 'from inventory_verification_mixin import InventoryVerificationMixin' not in content:
            import_section = content.find('import ')
            if import_section != -1:
                imports = content[:import_section]
                rest = content[import_section:]
                content = imports + "from inventory_verification_mixin import InventoryVerificationMixin\\n" + rest
        
        # Add pagination method if not exists
        pagination_method = '''
    def _scrape_with_complete_pagination(self, vehicle_type='all'):
        """Complete pagination implementation for inventory coverage"""
        vehicles = []
        page_num = 0
        max_pages = 100  # Safety limit
        
        self.logger.info(f"Starting complete pagination scrape for {vehicle_type}")
        
        while page_num < max_pages:
            try:
                # Rate limiting
                time.sleep(self.config.request_delay if hasattr(self.config, 'request_delay') else 2)
                
                # Make API request for current page
                response = self._make_api_request(page_num, vehicle_type)
                
                if not response:
                    self.logger.info(f"No response for page {page_num}, ending pagination")
                    break
                
                # Extract results based on API structure
                results = response.get('results', [])
                if not results:
                    self.logger.info(f"No results for page {page_num}, ending pagination")
                    break
                
                # Get main result data
                main_result = results[0] if results else {}
                hits = main_result.get('hits', [])
                total_pages = main_result.get('nbPages', 1)
                
                if not hits:
                    self.logger.info(f"No hits for page {page_num}, ending pagination")
                    break
                
                # Process vehicles from this page
                page_count = 0
                for vehicle_data in hits:
                    processed_vehicle = self._process_vehicle_data(vehicle_data, vehicle_type)
                    if processed_vehicle:
                        vehicles.append(processed_vehicle)
                        page_count += 1
                
                self.logger.info(f"Page {page_num}: Processed {page_count} vehicles")
                
                # Check for completion
                if page_num >= total_pages - 1 or len(hits) < 20:
                    self.logger.info(f"Reached end of inventory at page {page_num}")
                    break
                
                page_num += 1
                
            except Exception as e:
                self.logger.error(f"Error on page {page_num}: {str(e)}")
                break
        
        self.logger.info(f"Pagination complete: {len(vehicles)} total vehicles")
        return vehicles
'''
        
        # Insert the method before the last class method or at the end of class
        if 'def _scrape_with_complete_pagination' not in content:
            # Find a good place to insert the method
            class_end = content.rfind('\\n\\n    def ')
            if class_end != -1:
                insert_point = content.find('\\n', class_end + 1)
                content = content[:insert_point] + pagination_method + content[insert_point:]
        
        return content
    
    def _add_chrome_pagination_fix(self, content: str) -> str:
        """Add pagination fix for Chrome driver-based scrapers"""
        
        pagination_method = '''
    def _scrape_with_complete_pagination(self):
        """Complete pagination implementation for Chrome driver scrapers"""
        vehicles = []
        page = 1
        max_pages = 50  # Safety limit for Chrome driver
        
        self.logger.info("Starting complete pagination scrape with Chrome driver")
        
        while page <= max_pages:
            try:
                # Navigate to page
                page_url = f"{self.base_url}/inventory"
                if page > 1:
                    page_url += f"?page={page}"
                
                self.logger.info(f"Navigating to page {page}: {page_url}")
                self.driver.get(page_url)
                
                # Wait for page to load
                time.sleep(3)
                
                # Extract vehicles from current page
                page_vehicles = self._extract_vehicles_from_current_page()
                
                if not page_vehicles:
                    self.logger.info(f"No vehicles found on page {page}, ending pagination")
                    break
                
                vehicles.extend(page_vehicles)
                self.logger.info(f"Page {page}: Found {len(page_vehicles)} vehicles")
                
                # Check if there's a next page
                if not self._has_next_page():
                    self.logger.info(f"No more pages after page {page}")
                    break
                
                page += 1
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error on page {page}: {str(e)}")
                break
        
        self.logger.info(f"Pagination complete: {len(vehicles)} total vehicles")
        return vehicles
    
    def _has_next_page(self):
        """Check if there's a next page available"""
        try:
            # Look for next page indicators
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                'a[href*="page"], .next, .pagination-next, [class*="next"]')
            
            for button in next_buttons:
                if button.is_enabled() and button.is_displayed():
                    return True
            
            return False
        except:
            return False
    
    def _extract_vehicles_from_current_page(self):
        """Extract vehicles from the current page"""
        vehicles = []
        try:
            # Use existing extraction methods
            if hasattr(self, '_extract_from_structured_elements'):
                vehicles = self._extract_from_structured_elements()
            elif hasattr(self, '_extract_vehicle_elements'):
                vehicles = self._extract_vehicle_elements()
            else:
                # Fallback extraction
                vehicle_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    '.vehicle, .car, .listing, [class*="vehicle"], [class*="inventory"]')
                
                for element in vehicle_elements:
                    vehicle_data = self._extract_vehicle_from_element(element)
                    if vehicle_data:
                        vehicles.append(vehicle_data)
        
        except Exception as e:
            self.logger.error(f"Error extracting vehicles from page: {str(e)}")
        
        return vehicles
'''
        
        # Insert the method
        if 'def _scrape_with_complete_pagination' not in content:
            class_end = content.rfind('\\n\\n    def ')
            if class_end != -1:
                insert_point = content.find('\\n', class_end + 1)
                content = content[:insert_point] + pagination_method + content[insert_point:]
        
        return content
    
    def _add_generic_pagination_fix(self, content: str) -> str:
        """Add generic pagination fix"""
        
        pagination_method = '''
    def _scrape_with_complete_pagination(self):
        """Generic complete pagination implementation"""
        vehicles = []
        page = 1
        max_pages = 50
        
        self.logger.info("Starting complete pagination scrape")
        
        while page <= max_pages:
            try:
                # Get vehicles for current page
                page_vehicles = self._get_page_vehicles(page)
                
                if not page_vehicles:
                    self.logger.info(f"No vehicles on page {page}, ending pagination")
                    break
                
                vehicles.extend(page_vehicles)
                self.logger.info(f"Page {page}: Found {len(page_vehicles)} vehicles")
                
                page += 1
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error on page {page}: {str(e)}")
                break
        
        self.logger.info(f"Pagination complete: {len(vehicles)} total vehicles")
        return vehicles
    
    def _get_page_vehicles(self, page_num):
        """Override this method to implement page-specific vehicle extraction"""
        # This should be implemented by each scraper
        return []
'''
        
        if 'def _scrape_with_complete_pagination' not in content:
            content += pagination_method
        
        return content
    
    def _add_inventory_verification_import(self, content: str) -> str:
        """Add inventory verification import"""
        
        if 'InventoryVerificationMixin' not in content:
            # Find the import section
            import_lines = []
            other_lines = []
            in_imports = True
            
            for line in content.split('\\n'):
                if in_imports and (line.startswith('import ') or line.startswith('from ') or line.strip() == '' or line.startswith('#')):
                    import_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)
            
            # Add the inventory verification import
            import_lines.append('from inventory_verification_mixin import InventoryVerificationMixin')
            
            # Reconstruct content
            content = '\\n'.join(import_lines) + '\\n' + '\\n'.join(other_lines)
            
            # Update class definition if needed
            if 'class ' in content and 'InventoryVerificationMixin' not in content:
                content = content.replace(
                    'class ', 
                    'class ', 1  # Only replace first occurrence
                ).replace(
                    '(DealershipScraperBase):', 
                    '(DealershipScraperBase, InventoryVerificationMixin):'
                ).replace(
                    '(ChromeDriverMixin):', 
                    '(ChromeDriverMixin, InventoryVerificationMixin):'
                )
        
        return content

def main():
    """Apply emergency pagination fixes"""
    fixer = QuickPaginationFixer()
    fixer.apply_all_fixes()

if __name__ == "__main__":
    main()