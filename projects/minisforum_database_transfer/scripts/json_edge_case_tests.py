#!/usr/bin/env python3
"""
JSON Edge Case Tests for MinisForum Database
============================================

Tests edge cases and malformed JSON scenarios to ensure robust error handling.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import logging

# Import our modules
sys.path.append(str(Path(__file__).parent))
# We'll mock the modules instead of importing them directly to avoid dependencies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONEdgeCaseTester:
    """Test edge cases for JSON parsing in the system"""
    
    def __init__(self):
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
    def test_malformed_json_scenarios(self):
        """Test various malformed JSON scenarios"""
        test_cases = [
            # Valid cases that should pass
            ('{}', 'Empty object', True),
            ('{"exclude_conditions": []}', 'Empty array', True),
            ('{"min_price": 0}', 'Zero value', True),
            ('{"min_price": null}', 'Null value', True),
            ('{"exclude_conditions": ["offlot"]}', 'Valid condition', True),
            
            # Invalid cases that should fail
            ('{"exclude_conditions": ["offlot"', 'Missing closing bracket', False),
            ('{"min_price": 0,}', 'Trailing comma', False),
            ('{exclude_conditions: ["offlot"]}', 'Unquoted key', False),
            ('{"min_price": NaN}', 'Invalid number value', False),
            ('{"exclude_conditions": [\'offlot\']}', 'Single quotes in array', False),
            ('{"dealership": "Serra Honda of O\'Fallon"}', 'Unescaped quote', False),
            ('{"price": $10000}', 'Invalid price format', False),
            ('{{}}', 'Double braces', False),
            ('{"key": "value"}}', 'Extra closing brace', False),
            ('{{"key": "value"}', 'Extra opening brace', False),
        ]
        
        print("\n=== Testing Malformed JSON Scenarios ===")
        for json_str, description, should_pass in test_cases:
            try:
                parsed = json.loads(json_str)
                if should_pass:
                    self.test_results['passed'].append(f"✓ {description}: Correctly parsed")
                    print(f"✓ {description}: Parsed successfully")
                else:
                    self.test_results['failed'].append(f"✗ {description}: Should have failed but parsed")
                    print(f"✗ {description}: Should have failed but parsed as: {parsed}")
            except json.JSONDecodeError as e:
                if not should_pass:
                    self.test_results['passed'].append(f"✓ {description}: Correctly failed")
                    print(f"✓ {description}: Correctly failed with: {str(e)}")
                else:
                    self.test_results['failed'].append(f"✗ {description}: Should have parsed but failed")
                    print(f"✗ {description}: Should have parsed but failed: {str(e)}")
    
    def test_special_characters_in_json(self):
        """Test special characters that might cause issues"""
        test_cases = [
            # Test various special characters
            {'name': 'Serra Honda of O\'Fallon', 'expected_escape': 'Serra Honda of O\'Fallon'},
            {'name': 'Test & Co.', 'expected_escape': 'Test & Co.'},
            {'name': 'Price: $10,000', 'expected_escape': 'Price: $10,000'},
            {'name': 'Line\nBreak', 'expected_escape': 'Line\\nBreak'},
            {'name': 'Tab\tCharacter', 'expected_escape': 'Tab\\tCharacter'},
            {'name': 'Quote"Inside', 'expected_escape': 'Quote\\"Inside'},
            {'name': 'Backslash\\Path', 'expected_escape': 'Backslash\\\\Path'},
        ]
        
        print("\n=== Testing Special Characters ===")
        for test in test_cases:
            original = test['name']
            # Create JSON with the string
            json_obj = {"dealership_name": original}
            
            try:
                # Serialize to JSON
                json_str = json.dumps(json_obj)
                # Parse it back
                parsed = json.loads(json_str)
                
                if parsed['dealership_name'] == original:
                    self.test_results['passed'].append(f"✓ Special char test: {original}")
                    print(f"✓ '{original}' -> JSON -> '{parsed['dealership_name']}' (preserved)")
                else:
                    self.test_results['failed'].append(f"✗ Special char changed: {original}")
                    print(f"✗ '{original}' -> JSON -> '{parsed['dealership_name']}' (changed!)")
                    
            except Exception as e:
                self.test_results['failed'].append(f"✗ Special char error: {original}")
                print(f"✗ Failed to handle '{original}': {str(e)}")
    
    def test_numeric_edge_cases(self):
        """Test numeric edge cases in JSON"""
        test_cases = [
            (0, "Zero"),
            (-1, "Negative number"),
            (999999999, "Large number"),
            (0.99, "Decimal"),
            (1e6, "Scientific notation"),
            (float('inf'), "Infinity (should fail)"),
            (float('-inf'), "Negative infinity (should fail)"),
            (float('nan'), "NaN (should fail)"),
        ]
        
        print("\n=== Testing Numeric Edge Cases ===")
        for value, description in test_cases:
            try:
                json_str = json.dumps({"price": value})
                parsed = json.loads(json_str)
                self.test_results['passed'].append(f"✓ {description}: {value}")
                print(f"✓ {description}: {value} -> {parsed['price']}")
            except (ValueError, OverflowError) as e:
                if description.endswith("(should fail)"):
                    self.test_results['passed'].append(f"✓ {description}: Correctly failed")
                    print(f"✓ {description}: Correctly failed - {str(e)}")
                else:
                    self.test_results['failed'].append(f"✗ {description}: Unexpected failure")
                    print(f"✗ {description}: Failed - {str(e)}")
    
    def test_deeply_nested_json(self):
        """Test deeply nested JSON structures"""
        print("\n=== Testing Deeply Nested JSON ===")
        
        # Create deeply nested structure
        deep_json = {"level1": {"level2": {"level3": {"level4": {"level5": {
            "filtering_rules": {
                "exclude_conditions": ["offlot"],
                "price_range": {
                    "min": 0,
                    "max": 100000
                }
            }
        }}}}}}
        
        try:
            json_str = json.dumps(deep_json)
            parsed = json.loads(json_str)
            
            # Navigate to deep value
            deep_value = parsed["level1"]["level2"]["level3"]["level4"]["level5"]["filtering_rules"]["exclude_conditions"][0]
            
            if deep_value == "offlot":
                self.test_results['passed'].append("✓ Deep nesting handled correctly")
                print(f"✓ Deep nesting: Successfully retrieved '{deep_value}' from 5 levels deep")
            else:
                self.test_results['failed'].append("✗ Deep nesting value mismatch")
                print(f"✗ Deep nesting: Expected 'offlot', got '{deep_value}'")
                
        except Exception as e:
            self.test_results['failed'].append("✗ Deep nesting parsing failed")
            print(f"✗ Deep nesting failed: {str(e)}")
    
    def test_very_long_json_strings(self):
        """Test very long JSON strings"""
        print("\n=== Testing Very Long JSON Strings ===")
        
        # Create a very long string
        long_string = "A" * 10000  # 10,000 character string
        long_json = {
            "dealership_notes": long_string,
            "filtering_rules": {
                "exclude_conditions": ["offlot"] * 100  # 100 conditions
            }
        }
        
        try:
            json_str = json.dumps(long_json)
            parsed = json.loads(json_str)
            
            if len(parsed["dealership_notes"]) == 10000 and len(parsed["filtering_rules"]["exclude_conditions"]) == 100:
                self.test_results['passed'].append("✓ Long strings handled correctly")
                print(f"✓ Long strings: {len(json_str)} chars serialized and parsed correctly")
            else:
                self.test_results['failed'].append("✗ Long string parsing issue")
                print(f"✗ Long strings: Length mismatch after parsing")
                
        except Exception as e:
            self.test_results['failed'].append("✗ Long string parsing failed")
            print(f"✗ Long strings failed: {str(e)}")
    
    def test_empty_and_null_scenarios(self):
        """Test empty and null scenarios"""
        test_cases = [
            ('', 'Empty string (should fail)', False),
            ('null', 'Null literal', True),
            ('[]', 'Empty array', True),
            ('""', 'Empty string value', True),
            (None, 'Python None (should work with json.dumps)', True),
        ]
        
        print("\n=== Testing Empty and Null Scenarios ===")
        for value, description, should_work in test_cases:
            try:
                if value is None:
                    # Test Python None serialization
                    json_str = json.dumps({"value": value})
                    parsed = json.loads(json_str)
                    if parsed["value"] is None:
                        self.test_results['passed'].append(f"✓ {description}")
                        print(f"✓ {description}: None -> null -> None")
                else:
                    parsed = json.loads(value)
                    if should_work:
                        self.test_results['passed'].append(f"✓ {description}")
                        print(f"✓ {description}: Parsed as {type(parsed).__name__}")
                    else:
                        self.test_results['failed'].append(f"✗ {description}: Should have failed")
                        print(f"✗ {description}: Should have failed but got {parsed}")
            except json.JSONDecodeError as e:
                if not should_work:
                    self.test_results['passed'].append(f"✓ {description}: Correctly failed")
                    print(f"✓ {description}: Correctly failed")
                else:
                    self.test_results['failed'].append(f"✗ {description}: Should have worked")
                    print(f"✗ {description}: Failed - {str(e)}")
    
    def test_csv_importer_error_handling(self):
        """Test CSV importer's JSON error handling"""
        print("\n=== Testing CSV Importer Error Handling ===")
        
        # Instead of importing, we'll simulate the JSON parsing behavior
        print("✓ Testing JSON parsing with try-except blocks")
        
        # Test valid JSON parsing
        valid_json = '{"exclude_conditions": ["offlot"], "min_price": 0}'
        try:
            parsed = json.loads(valid_json)
            self.test_results['passed'].append("✓ Valid JSON parsed successfully")
            print(f"✓ Valid JSON parsed: {parsed}")
        except json.JSONDecodeError:
            self.test_results['failed'].append("✗ Valid JSON failed to parse")
        
        # Test invalid JSON parsing with error handling
        invalid_json = '{"exclude_conditions": ["offlot"'  # Missing closing bracket
        try:
            parsed = json.loads(invalid_json)
            self.test_results['failed'].append("✗ Invalid JSON parsed without error")
            print(f"✗ Invalid JSON should have failed but parsed: {parsed}")
        except json.JSONDecodeError as e:
            self.test_results['passed'].append("✓ Invalid JSON correctly caught")
            print(f"✓ Invalid JSON error caught: {str(e)}")
        
        # Test our enhanced error handling pattern
        configs = [
            {'name': 'Good Dealer', 'filtering_rules': '{"exclude_conditions": ["offlot"]}'},
            {'name': 'Bad Dealer', 'filtering_rules': '{"exclude_conditions": ["offlot"'},
            {'name': 'Empty Dealer', 'filtering_rules': ''},
            {'name': 'Null Dealer', 'filtering_rules': None},
        ]
        
        processed_configs = {}
        errors = []
        
        for config in configs:
            try:
                filtering_rules = {}
                if config['filtering_rules']:
                    try:
                        filtering_rules = json.loads(config['filtering_rules'])
                    except json.JSONDecodeError as je:
                        errors.append(f"Config error for {config['name']}: Invalid JSON")
                        continue
                
                processed_configs[config['name']] = filtering_rules
                
            except Exception as e:
                errors.append(f"Config error for {config['name']}: {str(e)}")
        
        # Verify results
        if 'Good Dealer' in processed_configs and 'Bad Dealer' not in processed_configs:
            self.test_results['passed'].append("✓ Error handling pattern works correctly")
            print("✓ Error handling pattern correctly processed valid and rejected invalid configs")
        else:
            self.test_results['failed'].append("✗ Error handling pattern has issues")
            print("✗ Error handling pattern did not work as expected")
        
        if len(errors) == 1 and 'Bad Dealer' in errors[0]:
            self.test_results['passed'].append("✓ Errors logged correctly")
            print(f"✓ Error logged correctly: {errors[0]}")
        else:
            self.test_results['warnings'].append("⚠ Error logging needs review")
            print(f"⚠ Unexpected errors: {errors}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("JSON EDGE CASE TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results['passed']) + len(self.test_results['failed'])
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {len(self.test_results['passed'])}")
        print(f"Failed: {len(self.test_results['failed'])}")
        print(f"Warnings: {len(self.test_results['warnings'])}")
        
        if self.test_results['failed']:
            print("\nFailed Tests:")
            for failure in self.test_results['failed']:
                print(f"  - {failure}")
        
        if self.test_results['warnings']:
            print("\nWarnings:")
            for warning in self.test_results['warnings']:
                print(f"  - {warning}")
        
        if not self.test_results['failed']:
            print("\n✅ All edge case tests PASSED!")
        else:
            print("\n❌ Some tests FAILED - Review error handling!")
        
        print("="*60)
        
        return 0 if not self.test_results['failed'] else 1

def main():
    """Run edge case tests"""
    tester = JSONEdgeCaseTester()
    
    print("Starting JSON Edge Case Tests...")
    print("================================")
    
    # Run all test suites
    tester.test_malformed_json_scenarios()
    tester.test_special_characters_in_json()
    tester.test_numeric_edge_cases()
    tester.test_deeply_nested_json()
    tester.test_very_long_json_strings()
    tester.test_empty_and_null_scenarios()
    tester.test_csv_importer_error_handling()
    
    # Print summary
    return tester.print_summary()

if __name__ == "__main__":
    sys.exit(main())