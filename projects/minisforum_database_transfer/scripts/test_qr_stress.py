"""
Comprehensive Stress Test for QR Code Generation System
Tests API reliability, error handling, edge cases, and production workloads
"""
import os
import sys
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil
import random
import string
import logging
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime
import psutil
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qr_code_generator import QRCodeGenerator
from database_connection import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qr_stress_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QRStressTest:
    """Comprehensive stress testing for QR code generation"""
    
    def __init__(self):
        self.test_results = {
            'api_tests': {},
            'error_handling': {},
            'file_system': {},
            'database': {},
            'edge_cases': {},
            'performance': {},
            'concurrent': {}
        }
        self.temp_dirs = []
        
    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def generate_test_vin(self, invalid=False):
        """Generate test VIN numbers"""
        if invalid:
            # Generate various invalid VIN formats
            invalid_types = [
                '',  # Empty
                'A' * 20,  # Too long
                'ABC',  # Too short
                '12345678901234567',  # Valid length but all numbers
                'IOUQ123456789012',  # Contains invalid letters (I, O, Q)
                'ABC@#$%^&*()1234',  # Special characters
                'ABC 123 DEF 45678',  # Spaces
                'ABC\n123DEF45678',  # Newline
                'ABC\t123DEF45678',  # Tab
                '🚗VIN123456789012',  # Emoji
                'VIN' + chr(0) + '123456789',  # Null character
            ]
            return random.choice(invalid_types)
        else:
            # Generate valid-looking VIN
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
    
    def generate_test_stock(self, invalid=False):
        """Generate test stock numbers"""
        if invalid:
            invalid_types = [
                '',  # Empty
                'A' * 100,  # Very long
                'STK@#$%',  # Special characters
                'STK 123',  # Spaces
                '../../../etc/passwd',  # Path traversal attempt
                'STK\x00123',  # Null character
                'CON',  # Windows reserved name
                'PRN',  # Windows reserved name
                '.hiddenfile',  # Hidden file
                'stock/nested/path',  # Nested path
            ]
            return random.choice(invalid_types)
        else:
            return f"STK{random.randint(10000, 99999)}"
    
    def test_api_endpoint(self):
        """Test 1: API Endpoint Testing"""
        logger.info("=== Testing API Endpoint ===")
        results = {}
        
        # Test valid URL
        try:
            response = requests.get("https://api.qrserver.com/v1/create-qr-code/", 
                                  params={'size': '388x388', 'data': 'TEST'},
                                  timeout=10)
            results['valid_url'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.content)
            }
        except Exception as e:
            results['valid_url'] = {'error': str(e)}
        
        # Test parameter encoding with special characters
        special_chars = [
            'VIN&TEST=123',
            'VIN TEST 123',
            'VIN+TEST+123',
            'VIN%20TEST%20123',
            'VIN#TEST@123',
            'VIN<>TEST[]123',
            'VIN"TEST\'123',
            'VIN\\TEST/123',
            'VIN🚗TEST123'
        ]
        
        results['special_chars'] = {}
        for char_test in special_chars:
            try:
                response = requests.get("https://api.qrserver.com/v1/create-qr-code/",
                                      params={'size': '388x388', 'data': char_test},
                                      timeout=5)
                results['special_chars'][char_test] = {
                    'status': response.status_code,
                    'success': response.status_code == 200
                }
            except Exception as e:
                results['special_chars'][char_test] = {'error': str(e)}
        
        # Test different sizes
        sizes = ['100x100', '500x500', '1000x1000', '2000x2000', '10x10', '5000x5000']
        results['sizes'] = {}
        for size in sizes:
            try:
                response = requests.get("https://api.qrserver.com/v1/create-qr-code/",
                                      params={'size': size, 'data': 'TEST'},
                                      timeout=5)
                results['sizes'][size] = {
                    'status': response.status_code,
                    'success': response.status_code == 200,
                    'content_length': len(response.content) if response.status_code == 200 else 0
                }
            except Exception as e:
                results['sizes'][size] = {'error': str(e)}
        
        self.test_results['api_tests'] = results
        return results
    
    def test_error_handling(self):
        """Test 2: Error Handling Analysis"""
        logger.info("=== Testing Error Handling ===")
        results = {}
        
        # Create mock QR generator
        generator = QRCodeGenerator()
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        # Test timeout scenarios
        with patch('requests.get') as mock_get:
            # Simulate timeout
            mock_get.side_effect = requests.Timeout("Connection timeout")
            success, message = generator.generate_qr_code(
                'TEST123', 'STK123', 'TestDealer', temp_dir
            )
            results['timeout'] = {'success': success, 'message': message}
        
        # Test network connectivity issues
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network unreachable")
            success, message = generator.generate_qr_code(
                'TEST456', 'STK456', 'TestDealer', temp_dir
            )
            results['network_error'] = {'success': success, 'message': message}
        
        # Test various HTTP status codes
        status_codes = [400, 401, 403, 404, 429, 500, 502, 503, 504]
        results['http_status'] = {}
        
        for status_code in status_codes:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_response.content = b'Error content'
                mock_get.return_value = mock_response
                
                success, message = generator.generate_qr_code(
                    f'TEST{status_code}', f'STK{status_code}', 'TestDealer', temp_dir
                )
                results['http_status'][status_code] = {
                    'success': success, 
                    'message': message
                }
        
        # Test invalid response content
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b''  # Empty content
            mock_get.return_value = mock_response
            
            success, message = generator.generate_qr_code(
                'TESTEMPTY', 'STKEMPTY', 'TestDealer', temp_dir
            )
            results['empty_response'] = {'success': success, 'message': message}
        
        self.test_results['error_handling'] = results
        return results
    
    def test_file_system_operations(self):
        """Test 3: File System Operations"""
        logger.info("=== Testing File System Operations ===")
        results = {}
        generator = QRCodeGenerator()
        
        # Test directory creation with various permissions
        test_scenarios = []
        
        # Normal case
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        test_scenarios.append(('normal', temp_dir))
        
        # Nested directories
        nested_dir = os.path.join(temp_dir, 'level1', 'level2', 'level3')
        test_scenarios.append(('nested', nested_dir))
        
        # Very long path (test OS limits)
        long_component = 'a' * 100
        long_path = os.path.join(temp_dir, long_component, long_component)
        test_scenarios.append(('long_path', long_path))
        
        # Unicode characters in path
        unicode_dir = os.path.join(temp_dir, 'test_üñíçødé_路径')
        test_scenarios.append(('unicode', unicode_dir))
        
        # Spaces in path
        space_dir = os.path.join(temp_dir, 'test with spaces', 'more spaces')
        test_scenarios.append(('spaces', space_dir))
        
        results['directory_creation'] = {}
        for scenario_name, test_path in test_scenarios:
            try:
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.content = b'QR_CODE_DATA'
                    mock_get.return_value = mock_response
                    
                    success, message = generator.generate_qr_code(
                        'TEST123', 'STK123', 'TestDealer', test_path
                    )
                    results['directory_creation'][scenario_name] = {
                        'success': success,
                        'path_exists': os.path.exists(test_path),
                        'message': message
                    }
            except Exception as e:
                results['directory_creation'][scenario_name] = {'error': str(e)}
        
        # Test file writing permissions
        if os.name != 'nt':  # Unix-like systems only
            try:
                readonly_dir = os.path.join(temp_dir, 'readonly')
                os.makedirs(readonly_dir)
                os.chmod(readonly_dir, 0o444)  # Read-only
                
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.content = b'QR_CODE_DATA'
                    mock_get.return_value = mock_response
                    
                    success, message = generator.generate_qr_code(
                        'TESTRO', 'STKRO', 'TestDealer', readonly_dir
                    )
                    results['readonly_directory'] = {
                        'success': success,
                        'message': message
                    }
                
                os.chmod(readonly_dir, 0o755)  # Restore permissions
            except Exception as e:
                results['readonly_directory'] = {'error': str(e)}
        
        # Test disk space scenarios (simulate)
        results['disk_space'] = {
            'available_gb': psutil.disk_usage('/').free / (1024**3),
            'percent_used': psutil.disk_usage('/').percent
        }
        
        # Test file overwrite scenarios
        existing_file_dir = os.path.join(temp_dir, 'existing')
        os.makedirs(existing_file_dir, exist_ok=True)
        existing_file = os.path.join(existing_file_dir, 'STK999.png')
        
        # Create existing file
        with open(existing_file, 'wb') as f:
            f.write(b'EXISTING_DATA')
        
        # Try to generate QR for same stock number
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'NEW_QR_DATA'
            mock_get.return_value = mock_response
            
            success, message = generator.generate_qr_code(
                'TESTEXIST', 'STK999', 'TestDealer', existing_file_dir
            )
            
            # Check if file was overwritten or skipped
            with open(existing_file, 'rb') as f:
                file_content = f.read()
            
            results['file_overwrite'] = {
                'success': success,
                'file_was_overwritten': file_content == b'NEW_QR_DATA',
                'file_content_preserved': file_content == b'EXISTING_DATA',
                'message': message
            }
        
        # Test Windows/Unix path compatibility
        path_tests = [
            ('forward_slash', 'test/path/file.png'),
            ('backward_slash', 'test\\path\\file.png'),
            ('mixed_slash', 'test/path\\file.png'),
            ('double_slash', 'test//path//file.png'),
            ('trailing_slash', 'test/path/'),
            ('dot_path', './test/path'),
            ('double_dot', '../test/path'),
        ]
        
        results['path_compatibility'] = {}
        for test_name, path_style in path_tests:
            try:
                test_path = os.path.join(temp_dir, 'pathtest', path_style)
                normalized = os.path.normpath(test_path)
                results['path_compatibility'][test_name] = {
                    'original': path_style,
                    'normalized': normalized,
                    'is_absolute': os.path.isabs(normalized)
                }
            except Exception as e:
                results['path_compatibility'][test_name] = {'error': str(e)}
        
        self.test_results['file_system'] = results
        return results
    
    def test_database_integration(self):
        """Test 4: Database Integration"""
        logger.info("=== Testing Database Integration ===")
        results = {}
        
        # Create mock database manager
        mock_db = Mock()
        generator = QRCodeGenerator(db_manager_instance=mock_db)
        
        # Test concurrent QR generation (simulate race conditions)
        results['concurrent_updates'] = {}
        
        # Simulate multiple threads updating same VIN
        def simulate_concurrent_update(thread_id):
            mock_db.execute_query = Mock(return_value=None)
            generator._update_qr_tracking(
                f'CONCURRENT_VIN', 
                'TestDealer', 
                f'/path/thread_{thread_id}.png', 
                True
            )
            return mock_db.execute_query.call_count
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(simulate_concurrent_update, i) for i in range(5)]
            results['concurrent_updates']['thread_calls'] = [f.result() for f in futures]
        
        # Test transaction safety
        # Simulate database connection failure during update
        mock_db.execute_query.side_effect = Exception("Database connection lost")
        try:
            generator._update_qr_tracking('TESTFAIL', 'TestDealer', '/path/fail.png', True)
            results['transaction_safety'] = {'handled_error': False}
        except Exception as e:
            results['transaction_safety'] = {'handled_error': True, 'error': str(e)}
        
        # Reset side effect
        mock_db.execute_query.side_effect = None
        
        # Test database connection pool exhaustion
        results['connection_pool'] = {}
        
        # Simulate many concurrent requests
        def simulate_batch_request(batch_id):
            mock_db.execute_query.return_value = [
                {'vin': f'VIN{i}', 'stock': f'STK{i}', 'location': 'TestDealer'}
                for i in range(10)
            ]
            return generator.get_qr_generation_status()
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(simulate_batch_request, i) for i in range(20)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    results['connection_pool']['errors'] = results['connection_pool'].get('errors', 0) + 1
        
        results['connection_pool']['duration'] = time.time() - start_time
        results['connection_pool']['requests'] = 20
        
        self.test_results['database'] = results
        return results
    
    def test_edge_cases(self):
        """Test 5: Edge Cases"""
        logger.info("=== Testing Edge Cases ===")
        results = {}
        generator = QRCodeGenerator()
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        # Test invalid VIN formats
        results['invalid_vins'] = {}
        for i in range(10):
            invalid_vin = self.generate_test_vin(invalid=True)
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = b'QR_DATA'
                mock_get.return_value = mock_response
                
                success, message = generator.generate_qr_code(
                    invalid_vin, f'STK{i}', 'TestDealer', temp_dir
                )
                results['invalid_vins'][f'test_{i}'] = {
                    'vin': repr(invalid_vin),  # Use repr to show special chars
                    'success': success,
                    'message': message
                }
        
        # Test invalid stock numbers
        results['invalid_stocks'] = {}
        for i in range(10):
            invalid_stock = self.generate_test_stock(invalid=True)
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = b'QR_DATA'
                mock_get.return_value = mock_response
                
                try:
                    success, message = generator.generate_qr_code(
                        f'VIN{i}', invalid_stock, 'TestDealer', temp_dir
                    )
                    results['invalid_stocks'][f'test_{i}'] = {
                        'stock': repr(invalid_stock),
                        'success': success,
                        'message': message,
                        'filename_created': os.path.exists(os.path.join(temp_dir, f'{invalid_stock}.png'))
                    }
                except Exception as e:
                    results['invalid_stocks'][f'test_{i}'] = {
                        'stock': repr(invalid_stock),
                        'error': str(e)
                    }
        
        # Test very long file paths
        results['long_paths'] = {}
        
        # Create deep nested structure
        deep_path = temp_dir
        for i in range(50):  # Create 50 levels deep
            deep_path = os.path.join(deep_path, f'level{i}')
        
        try:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = b'QR_DATA'
                mock_get.return_value = mock_response
                
                success, message = generator.generate_qr_code(
                    'VINDEEP', 'STKDEEP', 'TestDealer', deep_path
                )
                results['long_paths']['deep_nesting'] = {
                    'success': success,
                    'path_length': len(deep_path),
                    'message': message
                }
        except Exception as e:
            results['long_paths']['deep_nesting'] = {
                'error': str(e),
                'path_length': len(deep_path)
            }
        
        # Test special characters in dealership names
        special_dealers = [
            'Dealer & Sons',
            'Dealer/Auto',
            'Dealer\\Cars',
            'Dealer "Premium"',
            'Dealer\'s Choice',
            'Dealer<>Motors',
            'Dealer|Pipe',
            'Dealer*Star',
            'Dealer?Question',
            'Dealer:Colon',
            'Dealer.Com',
            'Dealer..Double',
            'Dealer ',  # Trailing space
            ' Dealer',  # Leading space
            'Dealer\nNewline',
            'Dealer\tTab',
            'Déaler Ünicode',
            '中文经销商',
            '🚗 Emoji Dealer'
        ]
        
        results['special_dealers'] = {}
        for dealer in special_dealers:
            try:
                dealer_dir = os.path.join(temp_dir, 'dealers', dealer)
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.content = b'QR_DATA'
                    mock_get.return_value = mock_response
                    
                    success, message = generator.generate_qr_code(
                        'VINSPEC', 'STKSPEC', dealer, dealer_dir
                    )
                    results['special_dealers'][dealer] = {
                        'success': success,
                        'dir_created': os.path.exists(dealer_dir) if success else False
                    }
            except Exception as e:
                results['special_dealers'][dealer] = {'error': str(e)}
        
        # Test API response size limits
        results['large_responses'] = {}
        response_sizes = [
            1024,  # 1KB
            1024 * 100,  # 100KB
            1024 * 1024,  # 1MB
            1024 * 1024 * 10,  # 10MB
            1024 * 1024 * 50,  # 50MB
        ]
        
        for size in response_sizes:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = b'Q' * size  # Large response
                mock_get.return_value = mock_response
                
                start_time = time.time()
                try:
                    success, message = generator.generate_qr_code(
                        f'VIN{size}', f'STK{size}', 'TestDealer', temp_dir
                    )
                    duration = time.time() - start_time
                    
                    # Check if file was actually written
                    file_path = os.path.join(temp_dir, f'STK{size}.png')
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    
                    results['large_responses'][f'{size//1024}KB'] = {
                        'success': success,
                        'duration': duration,
                        'file_size': file_size,
                        'size_match': file_size == size
                    }
                except Exception as e:
                    results['large_responses'][f'{size//1024}KB'] = {'error': str(e)}
        
        self.test_results['edge_cases'] = results
        return results
    
    def test_performance_and_load(self):
        """Test 6: Performance and Load Testing"""
        logger.info("=== Testing Performance and Load ===")
        results = {}
        generator = QRCodeGenerator()
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        # Test single QR generation performance
        results['single_generation'] = {}
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'Q' * 10240  # 10KB QR
            mock_get.return_value = mock_response
            
            times = []
            for i in range(10):
                start = time.time()
                generator.generate_qr_code(f'VIN{i}', f'STK{i}', 'TestDealer', temp_dir)
                times.append(time.time() - start)
            
            results['single_generation'] = {
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'total_time': sum(times)
            }
        
        # Test batch generation performance
        results['batch_generation'] = {}
        batch_sizes = [10, 50, 100, 500]
        
        for batch_size in batch_sizes:
            # Mock the database query
            mock_db = Mock()
            mock_db.execute_query = Mock(return_value=[
                {'vin': f'VIN{i}', 'stock': f'STK{i}', 'location': 'TestDealer'}
                for i in range(batch_size)
            ])
            generator.db = mock_db
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = b'QR_DATA'
                mock_get.return_value = mock_response
                
                start = time.time()
                result = generator.generate_batch_qr_codes('TestDealer', limit=batch_size)
                duration = time.time() - start
                
                results['batch_generation'][f'batch_{batch_size}'] = {
                    'duration': duration,
                    'qr_per_second': batch_size / duration if duration > 0 else 0,
                    'success_rate': result['success'] / result['total'] if result['total'] > 0 else 0
                }
        
        # Test concurrent generation
        results['concurrent_generation'] = {}
        worker_counts = [1, 5, 10, 20]
        
        for workers in worker_counts:
            def generate_qr_concurrent(worker_id):
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.content = b'QR_DATA'
                    mock_get.return_value = mock_response
                    
                    successes = 0
                    for i in range(10):  # Each worker generates 10 QRs
                        success, _ = generator.generate_qr_code(
                            f'VIN_W{worker_id}_I{i}',
                            f'STK_W{worker_id}_I{i}',
                            'TestDealer',
                            temp_dir
                        )
                        if success:
                            successes += 1
                    return successes
            
            start = time.time()
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(generate_qr_concurrent, i) for i in range(workers)]
                total_success = sum(f.result() for f in futures)
            duration = time.time() - start
            
            results['concurrent_generation'][f'{workers}_workers'] = {
                'duration': duration,
                'total_qrs': workers * 10,
                'successful': total_success,
                'qr_per_second': (workers * 10) / duration if duration > 0 else 0
            }
        
        # Test API rate limiting simulation
        results['rate_limiting'] = {}
        
        # Simulate rapid requests
        rapid_count = 100
        rapid_success = 0
        rapid_429s = 0
        
        with patch('requests.get') as mock_get:
            for i in range(rapid_count):
                # Simulate rate limiting after 50 requests
                if i < 50:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.content = b'QR_DATA'
                else:
                    mock_response = Mock()
                    mock_response.status_code = 429  # Too Many Requests
                    mock_response.content = b'Rate limited'
                
                mock_get.return_value = mock_response
                
                success, message = generator.generate_qr_code(
                    f'RAPID{i}', f'STKRAPID{i}', 'TestDealer', temp_dir
                )
                
                if success:
                    rapid_success += 1
                elif '429' in message:
                    rapid_429s += 1
        
        results['rate_limiting'] = {
            'total_requests': rapid_count,
            'successful': rapid_success,
            'rate_limited': rapid_429s,
            'success_rate': rapid_success / rapid_count
        }
        
        # Memory usage tracking
        import tracemalloc
        tracemalloc.start()
        
        # Generate many QRs to test memory usage
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'Q' * 50000  # 50KB QR
            mock_get.return_value = mock_response
            
            for i in range(100):
                generator.generate_qr_code(f'MEM{i}', f'STKMEM{i}', 'TestDealer', temp_dir)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        results['memory_usage'] = {
            'current_mb': current / 1024 / 1024,
            'peak_mb': peak / 1024 / 1024
        }
        
        self.test_results['performance'] = results
        return results
    
    def test_recovery_and_resilience(self):
        """Test 7: Recovery and Resilience"""
        logger.info("=== Testing Recovery and Resilience ===")
        results = {}
        generator = QRCodeGenerator()
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        # Test partial file write recovery
        results['partial_write'] = {}
        
        # Simulate file write interruption
        with patch('builtins.open') as mock_open:
            mock_file = MagicMock()
            mock_file.write.side_effect = IOError("Disk full")
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = b'QR_DATA'
                mock_get.return_value = mock_response
                
                success, message = generator.generate_qr_code(
                    'PARTIAL', 'STKPARTIAL', 'TestDealer', temp_dir
                )
                
                results['partial_write'] = {
                    'success': success,
                    'error_handled': not success,
                    'message': message
                }
        
        # Test network interruption during download
        results['network_interruption'] = {}
        
        def flaky_network_get(*args, **kwargs):
            # Simulate network interruption after headers
            response = Mock()
            response.status_code = 200
            response.iter_content = Mock(side_effect=requests.ConnectionError("Connection lost"))
            return response
        
        with patch('requests.get', side_effect=flaky_network_get):
            success, message = generator.generate_qr_code(
                'NETFAIL', 'STKNETFAIL', 'TestDealer', temp_dir
            )
            
            results['network_interruption'] = {
                'success': success,
                'error_handled': not success,
                'message': message
            }
        
        # Test database transaction rollback
        mock_db = Mock()
        generator.db = mock_db
        
        # Simulate database error during tracking update
        mock_db.execute_query.side_effect = [
            None,  # First call succeeds (getting path)
            Exception("Database constraint violation")  # Second fails (updating tracking)
        ]
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'QR_DATA'
            mock_get.return_value = mock_response
            
            # This should handle the database error gracefully
            generator._update_qr_tracking('DBFAIL', 'TestDealer', '/path/test.png', True)
            
            results['database_rollback'] = {
                'exception_raised': False,  # Should be caught and logged
                'update_attempted': mock_db.execute_query.called
            }
        
        # Test cleanup of orphaned files after failure
        results['orphan_cleanup'] = {}
        
        # Create some orphaned QR files
        for i in range(5):
            orphan_file = os.path.join(temp_dir, f'ORPHAN{i}.png')
            with open(orphan_file, 'wb') as f:
                f.write(b'ORPHAN_QR_DATA')
        
        # Mock database to show these as orphaned
        mock_db.execute_query.side_effect = None
        mock_db.execute_query.return_value = [
            {'vin': f'ORPHAN{i}', 'qr_file_path': os.path.join(temp_dir, f'ORPHAN{i}.png')}
            for i in range(5)
        ]
        
        # Test dry run first
        cleanup_dry = generator.cleanup_orphaned_qr_files('TestDealer', dry_run=True)
        files_before = len([f for f in os.listdir(temp_dir) if f.startswith('ORPHAN')])
        
        # Test actual cleanup
        cleanup_actual = generator.cleanup_orphaned_qr_files('TestDealer', dry_run=False)
        files_after = len([f for f in os.listdir(temp_dir) if f.startswith('ORPHAN')])
        
        results['orphan_cleanup'] = {
            'dry_run_found': cleanup_dry['orphaned'],
            'files_before': files_before,
            'files_removed': cleanup_actual['removed'],
            'files_after': files_after,
            'cleanup_successful': files_after == 0
        }
        
        self.test_results['recovery'] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("QR CODE GENERATION STRESS TEST REPORT")
        logger.info("="*80)
        
        # Summary statistics
        total_tests = sum(len(category) for category in self.test_results.values())
        failures = 0
        warnings = 0
        
        # Detailed results
        for category, results in self.test_results.items():
            logger.info(f"\n{category.upper().replace('_', ' ')}:")
            logger.info("-" * 50)
            
            if isinstance(results, dict):
                for test_name, test_result in results.items():
                    if isinstance(test_result, dict):
                        if 'error' in test_result or (isinstance(test_result.get('success'), bool) and not test_result['success']):
                            failures += 1
                            logger.warning(f"  ❌ {test_name}: {test_result}")
                        elif 'warning' in str(test_result).lower():
                            warnings += 1
                            logger.info(f"  ⚠️  {test_name}: {test_result}")
                        else:
                            logger.info(f"  ✅ {test_name}: {test_result}")
                    else:
                        logger.info(f"  • {test_name}: {test_result}")
        
        # Risk Assessment
        logger.info("\n" + "="*80)
        logger.info("RISK ASSESSMENT AND RECOMMENDATIONS")
        logger.info("="*80)
        
        risks = []
        
        # API reliability
        if 'api_tests' in self.test_results:
            if any('error' in str(r) for r in self.test_results['api_tests'].values()):
                risks.append("HIGH: API connectivity issues detected - implement retry logic with exponential backoff")
        
        # Error handling
        if 'error_handling' in self.test_results:
            http_errors = self.test_results['error_handling'].get('http_status', {})
            if any(not v.get('success', True) for v in http_errors.values()):
                risks.append("MEDIUM: Not all HTTP error codes are handled gracefully")
        
        # File system
        if 'file_system' in self.test_results:
            if 'readonly_directory' in self.test_results['file_system']:
                if not self.test_results['file_system']['readonly_directory'].get('success', True):
                    risks.append("MEDIUM: File permission errors not handled - add permission checks")
        
        # Performance
        if 'performance' in self.test_results:
            if 'rate_limiting' in self.test_results['performance']:
                rate_limit = self.test_results['performance']['rate_limiting']
                if rate_limit.get('rate_limited', 0) > 0:
                    risks.append("HIGH: API rate limiting detected - implement rate limit handling")
        
        # Edge cases
        if 'edge_cases' in self.test_results:
            if 'special_dealers' in self.test_results['edge_cases']:
                special_failures = sum(1 for d in self.test_results['edge_cases']['special_dealers'].values() 
                                     if 'error' in d)
                if special_failures > 0:
                    risks.append(f"MEDIUM: {special_failures} special character handling issues in dealership names")
        
        for risk in risks:
            logger.warning(f"  • {risk}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Tests Run: {total_tests}")
        logger.info(f"Failures: {failures}")
        logger.info(f"Warnings: {warnings}")
        logger.info(f"Success Rate: {((total_tests - failures) / total_tests * 100):.1f}%")
        
        # Production readiness assessment
        if failures == 0:
            logger.info("\n✅ PRODUCTION READY: All critical tests passed")
        elif failures < 5:
            logger.info("\n⚠️  PRODUCTION READY WITH CAUTION: Minor issues should be addressed")
        else:
            logger.error("\n❌ NOT PRODUCTION READY: Critical issues must be resolved")
        
        # Save detailed results to file
        with open('qr_stress_test_detailed_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        logger.info("\nDetailed results saved to: qr_stress_test_detailed_results.json")
        
        return self.test_results

def main():
    """Run the complete stress test suite"""
    tester = QRStressTest()
    
    try:
        # Run all tests
        logger.info("Starting QR Code Generation Stress Test...")
        
        tester.test_api_endpoint()
        tester.test_error_handling()
        tester.test_file_system_operations()
        tester.test_database_integration()
        tester.test_edge_cases()
        tester.test_performance_and_load()
        tester.test_recovery_and_resilience()
        
        # Generate report
        tester.generate_report()
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
    finally:
        # Cleanup
        tester.cleanup()
        logger.info("\nTest suite completed.")

if __name__ == "__main__":
    main()