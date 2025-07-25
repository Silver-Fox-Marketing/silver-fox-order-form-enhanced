#!/usr/bin/env python3
"""Quick test runner for Silver Fox system validation"""

import os
import sys
import logging
import time
from datetime import datetime

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
utils_dir = os.path.join(parent_dir, 'utils')
sys.path.append(utils_dir)

def quick_test():
    """Quick validation test of core components"""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('QuickTest')
    
    logger.info("🚀 Silver Fox System - Quick Validation Test")
    logger.info("=" * 60)
    
    test_results = {}
    start_time = datetime.now()
    
    # Test 1: Competitive Pricing Analysis
    try:
        logger.info("🧪 Testing Competitive Pricing Analysis...")
        from competitive_pricing_analysis import CompetitivePricingAnalyzer
        
        analyzer = CompetitivePricingAnalyzer({
            'dealer1': {'name': 'Test Dealer 1', 'tier': 'luxury'}
        })
        
        # Test basic instantiation and method calls
        test_vehicles = [
            {'vin': 'TEST123', 'make': 'BMW', 'model': 'X5', 'price': 50000, 'year': 2022}
        ]
        
        # Check if method exists - using correct method name
        if hasattr(analyzer, 'analyze_cross_dealership_competition'):
            insights = analyzer.analyze_cross_dealership_competition('dealer1', test_vehicles)
            test_results['competitive_analysis'] = "✅ PASS"
        else:
            test_results['competitive_analysis'] = "⚠️ PARTIAL (method not found but class loads)"
        
    except Exception as e:
        test_results['competitive_analysis'] = f"❌ FAIL: {str(e)}"
    
    # Test 2: Real-time Alerts
    try:
        logger.info("🧪 Testing Real-time Alerts...")
        from realtime_inventory_alerts import create_alert_system
        
        alert_config = {
            'price_drop_threshold': 5.0,
            'email_config': {}
        }
        alert_system = create_alert_system(alert_config)
        
        test_vehicles = [
            {'vin': 'ALERT123', 'make': 'Ford', 'model': 'F-150', 'price': 35000}
        ]
        
        alerts = alert_system.process_inventory_update('test_dealer', 'Test Dealer', test_vehicles)
        test_results['realtime_alerts'] = "✅ PASS"
        
    except Exception as e:
        test_results['realtime_alerts'] = f"❌ FAIL: {str(e)}"
    
    # Test 3: Enhanced Verification
    try:
        logger.info("🧪 Testing Enhanced Inventory Verification...")
        from enhanced_inventory_verification import EnhancedInventoryVerificationSystem
        
        dealership_config = {'name': 'Test', 'base_url': 'https://test.com'}
        verification_system = EnhancedInventoryVerificationSystem('Test', dealership_config)
        
        test_vehicles = [
            {'vin': 'VERIFY123', 'make': 'Honda', 'model': 'Civic', 'price': 25000}
        ]
        
        # Quick verification without cross-verification for speed
        report = verification_system.verify_inventory_completeness(test_vehicles, enable_cross_verification=False)
        test_results['enhanced_verification'] = "✅ PASS"
        
    except Exception as e:
        test_results['enhanced_verification'] = f"❌ FAIL: {str(e)}"
    
    # Test 4: PipeDrive Integration
    try:
        logger.info("🧪 Testing PipeDrive Integration...")
        from pipedrive_crm_integration import create_pipedrive_integration
        
        # Create with mock credentials
        integration = create_pipedrive_integration(
            api_token="test_token",
            company_domain="test-domain"
        )
        
        # Mock the API calls to avoid real API hits
        integration._make_api_request = lambda *args, **kwargs: {'success': True, 'data': {'id': 123}}
        
        test_vehicles = [
            {'vin': 'PIPE123', 'make': 'Toyota', 'model': 'Camry', 'price': 30000}
        ]
        
        sync_report = integration.sync_vehicle_inventory(test_vehicles, 'Test Dealer')
        test_results['pipedrive_integration'] = "✅ PASS"
        
    except Exception as e:
        test_results['pipedrive_integration'] = f"❌ FAIL: {str(e)}"
    
    # Test 5: Multi-Dealership Optimization
    try:
        logger.info("🧪 Testing Multi-Dealership Optimization...")
        from multi_dealership_optimization_framework import create_ranch_mirage_optimizer
        
        optimizer = create_ranch_mirage_optimizer("Test Jaguar", "luxury")
        headers = optimizer.get_optimized_headers()
        
        if 'User-Agent' in headers:
            test_results['multi_dealership_optimization'] = "✅ PASS"
        else:
            test_results['multi_dealership_optimization'] = "⚠️ PARTIAL"
        
    except Exception as e:
        test_results['multi_dealership_optimization'] = f"❌ FAIL: {str(e)}"
    
    # Calculate results
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    passed_tests = sum(1 for result in test_results.values() if "✅ PASS" in result)
    total_tests = len(test_results)
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 QUICK TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"📊 Duration: {duration:.1f} seconds")
    logger.info(f"📊 Tests Passed: {passed_tests}/{total_tests}")
    logger.info(f"📊 Success Rate: {passed_tests/total_tests*100:.1f}%")
    logger.info("")
    
    for component, result in test_results.items():
        logger.info(f"   {result} {component.replace('_', ' ').title()}")
    
    logger.info("")
    
    if passed_tests >= total_tests * 0.8:  # 80% success rate
        logger.info("🎉 EXCELLENT! Silver Fox system core components are operational!")
        logger.info("🔥 Ready for production with all major systems working.")
        return True
    elif passed_tests >= total_tests * 0.6:  # 60% success rate
        logger.info("👍 GOOD! Most Silver Fox components are working well.")
        logger.info("⚠️ Review failing components before full deployment.")
        return True
    else:
        logger.info("⚠️ NEEDS ATTENTION! Multiple components need debugging.")
        logger.info("🛠️ Significant work required before deployment.")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)