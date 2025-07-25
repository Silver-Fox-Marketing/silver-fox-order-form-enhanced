"""
Data consistency verification for Silver Fox Marketing dealership database
Ensures data remains consistent across tables and identifies discrepancies
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Set
import pandas as pd
from database_connection import db_manager
from database_config import CONDITION_MAPPING

logger = logging.getLogger(__name__)

class ConsistencyChecker:
    """Comprehensive data consistency verification"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self.consistency_results = {
            'timestamp': None,
            'checks_performed': 0,
            'inconsistencies_found': 0,
            'critical_issues': [],
            'warnings': [],
            'detailed_results': {}
        }
    
    def check_raw_normalized_consistency(self) -> Dict:
        """Check consistency between raw and normalized data"""
        logger.info("Checking raw vs normalized data consistency...")
        
        issues = []
        
        # Check 1: Every normalized record should have a corresponding raw record
        orphaned_normalized = self.db.execute_query("""
            SELECT 
                n.id as normalized_id,
                n.vin,
                n.stock,
                n.location,
                n.raw_data_id
            FROM normalized_vehicle_data n
            LEFT JOIN raw_vehicle_data r ON n.raw_data_id = r.id
            WHERE n.raw_data_id IS NOT NULL 
            AND r.id IS NULL
            LIMIT 100
        """)
        
        if orphaned_normalized:
            issues.append({
                'type': 'critical',
                'issue': 'orphaned_normalized_records',
                'count': len(orphaned_normalized),
                'sample_records': orphaned_normalized[:5],
                'description': 'Normalized records referencing non-existent raw records'
            })
        
        # Check 2: VIN consistency between raw and normalized
        vin_mismatches = self.db.execute_query("""
            SELECT 
                r.vin as raw_vin,
                n.vin as normalized_vin,
                r.stock as raw_stock,
                n.stock as normalized_stock,
                r.location
            FROM raw_vehicle_data r
            JOIN normalized_vehicle_data n ON r.id = n.raw_data_id
            WHERE r.vin != n.vin OR r.stock != n.stock
            LIMIT 50
        """)
        
        if vin_mismatches:
            issues.append({
                'type': 'critical',
                'issue': 'vin_stock_mismatches',
                'count': len(vin_mismatches),
                'sample_records': vin_mismatches[:5],
                'description': 'VIN or stock number mismatches between raw and normalized data'
            })
        
        # Check 3: Missing normalization for recent raw data
        missing_normalized = self.db.execute_query("""
            SELECT 
                r.id as raw_id,
                r.vin,
                r.stock,
                r.location,
                r.import_date
            FROM raw_vehicle_data r
            LEFT JOIN normalized_vehicle_data n ON r.id = n.raw_data_id
            WHERE n.raw_data_id IS NULL
            AND r.import_date >= CURRENT_DATE - INTERVAL '7 days'
            AND r.vin IS NOT NULL
            AND r.stock IS NOT NULL
            LIMIT 100
        """)
        
        if missing_normalized:
            issues.append({
                'type': 'warning',
                'issue': 'missing_normalized_records',
                'count': len(missing_normalized),
                'sample_records': missing_normalized[:5],
                'description': 'Recent raw records without corresponding normalized records'
            })
        
        return {
            'check_name': 'raw_normalized_consistency',
            'issues_found': len(issues),
            'issues': issues
        }
    
    def check_vin_history_consistency(self) -> Dict:
        """Check VIN history consistency"""
        logger.info("Checking VIN history consistency...")
        
        issues = []
        
        # Check 1: VIN history entries without corresponding raw data
        orphaned_history = self.db.execute_query("""
            SELECT 
                v.id as history_id,
                v.vin,
                v.dealership_name,
                v.scan_date,
                v.raw_data_id
            FROM vin_history v
            LEFT JOIN raw_vehicle_data r ON v.raw_data_id = r.id
            WHERE v.raw_data_id IS NOT NULL 
            AND r.id IS NULL
            LIMIT 50
        """)
        
        if orphaned_history:
            issues.append({
                'type': 'warning',
                'issue': 'orphaned_history_records',
                'count': len(orphaned_history),
                'sample_records': orphaned_history[:5],
                'description': 'VIN history records referencing deleted raw data'
            })
        
        # Check 2: Missing VIN history for recent normalized data
        missing_history = self.db.execute_query("""
            SELECT 
                n.vin,
                n.location,
                n.last_seen_date
            FROM normalized_vehicle_data n
            LEFT JOIN vin_history v ON n.vin = v.vin AND n.location = v.dealership_name
            WHERE v.vin IS NULL
            AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if missing_history:
            issues.append({
                'type': 'warning',
                'issue': 'missing_vin_history',
                'count': len(missing_history),
                'sample_records': missing_history[:5],
                'description': 'Recent vehicles without VIN history entries'
            })
        
        # Check 3: VIN history count vs normalized data scan count
        scan_count_mismatches = self.db.execute_query("""
            WITH history_counts AS (
                SELECT 
                    vin,
                    dealership_name,
                    COUNT(DISTINCT scan_date) as history_scan_count
                FROM vin_history
                WHERE scan_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY vin, dealership_name
            )
            SELECT 
                n.vin,
                n.location,
                n.vin_scan_count as normalized_count,
                h.history_scan_count
            FROM normalized_vehicle_data n
            JOIN history_counts h ON n.vin = h.vin AND n.location = h.dealership_name
            WHERE n.vin_scan_count != h.history_scan_count
            AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if scan_count_mismatches:
            issues.append({
                'type': 'warning',
                'issue': 'scan_count_mismatches',
                'count': len(scan_count_mismatches),
                'sample_records': scan_count_mismatches[:5],
                'description': 'Scan count mismatches between normalized data and VIN history'
            })
        
        return {
            'check_name': 'vin_history_consistency',
            'issues_found': len(issues),
            'issues': issues
        }
    
    def check_dealership_config_consistency(self) -> Dict:
        """Check dealership configuration consistency"""
        logger.info("Checking dealership configuration consistency...")
        
        issues = []
        
        # Check 1: Active dealerships without recent data
        inactive_dealers = self.db.execute_query("""
            SELECT 
                d.name,
                d.is_active,
                MAX(n.last_seen_date) as last_data_date,
                COUNT(n.id) as vehicle_count
            FROM dealership_configs d
            LEFT JOIN normalized_vehicle_data n ON d.name = n.location
            WHERE d.is_active = true
            GROUP BY d.name, d.is_active
            HAVING MAX(n.last_seen_date) < CURRENT_DATE - INTERVAL '2 days'
               OR MAX(n.last_seen_date) IS NULL
        """)
        
        if inactive_dealers:
            issues.append({
                'type': 'warning',
                'issue': 'active_dealers_no_data',
                'count': len(inactive_dealers),
                'sample_records': inactive_dealers,
                'description': 'Active dealerships without recent data'
            })
        
        # Check 2: Dealerships with data but no configuration
        unconfigured_dealers = self.db.execute_query("""
            SELECT DISTINCT
                n.location,
                COUNT(*) as vehicle_count,
                MAX(n.last_seen_date) as last_seen
            FROM normalized_vehicle_data n
            LEFT JOIN dealership_configs d ON n.location = d.name
            WHERE d.name IS NULL
            AND n.last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY n.location
        """)
        
        if unconfigured_dealers:
            issues.append({
                'type': 'critical',
                'issue': 'unconfigured_dealers',
                'count': len(unconfigured_dealers),
                'sample_records': unconfigured_dealers,
                'description': 'Dealerships with data but no configuration'
            })
        
        # Check 3: Configuration JSON validity
        invalid_configs = []
        try:
            configs = self.db.execute_query("""
                SELECT name, filtering_rules, output_rules
                FROM dealership_configs
                WHERE is_active = true
            """)
            
            for config in configs:
                # Test JSON parsing
                try:
                    if config['filtering_rules']:
                        import json
                        json.loads(json.dumps(config['filtering_rules']))
                    if config['output_rules']:
                        json.loads(json.dumps(config['output_rules']))
                except Exception as e:
                    invalid_configs.append({
                        'dealership': config['name'],
                        'error': str(e)
                    })
        except Exception as e:
            logger.error(f"Failed to check config JSON validity: {e}")
        
        if invalid_configs:
            issues.append({
                'type': 'critical',
                'issue': 'invalid_json_configs',
                'count': len(invalid_configs),
                'sample_records': invalid_configs[:5],
                'description': 'Dealership configurations with invalid JSON'
            })
        
        return {
            'check_name': 'dealership_config_consistency',
            'issues_found': len(issues),
            'issues': issues
        }
    
    def check_data_normalization_consistency(self) -> Dict:
        """Check data normalization consistency"""
        logger.info("Checking data normalization consistency...")
        
        issues = []
        
        # Check 1: Vehicle condition normalization consistency
        condition_issues = []
        
        # Get raw data with their normalized equivalents
        raw_normalized_pairs = self.db.execute_query("""
            SELECT 
                r.type as raw_type,
                r.status as raw_status,
                n.vehicle_condition as normalized_condition,
                r.location
            FROM raw_vehicle_data r
            JOIN normalized_vehicle_data n ON r.id = n.raw_data_id
            WHERE r.import_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 1000
        """)
        
        # Verify normalization rules are applied correctly
        for pair in raw_normalized_pairs:
            expected_condition = self._normalize_condition_test(
                pair['raw_type'], pair['raw_status']
            )
            
            if expected_condition != pair['normalized_condition']:
                condition_issues.append({
                    'raw_type': pair['raw_type'],
                    'raw_status': pair['raw_status'],
                    'expected': expected_condition,
                    'actual': pair['normalized_condition'],
                    'location': pair['location']
                })
        
        if condition_issues:
            issues.append({
                'type': 'warning',
                'issue': 'normalization_inconsistencies',
                'count': len(condition_issues),
                'sample_records': condition_issues[:10],
                'description': 'Vehicle condition normalization inconsistencies'
            })
        
        # Check 2: Price consistency (price vs MSRP)
        price_issues = self.db.execute_query("""
            SELECT 
                vin,
                stock,
                location,
                price,
                msrp,
                ROUND((price / NULLIF(msrp, 0) - 1) * 100, 2) as markup_percent
            FROM normalized_vehicle_data
            WHERE price IS NOT NULL 
            AND msrp IS NOT NULL 
            AND msrp > 0
            AND price > msrp * 1.5  -- More than 50% over MSRP
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if price_issues:
            issues.append({
                'type': 'warning',
                'issue': 'price_msrp_inconsistencies',
                'count': len(price_issues),
                'sample_records': price_issues[:10],
                'description': 'Vehicles priced significantly above MSRP'
            })
        
        # Check 3: Year consistency
        year_issues = self.db.execute_query("""
            SELECT 
                vin,
                stock,
                location,
                year,
                make,
                model
            FROM normalized_vehicle_data
            WHERE year IS NOT NULL
            AND (year < 1980 OR year > EXTRACT(YEAR FROM CURRENT_DATE) + 2)
            AND last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
            LIMIT 50
        """)
        
        if year_issues:
            issues.append({
                'type': 'critical',
                'issue': 'invalid_year_data',
                'count': len(year_issues),
                'sample_records': year_issues[:10],
                'description': 'Vehicles with impossible year values'
            })
        
        return {
            'check_name': 'data_normalization_consistency',
            'issues_found': len(issues),
            'issues': issues
        }
    
    def _normalize_condition_test(self, type_value: str, status_value: str) -> str:
        """Test version of condition normalization for consistency checking"""
        if pd.isna(type_value) and pd.isna(status_value):
            return 'onlot'
        
        # Check type first
        type_str = str(type_value).lower().strip() if not pd.isna(type_value) else ''
        if type_str in CONDITION_MAPPING:
            return CONDITION_MAPPING[type_str]
        
        # Check status if type doesn't match
        status_str = str(status_value).lower().strip() if not pd.isna(status_value) else ''
        if status_str in CONDITION_MAPPING:
            return CONDITION_MAPPING[status_str]
        
        return 'onlot'
    
    def check_temporal_consistency(self) -> Dict:
        """Check temporal data consistency"""
        logger.info("Checking temporal data consistency...")
        
        issues = []
        
        # Check 1: Future dates
        future_dates = self.db.execute_query("""
            SELECT 
                'normalized_vehicle_data' as table_name,
                'last_seen_date' as date_field,
                vin,
                location,
                last_seen_date as date_value
            FROM normalized_vehicle_data
            WHERE last_seen_date > CURRENT_DATE
            
            UNION ALL
            
            SELECT 
                'raw_vehicle_data' as table_name,
                'import_date' as date_field,
                vin,
                location,
                import_date as date_value
            FROM raw_vehicle_data
            WHERE import_date > CURRENT_DATE
            
            UNION ALL
            
            SELECT 
                'vin_history' as table_name,
                'scan_date' as date_field,
                vin,
                dealership_name as location,
                scan_date as date_value
            FROM vin_history
            WHERE scan_date > CURRENT_DATE
            
            LIMIT 50
        """)
        
        if future_dates:
            issues.append({
                'type': 'critical',
                'issue': 'future_dates',
                'count': len(future_dates),
                'sample_records': future_dates[:10],
                'description': 'Records with future dates'
            })
        
        # Check 2: Import date vs last seen date consistency
        date_inconsistencies = self.db.execute_query("""
            SELECT 
                n.vin,
                n.location,
                n.last_seen_date,
                r.import_date,
                n.last_seen_date - r.import_date as date_diff
            FROM normalized_vehicle_data n
            JOIN raw_vehicle_data r ON n.raw_data_id = r.id
            WHERE n.last_seen_date < r.import_date
            AND r.import_date >= CURRENT_DATE - INTERVAL '30 days'
            LIMIT 50
        """)
        
        if date_inconsistencies:
            issues.append({
                'type': 'warning',
                'issue': 'date_sequence_inconsistencies',
                'count': len(date_inconsistencies),
                'sample_records': date_inconsistencies[:10],
                'description': 'Last seen date before import date'
            })
        
        # Check 3: Gaps in VIN history
        history_gaps = self.db.execute_query("""
            WITH date_diffs AS (
                SELECT 
                    vin,
                    dealership_name,
                    scan_date,
                    LAG(scan_date) OVER (PARTITION BY vin, dealership_name ORDER BY scan_date) as prev_scan,
                    scan_date - LAG(scan_date) OVER (PARTITION BY vin, dealership_name ORDER BY scan_date) as gap_days
                FROM vin_history
                WHERE scan_date >= CURRENT_DATE - INTERVAL '30 days'
            )
            SELECT 
                vin,
                dealership_name,
                scan_date,
                prev_scan,
                gap_days
            FROM date_diffs
            WHERE gap_days > 7  -- Gaps longer than 7 days
            ORDER BY gap_days DESC
            LIMIT 50
        """)
        
        if history_gaps:
            issues.append({
                'type': 'warning',
                'issue': 'vin_history_gaps',
                'count': len(history_gaps),
                'sample_records': history_gaps[:10],
                'description': 'Large gaps in VIN history tracking'
            })
        
        return {
            'check_name': 'temporal_consistency',
            'issues_found': len(issues),
            'issues': issues
        }
    
    def check_cross_table_counts(self) -> Dict:
        """Check consistency of counts across related tables"""
        logger.info("Checking cross-table count consistency...")
        
        issues = []
        
        # Get counts from each table
        table_counts = {}
        
        # Raw data count (last 7 days)
        raw_count = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM raw_vehicle_data
            WHERE import_date >= CURRENT_DATE - INTERVAL '7 days'
        """, fetch='one')
        table_counts['raw_recent'] = raw_count['count']
        
        # Normalized data count (last 7 days)
        normalized_count = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM normalized_vehicle_data
            WHERE last_seen_date >= CURRENT_DATE - INTERVAL '7 days'
        """, fetch='one')
        table_counts['normalized_recent'] = normalized_count['count']
        
        # VIN history count (last 7 days)
        history_count = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM vin_history
            WHERE scan_date >= CURRENT_DATE - INTERVAL '7 days'
        """, fetch='one')
        table_counts['history_recent'] = history_count['count']
        
        # Check for significant discrepancies
        # Normalized should be <= Raw (due to filtering)
        if table_counts['normalized_recent'] > table_counts['raw_recent']:
            issues.append({
                'type': 'critical',
                'issue': 'normalized_exceeds_raw',
                'description': f"Normalized count ({table_counts['normalized_recent']}) exceeds raw count ({table_counts['raw_recent']})",
                'raw_count': table_counts['raw_recent'],
                'normalized_count': table_counts['normalized_recent']
            })
        
        # History count should be >= Normalized (vehicles can have multiple history entries)
        if table_counts['history_recent'] < table_counts['normalized_recent']:
            issues.append({
                'type': 'warning',
                'issue': 'history_less_than_normalized',
                'description': f"History count ({table_counts['history_recent']}) is less than normalized count ({table_counts['normalized_recent']})",
                'normalized_count': table_counts['normalized_recent'],
                'history_count': table_counts['history_recent']
            })
        
        # Check for empty tables when data is expected
        if table_counts['raw_recent'] == 0:
            issues.append({
                'type': 'critical',
                'issue': 'no_recent_raw_data',
                'description': 'No raw data imported in the last 7 days',
                'expected': 'Daily imports'
            })
        
        return {
            'check_name': 'cross_table_counts',
            'issues_found': len(issues),
            'issues': issues,
            'table_counts': table_counts
        }
    
    def run_full_consistency_check(self) -> Dict:
        """Run all consistency checks"""
        self.consistency_results['timestamp'] = datetime.now()
        
        check_functions = [
            self.check_raw_normalized_consistency,
            self.check_vin_history_consistency,
            self.check_dealership_config_consistency,
            self.check_data_normalization_consistency,
            self.check_temporal_consistency,
            self.check_cross_table_counts
        ]
        
        for check_func in check_functions:
            try:
                result = check_func()
                self.consistency_results['checks_performed'] += 1
                self.consistency_results['detailed_results'][result['check_name']] = result
                
                # Categorize issues
                for issue in result.get('issues', []):
                    if issue['type'] == 'critical':
                        self.consistency_results['critical_issues'].append({
                            'check': result['check_name'],
                            'issue': issue['issue'],
                            'count': issue.get('count', 1),
                            'description': issue.get('description', '')
                        })
                    else:  # warning
                        self.consistency_results['warnings'].append({
                            'check': result['check_name'],
                            'issue': issue['issue'],
                            'count': issue.get('count', 1),
                            'description': issue.get('description', '')
                        })
                
                self.consistency_results['inconsistencies_found'] += result['issues_found']
                
            except Exception as e:
                logger.error(f"Consistency check {check_func.__name__} failed: {e}")
                self.consistency_results['critical_issues'].append({
                    'check': check_func.__name__,
                    'issue': 'check_failed',
                    'error': str(e)
                })
        
        return self.consistency_results
    
    def generate_consistency_report(self) -> str:
        """Generate comprehensive consistency report"""
        if not self.consistency_results['timestamp']:
            return "No consistency check results available. Run check first."
        
        report = f"""
SILVER FOX MARKETING - DATA CONSISTENCY REPORT
==============================================
Generated: {self.consistency_results['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

CONSISTENCY SUMMARY
===================
Checks Performed: {self.consistency_results['checks_performed']}
Total Inconsistencies: {self.consistency_results['inconsistencies_found']}
Critical Issues: {len(self.consistency_results['critical_issues'])}
Warnings: {len(self.consistency_results['warnings'])}

CRITICAL ISSUES ({len(self.consistency_results['critical_issues'])})
===============
"""
        
        if self.consistency_results['critical_issues']:
            for issue in self.consistency_results['critical_issues']:
                report += f"❌ {issue['check']}: {issue['issue']}\n"
                report += f"   Description: {issue.get('description', 'N/A')}\n"
                if 'count' in issue:
                    report += f"   Count: {issue['count']}\n"
                report += "\n"
        else:
            report += "✅ No critical consistency issues found\n\n"
        
        report += f"""WARNINGS ({len(self.consistency_results['warnings'])})
========
"""
        
        if self.consistency_results['warnings']:
            for warning in self.consistency_results['warnings']:
                report += f"⚠️  {warning['check']}: {warning['issue']}\n"
                report += f"   Description: {warning.get('description', 'N/A')}\n"
                if 'count' in warning:
                    report += f"   Count: {warning['count']}\n"
                report += "\n"
        else:
            report += "✅ No warnings\n\n"
        
        # Add detailed results summary
        report += "DETAILED CHECK RESULTS\n"
        report += "======================\n"
        
        for check_name, result in self.consistency_results['detailed_results'].items():
            status = "PASS" if result['issues_found'] == 0 else "ISSUES FOUND"
            report += f"{check_name}: {status} ({result['issues_found']} issues)\n"
        
        report += "\nRECOMMENDations\n"
        report += "===============\n"
        
        if len(self.consistency_results['critical_issues']) == 0:
            report += "✅ Data consistency is good. No critical issues found.\n"
        else:
            report += "❌ Critical consistency issues require immediate attention:\n"
            for issue in self.consistency_results['critical_issues'][:5]:
                report += f"   - Fix {issue['issue']} in {issue['check']}\n"
        
        if len(self.consistency_results['warnings']) > 0:
            report += "\n⚠️  Consider addressing these warnings:\n"
            for warning in self.consistency_results['warnings'][:5]:
                report += f"   - {warning['issue']}\n"
        
        return report

