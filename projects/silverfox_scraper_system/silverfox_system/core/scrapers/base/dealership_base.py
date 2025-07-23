from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import json
import os
from datetime import datetime
import logging
from config import ScraperConfig
from validators import DataValidator
from utils import setup_logging, RateLimiter, save_data, load_data
from exceptions import *

class DealershipScraperBase(ABC):
    """Base class for individual dealership scrapers"""
    
    def __init__(self, dealership_config: Dict[str, Any], scraper_config: ScraperConfig = None):
        self.dealership_name = dealership_config.get('name', 'Unknown Dealership')
        self.dealership_id = dealership_config.get('id', self.dealership_name.lower().replace(' ', '_'))
        self.config = scraper_config or ScraperConfig()
        
        # Dealership-specific configuration
        self.dealership_config = dealership_config
        self.base_url = dealership_config.get('base_url', '')
        self.api_endpoint = dealership_config.get('api_endpoint', '')
        
        # Filtering rules specific to this dealership
        self.filtering_rules = dealership_config.get('filtering_rules', {})
        
        # Data extraction configuration
        self.extraction_config = dealership_config.get('extraction_config', {})
        
        # Processed items tracking
        self.processed_vehicles = set()
        self.processed_file = f"output_data/{self.dealership_id}_processed.json"
        
        # Setup logging
        self.logger = setup_logging(
            self.config.log_level, 
            f"logs/{self.dealership_id}.log"
        )
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            self.config.rate_limit_per_minute,
            60
        )
        
        # Data validator
        validation_rules = self.filtering_rules.get('validation_rules', {})
        self.validator = DataValidator(validation_rules)
        
        # Load previously processed vehicles
        self._load_processed_vehicles()
    
    @abstractmethod
    def scrape_inventory(self) -> List[Dict[str, Any]]:
        """Scrape vehicle inventory for this dealership"""
        pass
    
    @abstractmethod
    def extract_vehicle_data(self, raw_data: Any) -> Dict[str, Any]:
        """Extract vehicle data from raw scraping results"""
        pass
    
    def apply_conditional_filters(self, vehicles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply dealership-specific conditional filters"""
        if not self.filtering_rules.get('conditional_filters'):
            return vehicles
        
        filtered_vehicles = []
        filters = self.filtering_rules['conditional_filters']
        
        for vehicle in vehicles:
            should_include = True
            
            # Apply price range filters
            if 'price_range' in filters and 'price' in vehicle:
                price = vehicle.get('price', 0)
                if price:
                    min_price = filters['price_range'].get('min', 0)
                    max_price = filters['price_range'].get('max', float('inf'))
                    if not (min_price <= price <= max_price):
                        should_include = False
                        self.logger.debug(f"Vehicle {vehicle.get('vin', 'unknown')} filtered out by price range")
            
            # Apply year filters
            if 'year_range' in filters and 'year' in vehicle:
                year = vehicle.get('year', 0)
                if year:
                    min_year = filters['year_range'].get('min', 1900)
                    max_year = filters['year_range'].get('max', datetime.now().year + 1)
                    if not (min_year <= year <= max_year):
                        should_include = False
                        self.logger.debug(f"Vehicle {vehicle.get('vin', 'unknown')} filtered out by year range")
            
            # Apply make/model filters
            if 'allowed_makes' in filters and 'make' in vehicle:
                if vehicle['make'].lower() not in [make.lower() for make in filters['allowed_makes']]:
                    should_include = False
                    self.logger.debug(f"Vehicle {vehicle.get('vin', 'unknown')} filtered out by make restriction")
            
            if 'excluded_makes' in filters and 'make' in vehicle:
                if vehicle['make'].lower() in [make.lower() for make in filters['excluded_makes']]:
                    should_include = False
                    self.logger.debug(f"Vehicle {vehicle.get('vin', 'unknown')} filtered out by make exclusion")
            
            # Apply condition filters (new/used)
            if 'allowed_conditions' in filters and 'condition' in vehicle:
                if vehicle['condition'].lower() not in [cond.lower() for cond in filters['allowed_conditions']]:
                    should_include = False
                    self.logger.debug(f"Vehicle {vehicle.get('vin', 'unknown')} filtered out by condition")
            
            # Apply custom field filters
            if 'custom_filters' in filters:
                for field_name, field_rules in filters['custom_filters'].items():
                    if field_name in vehicle:
                        field_value = vehicle[field_name]
                        
                        # Required value filter
                        if 'required_values' in field_rules:
                            if field_value not in field_rules['required_values']:
                                should_include = False
                                break
                        
                        # Excluded value filter
                        if 'excluded_values' in field_rules:
                            if field_value in field_rules['excluded_values']:
                                should_include = False
                                break
                        
                        # Pattern matching filter
                        if 'pattern' in field_rules:
                            import re
                            if not re.match(field_rules['pattern'], str(field_value)):
                                should_include = False
                                break
            
            # Apply location-based filters
            if 'location_filters' in filters:
                location_config = filters['location_filters']
                if 'required_location' in location_config and 'location' in vehicle:
                    if location_config['required_location'].lower() not in vehicle['location'].lower():
                        should_include = False
                        self.logger.debug(f"Vehicle {vehicle.get('vin', 'unknown')} filtered out by location")
            
            if should_include:
                filtered_vehicles.append(vehicle)
        
        self.logger.info(f"Applied conditional filters: {len(vehicles)} -> {len(filtered_vehicles)} vehicles")
        return filtered_vehicles
    
    def process_vehicle(self, vehicle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual vehicle with validation and deduplication"""
        try:
            # Check for duplicates
            vehicle_id = vehicle_data.get('vin') or vehicle_data.get('stock_number') or vehicle_data.get('url')
            if vehicle_id in self.processed_vehicles:
                self.logger.debug(f"Skipping duplicate vehicle: {vehicle_id}")
                return None
            
            # Validate vehicle data
            validated_vehicle = self.validator.validate_item(vehicle_data)
            
            # Add processing metadata
            validated_vehicle['scraped_at'] = datetime.now().isoformat()
            validated_vehicle['dealership_id'] = self.dealership_id
            validated_vehicle['dealership_name'] = self.dealership_name
            
            # Mark as processed
            self.processed_vehicles.add(vehicle_id)
            
            return validated_vehicle
            
        except ValidationError as e:
            self.logger.warning(f"Validation failed for vehicle: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing vehicle: {str(e)}")
            return None
    
    def run_scraping_session(self) -> Dict[str, Any]:
        """Run complete scraping session for this dealership"""
        session_start = datetime.now()
        self.logger.info(f"Starting scraping session for {self.dealership_name}")
        
        try:
            # Scrape raw inventory
            raw_inventory = self.scrape_inventory()
            self.logger.info(f"Scraped {len(raw_inventory)} raw vehicles")
            
            # Extract and process vehicle data
            processed_vehicles = []
            for raw_vehicle in raw_inventory:
                try:
                    vehicle_data = self.extract_vehicle_data(raw_vehicle)
                    processed_vehicle = self.process_vehicle(vehicle_data)
                    if processed_vehicle:
                        processed_vehicles.append(processed_vehicle)
                except Exception as e:
                    self.logger.error(f"Error processing vehicle: {str(e)}")
                    continue
            
            # Apply conditional filters
            filtered_vehicles = self.apply_conditional_filters(processed_vehicles)
            
            # Save results
            output_file = f"output_data/{self.dealership_id}_{session_start.strftime('%Y%m%d_%H%M%S')}.json"
            save_data(filtered_vehicles, output_file)
            
            # Also save as CSV for pipeline processing
            import pandas as pd
            csv_file = output_file.replace('.json', '.csv')
            df = pd.DataFrame(filtered_vehicles)
            df.to_csv(csv_file, index=False)
            
            # Update processed vehicles log
            self._save_processed_vehicles()
            
            session_result = {
                'dealership_id': self.dealership_id,
                'dealership_name': self.dealership_name,
                'session_start': session_start.isoformat(),
                'session_end': datetime.now().isoformat(),
                'raw_count': len(raw_inventory),
                'processed_count': len(processed_vehicles),
                'filtered_count': len(filtered_vehicles),
                'output_file': output_file,
                'success': True
            }
            
            self.logger.info(f"Scraping session completed successfully: {len(filtered_vehicles)} vehicles")
            return session_result
            
        except Exception as e:
            self.logger.error(f"Scraping session failed: {str(e)}")
            return {
                'dealership_id': self.dealership_id,
                'dealership_name': self.dealership_name,
                'session_start': session_start.isoformat(),
                'session_end': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    
    def _load_processed_vehicles(self):
        """Load previously processed vehicles"""
        try:
            processed_data = load_data(self.processed_file)
            if processed_data:
                self.processed_vehicles = set(processed_data.get('processed_ids', []))
                self.logger.info(f"Loaded {len(self.processed_vehicles)} previously processed vehicles")
        except Exception as e:
            self.logger.warning(f"Could not load processed vehicles: {str(e)}")
            self.processed_vehicles = set()
    
    def _save_processed_vehicles(self):
        """Save processed vehicles to file"""
        try:
            processed_data = {
                'dealership_id': self.dealership_id,
                'last_updated': datetime.now().isoformat(),
                'processed_ids': list(self.processed_vehicles)
            }
            save_data(processed_data, self.processed_file)
        except Exception as e:
            self.logger.error(f"Could not save processed vehicles: {str(e)}")
    
    def get_filtering_rules(self) -> Dict[str, Any]:
        """Get current filtering rules for this dealership"""
        return self.filtering_rules
    
    def update_filtering_rules(self, new_rules: Dict[str, Any]) -> bool:
        """Update filtering rules for this dealership"""
        try:
            self.filtering_rules.update(new_rules)
            # Update validator if validation rules changed
            if 'validation_rules' in new_rules:
                self.validator = DataValidator(self.filtering_rules.get('validation_rules', {}))
            self.logger.info("Filtering rules updated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update filtering rules: {str(e)}")
            return False