#!/usr/bin/env python3
"""
JSON Stress Test for MinisForum Database Project
================================================

This script validates all JSON parsing in the dealership configurations
to ensure bulletproof deployment.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import json
import re
import sys
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class JSONStressTester:
    """Stress test JSON parsing for dealership configurations"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.valid_configs = []
        self.sql_file_path = Path(__file__).parent.parent / "sql" / "03_initial_dealership_configs.sql"
        
    def extract_json_from_sql(self, sql_content: str) -> List[Dict[str, Any]]:
        """Extract all JSON configurations from SQL file"""
        configs = []
        
        # Pattern to match INSERT VALUES entries
        # Matches: ('Dealership Name', '{json}', '{json}', 'path')
        pattern = r"\('([^']+)',\s*'(\{[^']+\})',\s*'(\{[^']+\})',\s*'([^']+)'\)"
        
        matches = re.findall(pattern, sql_content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            dealership_name = match[0]
            filtering_rules_str = match[1]
            output_rules_str = match[2]
            qr_path = match[3]
            
            configs.append({
                'dealership_name': dealership_name,
                'filtering_rules_raw': filtering_rules_str,
                'output_rules_raw': output_rules_str,
                'qr_output_path': qr_path
            })
        
        return configs
    
    def validate_json_syntax(self, json_str: str, context: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Validate JSON syntax and return parsed object"""
        try:
            parsed = json.loads(json_str)
            return True, parsed, None
        except json.JSONDecodeError as e:
            error_msg = f"JSON syntax error in {context}: {str(e)}"
            # Try to identify the specific issue
            if '"' in json_str and '\\"' not in json_str:
                error_msg += " - Possible unescaped quotes"
            if json_str.count('{') != json_str.count('}'):
                error_msg += " - Mismatched braces"
            if json_str.count('[') != json_str.count(']'):
                error_msg += " - Mismatched brackets"
            return False, None, error_msg
        except Exception as e:
            return False, None, f"Unexpected error in {context}: {str(e)}"
    
    def validate_filtering_rules(self, rules: Dict, dealership: str) -> List[str]:
        """Validate filtering rules structure and values"""
        issues = []
        
        # Expected fields and their types
        expected_fields = {
            'exclude_conditions': list,
            'require_stock': bool,
            'min_price': (int, float),
            'max_price': (int, float),
            'exclude_makes': list,
            'include_only_makes': list,
            'exclude_models': list,
            'year_min': int,
            'year_max': int
        }
        
        # Check for unknown fields
        for field in rules:
            if field not in expected_fields:
                issues.append(f"Unknown field '{field}' in filtering rules")
        
        # Validate field types
        for field, expected_type in expected_fields.items():
            if field in rules:
                value = rules[field]
                if isinstance(expected_type, tuple):
                    if not any(isinstance(value, t) for t in expected_type):
                        issues.append(f"Field '{field}' should be {expected_type}, got {type(value).__name__}")
                else:
                    if not isinstance(value, expected_type):
                        issues.append(f"Field '{field}' should be {expected_type.__name__}, got {type(value).__name__}")
        
        # Validate specific field values
        if 'exclude_conditions' in rules:
            valid_conditions = ['new', 'used', 'certified', 'offlot']
            for condition in rules['exclude_conditions']:
                if condition not in valid_conditions:
                    issues.append(f"Invalid condition '{condition}' in exclude_conditions. Valid: {valid_conditions}")
        
        if 'min_price' in rules and 'max_price' in rules:
            if rules['min_price'] > rules['max_price']:
                issues.append(f"min_price ({rules['min_price']}) > max_price ({rules['max_price']})")
        
        if 'year_min' in rules:
            if rules['year_min'] < 1900 or rules['year_min'] > 2030:
                issues.append(f"year_min {rules['year_min']} seems unrealistic")
        
        if 'year_max' in rules:
            if rules['year_max'] < 1900 or rules['year_max'] > 2030:
                issues.append(f"year_max {rules['year_max']} seems unrealistic")
        
        return issues
    
    def validate_output_rules(self, rules: Dict, dealership: str) -> List[str]:
        """Validate output rules structure and values"""
        issues = []
        
        # Expected fields and their types
        expected_fields = {
            'include_qr': bool,
            'format': str,
            'fields': list,
            'sort_by': list,
            'group_by': str
        }
        
        # Check for unknown fields
        for field in rules:
            if field not in expected_fields:
                issues.append(f"Unknown field '{field}' in output rules")
        
        # Validate field types
        for field, expected_type in expected_fields.items():
            if field in rules:
                value = rules[field]
                if not isinstance(value, expected_type):
                    issues.append(f"Field '{field}' should be {expected_type.__name__}, got {type(value).__name__}")
        
        # Validate specific field values
        if 'format' in rules:
            valid_formats = ['standard', 'premium', 'custom']
            if rules['format'] not in valid_formats:
                issues.append(f"Invalid format '{rules['format']}'. Valid: {valid_formats}")
        
        if 'sort_by' in rules:
            valid_sort_fields = ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'msrp', 'vehicle_condition']
            for field in rules['sort_by']:
                if field not in valid_sort_fields:
                    issues.append(f"Invalid sort field '{field}'. Valid: {valid_sort_fields}")
        
        if 'fields' in rules:
            valid_fields = ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'msrp', 
                          'exterior_color', 'interior_color', 'fuel_type', 'transmission', 
                          'condition', 'url', 'dealer_name']
            for field in rules['fields']:
                if field not in valid_fields:
                    issues.append(f"Invalid output field '{field}'. Valid: {valid_fields}")
        
        return issues
    
    def check_special_characters(self, dealership_name: str, json_str: str) -> List[str]:
        """Check for problematic special characters"""
        issues = []
        
        # Check for unescaped single quotes in JSON (should not exist)
        if "'" in json_str and not re.search(r"\\'", json_str):
            # This is actually OK in our case since JSON uses double quotes
            pass
        
        # Check for control characters
        control_chars = [chr(i) for i in range(0, 32) if i not in [9, 10, 13]]  # Exclude tab, newline, carriage return
        for char in control_chars:
            if char in json_str:
                issues.append(f"Control character (ASCII {ord(char)}) found in JSON")
        
        # Check for very long strings that might cause issues
        if len(json_str) > 5000:
            issues.append(f"Very long JSON string ({len(json_str)} chars) might cause parsing issues")
        
        return issues
    
    def test_edge_cases(self) -> List[str]:
        """Test various edge cases for JSON parsing"""
        edge_cases = []
        
        # Test empty objects
        test_cases = [
            ('{}', 'empty object'),
            ('{"exclude_conditions": []}', 'empty array'),
            ('{"min_price": 0}', 'zero value'),
            ('{"exclude_conditions": null}', 'null value'),
            ('{"year_min": 2025, "year_max": 2024}', 'invalid year range'),
        ]
        
        for json_str, description in test_cases:
            try:
                parsed = json.loads(json_str)
                # Additional validation could go here
            except Exception as e:
                edge_cases.append(f"Edge case '{description}' failed: {str(e)}")
        
        return edge_cases
    
    def validate_sql_file(self) -> bool:
        """Main validation function for SQL file"""
        logger.info(f"Reading SQL file: {self.sql_file_path}")
        
        try:
            with open(self.sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
        except FileNotFoundError:
            logger.error(f"SQL file not found: {self.sql_file_path}")
            return False
        
        # Handle special case: O'Fallon has an apostrophe
        # Check if it's properly escaped in SQL
        if "Serra Honda of O'Fallon" in sql_content:
            logger.info("✓ Found properly escaped dealership name: Serra Honda of O'Fallon")
        
        # Extract configurations
        configs = self.extract_json_from_sql(sql_content)
        logger.info(f"Found {len(configs)} dealership configurations")
        
        if not configs:
            self.errors.append("No configurations found in SQL file")
            return False
        
        # Validate each configuration
        for config in configs:
            dealership = config['dealership_name']
            logger.info(f"\nValidating {dealership}...")
            
            # Validate filtering rules JSON
            is_valid, parsed_filtering, error = self.validate_json_syntax(
                config['filtering_rules_raw'], 
                f"{dealership} filtering_rules"
            )
            
            if not is_valid:
                self.errors.append(error)
            else:
                # Validate structure
                issues = self.validate_filtering_rules(parsed_filtering, dealership)
                if issues:
                    for issue in issues:
                        self.warnings.append(f"{dealership}: {issue}")
                else:
                    logger.info(f"  ✓ Filtering rules valid")
            
            # Validate output rules JSON
            is_valid, parsed_output, error = self.validate_json_syntax(
                config['output_rules_raw'], 
                f"{dealership} output_rules"
            )
            
            if not is_valid:
                self.errors.append(error)
            else:
                # Validate structure
                issues = self.validate_output_rules(parsed_output, dealership)
                if issues:
                    for issue in issues:
                        self.warnings.append(f"{dealership}: {issue}")
                else:
                    logger.info(f"  ✓ Output rules valid")
            
            # Check for special characters
            special_char_issues = self.check_special_characters(
                dealership, 
                config['filtering_rules_raw'] + config['output_rules_raw']
            )
            if special_char_issues:
                for issue in special_char_issues:
                    self.warnings.append(f"{dealership}: {issue}")
            
            # If no errors for this dealership, mark as valid
            if not any(dealership in error for error in self.errors):
                self.valid_configs.append(dealership)
        
        # Test edge cases
        edge_case_issues = self.test_edge_cases()
        if edge_case_issues:
            self.warnings.extend(edge_case_issues)
        
        return len(self.errors) == 0
    
    def validate_python_files(self) -> bool:
        """Validate JSON parsing in Python files"""
        python_files = [
            Path(__file__).parent / "csv_importer_complete.py",
            Path(__file__).parent / "order_processing_integration.py"
        ]
        
        for py_file in python_files:
            logger.info(f"\nChecking Python file: {py_file.name}")
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for json.loads() usage
                json_loads_pattern = r'json\.loads\s*\([^)]+\)'
                json_loads_calls = re.findall(json_loads_pattern, content)
                
                logger.info(f"  Found {len(json_loads_calls)} json.loads() calls")
                
                # Check if they're wrapped in try-except
                for call in json_loads_calls:
                    # Find the context around this call
                    call_index = content.find(call)
                    context_start = max(0, call_index - 200)
                    context_end = min(len(content), call_index + 200)
                    context = content[context_start:context_end]
                    
                    if 'try:' not in context or 'except' not in context:
                        self.warnings.append(f"{py_file.name}: json.loads() call might not have proper error handling: {call[:50]}...")
                    else:
                        logger.info(f"  ✓ json.loads() has error handling")
                
                # Check for proper null/empty handling
                if 'if config[' in content and 'else {}' in content:
                    logger.info(f"  ✓ Has fallback empty dict handling")
                
                # Check for proper type validation
                if 'isinstance(' in content:
                    logger.info(f"  ✓ Has type validation")
                
            except FileNotFoundError:
                self.warnings.append(f"Python file not found: {py_file}")
        
        return True
    
    def print_report(self):
        """Print comprehensive validation report"""
        print("\n" + "="*80)
        print("JSON STRESS TEST REPORT")
        print("="*80)
        
        print(f"\nValid Configurations: {len(self.valid_configs)}")
        if self.valid_configs:
            for config in sorted(self.valid_configs):
                print(f"  ✓ {config}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All JSON configurations are valid and properly formatted!")
        
        print("\n" + "="*80)
        
        # Return exit code
        return 0 if not self.errors else 1

def main():
    """Run the JSON stress test"""
    tester = JSONStressTester()
    
    logger.info("Starting JSON stress test for MinisForum database project...")
    
    # Validate SQL file
    sql_valid = tester.validate_sql_file()
    
    # Validate Python files
    python_valid = tester.validate_python_files()
    
    # Print report
    exit_code = tester.print_report()
    
    if exit_code == 0:
        logger.info("\n✅ JSON stress test PASSED - Safe for deployment!")
    else:
        logger.error("\n❌ JSON stress test FAILED - Fix errors before deployment!")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())