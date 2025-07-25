"""
Data validation and integrity verification for Silver Fox Marketing dealership database
Ensures data quality and consistency across all operations
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
from database_connection import db_manager
from database_config import CONDITION_MAPPING, REQUIRED_COLUMNS

logger = logging.getLogger(__name__)

class DataValidator:
    """Comprehensive data validation and integrity checking"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.validation_results = {
            'timestamp': None,
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'warnings': [],
            'errors': [],
            'critical_issues': []
        }
    
    def validate_vin_integrity(self) -> Dict:
        """Validate VIN integrity across all tables"""
        logger.info("Validating VIN integrity...")
        
        issues = []
        
        # Check for duplicate VINs at same dealership
        duplicate_vins = self.db.execute_query("""
            SELECT vin, location, COUNT(*) as count
            FROM normalized_vehicle_data
            WHERE last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY vin, location
            HAVING COUNT(*) > 1
        """)
        
        if duplicate_vins:
            issues.append({
                'type': 'critical',
                'issue': 'duplicate_vins_same_dealer',
                'count': len(duplicate_vins),
                'details': duplicate_vins[:10]  # First 10 examples
            })
        
        # Check for invalid VIN formats
        invalid_vins = self.db.execute_query("""
            SELECT vin, location, stock
            FROM normalized_vehicle_data
            WHERE LENGTH(vin) != 17 
               OR vin ~ '[IOQ]'  -- VINs cannot contain I, O, or Q
               OR vin !~ '^[A-Z0-9]+$'  -- Must be alphanumeric
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 100
        """)
        
        if invalid_vins:
            issues.append({
                'type': 'error',
                'issue': 'invalid_vin_format',
                'count': len(invalid_vins),
                'details': invalid_vins[:10]
            })
        
        # Check for VINs with impossible year/model combinations
        impossible_combos = self.db.execute_query("""
            SELECT vin, year, make, model, location
            FROM normalized_vehicle_data
            WHERE (year < 1980 OR year > EXTRACT(YEAR FROM CURRENT_DATE) + 2)
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if impossible_combos:
            issues.append({
                'type': 'warning',
                'issue': 'impossible_year_combinations',
                'count': len(impossible_combos),
                'details': impossible_combos[:10]
            })
        
        return {
            'vin_validation_passed': len([i for i in issues if i['type'] == 'critical']) == 0,
            'issues_found': len(issues),
            'issues': issues
        }
    
    def validate_price_consistency(self) -> Dict:
        """Validate price data consistency"""
        logger.info("Validating price consistency...")
        
        issues = []
        
        # Check for unrealistic prices
        price_outliers = self.db.execute_query("""
            SELECT vin, make, model, year, price, location
            FROM normalized_vehicle_data
            WHERE (price < 1000 OR price > 500000)
            AND price IS NOT NULL
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if price_outliers:
            issues.append({
                'type': 'warning',
                'issue': 'price_outliers',
                'count': len(price_outliers),
                'details': price_outliers[:10]
            })
        
        # Check for price > MSRP by significant margin
        price_msrp_issues = self.db.execute_query("""
            SELECT vin, make, model, price, msrp, location,
                   ROUND((price / NULLIF(msrp, 0) - 1) * 100, 2) as price_markup_percent
            FROM normalized_vehicle_data
            WHERE msrp IS NOT NULL 
            AND msrp > 0 
            AND price > msrp * 1.2  -- More than 20% over MSRP
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if price_msrp_issues:
            issues.append({
                'type': 'warning',
                'issue': 'price_exceeds_msrp',
                'count': len(price_msrp_issues),
                'details': price_msrp_issues[:10]
            })
        
        return {
            'price_validation_passed': len([i for i in issues if i['type'] == 'critical']) == 0,
            'issues_found': len(issues),
            'issues': issues
        }
    
    def validate_dealer_configuration(self) -> Dict:
        """Validate dealership configuration integrity"""
        logger.info("Validating dealer configurations...")
        
        issues = []
        
        # Check for active dealerships without recent data
        inactive_dealers = self.db.execute_query("""
            SELECT d.name, d.is_active, MAX(n.last_seen_date) as last_data
            FROM dealership_configs d
            LEFT JOIN normalized_vehicle_data n ON d.name = n.location
            WHERE d.is_active = true
            GROUP BY d.name, d.is_active
            HAVING MAX(n.last_seen_date) < CURRENT_DATE - INTERVAL '7 days'
               OR MAX(n.last_seen_date) IS NULL
        """)
        
        if inactive_dealers:
            issues.append({
                'type': 'warning',
                'issue': 'active_dealers_no_recent_data',
                'count': len(inactive_dealers),
                'details': inactive_dealers
            })
        
        # Check for dealers with data but no configuration
        unconfigured_dealers = self.db.execute_query("""
            SELECT DISTINCT n.location, COUNT(*) as vehicle_count
            FROM normalized_vehicle_data n
            LEFT JOIN dealership_configs d ON n.location = d.name
            WHERE d.name IS NULL
            AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY n.location
        """)
        
        if unconfigured_dealers:
            issues.append({
                'type': 'error',
                'issue': 'dealers_without_config',
                'count': len(unconfigured_dealers),
                'details': unconfigured_dealers
            })
        
        # Validate JSON configuration syntax
        invalid_configs = self.db.execute_query("""
            SELECT name, 'filtering_rules' as config_type
            FROM dealership_configs
            WHERE filtering_rules IS NOT NULL 
            AND NOT (filtering_rules::text ~ '^\\{.*\\}$')
            
            UNION
            
            SELECT name, 'output_rules' as config_type
            FROM dealership_configs
            WHERE output_rules IS NOT NULL 
            AND NOT (output_rules::text ~ '^\\{.*\\}$')
        """)
        
        if invalid_configs:
            issues.append({
                'type': 'critical',
                'issue': 'invalid_json_configs',
                'count': len(invalid_configs),
                'details': invalid_configs
            })
        
        return {
            'config_validation_passed': len([i for i in issues if i['type'] == 'critical']) == 0,
            'issues_found': len(issues),
            'issues': issues
        }
    
    def validate_data_freshness(self) -> Dict:
        """Validate data freshness and update patterns"""
        logger.info("Validating data freshness...")
        
        issues = []
        
        # Check for stale data (no updates in 24 hours for active dealers)
        stale_dealers = self.db.execute_query("""
            SELECT 
                d.name,
                MAX(r.import_date) as last_import,
                COUNT(DISTINCT r.import_date) as import_days_last_week
            FROM dealership_configs d
            LEFT JOIN raw_vehicle_data r ON d.name = r.location
            WHERE d.is_active = true
            AND r.import_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY d.name
            HAVING MAX(r.import_date) < CURRENT_DATE - INTERVAL '1 day'
               OR COUNT(DISTINCT r.import_date) < 5  -- Less than 5 days of data
        """)
        
        if stale_dealers:
            issues.append({
                'type': 'warning',
                'issue': 'stale_dealer_data',
                'count': len(stale_dealers),
                'details': stale_dealers
            })
        
        # Check for unusual import volumes
        volume_anomalies = self.db.execute_query("""
            WITH daily_imports AS (
                SELECT 
                    location,
                    import_date,
                    COUNT(*) as daily_count
                FROM raw_vehicle_data
                WHERE import_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY location, import_date
            ),
            avg_volumes AS (
                SELECT 
                    location,
                    AVG(daily_count) as avg_daily,
                    STDDEV(daily_count) as stddev_daily
                FROM daily_imports
                GROUP BY location
                HAVING COUNT(*) >= 3  -- At least 3 days of data
            )
            SELECT 
                di.location,
                di.import_date,
                di.daily_count,
                av.avg_daily,
                ROUND((di.daily_count - av.avg_daily) / NULLIF(av.stddev_daily, 0), 2) as z_score
            FROM daily_imports di
            JOIN avg_volumes av ON di.location = av.location
            WHERE ABS((di.daily_count - av.avg_daily) / NULLIF(av.stddev_daily, 0)) > 2
            ORDER BY ABS((di.daily_count - av.avg_daily) / NULLIF(av.stddev_daily, 0)) DESC
            LIMIT 20
        """)
        
        if volume_anomalies:
            issues.append({
                'type': 'warning',
                'issue': 'unusual_import_volumes',
                'count': len(volume_anomalies),
                'details': volume_anomalies[:10]
            })
        
        return {
            'freshness_validation_passed': True,  # Warnings don't fail validation
            'issues_found': len(issues),
            'issues': issues
        }
    
    def validate_referential_integrity(self) -> Dict:
        """Validate referential integrity between tables"""
        logger.info("Validating referential integrity...")
        
        issues = []
        
        # Check for orphaned normalized records
        orphaned_normalized = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data n
            LEFT JOIN raw_vehicle_data r ON n.raw_data_id = r.id
            WHERE n.raw_data_id IS NOT NULL 
            AND r.id IS NULL
        """, fetch='one')
        
        if orphaned_normalized['count'] > 0:
            issues.append({
                'type': 'critical',
                'issue': 'orphaned_normalized_records',
                'count': orphaned_normalized['count']
            })
        
        # Check for orphaned VIN history records
        orphaned_history = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM vin_history v
            LEFT JOIN raw_vehicle_data r ON v.raw_data_id = r.id
            WHERE v.raw_data_id IS NOT NULL 
            AND r.id IS NULL
        """, fetch='one')
        
        if orphaned_history['count'] > 0:
            issues.append({
                'type': 'error',
                'issue': 'orphaned_history_records',
                'count': orphaned_history['count']
            })
        
        # Check for missing dealer configurations
        missing_configs = self.db.execute_query("""
            SELECT DISTINCT n.location
            FROM normalized_vehicle_data n
            LEFT JOIN dealership_configs d ON n.location = d.name
            WHERE d.name IS NULL
            AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        
        if missing_configs:
            issues.append({
                'type': 'error',
                'issue': 'missing_dealer_configs',
                'count': len(missing_configs),
                'details': [config['location'] for config in missing_configs]
            })
        
        return {
            'integrity_validation_passed': len([i for i in issues if i['type'] == 'critical']) == 0,
            'issues_found': len(issues),
            'issues': issues
        }
    
    def validate_business_rules(self) -> Dict:
        """Validate Silver Fox specific business rules"""
        logger.info("Validating business rules...")
        
        issues = []
        
        # Check for vehicles missing stock numbers (critical for QR generation)
        missing_stock = self.db.execute_query("""
            SELECT vin, location, make, model
            FROM normalized_vehicle_data
            WHERE (stock IS NULL OR stock = '')
            AND vehicle_condition IN ('new', 'po', 'cpo', 'onlot')
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if missing_stock:
            issues.append({
                'type': 'critical',
                'issue': 'missing_stock_numbers',
                'count': len(missing_stock),
                'details': missing_stock[:10],
                'impact': 'Cannot generate QR codes for order processing'
            })
        
        # Check for off-lot vehicles that should be filtered
        offlot_vehicles = self.db.execute_query("""
            SELECT location, COUNT(*) as offlot_count
            FROM normalized_vehicle_data
            WHERE vehicle_condition = 'offlot'
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY location
            HAVING COUNT(*) > 100  -- Unusual amount of off-lot vehicles
        """)
        
        if offlot_vehicles:
            issues.append({
                'type': 'warning',
                'issue': 'excessive_offlot_vehicles',
                'count': len(offlot_vehicles),
                'details': offlot_vehicles,
                'impact': 'May indicate scraping or classification issues'
            })
        
        # Check for dealers with no QR output path configured
        no_qr_path = self.db.execute_query("""
            SELECT d.name, COUNT(n.id) as vehicle_count
            FROM dealership_configs d
            JOIN normalized_vehicle_data n ON d.name = n.location
            WHERE d.is_active = true
            AND (d.qr_output_path IS NULL OR d.qr_output_path = '')
            AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY d.name
        """)
        
        if no_qr_path:
            issues.append({
                'type': 'error',
                'issue': 'dealers_without_qr_path',
                'count': len(no_qr_path),
                'details': no_qr_path,
                'impact': 'Cannot export with QR code paths for order processing'
            })
        
        return {
            'business_rules_passed': len([i for i in issues if i['type'] == 'critical']) == 0,
            'issues_found': len(issues),
            'issues': issues
        }
    
    def run_full_validation(self) -> Dict:
        """Run all validation checks and compile results"""
        self.validation_results['timestamp'] = datetime.now()
        
        validation_functions = [
            ('VIN Integrity', self.validate_vin_integrity),
            ('Price Consistency', self.validate_price_consistency),
            ('Dealer Configuration', self.validate_dealer_configuration),
            ('Data Freshness', self.validate_data_freshness),
            ('Referential Integrity', self.validate_referential_integrity),
            ('Business Rules', self.validate_business_rules)
        ]
        
        all_results = {}
        overall_passed = True
        
        for check_name, check_func in validation_functions:
            logger.info(f"Running: {check_name}")
            
            try:
                result = check_func()
                all_results[check_name] = result
                
                self.validation_results['total_checks'] += 1
                
                if result.get(f"{check_name.lower().replace(' ', '_')}_passed", True):
                    self.validation_results['passed_checks'] += 1
                else:
                    self.validation_results['failed_checks'] += 1
                    overall_passed = False
                
                # Categorize issues
                for issue in result.get('issues', []):
                    if issue['type'] == 'critical':
                        self.validation_results['critical_issues'].append({
                            'check': check_name,
                            'issue': issue['issue'],
                            'count': issue.get('count', 1)
                        })
                        overall_passed = False
                    elif issue['type'] == 'error':
                        self.validation_results['errors'].append({
                            'check': check_name,
                            'issue': issue['issue'],
                            'count': issue.get('count', 1)
                        })
                    else:  # warning
                        self.validation_results['warnings'].append({
                            'check': check_name,
                            'issue': issue['issue'],
                            'count': issue.get('count', 1)
                        })
            
            except Exception as e:
                logger.error(f"Validation check {check_name} failed: {e}")
                self.validation_results['failed_checks'] += 1
                self.validation_results['errors'].append({
                    'check': check_name,
                    'issue': 'validation_check_failed',
                    'error': str(e)
                })
                overall_passed = False
        
        self.validation_results['overall_passed'] = overall_passed
        self.validation_results['detailed_results'] = all_results
        
        return self.validation_results
    
    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report"""
        if not self.validation_results['timestamp']:
            return "No validation results available. Run validation first."
        
        report = f"""
SILVER FOX MARKETING - DATABASE VALIDATION REPORT
=================================================
Generated: {self.validation_results['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

VALIDATION SUMMARY
------------------
Total Checks: {self.validation_results['total_checks']}
Passed: {self.validation_results['passed_checks']}
Failed: {self.validation_results['failed_checks']}
Overall Status: {'PASSED' if self.validation_results['overall_passed'] else 'FAILED'}

CRITICAL ISSUES ({len(self.validation_results['critical_issues'])})
{"=" * 20}
"""
        
        for issue in self.validation_results['critical_issues']:
            report += f"❌ {issue['check']}: {issue['issue']} (Count: {issue.get('count', 'N/A')})\n"
        
        if not self.validation_results['critical_issues']:
            report += "✅ No critical issues found\n"
        
        report += f"""
ERRORS ({len(self.validation_results['errors'])})
{"=" * 10}
"""
        
        for error in self.validation_results['errors']:
            report += f"⚠️  {error['check']}: {error['issue']} (Count: {error.get('count', 'N/A')})\n"
        
        if not self.validation_results['errors']:
            report += "✅ No errors found\n"
        
        report += f"""
WARNINGS ({len(self.validation_results['warnings'])})
{"=" * 15}
"""
        
        for warning in self.validation_results['warnings']:
            report += f"⚠️  {warning['check']}: {warning['issue']} (Count: {warning.get('count', 'N/A')})\n"
        
        if not self.validation_results['warnings']:
            report += "✅ No warnings\n"
        
        report += """
RECOMMENDATIONS
===============
"""
        
        if self.validation_results['overall_passed']:
            report += "✅ All critical validations passed. Database is ready for production use.\n"
        else:
            report += "❌ Critical issues found. Address these before production use:\n"
            for issue in self.validation_results['critical_issues']:
                report += f"   - Fix {issue['issue']} in {issue['check']}\n"
        
        if self.validation_results['errors']:
            report += "\n⚠️  Address these errors to improve data quality:\n"
            for error in self.validation_results['errors'][:5]:  # Top 5
                report += f"   - {error['issue']}\n"
        
        return report

def main():
    """Main function for command-line validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate dealership database integrity')
    parser.add_argument('--full', action='store_true', help='Run full validation suite')
    parser.add_argument('--vin', action='store_true', help='Validate VIN integrity only')
    parser.add_argument('--price', action='store_true', help='Validate price consistency only')
    parser.add_argument('--config', action='store_true', help='Validate dealer configurations only')
    parser.add_argument('--report', help='Save report to file')
    
    args = parser.parse_args()
    
    validator = DataValidator()
    
    try:
        if args.full or not any([args.vin, args.price, args.config]):
            print("Running full database validation...")
            results = validator.run_full_validation()
        else:
            # Run specific validations
            if args.vin:
                results = validator.validate_vin_integrity()
            elif args.price:
                results = validator.validate_price_consistency()
            elif args.config:
                results = validator.validate_dealer_configuration()
        
        # Generate and display report
        report = validator.generate_validation_report()
        print(report)
        
        # Save report if requested
        if args.report:
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"\nReport saved to: {args.report}")
    
    except Exception as e:
        print(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()