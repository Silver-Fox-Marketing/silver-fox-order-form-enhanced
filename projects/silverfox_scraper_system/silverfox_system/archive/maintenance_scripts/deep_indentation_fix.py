#!/usr/bin/env python3
"""
Deep Indentation Fix - More robust fix for persistent indentation issues
"""

import os
import re
from pathlib import Path

def fix_specific_indentation_issues():
    """Fix known specific indentation problems"""
    
    problematic_files = [
        "scraper/dealerships/joemachenscdjr.py",
        "scraper/dealerships/bmwofweststlouis.py", 
        "scraper/dealerships/frankletahonda.py",
        "scraper/dealerships/suntrupfordwest.py",
        "scraper/dealerships/wcvolvocars.py"
    ]
    
    fixes_made = 0
    
    for file_path in problematic_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                print(f"🔧 Fixing {os.path.basename(file_path)}...")
                
                # More aggressive indentation fixes
                fixed_lines = []
                for i, line in enumerate(lines, 1):
                    fixed_line = line
                    
                    # Convert tabs to spaces
                    fixed_line = fixed_line.expandtabs(4)
                    
                    # Fix common problematic patterns
                    if re.match(r'^\s+\\\s*$', fixed_line):
                        # Remove line continuations that are causing issues
                        continue
                    
                    # Fix if/else indentation issues
                    if 'if ' in fixed_line and fixed_line.strip().endswith('\\'):
                        fixed_line = fixed_line.rstrip().rstrip('\\') + ':\n'
                    
                    # Fix function/class definition issues
                    if re.match(r'^\s*(def|class)\s+', fixed_line) and not fixed_line.strip().endswith(':'):
                        if '(' in fixed_line and ')' in fixed_line and not fixed_line.strip().endswith(':'):
                            fixed_line = fixed_line.rstrip() + ':\n'
                    
                    fixed_lines.append(fixed_line)
                
                # Write back the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(fixed_lines)
                
                print(f"   ✅ Applied deep fixes to {os.path.basename(file_path)}")
                fixes_made += 1
                
                # Test compilation
                try:
                    with open(file_path, 'r') as f:
                        compile(f.read(), file_path, 'exec')
                    print(f"   ✅ Syntax validation passed")
                except SyntaxError as e:
                    print(f"   ⚠️ Still has syntax issue: {e}")
                    # Try more aggressive fix
                    aggressive_fix_file(file_path, e.lineno)
                
            except Exception as e:
                print(f"   ❌ Failed to fix {file_path}: {e}")
        else:
            print(f"   ❓ File not found: {file_path}")
    
    return fixes_made

def aggressive_fix_file(file_path: str, error_line: int):
    """Apply more aggressive fixes around problem line"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Fix around the problem line
        start_line = max(0, error_line - 5)
        end_line = min(len(lines), error_line + 5)
        
        print(f"   🔧 Applying aggressive fix around line {error_line}")
        
        for i in range(start_line, end_line):
            if i < len(lines):
                # More aggressive line cleanup
                line = lines[i]
                
                # Remove trailing backslashes
                if line.strip().endswith('\\'):
                    lines[i] = line.rstrip().rstrip('\\') + '\n'
                
                # Fix indentation inconsistencies
                if line.startswith('\t'):
                    lines[i] = line.expandtabs(4)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"   ✅ Applied aggressive fix to {os.path.basename(file_path)}")
        
    except Exception as e:
        print(f"   ❌ Aggressive fix failed: {e}")

def create_corrected_test():
    """Create a corrected test that uses the right method names"""
    
    test_content = '''#!/usr/bin/env python3
"""
Corrected Component Test - Uses correct method names
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

def test_order_processor_with_correct_methods():
    """Test OrderProcessor with the actual available methods"""
    print("📝 TESTING ORDER PROCESSOR (CORRECTED)")
    print("-" * 50)
    
    try:
        from order_processor import OrderProcessor
        
        # Initialize processor
        processor = OrderProcessor("corrected_test.db")
        print("   ✅ OrderProcessor initialized successfully")
        
        # Create test CSV data
        test_data = pd.DataFrame([
            {
                'vin': '1HGCM82633A123456',
                'year': 2024,
                'make': 'Honda', 
                'model': 'Accord',
                'dealer_name': 'Test Honda',
                'price': 25000
            }
        ])
        
        # Save as CSV first
        test_csv = "test_data.csv"
        test_data.to_csv(test_csv, index=False)
        
        # Use the correct method name
        result = processor.import_normalized_data(test_csv)
        print(f"   ✅ Data import successful: {result}")
        
        # Test search functionality
        search_result = processor.search_vehicles({'make': 'Honda'})
        print(f"   ✅ Search working: Found {len(search_result)} Honda vehicles")
        
        # Clean up
        os.remove(test_csv)
        
        return True
        
    except Exception as e:
        print(f"   ❌ OrderProcessor test failed: {e}")
        return False

def test_complete_pipeline_corrected():
    """Test complete pipeline with corrected method calls"""
    print("\\n🎯 COMPLETE PIPELINE TEST (CORRECTED)")
    print("-" * 50)
    
    try:
        from normalizer import VehicleDataNormalizer
        from order_processor import OrderProcessor
        from qr_processor import QRProcessor
        
        # Step 1: Normalize data
        normalizer = VehicleDataNormalizer()
        raw_data = pd.DataFrame([
            {
                'vin': '1HGCM82633A123456',
                'year': 2024,
                'make': 'Honda',
                'model': 'Accord',
                'dealer_name': 'Test Honda'
            }
        ])
        
        normalized_data = normalizer.normalize_dataframe(raw_data)
        print(f"   ✅ Step 1 - Normalization: {len(normalized_data)} vehicles")
        
        # Step 2: Process orders using CSV import method
        processor = OrderProcessor("pipeline_test.db")
        csv_file = "pipeline_test.csv"
        normalized_data.to_csv(csv_file, index=False)
        
        import_result = processor.import_normalized_data(csv_file)
        print(f"   ✅ Step 2 - Order processing: {import_result}")
        
        # Step 3: Generate QR codes
        qr_processor = QRProcessor()
        qr_result = qr_processor.generate_qr_codes("1HGCM82633A123456", "https://example.com", "pipeline_qr")
        print(f"   ✅ Step 3 - QR Generation: {len(qr_result)} QR codes created")
        
        # Clean up
        os.remove(csv_file)
        
        print("\\n🎉 COMPLETE PIPELINE WORKING SUCCESSFULLY!")
        return True
        
    except Exception as e:
        print(f"   ❌ Complete pipeline failed: {e}")
        return False

def main():
    """Run corrected tests"""
    print("🔧 CORRECTED COMPONENT TESTING")
    print("=" * 60)
    
    tests = [
        test_order_processor_with_correct_methods,
        test_complete_pipeline_corrected
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\\n📊 FINAL RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🏆 ALL CORRECTED TESTS PASSED!")
        print("✅ Pipeline is fully functional with correct method calls")
    
if __name__ == "__main__":
    main()
'''
    
    with open("corrected_component_test.py", 'w') as f:
        f.write(test_content)
    
    print("   ✅ Created corrected_component_test.py")

def main():
    """Main execution"""
    print("🔧 DEEP INDENTATION FIX SCRIPT")
    print("=" * 60)
    
    # Apply deep fixes
    fixes = fix_specific_indentation_issues()
    print(f"\\n✅ Applied deep fixes to {fixes} files")
    
    # Create corrected test
    create_corrected_test()
    
    print("\\n🎯 Run 'python corrected_component_test.py' to validate fixes")

if __name__ == "__main__":
    main()