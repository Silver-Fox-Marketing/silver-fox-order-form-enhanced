#!/usr/bin/env python3
"""
Rapid Scraper Assessment Tool
Quickly test all dealership scrapers to categorize their status and prioritize optimization
"""

import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper', 'dealerships'))

def get_all_scraper_files():
    """Get list of all scraper files in dealerships directory"""
    dealerships_dir = Path(__file__).parent / 'scraper' / 'dealerships'
    
    if not dealerships_dir.exists():
        print(f"❌ Dealerships directory not found: {dealerships_dir}")
        return []
    
    # Get all Python files that look like scrapers
    scraper_files = []
    for file_path in dealerships_dir.glob('*.py'):
        if file_path.name != '__init__.py' and 'working' in file_path.name:
            scraper_files.append(file_path)
    
    return sorted(scraper_files)

def extract_scraper_info(file_path: Path) -> Dict[str, Any]:
    """Extract basic information about a scraper file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract scraper class name (more flexible pattern)
        import re
        class_patterns = [
            r'class\s+(\w+Scraper[^(]*)\(',  # Standard scraper pattern
            r'class\s+(\w+WorkingScraper[^(]*)\(',  # Working scraper pattern
            r'class\s+(\w+[^(]*Scraper[^(]*)\(',  # Any scraper pattern
        ]
        
        class_name = None
        for pattern in class_patterns:
            class_match = re.search(pattern, content)
            if class_match:
                class_name = class_match.group(1)
                break
        
        # Check for key indicators
        has_selenium = 'selenium' in content.lower()
        has_requests = 'requests' in content.lower()
        has_api_calls = 'api' in content.lower() or 'algolia' in content.lower()
        has_pagination = 'page' in content.lower() and ('while' in content or 'for' in content)
        has_error_handling = 'try:' in content and 'except:' in content
        
        # Estimate complexity
        lines = len(content.split('\n'))
        complexity = 'High' if lines > 400 else 'Medium' if lines > 200 else 'Low'
        
        # Extract dealership info
        dealership_id = file_path.stem.replace('_working', '').replace('_', '')
        
        # Look for base URL
        url_match = re.search(r'[\'"]https?://[^\'"]+[\'"]', content)
        base_url = url_match.group().strip('\'"') if url_match else None
        
        return {
            'file_name': file_path.name,
            'dealership_id': dealership_id,
            'class_name': class_name,
            'base_url': base_url,
            'file_size': file_path.stat().st_size,
            'lines_of_code': lines,
            'complexity': complexity,
            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'features': {
                'has_selenium': has_selenium,
                'has_requests': has_requests,
                'has_api_calls': has_api_calls,
                'has_pagination': has_pagination,
                'has_error_handling': has_error_handling
            }
        }
    except Exception as e:
        return {
            'file_name': file_path.name,
            'dealership_id': file_path.stem.replace('_working', ''),
            'error': str(e),
            'status': 'file_error'
        }

def quick_scraper_test(scraper_info: Dict[str, Any], timeout_seconds: int = 30) -> Dict[str, Any]:
    """Perform a quick test of a scraper (limited time)"""
    
    # Suppress most logging to reduce noise
    logging.getLogger().setLevel(logging.CRITICAL)
    
    test_result = {
        'dealership_id': scraper_info['dealership_id'],
        'test_timestamp': datetime.now().isoformat(),
        'status': 'untested',
        'vehicles_found': 0,
        'execution_time': 0,
        'error_message': None,
        'data_quality': 0,
        'needs_optimization': True
    }
    
    if 'error' in scraper_info:
        test_result['status'] = 'import_error'
        test_result['error_message'] = scraper_info['error']
        return test_result
    
    try:
        # Dynamic import of scraper class
        module_name = scraper_info['file_name'].replace('.py', '')
        class_name = scraper_info['class_name']
        
        if not class_name:
            test_result['status'] = 'no_class_found'
            return test_result
        
        # Import the module
        module = __import__(module_name)
        scraper_class = getattr(module, class_name)
        
        # Create config
        config = {
            'id': scraper_info['dealership_id'],
            'name': scraper_info['dealership_id'].title(),
            'base_url': scraper_info.get('base_url', '')
        }
        
        # Simple config class
        class QuickConfig:
            request_delay = 0.5  # Fast testing
            timeout = 10  # Quick timeout
        
        # Test the scraper with timeout
        start_time = time.time()
        
        scraper = scraper_class(config, QuickConfig())
        vehicles = scraper.scrape_inventory()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Analyze results
        if vehicles:
            # Calculate data quality
            total_fields = len(vehicles) * 8  # Assume 8 key fields per vehicle
            filled_fields = 0
            
            for vehicle in vehicles:
                for field in ['vin', 'stock_number', 'year', 'make', 'model', 'price', 'mileage', 'condition']:
                    if vehicle.get(field):
                        filled_fields += 1
            
            data_quality = (filled_fields / total_fields * 100) if total_fields > 0 else 0
            
            # Determine status
            if len(vehicles) >= 10 and data_quality >= 70:
                status = 'excellent'
                needs_optimization = False
            elif len(vehicles) >= 5 and data_quality >= 50:
                status = 'good'
                needs_optimization = False
            elif len(vehicles) >= 1:
                status = 'partial'
                needs_optimization = True
            else:
                status = 'no_data'
                needs_optimization = True
            
            test_result.update({
                'status': status,
                'vehicles_found': len(vehicles),
                'execution_time': execution_time,
                'data_quality': data_quality,
                'needs_optimization': needs_optimization
            })
        else:
            test_result.update({
                'status': 'no_vehicles',
                'execution_time': execution_time,
                'needs_optimization': True
            })
        
    except Exception as e:
        test_result.update({
            'status': 'runtime_error',
            'error_message': str(e),
            'execution_time': time.time() - start_time if 'start_time' in locals() else 0,
            'needs_optimization': True
        })
    
    return test_result

def assess_all_scrapers():
    """Assess all scrapers and categorize them"""
    print("🔍 RAPID SCRAPER ASSESSMENT")
    print("Testing all dealership scrapers to prioritize optimization")
    print("=" * 70)
    
    scraper_files = get_all_scraper_files()
    
    if not scraper_files:
        print("❌ No scraper files found")
        return
    
    print(f"📋 Found {len(scraper_files)} scraper files to assess")
    print()
    
    assessment_results = {
        'assessment_timestamp': datetime.now().isoformat(),
        'total_scrapers': len(scraper_files),
        'results': [],
        'summary': {
            'excellent': 0,
            'good': 0,
            'partial': 0,
            'no_vehicles': 0,
            'errors': 0
        }
    }
    
    # Quick assessment of each scraper
    for i, file_path in enumerate(scraper_files, 1):
        print(f"[{i:2d}/{len(scraper_files)}] Testing {file_path.stem}...", end=" ")
        
        # Extract scraper info
        scraper_info = extract_scraper_info(file_path)
        
        if 'error' in scraper_info:
            print(f"❌ File error")
            assessment_results['summary']['errors'] += 1
            assessment_results['results'].append({
                **scraper_info,
                'test_result': {'status': 'file_error', 'error_message': scraper_info['error']}
            })
            continue
        
        # Quick test
        try:
            test_result = quick_scraper_test(scraper_info, timeout_seconds=20)
            
            # Print result
            status = test_result['status']
            vehicles = test_result['vehicles_found']
            quality = test_result.get('data_quality', 0)
            exec_time = test_result.get('execution_time', 0)
            
            if status == 'excellent':
                print(f"✅ EXCELLENT ({vehicles} vehicles, {quality:.0f}% quality, {exec_time:.1f}s)")
                assessment_results['summary']['excellent'] += 1
            elif status == 'good':
                print(f"✅ GOOD ({vehicles} vehicles, {quality:.0f}% quality, {exec_time:.1f}s)")
                assessment_results['summary']['good'] += 1
            elif status == 'partial':
                print(f"⚠️ PARTIAL ({vehicles} vehicles, {quality:.0f}% quality, {exec_time:.1f}s)")
                assessment_results['summary']['partial'] += 1
            elif status == 'no_vehicles':
                print(f"❌ NO DATA ({exec_time:.1f}s)")
                assessment_results['summary']['no_vehicles'] += 1
            else:
                print(f"❌ ERROR ({test_result.get('error_message', 'Unknown error')[:50]})")
                assessment_results['summary']['errors'] += 1
            
            assessment_results['results'].append({
                **scraper_info,
                'test_result': test_result
            })
            
        except Exception as e:
            print(f"❌ EXCEPTION ({str(e)[:50]})")
            assessment_results['summary']['errors'] += 1
            assessment_results['results'].append({
                **scraper_info,
                'test_result': {'status': 'exception', 'error_message': str(e)}
            })
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("📊 ASSESSMENT SUMMARY")
    print("=" * 70)
    
    summary = assessment_results['summary']
    total = assessment_results['total_scrapers']
    
    print(f"Total scrapers assessed: {total}")
    print(f"✅ Excellent (ready for on-lot optimization): {summary['excellent']}")
    print(f"✅ Good (minor optimization needed): {summary['good']}")
    print(f"⚠️ Partial (significant optimization needed): {summary['partial']}")
    print(f"❌ No data (major rework required): {summary['no_vehicles']}")
    print(f"❌ Errors (technical issues): {summary['errors']}")
    
    # Identify priority scrapers for on-lot optimization
    ready_for_optimization = []
    needs_work = []
    
    for result in assessment_results['results']:
        test_result = result.get('test_result', {})
        status = test_result.get('status', 'unknown')
        
        if status in ['excellent', 'good']:
            ready_for_optimization.append(result)
        else:
            needs_work.append(result)
    
    print(f"\n🎯 OPTIMIZATION PRIORITIES:")
    print(f"Ready for on-lot methodology: {len(ready_for_optimization)} scrapers")
    print(f"Need technical fixes first: {len(needs_work)} scrapers")
    
    if ready_for_optimization:
        print(f"\n✅ READY FOR ON-LOT OPTIMIZATION:")
        for result in ready_for_optimization[:10]:  # Show top 10
            test = result['test_result']
            print(f"   {result['dealership_id']}: {test['vehicles_found']} vehicles, {test.get('data_quality', 0):.0f}% quality")
    
    if needs_work:
        print(f"\n⚠️ NEEDS TECHNICAL WORK FIRST:")
        for result in needs_work[:10]:  # Show top 10 problems
            test = result['test_result']
            error = test.get('error_message', test.get('status', 'Unknown issue'))
            print(f"   {result['dealership_id']}: {error[:60]}")
    
    # Save detailed results
    results_file = 'rapid_scraper_assessment_results.json'
    with open(results_file, 'w') as f:
        json.dump(assessment_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return assessment_results

if __name__ == "__main__":
    results = assess_all_scrapers()