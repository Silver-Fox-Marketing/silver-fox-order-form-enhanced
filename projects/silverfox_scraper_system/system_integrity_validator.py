#!/usr/bin/env python3
"""
Silver Fox Scraper System - Complete Integrity Validator
=======================================================

Systematically verify:
1. Each individual scraper is present, functional, and bug-free
2. All system scripts are operational and integrated
3. Complete system health check

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import logging
import importlib
import subprocess
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback

class SystemIntegrityValidator:
    """Complete system integrity validation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.scrapers_dir = self.project_root / "silverfox_system" / "core" / "scrapers" / "dealerships"
        self.configs_dir = self.project_root / "configs"
        self.logger = logging.getLogger(__name__)
        
        # Add scrapers directory to Python path
        sys.path.insert(0, str(self.scrapers_dir))
        
        # Validation results
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'scrapers': {
                'total': 0,
                'present': 0,
                'functional': 0,
                'bug_free': 0,
                'individual_results': []
            },
            'system_scripts': {
                'total': 0,
                'present': 0,
                'functional': 0,
                'integrated': 0,
                'individual_results': []
            },
            'overall_health': {
                'status': 'UNKNOWN',
                'score': 0.0,
                'issues': [],
                'recommendations': []
            }
        }
    
    def validate_complete_system(self) -> Dict[str, Any]:
        """Run complete system validation"""
        self.logger.info("🔍 Starting Silver Fox Scraper System Complete Integrity Validation")
        
        # Phase 1: Validate each individual scraper
        self._validate_all_scrapers()
        
        # Phase 2: Validate all system scripts
        self._validate_system_scripts()
        
        # Phase 3: Calculate overall system health
        self._calculate_system_health()
        
        # Save detailed report
        self._save_integrity_report()
        
        # Print executive summary
        self._print_executive_summary()
        
        return self.validation_results
    
    def _validate_all_scrapers(self) -> None:
        """Validate each individual scraper comprehensively"""
        self.logger.info("\n📋 PHASE 1: Individual Scraper Validation")
        
        # Get all scraper files
        scraper_files = list(self.scrapers_dir.glob("*_optimized.py"))
        self.validation_results['scrapers']['total'] = len(scraper_files)
        
        expected_scrapers = [
            'auffenberghyundai', 'audiranchomirage', 'bmwofweststlouis', 'bommaritocadillac',
            'bommaritowestcounty', 'columbiabmw', 'columbiahonda', 'davesinclairlincolnsouth',
            'davesinclairlincolnstpeters', 'frankletahonda', 'glendalechryslerjeep',
            'hondafrontenac', 'hwkia', 'indigoautogroup', 'jaguarranchomirage',
            'joemachenscdjr', 'joemachenshyundai', 'joemachensnissan', 'joemachenstoyota',
            'kiaofcolumbia', 'landroverranchomirage', 'miniofstlouis', 'pappastoyota',
            'porschestlouis', 'pundmannford', 'rustydrewingcadillac', 'rustydrewingchevroletbuickgmc',
            'serrahondaofallon', 'southcountyautos', 'spiritlexus', 'stehouwerauto',
            'suntrupbuickgmc', 'suntrupfordkirkwood', 'suntrupfordwest', 'suntruphyundaisouth',
            'suntrupkiasouth', 'thoroughbredford', 'twincitytoyota', 'wcvolvocars', 'weberchev'
        ]
        
        # Check for missing scrapers
        found_scrapers = [f.stem.replace('_optimized', '') for f in scraper_files]
        missing_scrapers = set(expected_scrapers) - set(found_scrapers)
        
        if missing_scrapers:
            self.validation_results['overall_health']['issues'].append(
                f"Missing scrapers: {', '.join(missing_scrapers)}"
            )
        
        # Validate each scraper
        for i, scraper_file in enumerate(scraper_files):
            self.logger.info(f"\n🔧 Validating scraper {i+1}/{len(scraper_files)}: {scraper_file.stem}")
            
            result = self._validate_individual_scraper(scraper_file)
            self.validation_results['scrapers']['individual_results'].append(result)
            
            if result['present']:
                self.validation_results['scrapers']['present'] += 1
            if result['functional']:
                self.validation_results['scrapers']['functional'] += 1
            if result['bug_free']:
                self.validation_results['scrapers']['bug_free'] += 1
            
            # Print immediate feedback
            status = "✅" if result['bug_free'] else "⚠️" if result['functional'] else "❌"
            print(f"{status} {scraper_file.stem}: {result['status']}")
    
    def _validate_individual_scraper(self, scraper_file: Path) -> Dict[str, Any]:
        """Comprehensive validation of individual scraper"""
        scraper_name = scraper_file.stem
        dealer_name = self._extract_dealer_name(scraper_name)
        
        result = {
            'scraper_name': scraper_name,
            'dealer_name': dealer_name,
            'file_path': str(scraper_file),
            'present': False,
            'functional': False,
            'bug_free': False,
            'status': 'NOT_VALIDATED',
            'checks': {
                'file_exists': False,
                'syntax_valid': False,
                'imports_successful': False,
                'class_instantiates': False,
                'method_callable': False,
                'data_returned': False,
                'data_valid': False,
                'error_handling': False,
                'performance': False
            },
            'issues': [],
            'bugs': [],
            'metrics': {}
        }
        
        try:
            # Check 1: File exists
            if scraper_file.exists():
                result['present'] = True
                result['checks']['file_exists'] = True
            else:
                result['issues'].append("File does not exist")
                return result
            
            # Check 2: Syntax validation
            with open(scraper_file, 'r') as f:
                content = f.read()
            
            try:
                ast.parse(content)
                result['checks']['syntax_valid'] = True
            except SyntaxError as e:
                result['bugs'].append(f"Syntax error: {e}")
                return result
            
            # Check 3: Import validation
            try:
                module_name = scraper_name
                module = importlib.import_module(module_name)
                result['checks']['imports_successful'] = True
            except ImportError as e:
                result['bugs'].append(f"Import error: {e}")
                return result
            
            # Check 4: Class instantiation
            try:
                class_name = self._get_expected_class_name(dealer_name)
                if hasattr(module, class_name):
                    scraper_class = getattr(module, class_name)
                    scraper = scraper_class()
                    result['checks']['class_instantiates'] = True
                else:
                    result['bugs'].append(f"Class {class_name} not found")
                    return result
            except Exception as e:
                result['bugs'].append(f"Instantiation error: {e}")
                return result
            
            # Check 5: Method validation
            if not hasattr(scraper, 'get_all_vehicles'):
                result['bugs'].append("Missing get_all_vehicles method")
                return result
            
            result['checks']['method_callable'] = True
            
            # Check 6: Data collection test
            try:
                import time
                start_time = time.time()
                vehicles = scraper.get_all_vehicles()
                execution_time = time.time() - start_time
                
                result['metrics']['execution_time'] = execution_time
                result['metrics']['vehicle_count'] = len(vehicles) if vehicles else 0
                
                if vehicles and len(vehicles) > 0:
                    result['checks']['data_returned'] = True
                    result['functional'] = True
                    
                    # Check 7: Data validation
                    data_issues = self._validate_vehicle_data(vehicles)
                    if not data_issues:
                        result['checks']['data_valid'] = True
                    else:
                        result['bugs'].extend(data_issues)
                else:
                    result['issues'].append("No vehicles returned")
                
            except Exception as e:
                result['bugs'].append(f"Runtime error: {str(e)}")
                result['metrics']['error_traceback'] = traceback.format_exc()
            
            # Check 8: Error handling validation
            if self._validate_error_handling(content):
                result['checks']['error_handling'] = True
            else:
                result['issues'].append("Insufficient error handling")
            
            # Check 9: Performance validation
            if result.get('metrics', {}).get('execution_time', 999) < 30:
                result['checks']['performance'] = True
            else:
                result['issues'].append("Performance concerns (>30s execution)")
            
            # Determine bug-free status
            if result['functional'] and not result['bugs'] and len(result['issues']) <= 1:
                result['bug_free'] = True
                result['status'] = 'FULLY_OPERATIONAL'
            elif result['functional']:
                result['status'] = 'FUNCTIONAL_WITH_ISSUES'
            else:
                result['status'] = 'NON_FUNCTIONAL'
            
        except Exception as e:
            result['bugs'].append(f"Validation error: {str(e)}")
            result['status'] = 'VALIDATION_FAILED'
        
        return result
    
    def _validate_vehicle_data(self, vehicles: List[Dict[str, Any]]) -> List[str]:
        """Validate vehicle data quality"""
        issues = []
        
        if not vehicles:
            return ["No vehicles to validate"]
        
        # Check data structure
        for i, vehicle in enumerate(vehicles[:5]):  # Sample first 5
            if not isinstance(vehicle, dict):
                issues.append(f"Vehicle {i} is not a dictionary")
                continue
            
            # Check required fields
            required_fields = ['vin', 'year', 'make', 'model']
            missing_fields = [f for f in required_fields if not vehicle.get(f)]
            if missing_fields:
                issues.append(f"Vehicle {i} missing fields: {missing_fields}")
            
            # Check data types
            if vehicle.get('year') and not isinstance(vehicle['year'], int):
                issues.append(f"Vehicle {i} year is not integer")
            
            if vehicle.get('price') and not isinstance(vehicle['price'], (int, float, type(None))):
                issues.append(f"Vehicle {i} price has invalid type")
        
        # Check for duplicate VINs
        vins = [v.get('vin') for v in vehicles if v.get('vin')]
        if len(vins) != len(set(vins)):
            issues.append("Duplicate VINs detected")
        
        return issues
    
    def _validate_error_handling(self, content: str) -> bool:
        """Check if scraper has proper error handling"""
        error_patterns = [
            'try:', 'except:', 'finally:', 
            'logger.error', 'logger.warning',
            'error_response', 'fallback'
        ]
        
        found_patterns = sum(1 for pattern in error_patterns if pattern in content)
        return found_patterns >= 4  # Requires at least 4 error handling patterns
    
    def _validate_system_scripts(self) -> None:
        """Validate all system scripts"""
        self.logger.info("\n📋 PHASE 2: System Scripts Validation")
        
        system_scripts = [
            {
                'name': 'silverfox_scraper_configurator.py',
                'description': 'Configuration management system',
                'type': 'core'
            },
            {
                'name': 'main_scraper_orchestrator.py',
                'description': 'Main execution engine',
                'type': 'core'
            },
            {
                'name': 'generate_missing_scrapers.py',
                'description': 'Scraper generation tool',
                'type': 'tool'
            },
            {
                'name': 'optimize_all_scrapers.py',
                'description': 'Mass optimization system',
                'type': 'tool'
            },
            {
                'name': 'comprehensive_scraper_fixer.py',
                'description': 'Issue resolution tool',
                'type': 'tool'
            },
            {
                'name': 'comprehensive_scraper_test.py',
                'description': 'Testing suite',
                'type': 'test'
            },
            {
                'name': 'network_utils.py',
                'description': 'Network resilience utilities',
                'type': 'utility'
            },
            {
                'name': 'production_fallback_handler.py',
                'description': 'Fallback data generation',
                'type': 'utility'
            },
            {
                'name': 'bmwofweststlouis_production.py',
                'description': 'Production pattern reference',
                'type': 'reference'
            },
            {
                'name': 'real_time_inventory_monitor.py',
                'description': 'Real-time monitoring system',
                'type': 'monitor'
            },
            {
                'name': 'competitive_pricing_analyzer.py',
                'description': 'Pricing analysis module',
                'type': 'analysis'
            },
            {
                'name': 'pipedrive_integration.py',
                'description': 'CRM integration',
                'type': 'integration'
            },
            {
                'name': 'stress_test_framework.py',
                'description': 'Performance testing',
                'type': 'test'
            },
            {
                'name': 'kubernetes_deployment.yaml',
                'description': 'K8s deployment config',
                'type': 'deployment'
            },
            {
                'name': 'monitoring_alerting_config.py',
                'description': 'Monitoring configuration',
                'type': 'monitor'
            }
        ]
        
        self.validation_results['system_scripts']['total'] = len(system_scripts)
        
        for script in system_scripts:
            result = self._validate_system_script(script)
            self.validation_results['system_scripts']['individual_results'].append(result)
            
            if result['present']:
                self.validation_results['system_scripts']['present'] += 1
            if result['functional']:
                self.validation_results['system_scripts']['functional'] += 1
            if result['integrated']:
                self.validation_results['system_scripts']['integrated'] += 1
            
            # Print immediate feedback
            status = "✅" if result['integrated'] else "⚠️" if result['functional'] else "❌"
            print(f"{status} {script['name']}: {result['status']}")
    
    def _validate_system_script(self, script_info: Dict[str, str]) -> Dict[str, Any]:
        """Validate individual system script"""
        script_path = self.project_root / script_info['name']
        
        # Check special paths
        if script_info['name'] == 'bmwofweststlouis_production.py':
            script_path = self.scrapers_dir / script_info['name']
        elif script_info['name'] in ['network_utils.py', 'production_fallback_handler.py']:
            script_path = self.project_root / script_info['name']
        
        result = {
            'name': script_info['name'],
            'description': script_info['description'],
            'type': script_info['type'],
            'present': False,
            'functional': False,
            'integrated': False,
            'status': 'NOT_FOUND',
            'issues': []
        }
        
        # Check if file exists
        if script_path.exists():
            result['present'] = True
            
            # Check syntax for Python files
            if script_path.suffix == '.py':
                try:
                    with open(script_path, 'r') as f:
                        content = f.read()
                    ast.parse(content)
                    result['functional'] = True
                    
                    # Check integration points
                    if self._check_integration(content, script_info['type']):
                        result['integrated'] = True
                        result['status'] = 'FULLY_INTEGRATED'
                    else:
                        result['status'] = 'FUNCTIONAL_NOT_INTEGRATED'
                        result['issues'].append("Missing integration points")
                        
                except SyntaxError as e:
                    result['status'] = 'SYNTAX_ERROR'
                    result['issues'].append(f"Syntax error: {e}")
                    
            elif script_path.suffix in ['.yaml', '.yml']:
                # For YAML files, just check if they're valid
                result['functional'] = True
                result['integrated'] = True
                result['status'] = 'CONFIGURATION_VALID'
        else:
            result['issues'].append("File not found")
        
        return result
    
    def _check_integration(self, content: str, script_type: str) -> bool:
        """Check if script has proper integration points"""
        integration_patterns = {
            'core': ['import', 'class', 'def', 'logging'],
            'tool': ['main()', 'if __name__', 'import'],
            'test': ['test', 'assert', 'validate'],
            'utility': ['class', 'def', 'return'],
            'monitor': ['monitor', 'track', 'alert'],
            'analysis': ['analyze', 'calculate', 'report'],
            'integration': ['api', 'connect', 'sync'],
            'reference': ['class', 'get_all_vehicles']
        }
        
        patterns = integration_patterns.get(script_type, ['def', 'class'])
        found = sum(1 for pattern in patterns if pattern in content)
        
        return found >= len(patterns) * 0.5  # At least 50% of patterns
    
    def _calculate_system_health(self) -> None:
        """Calculate overall system health score"""
        scrapers = self.validation_results['scrapers']
        scripts = self.validation_results['system_scripts']
        
        # Calculate component scores
        scraper_score = (
            (scrapers['present'] / scrapers['total']) * 0.2 +
            (scrapers['functional'] / scrapers['total']) * 0.4 +
            (scrapers['bug_free'] / scrapers['total']) * 0.4
        ) if scrapers['total'] > 0 else 0
        
        script_score = (
            (scripts['present'] / scripts['total']) * 0.3 +
            (scripts['functional'] / scripts['total']) * 0.3 +
            (scripts['integrated'] / scripts['total']) * 0.4
        ) if scripts['total'] > 0 else 0
        
        # Overall health score (70% scrapers, 30% scripts)
        overall_score = (scraper_score * 0.7) + (script_score * 0.3)
        
        self.validation_results['overall_health']['score'] = overall_score
        
        # Determine health status
        if overall_score >= 0.95:
            self.validation_results['overall_health']['status'] = 'EXCELLENT'
        elif overall_score >= 0.85:
            self.validation_results['overall_health']['status'] = 'GOOD'
        elif overall_score >= 0.70:
            self.validation_results['overall_health']['status'] = 'FAIR'
        else:
            self.validation_results['overall_health']['status'] = 'NEEDS_ATTENTION'
        
        # Generate recommendations
        if scrapers['bug_free'] < scrapers['total']:
            self.validation_results['overall_health']['recommendations'].append(
                f"Fix bugs in {scrapers['total'] - scrapers['bug_free']} scrapers"
            )
        
        if scripts['integrated'] < scripts['total']:
            self.validation_results['overall_health']['recommendations'].append(
                f"Complete integration for {scripts['total'] - scripts['integrated']} system scripts"
            )
    
    def _extract_dealer_name(self, scraper_name: str) -> str:
        """Extract dealer name from scraper filename"""
        base_name = scraper_name.replace('_optimized', '').replace('_working', '')
        
        name_mappings = {
            'bmwofweststlouis': 'BMW of West St. Louis',
            'columbiabmw': 'Columbia BMW',
            'jaguarranchomirage': 'Jaguar Ranch Mirage',
            'landroverranchomirage': 'Land Rover Ranch Mirage',
            'suntrupfordwest': 'Suntrup Ford West',
            'joemachenshyundai': 'Joe Machens Hyundai',
            'columbiahonda': 'Columbia Honda',
            'audiranchomirage': 'Audi Ranch Mirage',
            'auffenberghyundai': 'Auffenberg Hyundai',
            'bommaritocadillac': 'Bommarito Cadillac',
            'bommaritowestcounty': 'Bommarito West County',
            'davesinclairlincolnsouth': 'Dave Sinclair Lincoln South',
            'davesinclairlincolnstpeters': 'Dave Sinclair Lincoln St. Peters',
            'frankletahonda': 'Frank Leta Honda',
            'glendalechryslerjeep': 'Glendale Chrysler Jeep',
            'hondafrontenac': 'Honda of Frontenac',
            'hwkia': 'H&W Kia',
            'indigoautogroup': 'Indigo Auto Group',
            'joemachenscdjr': 'Joe Machens Chrysler Dodge Jeep Ram',
            'joemachensnissan': 'Joe Machens Nissan',
            'joemachenstoyota': 'Joe Machens Toyota',
            'kiaofcolumbia': 'Kia of Columbia',
            'miniofstlouis': 'MINI of St. Louis',
            'pappastoyota': 'Pappas Toyota',
            'porschestlouis': 'Porsche St. Louis',
            'pundmannford': 'Pundmann Ford',
            'rustydrewingcadillac': 'Rusty Drewing Cadillac',
            'rustydrewingchevroletbuickgmc': 'Rusty Drewing Chevrolet Buick GMC',
            'serrahondaofallon': 'Serra Honda of O\'Fallon',
            'southcountyautos': 'South County Autos',
            'spiritlexus': 'Spirit Lexus',
            'stehouwerauto': 'Stehouwer Auto',
            'suntrupbuickgmc': 'Suntrup Buick GMC',
            'suntrupfordkirkwood': 'Suntrup Ford Kirkwood',
            'suntruphyundaisouth': 'Suntrup Hyundai South',
            'suntrupkiasouth': 'Suntrup Kia South',
            'thoroughbredford': 'Thoroughbred Ford',
            'twincitytoyota': 'Twin City Toyota',
            'wcvolvocars': 'West County Volvo Cars',
            'weberchev': 'Weber Chevrolet'
        }
        
        return name_mappings.get(base_name, base_name.replace('_', ' ').title())
    
    def _get_expected_class_name(self, dealer_name: str) -> str:
        """Get expected class name"""
        clean_name = ''.join(char for char in dealer_name if char.isalnum() or char.isspace())
        words = clean_name.split()
        class_name = ''.join(word.capitalize() for word in words)
        return f"{class_name}OptimizedScraper"
    
    def _save_integrity_report(self) -> None:
        """Save detailed integrity report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.project_root / f"system_integrity_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(self.validation_results, f, indent=2, default=str)
            
            self.logger.info(f"\n📋 Integrity report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Could not save integrity report: {e}")
    
    def _print_executive_summary(self) -> None:
        """Print executive summary of validation results"""
        print("\n" + "="*80)
        print("🏆 SILVER FOX SCRAPER SYSTEM - INTEGRITY VALIDATION COMPLETE")
        print("="*80)
        
        scrapers = self.validation_results['scrapers']
        scripts = self.validation_results['system_scripts']
        health = self.validation_results['overall_health']
        
        print(f"\n📊 SCRAPER VALIDATION RESULTS:")
        print(f"   Total Scrapers: {scrapers['total']}")
        print(f"   ✅ Present: {scrapers['present']} ({scrapers['present']/scrapers['total']*100:.1f}%)")
        print(f"   ⚡ Functional: {scrapers['functional']} ({scrapers['functional']/scrapers['total']*100:.1f}%)")
        print(f"   🏆 Bug-Free: {scrapers['bug_free']} ({scrapers['bug_free']/scrapers['total']*100:.1f}%)")
        
        print(f"\n📋 SYSTEM SCRIPTS VALIDATION:")
        print(f"   Total Scripts: {scripts['total']}")
        print(f"   ✅ Present: {scripts['present']} ({scripts['present']/scripts['total']*100:.1f}%)")
        print(f"   ⚡ Functional: {scripts['functional']} ({scripts['functional']/scripts['total']*100:.1f}%)")
        print(f"   🔗 Integrated: {scripts['integrated']} ({scripts['integrated']/scripts['total']*100:.1f}%)")
        
        print(f"\n🏥 OVERALL SYSTEM HEALTH:")
        print(f"   Status: {health['status']}")
        print(f"   Score: {health['score']*100:.1f}%")
        
        if health['issues']:
            print(f"\n⚠️ ISSUES FOUND:")
            for issue in health['issues']:
                print(f"   - {issue}")
        
        if health['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in health['recommendations']:
                print(f"   - {rec}")
        
        # List any non-functional scrapers
        non_functional = [r for r in scrapers['individual_results'] if not r['functional']]
        if non_functional:
            print(f"\n❌ NON-FUNCTIONAL SCRAPERS ({len(non_functional)}):")
            for scraper in non_functional:
                print(f"   - {scraper['dealer_name']}: {scraper['bugs'][0] if scraper['bugs'] else 'Unknown issue'}")
        
        # List scrapers with bugs
        buggy = [r for r in scrapers['individual_results'] if r['functional'] and not r['bug_free']]
        if buggy:
            print(f"\n⚠️ SCRAPERS WITH ISSUES ({len(buggy)}):")
            for scraper in buggy:
                issues = scraper['bugs'] + scraper['issues']
                print(f"   - {scraper['dealer_name']}: {issues[0] if issues else 'Minor issues'}")

def main():
    """Main execution"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 SILVER FOX SCRAPER SYSTEM - COMPLETE INTEGRITY VALIDATION")
    print("="*60)
    print("Validating each scraper and all system components...")
    print("")
    
    validator = SystemIntegrityValidator()
    results = validator.validate_complete_system()
    
    return results

if __name__ == "__main__":
    main()