def main():
    """Main function for consistency checking"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database consistency verification')
    parser.add_argument('--full', action='store_true', help='Run full consistency check')
    parser.add_argument('--raw-normalized', action='store_true', help='Check raw vs normalized consistency')
    parser.add_argument('--vin-history', action='store_true', help='Check VIN history consistency')
    parser.add_argument('--configs', action='store_true', help='Check dealership configuration consistency')
    parser.add_argument('--normalization', action='store_true', help='Check data normalization consistency')
    parser.add_argument('--temporal', action='store_true', help='Check temporal consistency')
    parser.add_argument('--counts', action='store_true', help='Check cross-table count consistency')
    parser.add_argument('--report', help='Save report to file')
    
    args = parser.parse_args()
    
    checker = ConsistencyChecker()
    
    try:
        if args.full or not any([args.raw_normalized, args.vin_history, args.configs, 
                                args.normalization, args.temporal, args.counts]):
            print("Running full consistency check...")
            results = checker.run_full_consistency_check()
            
            print(f"\nConsistency Check Complete:")
            print(f"  Checks Performed: {results['checks_performed']}")
            print(f"  Critical Issues: {len(results['critical_issues'])}")
            print(f"  Warnings: {len(results['warnings'])}")
            
        else:
            # Run specific checks
            if args.raw_normalized:
                result = checker.check_raw_normalized_consistency()
                print(f"Raw-Normalized Consistency: {result['issues_found']} issues found")
            
            if args.vin_history:
                result = checker.check_vin_history_consistency()
                print(f"VIN History Consistency: {result['issues_found']} issues found")
            
            if args.configs:
                result = checker.check_dealership_config_consistency()
                print(f"Config Consistency: {result['issues_found']} issues found")
            
            if args.normalization:
                result = checker.check_data_normalization_consistency()
                print(f"Normalization Consistency: {result['issues_found']} issues found")
            
            if args.temporal:
                result = checker.check_temporal_consistency()
                print(f"Temporal Consistency: {result['issues_found']} issues found")
            
            if args.counts:
                result = checker.check_cross_table_counts()
                print(f"Count Consistency: {result['issues_found']} issues found")
        
        # Generate and save report
        if args.report:
            report = checker.generate_consistency_report()
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"Report saved to: {args.report}")
        
    except Exception as e:
        print(f"Consistency check failed: {e}")
        raise

if __name__ == "__main__":
    main()