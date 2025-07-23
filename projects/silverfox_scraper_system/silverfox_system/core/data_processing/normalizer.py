#!/usr/bin/env python3
"""
Vehicle Data Normalizer - Complete Normalization System
Handles the complete 22-column normalized dataset structure used by all scrapers
"""

import pandas as pd
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

class VehicleDataNormalizer:
    """Normalizes raw scraped vehicle data according to business rules"""
    
    def __init__(self, normalization_rules: Dict[str, Any] = None):
        """Initialize normalizer with rules"""
        self.normalization_rules = normalization_rules or self._load_default_rules()
        
    def _load_default_rules(self) -> Dict[str, Any]:
        """Load complete normalization rules for 22-column structure"""
        return {
            # Status normalization (condition/availability mapping)
            'status_mapping': {
                # Certified Pre-Owned variations
                'Certified Used': 'cpo',
                'Certified Pre-Owned': 'cpo',
                'Certified': 'cpo',
                'CPO': 'cpo',
                
                # Used/Pre-Owned variations
                'Used': 'po',
                'used': 'po',
                'Pre-Owned': 'po',
                'pre-owned': 'po',
                'Previously Owned': 'po',
                
                # New vehicle variations
                'new': 'new',
                'New': 'new',
                'NEW': 'new',
                
                # Off-lot/Transit variations (not physically on lot)
                'In-transit': 'offlot',
                'In-Transit': 'offlot',
                'Allocated': 'offlot',
                'In-Build-Phase': 'offlot',
                'In Transit': 'offlot',
                'In Transit to U.S.': 'offlot',
                'Arriving Soon': 'offlot',
                'In Production': 'offlot',
                'Build Phase': 'offlot',
                'Being Built': 'offlot',
                'Courtesy Vehicle': 'offlot',
                'In-Service Courtesy Vehicle': 'offlot',
                'Dealer Ordered': 'offlot',
                'In-Service FCTP': 'offlot',
                'In-service': 'offlot',
                'Factory Order': 'offlot',
                'Custom Order': 'offlot',
                
                # On-lot variations (physically available)
                'On-Lot': 'onlot',
                'In-Lot': 'onlot',
                'InStock': 'onlot',
                'In Stock': 'onlot',
                'In-stock': 'onlot',
                'Available': 'onlot',
                'On Lot': 'onlot',
                'Available at Retailer': 'onlot',
                'Ready for Delivery': 'onlot',
                'Immediate Delivery': 'onlot'
            },
            
            # Make normalization (brand standardization)
            'make_mapping': {
                'HYUNDAI': 'Hyundai',
                'hyundai': 'Hyundai',
                'HONDA': 'Honda',
                'honda': 'Honda',
                'TOYOTA': 'Toyota',
                'toyota': 'Toyota',
                'FORD': 'Ford',
                'ford': 'Ford',
                'BMW': 'BMW',
                'bmw': 'BMW',
                'CHEVROLET': 'Chevrolet',
                'chevrolet': 'Chevrolet',
                'CHEVY': 'Chevrolet',
                'chevy': 'Chevrolet',
                'CADILLAC': 'Cadillac',
                'cadillac': 'Cadillac',
                'BUICK': 'Buick',
                'buick': 'Buick',
                'GMC': 'GMC',
                'gmc': 'GMC',
                'KIA': 'Kia',
                'kia': 'Kia',
                'NISSAN': 'Nissan',
                'nissan': 'Nissan',
                'VOLVO': 'Volvo',
                'volvo': 'Volvo',
                'AUDI': 'Audi',
                'audi': 'Audi',
                'MERCEDES-BENZ': 'Mercedes-Benz',
                'mercedes-benz': 'Mercedes-Benz',
                'MERCEDES': 'Mercedes-Benz',
                'mercedes': 'Mercedes-Benz',
                'LEXUS': 'Lexus',
                'lexus': 'Lexus',
                'PORSCHE': 'Porsche',
                'porsche': 'Porsche',
                'JAGUAR': 'Jaguar',
                'jaguar': 'Jaguar',
                'LAND ROVER': 'Land Rover',
                'land rover': 'Land Rover',
                'MINI': 'MINI',
                'mini': 'MINI',
                'LINCOLN': 'Lincoln',
                'lincoln': 'Lincoln',
                'CHRYSLER': 'Chrysler',
                'chrysler': 'Chrysler',
                'DODGE': 'Dodge',
                'dodge': 'Dodge',
                'JEEP': 'Jeep',
                'jeep': 'Jeep',
                'RAM': 'Ram',
                'ram': 'Ram'
            },
            
            # Complete 22-column structure
            'output_fields': [
                'vin',                  # Vehicle Identification Number
                'stock_number',         # Dealer stock number
                'year',                 # Model year
                'make',                 # Vehicle make/brand
                'model',                # Vehicle model
                'trim',                 # Trim level/package
                'price',                # Listed price
                'msrp',                 # Manufacturer suggested retail price
                'mileage',              # Vehicle mileage
                'exterior_color',       # Exterior color
                'interior_color',       # Interior color
                'body_style',           # Body style (sedan, SUV, etc.)
                'fuel_type',            # Fuel type (gas, hybrid, electric)
                'transmission',         # Transmission type
                'engine',               # Engine description
                'original_status',      # Original status from source
                'normalized_status',    # Normalized status (new/po/cpo/etc.)
                'condition',            # Vehicle condition
                'dealer_name',          # Dealership name
                'dealer_id',            # Dealership identifier
                'url',                  # Vehicle detail page URL
                'scraped_at'            # Timestamp when scraped
            ],
            
            # Required fields for valid record
            'required_fields': [
                'vin', 'make', 'model', 'year', 'dealer_name'
            ],
            
            # Field mappings for normalization
            'field_mappings': {
                'condition': 'status_mapping',
                'status': 'status_mapping',
                'vehicle_status': 'status_mapping',
                'availability': 'status_mapping',
                'original_status': 'status_mapping',
                'normalized_status': 'status_mapping'
            },
            
            # Default values for missing fields
            'default_values': {
                'normalized_status': 'unknown',
                'condition': 'unknown',
                'original_status': 'unknown',
                'stock_number': '',
                'trim': '',
                'price': None,
                'msrp': None,
                'mileage': None,
                'exterior_color': '',
                'interior_color': '',
                'body_style': '',
                'fuel_type': '',
                'transmission': '',
                'engine': '',
                'url': '',
                'scraped_at': datetime.now().isoformat()
            }
        }
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize a complete dataframe to 22-column structure"""
        print(f"🔄 Normalizing {len(df)} vehicles...")
        
        # Create normalized dataframe with all required columns
        normalized_df = pd.DataFrame()
        
        # Process each output field
        for field in self.normalization_rules['output_fields']:
            if field in df.columns:
                # Field exists, copy with normalization
                normalized_df[field] = self._normalize_field(df[field], field)
            else:
                # Field missing, use default value
                default_val = self.normalization_rules['default_values'].get(field, '')
                normalized_df[field] = [default_val] * len(df)
        
        # Normalize specific fields
        normalized_df = self._normalize_makes(normalized_df)
        normalized_df = self._normalize_statuses(normalized_df)
        normalized_df = self._normalize_prices(normalized_df)
        normalized_df = self._normalize_years(normalized_df)
        normalized_df = self._clean_vins(normalized_df)
        
        # Filter out invalid records
        before_filter = len(normalized_df)
        normalized_df = self._filter_valid_records(normalized_df)
        after_filter = len(normalized_df)
        
        if before_filter != after_filter:
            print(f"🔍 Filtered out {before_filter - after_filter} invalid records")
        
        print(f"✅ Normalization complete: {len(normalized_df)} valid vehicles")
        return normalized_df
    
    def _normalize_field(self, series: pd.Series, field_name: str) -> pd.Series:
        """Normalize a specific field based on rules"""
        if field_name in self.normalization_rules['field_mappings']:
            mapping_type = self.normalization_rules['field_mappings'][field_name]
            mapping = self.normalization_rules.get(mapping_type, {})
            return series.map(mapping).fillna(series)
        return series
    
    def _normalize_makes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize vehicle makes to standard format"""
        if 'make' in df.columns:
            make_mapping = self.normalization_rules['make_mapping']
            df['make'] = df['make'].astype(str).map(make_mapping).fillna(df['make'])
        return df
    
    def _normalize_statuses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize status fields using status mapping"""
        status_mapping = self.normalization_rules['status_mapping']
        
        # Normalize condition field
        if 'condition' in df.columns:
            df['condition'] = df['condition'].astype(str).map(status_mapping).fillna(df['condition'])
        
        # Normalize normalized_status field
        if 'normalized_status' in df.columns:
            df['normalized_status'] = df['normalized_status'].astype(str).map(status_mapping).fillna(df['normalized_status'])
        
        # If normalized_status is still unknown, try to derive from condition
        if 'condition' in df.columns and 'normalized_status' in df.columns:
            mask = (df['normalized_status'] == 'unknown') | (df['normalized_status'].isna())
            df.loc[mask, 'normalized_status'] = df.loc[mask, 'condition'].map(status_mapping).fillna('unknown')
        
        return df
    
    def _normalize_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize price fields to numeric values"""
        for price_field in ['price', 'msrp']:
            if price_field in df.columns:
                df[price_field] = df[price_field].apply(self._extract_price)
        return df
    
    def _extract_price(self, price_str) -> Optional[float]:
        """Extract numeric price from string"""
        if pd.isna(price_str) or price_str is None:
            return None
        
        # Convert to string
        price_str = str(price_str).strip()
        
        # Handle special cases
        if price_str.lower() in ['', 'call for price', 'please call for price', 'n/a', 'na']:
            return None
        
        # Extract numeric value using regex
        price_match = re.search(r'[\d,]+(?:\.\d{2})?', price_str.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group().replace(',', ''))
            except ValueError:
                return None
        
        return None
    
    def _normalize_years(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize year field to integer"""
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        return df
    
    def _clean_vins(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate VIN fields"""
        if 'vin' in df.columns:
            # Remove non-alphanumeric characters and convert to uppercase
            df['vin'] = df['vin'].astype(str).str.replace(r'[^A-Za-z0-9]', '', regex=True).str.upper()
            
            # Replace empty strings with NaN
            df['vin'] = df['vin'].replace('', pd.NA)
        
        return df
    
    def _filter_valid_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out records missing required fields"""
        mask = pd.Series([True] * len(df))
        
        for field in self.normalization_rules['required_fields']:
            if field in df.columns:
                # Check for non-empty values
                field_mask = df[field].notna() & (df[field].astype(str).str.strip() != '')
                mask = mask & field_mask
        
        return df[mask].copy()
    
    def normalize_csv_file(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """Normalize a raw CSV file and save to normalized CSV"""
        try:
            print(f"📂 Starting normalization of {input_file}")
            
            # Read raw CSV data
            df = pd.read_csv(input_file)
            original_count = len(df)
            
            print(f"📊 Loaded {original_count} records from raw CSV")
            
            # Normalize the data
            normalized_df = self.normalize_dataframe(df)
            normalized_count = len(normalized_df)
            
            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Save normalized CSV with all 22 columns in correct order
            normalized_df[self.normalization_rules['output_fields']].to_csv(output_file, index=False)
            
            # Generate statistics
            stats = {
                'input_file': input_file,
                'output_file': output_file,
                'original_count': original_count,
                'normalized_count': normalized_count,
                'filtered_count': original_count - normalized_count,
                'success_rate': (normalized_count / original_count * 100) if original_count > 0 else 0,
                'normalization_timestamp': datetime.now().isoformat(),
                'column_count': len(self.normalization_rules['output_fields']),
                'columns': self.normalization_rules['output_fields']
            }
            
            print(f"✅ Normalization complete:")
            print(f"   📥 Input: {original_count} records")
            print(f"   📤 Output: {normalized_count} records")
            print(f"   📊 Success rate: {stats['success_rate']:.1f}%")
            print(f"   💾 Saved to: {output_file}")
            
            return stats
            
        except Exception as e:
            error_stats = {
                'success': False,
                'error': str(e),
                'input_file': input_file,
                'output_file': output_file,
                'normalization_timestamp': datetime.now().isoformat()
            }
            print(f"❌ Normalization failed: {e}")
            return error_stats
    
    def get_normalization_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a detailed normalization report"""
        report = {
            'total_records': len(df),
            'column_count': len(df.columns),
            'missing_fields': {},
            'data_quality': {},
            'normalization_coverage': {}
        }
        
        # Check for missing required fields
        for field in self.normalization_rules['required_fields']:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                report['missing_fields'][field] = {
                    'missing_count': int(missing_count),
                    'missing_percentage': float(missing_count / len(df) * 100)
                }
        
        # Data quality metrics
        if 'vin' in df.columns:
            valid_vins = df['vin'].astype(str).str.len() == 17
            report['data_quality']['valid_vins'] = int(valid_vins.sum())
        
        if 'year' in df.columns:
            current_year = datetime.now().year
            reasonable_years = (df['year'] >= 1990) & (df['year'] <= current_year + 2)
            report['data_quality']['reasonable_years'] = int(reasonable_years.sum())
        
        if 'price' in df.columns:
            valid_prices = df['price'].notna() & (df['price'] > 0)
            report['data_quality']['valid_prices'] = int(valid_prices.sum())
        
        return report

# Backwards compatibility
DataNormalizer = VehicleDataNormalizer

if __name__ == "__main__":
    # Test normalization
    normalizer = VehicleDataNormalizer()
    
    print("🚗 Vehicle Data Normalizer - Complete 22-Column System")
    print("=" * 60)
    
    # Display normalization rules summary
    rules = normalizer.normalization_rules
    print(f"📊 Output columns: {len(rules['output_fields'])}")
    print(f"🔧 Status mappings: {len(rules['status_mapping'])}")
    print(f"🏢 Make mappings: {len(rules['make_mapping'])}")
    print(f"✅ Required fields: {', '.join(rules['required_fields'])}")
    
    print("\n🎯 Complete 22-Column Structure:")
    for i, field in enumerate(rules['output_fields'], 1):
        print(f"   {i:2d}. {field}")
    
    print(f"\n🔄 Ready to normalize vehicle data to standardized format")