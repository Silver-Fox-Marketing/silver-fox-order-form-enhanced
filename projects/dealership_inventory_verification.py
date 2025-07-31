#!/usr/bin/env python3
"""
Dealership Inventory Verification System
=========================================
Comprehensive system to verify scraper performance and inventory accuracy
"""

import sys
import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add paths for both systems
sys.path.append('silverfox_scraper_system/silverfox_system')
sys.path.append('minisforum_database_transfer/bulletproof_package/scripts')

# Import database system
from database_connection import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DealershipInventoryVerifier:
    """Comprehensive dealership inventory verification system"""
    
    def __init__(self):
        self.db = db_manager
        self.scraper_registry_file = Path("scraper_integration_registry.json")
        self.verification_results = {}
        
        # Load scraper registry
        if self.scraper_registry_file.exists():
            with open(self.scraper_registry_file, 'r') as f:
                self.scraper_registry = json.load(f)
        else:
            self.scraper_registry = {}
    
    def verify_dealership_inventory(self, dealership_name: str) -> Dict[str, Any]:
        """Comprehensive inventory verification for a specific dealership"""
        logger.info(f"Starting inventory verification for {dealership_name}")
        
        verification = {
            'dealership_name': dealership_name,
            'timestamp': datetime.now().isoformat(),
            'scraper_status': 'unknown',
            'inventory_stats': {},
            'data_quality': {},
            'recent_activity': {},
            'recommendations': [],
            'alerts': []
        }
        
        try:
            # 1. Check scraper integration status
            verification['scraper_status'] = self._check_scraper_status(dealership_name)
            
            # 2. Get inventory statistics
            verification['inventory_stats'] = self._get_inventory_stats(dealership_name)
            
            # 3. Analyze data quality
            verification['data_quality'] = self._analyze_data_quality(dealership_name)
            
            # 4. Check recent activity
            verification['recent_activity'] = self._check_recent_activity(dealership_name)
            
            # 5. Generate recommendations and alerts
            verification['recommendations'] = self._generate_recommendations(verification)
            verification['alerts'] = self._generate_alerts(verification)
            
            # 6. Calculate overall health score
            verification['health_score'] = self._calculate_health_score(verification)
            
            return verification
            
        except Exception as e:
            logger.error(f"Error verifying {dealership_name}: {e}")
            verification['error'] = str(e)
            verification['health_score'] = 0
            return verification
    
    def _check_scraper_status(self, dealership_name: str) -> Dict[str, Any]:
        """Check if scraper is properly integrated and functioning"""
        status = {
            'is_integrated': False,
            'class_name': None,
            'module_path': None,
            'last_tested': None,
            'can_instantiate': False
        }
        
        # Check scraper registry
        scrapers = self.scraper_registry.get('scrapers', {})
        if dealership_name in scrapers:
            scraper_info = scrapers[dealership_name]
            status['is_integrated'] = scraper_info.get('status') == 'active'
            status['class_name'] = scraper_info.get('class_name')
            status['module_path'] = scraper_info.get('module_path')
            status['last_tested'] = scraper_info.get('last_tested')
            
            # Test if we can still instantiate the scraper
            if status['is_integrated']:
                try:
                    # Dynamic import test
                    module = __import__(status['module_path'], fromlist=[''])
                    scraper_class = getattr(module, status['class_name'])
                    scraper_instance = scraper_class()
                    status['can_instantiate'] = True
                except Exception as e:
                    status['can_instantiate'] = False
                    status['instantiation_error'] = str(e)
        
        return status
    
    def _get_inventory_stats(self, dealership_name: str) -> Dict[str, Any]:
        """Get comprehensive inventory statistics"""
        stats = {
            'raw_vehicle_count': 0,
            'normalized_vehicle_count': 0,
            'unique_vins': 0,
            'makes_represented': 0,
            'year_range': {'min': None, 'max': None},
            'price_range': {'min': None, 'max': None, 'avg': None},
            'last_import': None,
            'import_frequency': 'unknown'
        }
        
        try:
            # Raw vehicle count
            raw_result = self.db.execute_query("""
                SELECT COUNT(*) as count, 
                       COUNT(DISTINCT vin) as unique_vins,
                       COUNT(DISTINCT make) as unique_makes,
                       MIN(year) as min_year, MAX(year) as max_year,
                       MIN(price) as min_price, MAX(price) as max_price, AVG(price) as avg_price,
                       MAX(import_timestamp) as last_import
                FROM raw_vehicle_data 
                WHERE location = %s
            """, (dealership_name,))
            
            if raw_result:
                row = raw_result[0]
                stats['raw_vehicle_count'] = row['count']
                stats['unique_vins'] = row['unique_vins']
                stats['makes_represented'] = row['unique_makes']
                stats['year_range'] = {'min': row['min_year'], 'max': row['max_year']}
                stats['price_range'] = {
                    'min': float(row['min_price']) if row['min_price'] else None,
                    'max': float(row['max_price']) if row['max_price'] else None,
                    'avg': float(row['avg_price']) if row['avg_price'] else None
                }
                stats['last_import'] = row['last_import'].isoformat() if row['last_import'] else None
            
            # Normalized vehicle count
            norm_result = self.db.execute_query("""
                SELECT COUNT(*) as count FROM normalized_vehicle_data nv
                JOIN raw_vehicle_data rv ON nv.raw_data_id = rv.id
                WHERE rv.location = %s
            """, (dealership_name,))
            
            if norm_result:
                stats['normalized_vehicle_count'] = norm_result[0]['count']
            
            # Calculate import frequency
            if stats['last_import']:
                last_import = datetime.fromisoformat(stats['last_import'].replace('Z', '+00:00').replace('+00:00', ''))
                days_since = (datetime.now() - last_import).days
                if days_since == 0:
                    stats['import_frequency'] = 'today'
                elif days_since == 1:
                    stats['import_frequency'] = 'yesterday'
                elif days_since <= 7:
                    stats['import_frequency'] = f'{days_since} days ago'
                else:
                    stats['import_frequency'] = f'{days_since} days ago (stale)'
            
        except Exception as e:
            logger.error(f"Error getting inventory stats for {dealership_name}: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def _analyze_data_quality(self, dealership_name: str) -> Dict[str, Any]:
        """Analyze data quality metrics"""
        quality = {
            'completeness_score': 0,
            'consistency_score': 0,
            'freshness_score': 0,
            'duplicate_rate': 0,
            'missing_field_rates': {},
            'overall_score': 0
        }
        
        try:
            # Get data completeness
            completeness_result = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(vin) as has_vin,
                    COUNT(make) as has_make,
                    COUNT(model) as has_model,
                    COUNT(year) as has_year,
                    COUNT(price) as has_price,
                    COUNT(stock) as has_stock
                FROM raw_vehicle_data 
                WHERE location = %s
            """, (dealership_name,))
            
            if completeness_result and completeness_result[0]['total_records'] > 0:
                row = completeness_result[0]
                total = row['total_records']
                
                # Calculate field completion rates
                field_rates = {
                    'vin': (row['has_vin'] / total) * 100,
                    'make': (row['has_make'] / total) * 100,
                    'model': (row['has_model'] / total) * 100,
                    'year': (row['has_year'] / total) * 100,
                    'price': (row['has_price'] / total) * 100,
                    'stock': (row['has_stock'] / total) * 100,
                }
                
                quality['missing_field_rates'] = {k: 100 - v for k, v in field_rates.items()}
                quality['completeness_score'] = sum(field_rates.values()) / len(field_rates)
            
            # Check for duplicates
            duplicate_result = self.db.execute_query("""
                SELECT vin, COUNT(*) as count
                FROM raw_vehicle_data 
                WHERE location = %s AND vin IS NOT NULL
                GROUP BY vin
                HAVING COUNT(*) > 1
            """, (dealership_name,))
            
            if duplicate_result:
                total_vins = self.db.execute_query("""
                    SELECT COUNT(DISTINCT vin) as count FROM raw_vehicle_data 
                    WHERE location = %s AND vin IS NOT NULL
                """, (dealership_name,))[0]['count']
                
                duplicate_vins = len(duplicate_result)
                quality['duplicate_rate'] = (duplicate_vins / total_vins * 100) if total_vins > 0 else 0
            
            # Freshness score based on last import
            inventory_stats = self._get_inventory_stats(dealership_name)
            if inventory_stats.get('last_import'):
                last_import = datetime.fromisoformat(inventory_stats['last_import'])
                hours_since = (datetime.now() - last_import).total_seconds() / 3600
                
                if hours_since <= 24:
                    quality['freshness_score'] = 100
                elif hours_since <= 72:
                    quality['freshness_score'] = 80
                elif hours_since <= 168:  # 1 week
                    quality['freshness_score'] = 60
                else:
                    quality['freshness_score'] = 30
            
            # Calculate overall quality score
            scores = [
                quality['completeness_score'],
                100 - quality['duplicate_rate'],  # Lower duplicates = higher score
                quality['freshness_score']
            ]
            quality['overall_score'] = sum(scores) / len(scores)
            
        except Exception as e:
            logger.error(f"Error analyzing data quality for {dealership_name}: {e}")
            quality['error'] = str(e)
        
        return quality
    
    def _check_recent_activity(self, dealership_name: str) -> Dict[str, Any]:
        """Check recent scraper and processing activity"""
        activity = {
            'recent_jobs': [],
            'job_success_rate': 0,
            'avg_vehicles_per_job': 0,
            'last_successful_job': None
        }
        
        try:
            # Get recent jobs (last 10)
            jobs_result = self.db.execute_query("""
                SELECT job_type, vehicle_count, status, created_at, export_file
                FROM order_processing_jobs 
                WHERE dealership_name = %s
                ORDER BY created_at DESC 
                LIMIT 10
            """, (dealership_name,))
            
            if jobs_result:
                activity['recent_jobs'] = [
                    {
                        'job_type': job['job_type'],
                        'vehicle_count': job['vehicle_count'],
                        'status': job['status'],
                        'created_at': job['created_at'].isoformat(),
                        'has_export': bool(job['export_file'])
                    }
                    for job in jobs_result
                ]
                
                # Calculate success metrics
                completed_jobs = [j for j in jobs_result if j['status'] == 'completed']
                if jobs_result:
                    activity['job_success_rate'] = (len(completed_jobs) / len(jobs_result)) * 100
                
                if completed_jobs:
                    total_vehicles = sum(job['vehicle_count'] for job in completed_jobs)
                    activity['avg_vehicles_per_job'] = total_vehicles / len(completed_jobs)
                    activity['last_successful_job'] = completed_jobs[0]['created_at'].isoformat()
            
        except Exception as e:
            logger.error(f"Error checking recent activity for {dealership_name}: {e}")
            activity['error'] = str(e)
        
        return activity
    
    def _generate_recommendations(self, verification: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on verification results"""
        recommendations = []
        
        # Scraper status recommendations
        scraper_status = verification.get('scraper_status', {})
        if not scraper_status.get('is_integrated'):
            recommendations.append("🔧 Scraper needs integration - run scraper import process")
        elif not scraper_status.get('can_instantiate'):
            recommendations.append("⚠️ Scraper integration broken - check class name and module path")
        
        # Data quality recommendations
        data_quality = verification.get('data_quality', {})
        if data_quality.get('overall_score', 0) < 70:
            recommendations.append("📊 Low data quality - review scraper data extraction")
        
        if data_quality.get('duplicate_rate', 0) > 10:
            recommendations.append("🔄 High duplicate rate - implement better deduplication")
        
        if data_quality.get('freshness_score', 0) < 60:
            recommendations.append("🕐 Stale data - increase scraper run frequency")
        
        # Inventory recommendations
        inventory_stats = verification.get('inventory_stats', {})
        if inventory_stats.get('raw_vehicle_count', 0) < 20:
            recommendations.append("📈 Low vehicle count - verify scraper is getting all inventory")
        
        if inventory_stats.get('normalized_vehicle_count', 0) == 0:
            recommendations.append("🔄 No normalized data - run data normalization process")
        
        # Activity recommendations
        recent_activity = verification.get('recent_activity', {})
        if recent_activity.get('job_success_rate', 0) < 80:
            recommendations.append("🎯 Low job success rate - investigate job failures")
        
        if recent_activity.get('avg_vehicles_per_job', 0) < 10:
            recommendations.append("📋 Low vehicles per job - check scraper vehicle retrieval")
        
        return recommendations
    
    def _generate_alerts(self, verification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for critical issues"""
        alerts = []
        
        # Critical scraper issues
        scraper_status = verification.get('scraper_status', {})
        if not scraper_status.get('can_instantiate'):
            alerts.append({
                'level': 'critical',
                'type': 'scraper_broken',
                'message': 'Scraper cannot be instantiated - immediate attention required'
            })
        
        # Data freshness alerts
        data_quality = verification.get('data_quality', {})
        if data_quality.get('freshness_score', 0) < 30:
            alerts.append({
                'level': 'warning',
                'type': 'stale_data',
                'message': 'Data is over 1 week old - scraper may not be running'
            })
        
        # Low inventory alerts
        inventory_stats = verification.get('inventory_stats', {})
        if inventory_stats.get('raw_vehicle_count', 0) < 5:
            alerts.append({
                'level': 'warning',
                'type': 'low_inventory',
                'message': 'Very low vehicle count - verify scraper functionality'
            })
        
        # Job failure alerts
        recent_activity = verification.get('recent_activity', {})
        if recent_activity.get('job_success_rate', 0) < 50:
            alerts.append({
                'level': 'critical',
                'type': 'job_failures',
                'message': 'High job failure rate - system needs debugging'
            })
        
        return alerts
    
    def _calculate_health_score(self, verification: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)"""
        scores = []
        
        # Scraper integration score
        scraper_status = verification.get('scraper_status', {})
        if scraper_status.get('can_instantiate'):
            scores.append(100)
        elif scraper_status.get('is_integrated'):
            scores.append(50)
        else:
            scores.append(0)
        
        # Data quality score
        data_quality = verification.get('data_quality', {})
        scores.append(data_quality.get('overall_score', 0))
        
        # Inventory adequacy score
        inventory_stats = verification.get('inventory_stats', {})
        vehicle_count = inventory_stats.get('raw_vehicle_count', 0)
        if vehicle_count >= 50:
            scores.append(100)
        elif vehicle_count >= 20:
            scores.append(80)
        elif vehicle_count >= 10:
            scores.append(60)
        elif vehicle_count >= 5:
            scores.append(40)
        else:
            scores.append(20)
        
        # Activity score
        recent_activity = verification.get('recent_activity', {})
        job_success_rate = recent_activity.get('job_success_rate', 0)
        scores.append(job_success_rate)
        
        return sum(scores) / len(scores) if scores else 0
    
    def verify_all_dealerships(self) -> Dict[str, Any]:
        """Verify inventory for all integrated dealerships"""
        logger.info("Starting comprehensive inventory verification for all dealerships")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_dealerships': 0,
            'verified_dealerships': 0,
            'dealerships': {},
            'overall_health': 0,
            'summary': {
                'healthy': 0,
                'needs_attention': 0,
                'critical': 0
            }
        }
        
        # Get all dealerships from registry
        scrapers = self.scraper_registry.get('scrapers', {})
        results['total_dealerships'] = len(scrapers)
        
        health_scores = []
        
        for dealership_name in scrapers.keys():
            try:
                logger.info(f"Verifying {dealership_name}")
                verification = self.verify_dealership_inventory(dealership_name)
                results['dealerships'][dealership_name] = verification
                results['verified_dealerships'] += 1
                
                # Categorize health
                health_score = verification.get('health_score', 0)
                health_scores.append(health_score)
                
                if health_score >= 80:
                    results['summary']['healthy'] += 1
                elif health_score >= 60:
                    results['summary']['needs_attention'] += 1
                else:
                    results['summary']['critical'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to verify {dealership_name}: {e}")
                results['dealerships'][dealership_name] = {
                    'error': str(e),
                    'health_score': 0
                }
                results['summary']['critical'] += 1
        
        # Calculate overall health
        if health_scores:
            results['overall_health'] = sum(health_scores) / len(health_scores)
        
        return results

def main():
    """Main verification process"""
    print("=" * 70)
    print("DEALERSHIP INVENTORY VERIFICATION SYSTEM")
    print("=" * 70)
    
    verifier = DealershipInventoryVerifier()
    
    # Test database connection
    if not verifier.db.test_connection():
        print("ERROR: Database connection failed")
        return False
    
    print("✅ Database connection verified")
    
    # Run comprehensive verification
    print("\nRunning comprehensive inventory verification...")
    results = verifier.verify_all_dealerships()
    
    # Display summary
    print(f"\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    print(f"Total dealerships: {results['total_dealerships']}")
    print(f"Successfully verified: {results['verified_dealerships']}")
    print(f"Overall system health: {results['overall_health']:.1f}%")
    
    print(f"\nHealth breakdown:")
    print(f"  🟢 Healthy (80%+): {results['summary']['healthy']}")
    print(f"  🟡 Needs attention (60-79%): {results['summary']['needs_attention']}")
    print(f"  🔴 Critical (<60%): {results['summary']['critical']}")
    
    # Show individual dealership status
    print(f"\nDealership Status:")
    for name, verification in results['dealerships'].items():
        health = verification.get('health_score', 0)
        if health >= 80:
            status = "🟢"
        elif health >= 60:
            status = "🟡"
        else:
            status = "🔴"
        
        vehicle_count = verification.get('inventory_stats', {}).get('raw_vehicle_count', 0)
        print(f"  {status} {name}: {health:.1f}% health, {vehicle_count} vehicles")
        
        # Show critical alerts
        alerts = verification.get('alerts', [])
        critical_alerts = [a for a in alerts if a.get('level') == 'critical']
        if critical_alerts:
            for alert in critical_alerts:
                print(f"    ❌ {alert['message']}")
    
    # Save detailed results
    results_file = Path("dealership_inventory_verification.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Overall assessment
    if results['overall_health'] >= 80:
        print(f"\n🎉 SYSTEM STATUS: EXCELLENT")
        print("All dealerships are performing well!")
    elif results['overall_health'] >= 60:
        print(f"\n⚠️ SYSTEM STATUS: NEEDS ATTENTION")
        print("Some dealerships require optimization.")
    else:
        print(f"\n🚨 SYSTEM STATUS: CRITICAL")
        print("Multiple dealerships need immediate attention.")
    
    return results['overall_health'] >= 60

if __name__ == "__main__":
    main()