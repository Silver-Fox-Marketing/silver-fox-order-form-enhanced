import qrcode
import requests
import sqlite3
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from PIL import Image
import smtplib
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
import schedule
import time
import logging
from utils import setup_logging

@dataclass
class QRVerificationResult:
    """Result of QR code verification"""
    vin: str
    url: str
    status: str  # 'valid', 'invalid', 'error'
    http_status: int
    error_message: str = None
    verified_at: str = None
    response_time: float = 0.0
    
    def __post_init__(self):
        if self.verified_at is None:
            self.verified_at = datetime.now().isoformat()

class QRProcessor:
    """QR Code generation and verification system for vehicle dealership pages"""
    
    def __init__(self, database_path: str = "data/order_processing.db"):
        self.logger = setup_logging("INFO", "logs/qr_processor.log")
        self.database_path = database_path
        
        # QR code settings
        self.qr_settings = {
            'version': 1,
            'error_correction': qrcode.constants.ERROR_CORRECT_L,
            'box_size': 10,
            'border': 4
        }
        
        # Verification settings
        self.verification_timeout = 10  # seconds
        self.max_retries = 3
        
        # Initialize QR verification database
        self._init_qr_database()
        
        # Common error patterns
        self.error_patterns = {
            'dealership_down': ['connection refused', 'timeout', 'network unreachable'],
            'page_not_found': ['404', 'not found', 'page does not exist'],
            'vehicle_sold': ['no longer available', 'sold', 'unavailable'],
            'temporary_error': ['500', 'server error', 'temporary'],
            'redirect_loop': ['too many redirects', 'redirect loop'],
            'ssl_error': ['ssl', 'certificate', 'handshake failed']
        }
    
    def _init_qr_database(self):
        """Initialize QR verification tracking database"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # QR codes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qr_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vin TEXT NOT NULL,
                    url TEXT NOT NULL,
                    qr_path_1 TEXT,
                    qr_path_2 TEXT,
                    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_verified TEXT,
                    verification_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (vin) REFERENCES vehicles (vin)
                )
            """)
            
            # QR verification history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qr_verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vin TEXT NOT NULL,
                    url TEXT NOT NULL,
                    http_status INTEGER,
                    status TEXT,
                    error_category TEXT,
                    error_message TEXT,
                    response_time REAL,
                    verified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vin) REFERENCES vehicles (vin)
                )
            """)
            
            # QR scan tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qr_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vin TEXT NOT NULL,
                    scanned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    scan_source TEXT,
                    verification_triggered BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (vin) REFERENCES vehicles (vin)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_qr_codes_vin ON qr_codes (vin)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_qr_verifications_vin ON qr_verifications (vin)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_qr_scans_vin ON qr_scans (vin)")
            
            conn.commit()
        
        self.logger.info("QR database initialized")
    
    def generate_qr_codes(self, vin: str, vehicle_url: str, output_dir: str = "output_data/qr_codes") -> Dict[str, str]:
        """Generate dual QR codes for vehicle shortcut pack"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Clean VIN for filename
            clean_vin = vin.replace(' ', '').upper()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate two identical QR codes (as per requirements)
            qr_paths = {}
            
            for i in range(1, 3):  # Generate QR code 1 and 2
                # Create QR code
                qr = qrcode.QRCode(**self.qr_settings)
                qr.add_data(vehicle_url)
                qr.make(fit=True)
                
                # Create image
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Save with unique names
                filename = f"qr_{clean_vin}_{i}_{timestamp}.png"
                qr_path = os.path.join(output_dir, filename)
                qr_img.save(qr_path)
                
                qr_paths[f'qr_path_{i}'] = qr_path
                
                self.logger.info(f"Generated QR code {i} for VIN {vin}: {qr_path}")
            
            # Store in database
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO qr_codes 
                    (vin, url, qr_path_1, qr_path_2, generated_at, verification_status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (
                    vin, vehicle_url, qr_paths['qr_path_1'], qr_paths['qr_path_2'],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            
            return {
                'vin': vin,
                'url': vehicle_url,
                'qr_path_1': qr_paths['qr_path_1'],
                'qr_path_2': qr_paths['qr_path_2'],
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate QR codes for VIN {vin}: {str(e)}")
            raise
    
    def verify_qr_url(self, vin: str, url: str) -> QRVerificationResult:
        """Verify that QR code URL is accessible and valid"""
        start_time = time.time()
        
        try:
            # Configure request session
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Attempt verification with retries
            last_exception = None
            
            for attempt in range(self.max_retries):
                try:
                    response = session.get(
                        url, 
                        timeout=self.verification_timeout,
                        allow_redirects=True
                    )
                    
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        # Check if page content indicates vehicle is available
                        content = response.text.lower()
                        
                        # Look for indicators that vehicle is no longer available
                        unavailable_indicators = [
                            'no longer available', 'sold', 'unavailable',
                            'not found', 'removed', 'expired'
                        ]
                        
                        if any(indicator in content for indicator in unavailable_indicators):
                            return QRVerificationResult(
                                vin=vin, url=url, status='invalid',
                                http_status=response.status_code,
                                error_message='Vehicle appears to be sold/unavailable',
                                response_time=response_time
                            )
                        
                        return QRVerificationResult(
                            vin=vin, url=url, status='valid',
                            http_status=response.status_code,
                            response_time=response_time
                        )
                    
                    elif response.status_code in [301, 302, 303, 307, 308]:
                        # Handle redirects - verify final URL
                        final_url = response.url
                        if final_url != url:
                            self.logger.info(f"VIN {vin} redirected from {url} to {final_url}")
                        
                        return QRVerificationResult(
                            vin=vin, url=final_url, status='valid',
                            http_status=response.status_code,
                            response_time=response_time
                        )
                    
                    else:
                        return QRVerificationResult(
                            vin=vin, url=url, status='invalid',
                            http_status=response.status_code,
                            error_message=f'HTTP {response.status_code}',
                            response_time=response_time
                        )
                
                except requests.RequestException as e:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            
            # All retries failed
            response_time = time.time() - start_time
            error_msg = str(last_exception)
            
            return QRVerificationResult(
                vin=vin, url=url, status='error',
                http_status=0,
                error_message=error_msg,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return QRVerificationResult(
                vin=vin, url=url, status='error',
                http_status=0,
                error_message=str(e),
                response_time=response_time
            )
    
    def categorize_error(self, error_message: str) -> str:
        """Categorize error for easier fixing"""
        if not error_message:
            return 'unknown'
        
        error_lower = error_message.lower()
        
        for category, patterns in self.error_patterns.items():
            if any(pattern in error_lower for pattern in patterns):
                return category
        
        return 'other'
    
    def verify_all_qr_codes(self, force_verify: bool = False) -> Dict[str, Any]:
        """Verify all QR codes in database"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Get QR codes to verify
            if force_verify:
                cursor.execute("SELECT vin, url FROM qr_codes")
            else:
                # Only verify if not verified today
                today = datetime.now().date().isoformat()
                cursor.execute("""
                    SELECT vin, url FROM qr_codes 
                    WHERE last_verified IS NULL 
                       OR DATE(last_verified) < DATE(?)
                """, (today,))
            
            qr_codes = cursor.fetchall()
        
        if not qr_codes:
            self.logger.info("No QR codes need verification")
            return {'verified': 0, 'valid': 0, 'invalid': 0, 'errors': 0}
        
        results = {'verified': 0, 'valid': 0, 'invalid': 0, 'errors': 0}
        failed_verifications = []
        
        self.logger.info(f"Starting verification of {len(qr_codes)} QR codes")
        
        for vin, url in qr_codes:
            verification_result = self.verify_qr_url(vin, url)
            
            # Update counters
            results['verified'] += 1
            if verification_result.status == 'valid':
                results['valid'] += 1
            elif verification_result.status == 'invalid':
                results['invalid'] += 1
                failed_verifications.append(verification_result)
            else:
                results['errors'] += 1
                failed_verifications.append(verification_result)
            
            # Store verification result
            self._store_verification_result(verification_result)
            
            # Update QR codes table
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE qr_codes 
                    SET last_verified = ?, verification_status = ?
                    WHERE vin = ?
                """, (verification_result.verified_at, verification_result.status, vin))
                conn.commit()
            
            # Small delay to avoid overwhelming servers
            time.sleep(0.5)
        
        self.logger.info(f"Verification complete: {results}")
        
        # Send notification for failed verifications
        if failed_verifications:
            self._send_failure_notification(failed_verifications)
        
        return {
            **results,
            'failed_verifications': failed_verifications,
            'verification_completed_at': datetime.now().isoformat()
        }
    
    def _store_verification_result(self, result: QRVerificationResult):
        """Store verification result in database"""
        error_category = self.categorize_error(result.error_message) if result.error_message else None
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO qr_verifications 
                (vin, url, http_status, status, error_category, error_message, 
                 response_time, verified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.vin, result.url, result.http_status, result.status,
                error_category, result.error_message, result.response_time,
                result.verified_at
            ))
            conn.commit()
    
    def record_qr_scan(self, vin: str, scan_source: str = 'manual'):
        """Record QR code scan and trigger verification if needed"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Record the scan
            cursor.execute("""
                INSERT INTO qr_scans (vin, scan_source, verification_triggered)
                VALUES (?, ?, TRUE)
            """, (vin, scan_source))
            
            conn.commit()
        
        # Trigger immediate verification for this VIN
        cursor.execute("SELECT url FROM qr_codes WHERE vin = ?", (vin,))
        result = cursor.fetchone()
        
        if result:
            url = result[0]
            verification_result = self.verify_qr_url(vin, url)
            self._store_verification_result(verification_result)
            
            # Update QR codes table
            cursor.execute("""
                UPDATE qr_codes 
                SET last_verified = ?, verification_status = ?
                WHERE vin = ?
            """, (verification_result.verified_at, verification_result.status, vin))
            conn.commit()
            
            self.logger.info(f"QR scan verification for VIN {vin}: {verification_result.status}")
            return verification_result
        
        return None
    
    def get_pre_print_validation_report(self) -> Dict[str, Any]:
        """Generate pre-print validation report to prevent printing incorrect QR codes"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Get recent verification status
            cursor.execute("""
                SELECT 
                    qr.vin, qr.url, qr.verification_status, qr.last_verified,
                    v.year, v.make, v.model, v.dealer_name
                FROM qr_codes qr
                LEFT JOIN vehicles v ON qr.vin = v.vin
                WHERE qr.verification_status IN ('invalid', 'error')
                   OR qr.last_verified IS NULL
                   OR DATE(qr.last_verified) < DATE('now', '-1 day')
                ORDER BY qr.last_verified ASC
            """)
            
            problematic_qrs = cursor.fetchall()
            
            # Get error summary
            cursor.execute("""
                SELECT error_category, COUNT(*) as count
                FROM qr_verifications 
                WHERE DATE(verified_at) = DATE('now')
                  AND status != 'valid'
                GROUP BY error_category
                ORDER BY count DESC
            """)
            
            error_summary = cursor.fetchall()
        
        report = {
            'total_problematic_qrs': len(problematic_qrs),
            'problematic_vehicles': [
                {
                    'vin': row[0], 'url': row[1], 'status': row[2],
                    'last_verified': row[3], 'vehicle_info': f"{row[4]} {row[5]} {row[6]}",
                    'dealer': row[7]
                }
                for row in problematic_qrs
            ],
            'error_categories': [
                {'category': row[0], 'count': row[1]}
                for row in error_summary
            ],
            'report_generated_at': datetime.now().isoformat(),
            'print_safe': len(problematic_qrs) == 0
        }
        
        return report
    
    def _send_failure_notification(self, failed_verifications: List[QRVerificationResult]):
        """Send email notification for failed QR verifications"""
        try:
            # Create notification message
            message_body = "QR Code Verification Failures Report\n"
            message_body += "=" * 50 + "\n\n"
            
            # Group by error category
            error_groups = {}
            for failure in failed_verifications:
                category = self.categorize_error(failure.error_message)
                if category not in error_groups:
                    error_groups[category] = []
                error_groups[category].append(failure)
            
            # Format message
            for category, failures in error_groups.items():
                message_body += f"\n{category.upper()} ({len(failures)} vehicles):\n"
                message_body += "-" * 30 + "\n"
                
                for failure in failures[:10]:  # Limit to 10 per category
                    message_body += f"VIN: {failure.vin}\n"
                    message_body += f"URL: {failure.url}\n"
                    message_body += f"Status: HTTP {failure.http_status}\n"
                    message_body += f"Error: {failure.error_message}\n\n"
                
                if len(failures) > 10:
                    message_body += f"... and {len(failures) - 10} more\n\n"
            
            message_body += f"\nTotal failures: {len(failed_verifications)}\n"
            message_body += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Log the notification (actual email sending would require SMTP config)
            self.logger.warning(f"QR Verification failures detected: {len(failed_verifications)} vehicles")
            self.logger.info("Failure notification prepared (email configuration needed for sending)")
            
            # Save notification to file for manual review
            notification_file = f"output_data/qr_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            os.makedirs('output_data', exist_ok=True)
            with open(notification_file, 'w') as f:
                f.write(message_body)
            
            self.logger.info(f"Failure report saved to: {notification_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
    
    def setup_daily_verification_schedule(self):
        """Setup daily QR verification schedule"""
        # Schedule daily verification at 6 AM
        schedule.every().day.at("06:00").do(self.verify_all_qr_codes)
        
        self.logger.info("Daily QR verification scheduled for 6:00 AM")
        
        return schedule
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get QR verification statistics"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_qrs,
                    SUM(CASE WHEN verification_status = 'valid' THEN 1 ELSE 0 END) as valid,
                    SUM(CASE WHEN verification_status = 'invalid' THEN 1 ELSE 0 END) as invalid,
                    SUM(CASE WHEN verification_status = 'error' THEN 1 ELSE 0 END) as errors,
                    SUM(CASE WHEN verification_status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM qr_codes
            """)
            
            overall_stats = cursor.fetchone()
            
            # Recent verification activity
            cursor.execute("""
                SELECT DATE(verified_at) as date, COUNT(*) as count
                FROM qr_verifications
                WHERE DATE(verified_at) >= DATE('now', '-7 days')
                GROUP BY DATE(verified_at)
                ORDER BY date DESC
            """)
            
            recent_activity = cursor.fetchall()
            
            # Error distribution
            cursor.execute("""
                SELECT error_category, COUNT(*) as count
                FROM qr_verifications
                WHERE error_category IS NOT NULL
                  AND DATE(verified_at) >= DATE('now', '-30 days')
                GROUP BY error_category
                ORDER BY count DESC
            """)
            
            error_distribution = cursor.fetchall()
        
        return {
            'total_qr_codes': overall_stats[0],
            'valid_qrs': overall_stats[1],
            'invalid_qrs': overall_stats[2],
            'error_qrs': overall_stats[3],
            'pending_qrs': overall_stats[4],
            'success_rate': (overall_stats[1] / overall_stats[0] * 100) if overall_stats[0] > 0 else 0,
            'recent_activity': [{'date': row[0], 'verifications': row[1]} for row in recent_activity],
            'error_distribution': [{'category': row[0], 'count': row[1]} for row in error_distribution],
            'last_updated': datetime.now().isoformat()
        }

def create_qr_processor(database_path: str = "data/order_processing.db") -> QRProcessor:
    """Create a configured QRProcessor instance"""
    return QRProcessor(database_path)

def generate_qrs_for_order(order_id: str) -> Dict[str, Any]:
    """Generate QR codes for all vehicles in an order"""
    from order_processor import create_order_processor
    
    # Get vehicles from order
    order_processor = create_order_processor()
    qr_processor = create_qr_processor()
    
    with sqlite3.connect(order_processor.database_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT v.vin, v.url
            FROM order_items oi
            JOIN vehicles v ON oi.vin = v.vin
            WHERE oi.order_id = ? AND v.url IS NOT NULL
        """, (order_id,))
        
        vehicles = cursor.fetchall()
    
    if not vehicles:
        return {'error': f'No vehicles with URLs found for order {order_id}'}
    
    results = []
    for vin, url in vehicles:
        try:
            qr_result = qr_processor.generate_qr_codes(vin, url)
            results.append(qr_result)
        except Exception as e:
            results.append({'vin': vin, 'error': str(e)})
    
    return {
        'order_id': order_id,
        'total_vehicles': len(vehicles),
        'successful_qrs': len([r for r in results if 'error' not in r]),
        'failed_qrs': len([r for r in results if 'error' in r]),
        'qr_results': results,
        'generated_at': datetime.now().isoformat()
    }