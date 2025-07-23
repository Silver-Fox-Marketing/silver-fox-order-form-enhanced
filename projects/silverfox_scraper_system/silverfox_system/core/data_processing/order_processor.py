import pandas as pd
import sqlite3
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
import json
from utils import setup_logging, save_data, load_data
from google_sheets_filters import GoogleSheetsFilters, apply_all_google_sheets_filters

@dataclass
class OrderConfig:
    """Configuration for order processing"""
    order_id: str
    order_type: str  # 'list', 'comparative', 'bulk'
    dealerships: List[str]
    filters: Dict[str, Any]
    priority: int = 1
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class OrderProcessor:
    """Advanced order processing system with local database optimization"""
    
    def __init__(self, database_path: str = "data/order_processing.db"):
        self.logger = setup_logging("INFO", "logs/order_processor.log")
        self.database_path = database_path
        
        # Ensure database directory exists
        if database_path and os.path.dirname(database_path):
            os.makedirs(os.path.dirname(database_path), exist_ok=True)
        else:
            # Default to current directory if no path specified
            self.database_path = "order_processing.db"
        
        # Initialize database
        self._init_database()
        
        # VIN index cache for fast lookups
        self.vin_index = {}
        self.dealership_index = defaultdict(list)
        
        # Processing rules
        self.processing_rules = self._load_processing_rules()
        
        # Google Sheets filters integration
        self.sheets_filters = GoogleSheetsFilters(database_path)
        
    def _init_database(self):
        """Initialize SQLite database with optimized schema"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Vehicles table with indexes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vin TEXT NOT NULL UNIQUE,
                    stock_number TEXT,
                    year INTEGER,
                    make TEXT,
                    model TEXT,
                    trim TEXT,
                    price REAL,
                    msrp REAL,
                    mileage INTEGER,
                    exterior_color TEXT,
                    interior_color TEXT,
                    body_style TEXT,
                    fuel_type TEXT,
                    transmission TEXT,
                    engine TEXT,
                    original_status TEXT,
                    normalized_status TEXT,
                    condition TEXT,
                    dealer_name TEXT,
                    dealer_id TEXT,
                    url TEXT,
                    scraped_at TEXT,
                    processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL UNIQUE,
                    order_type TEXT NOT NULL,
                    dealerships TEXT, -- JSON array
                    filters TEXT, -- JSON object
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT,
                    results_path TEXT
                )
            """)
            
            # Order items (VINs associated with orders)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    vin TEXT NOT NULL,
                    processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id),
                    FOREIGN KEY (vin) REFERENCES vehicles (vin)
                )
            """)
            
            # Create indexes for fast queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_vin ON vehicles (vin)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_dealer ON vehicles (dealer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles (normalized_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_make_model ON vehicles (make, model)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_vin ON order_items (vin)")
            
            conn.commit()
            
        self.logger.info("Database initialized with optimized schema")
    
    def _load_processing_rules(self) -> Dict[str, Any]:
        """Load processing rules with enhanced capabilities"""
        return {
            'status_priorities': {
                'new': 1,
                'onlot': 2,
                'cpo': 3,
                'po': 4,
                'offlot': 5,
                'unknown': 6
            },
            'dealership_filters': {
                'default': {
                    'exclude_statuses': ['unknown'],
                    'min_price': 0,
                    'max_price': None,
                    'required_fields': ['vin', 'make', 'model', 'year']
                }
            },
            'order_types': {
                'list': {
                    'description': 'Process specific VIN list',
                    'requires_vin_list': True
                },
                'comparative': {
                    'description': 'Compare vehicles across dealerships',
                    'group_by': ['make', 'model', 'year'],
                    'sort_by': ['price', 'mileage']
                },
                'bulk': {
                    'description': 'Process all inventory for dealerships',
                    'batch_size': 1000
                }
            }
        }
    
    def import_normalized_data(self, csv_file_path: str) -> Dict[str, Any]:
        """Import normalized CSV data into database with optimizations"""
        try:
            self.logger.info(f"Importing normalized data from {csv_file_path}")
            
            # Read CSV with pandas for efficiency
            df = pd.read_csv(csv_file_path)
            original_count = len(df)
            
            # Data validation and cleaning
            df = self._validate_and_clean_data(df)
            cleaned_count = len(df)
            
            # Batch insert for performance
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Use INSERT OR REPLACE for upsert behavior
                insert_sql = """
                    INSERT OR REPLACE INTO vehicles 
                    (vin, stock_number, year, make, model, trim, price, msrp, mileage,
                     exterior_color, interior_color, body_style, fuel_type, transmission, engine,
                     original_status, normalized_status, condition, dealer_name, dealer_id, url, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Convert DataFrame to list of tuples for batch insert
                data_tuples = []
                for _, row in df.iterrows():
                    data_tuples.append((
                        row.get('vin'), row.get('stock_number'), row.get('year'),
                        row.get('make'), row.get('model'), row.get('trim'),
                        row.get('price'), row.get('msrp'), row.get('mileage'),
                        row.get('exterior_color'), row.get('interior_color'), row.get('body_style'),
                        row.get('fuel_type'), row.get('transmission'), row.get('engine'),
                        row.get('original_status'), row.get('normalized_status'), row.get('condition'),
                        row.get('dealer_name'), row.get('dealer_id'), row.get('url'), row.get('scraped_at')
                    ))
                
                cursor.executemany(insert_sql, data_tuples)
                conn.commit()
                
                inserted_count = cursor.rowcount
            
            # Update indexes
            self._rebuild_indexes()
            
            result = {
                'imported_file': csv_file_path,
                'original_records': original_count,
                'cleaned_records': cleaned_count,
                'inserted_records': inserted_count,
                'dropped_records': original_count - cleaned_count,
                'processed_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Import complete: {inserted_count} records processed")
            return result
            
        except Exception as e:
            self.logger.error(f"Import failed: {str(e)}")
            raise
    
    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced data validation and cleaning"""
        initial_count = len(df)
        
        # Remove records without VIN
        df = df.dropna(subset=['vin'])
        df = df[df['vin'].str.strip() != '']
        
        # Clean and validate VINs (17 characters, alphanumeric)
        df['vin'] = df['vin'].str.strip().str.upper()
        df = df[df['vin'].str.len() == 17]
        df = df[df['vin'].str.match(r'^[A-HJ-NPR-Z0-9]{17}$')]
        
        # Validate required fields
        required_fields = ['make', 'model', 'year', 'dealer_id']
        for field in required_fields:
            if field in df.columns:
                df = df.dropna(subset=[field])
        
        # Data type conversions with error handling
        numeric_fields = ['year', 'price', 'msrp', 'mileage']
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        # Year validation
        if 'year' in df.columns:
            current_year = datetime.now().year
            df = df[(df['year'] >= 1900) & (df['year'] <= current_year + 2)]
        
        # Remove duplicates (keep most recent)
        df = df.drop_duplicates(subset=['vin'], keep='last')
        
        cleaned_count = len(df)
        dropped = initial_count - cleaned_count
        
        if dropped > 0:
            self.logger.info(f"Data cleaning: {dropped} records dropped, {cleaned_count} records retained")
        
        return df
    
    def _rebuild_indexes(self):
        """Rebuild in-memory indexes for fast lookups"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Build VIN index
            cursor.execute("SELECT vin, dealer_id, normalized_status FROM vehicles")
            rows = cursor.fetchall()
            
            self.vin_index.clear()
            self.dealership_index.clear()
            
            for vin, dealer_id, status in rows:
                self.vin_index[vin] = {'dealer_id': dealer_id, 'status': status}
                self.dealership_index[dealer_id].append(vin)
        
        self.logger.info(f"Indexes rebuilt: {len(self.vin_index)} VINs, {len(self.dealership_index)} dealerships")
    
    def create_order(self, order_config: OrderConfig) -> str:
        """Create a new order with enhanced configuration"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO orders (order_id, order_type, dealerships, filters, priority, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    order_config.order_id,
                    order_config.order_type,
                    json.dumps(order_config.dealerships),
                    json.dumps(order_config.filters),
                    order_config.priority,
                    order_config.created_at
                ))
                
                conn.commit()
            
            self.logger.info(f"Order created: {order_config.order_id} ({order_config.order_type})")
            return order_config.order_id
            
        except Exception as e:
            self.logger.error(f"Failed to create order {order_config.order_id}: {str(e)}")
            raise
    
    def process_order(self, order_id: str) -> Dict[str, Any]:
        """Process an order with Google Sheets-compatible logic"""
        try:
            # Get order details
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT order_type, dealerships, filters, priority 
                    FROM orders WHERE order_id = ?
                """, (order_id,))
                
                order_row = cursor.fetchone()
                if not order_row:
                    raise ValueError(f"Order {order_id} not found")
                
                order_type, dealerships_json, filters_json, priority = order_row
                dealerships = json.loads(dealerships_json)
                filters = json.loads(filters_json)
            
            # Get data for processing with Google Sheets filters
            df = self._get_order_dataframe(dealerships, filters)
            
            # Apply Google Sheets processing logic
            sheets_result = apply_all_google_sheets_filters(df, filters)
            
            # Process based on order type with Sheets logic
            if order_type == 'list':
                result = self._process_list_order_with_sheets(order_id, dealerships, filters, sheets_result)
            elif order_type == 'comparative':
                result = self._process_comparative_order_with_sheets(order_id, dealerships, filters, sheets_result)
            elif order_type == 'bulk':
                result = self._process_bulk_order_with_sheets(order_id, dealerships, filters, sheets_result)
            else:
                raise ValueError(f"Unknown order type: {order_type}")
            
            # Update order status
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE orders 
                    SET status = 'completed', processed_at = ?, results_path = ?
                    WHERE order_id = ?
                """, (datetime.now().isoformat(), result.get('output_file'), order_id))
                conn.commit()
            
            self.logger.info(f"Order {order_id} processed successfully with Google Sheets logic")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process order {order_id}: {str(e)}")
            
            # Update order status to failed
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE orders SET status = 'failed', processed_at = ?
                    WHERE order_id = ?
                """, (datetime.now().isoformat(), order_id))
                conn.commit()
            
            raise
    
    def _process_list_order(self, order_id: str, dealerships: List[str], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a list order with specific VINs"""
        vin_list = filters.get('vin_list', [])
        if not vin_list:
            raise ValueError("List order requires vin_list in filters")
        
        # Build optimized query
        placeholders = ','.join(['?' for _ in vin_list])
        where_conditions = [f"vin IN ({placeholders})"]
        query_params = vin_list.copy()
        
        if dealerships:
            dealer_placeholders = ','.join(['?' for _ in dealerships])
            where_conditions.append(f"dealer_id IN ({dealer_placeholders})")
            query_params.extend(dealerships)
        
        # Add status filters
        if 'exclude_statuses' in filters:
            status_placeholders = ','.join(['?' for _ in filters['exclude_statuses']])
            where_conditions.append(f"normalized_status NOT IN ({status_placeholders})")
            query_params.extend(filters['exclude_statuses'])
        
        query = f"""
            SELECT * FROM vehicles 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY 
                CASE normalized_status
                    WHEN 'new' THEN 1
                    WHEN 'onlot' THEN 2
                    WHEN 'cpo' THEN 3
                    WHEN 'po' THEN 4
                    WHEN 'offlot' THEN 5
                    ELSE 6
                END,
                price ASC
        """
        
        # Execute query and get results
        with sqlite3.connect(self.database_path) as conn:
            df = pd.read_sql_query(query, conn, params=query_params)
        
        # Save results
        output_file = f"output_data/list_order_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.makedirs('output_data', exist_ok=True)
        df.to_csv(output_file, index=False)
        
        # Record order items
        self._record_order_items(order_id, df['vin'].tolist())
        
        return {
            'order_id': order_id,
            'order_type': 'list',
            'requested_vins': len(vin_list),
            'found_vehicles': len(df),
            'output_file': output_file,
            'processed_at': datetime.now().isoformat()
        }
    
    def _process_comparative_order(self, order_id: str, dealerships: List[str], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparative order across dealerships"""
        # Build query for comparison
        where_conditions = []
        query_params = []
        
        if dealerships:
            dealer_placeholders = ','.join(['?' for _ in dealerships])
            where_conditions.append(f"dealer_id IN ({dealer_placeholders})")
            query_params.extend(dealerships)
        
        # Add make/model filters if specified
        if 'make' in filters:
            where_conditions.append("make = ?")
            query_params.append(filters['make'])
        
        if 'model' in filters:
            where_conditions.append("model = ?")
            query_params.append(filters['model'])
        
        # Price range filters
        if 'min_price' in filters and filters['min_price']:
            where_conditions.append("price >= ?")
            query_params.append(filters['min_price'])
        
        if 'max_price' in filters and filters['max_price']:
            where_conditions.append("price <= ?")
            query_params.append(filters['max_price'])
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        query = f"""
            SELECT *, 
                   ROW_NUMBER() OVER (
                       PARTITION BY make, model, year 
                       ORDER BY price ASC, mileage ASC
                   ) as rank_within_group
            FROM vehicles 
            WHERE {where_clause}
            ORDER BY make, model, year, price ASC
        """
        
        # Execute query
        with sqlite3.connect(self.database_path) as conn:
            df = pd.read_sql_query(query, conn, params=query_params)
        
        # Save results
        output_file = f"output_data/comparative_order_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        
        # Record order items
        self._record_order_items(order_id, df['vin'].tolist())
        
        # Generate comparison summary
        summary = df.groupby(['make', 'model', 'year']).agg({
            'price': ['min', 'max', 'mean'],
            'vin': 'count',
            'dealer_id': 'nunique'
        }).round(2)
        
        summary_file = output_file.replace('.csv', '_summary.json')
        summary.to_json(summary_file, orient='index', indent=2)
        
        return {
            'order_id': order_id,
            'order_type': 'comparative',
            'vehicles_found': len(df),
            'dealerships_included': df['dealer_id'].nunique(),
            'output_file': output_file,
            'summary_file': summary_file,
            'processed_at': datetime.now().isoformat()
        }
    
    def _process_bulk_order(self, order_id: str, dealerships: List[str], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Process bulk order for entire dealership inventories"""
        batch_size = filters.get('batch_size', 1000)
        
        # Build base query
        where_conditions = []
        query_params = []
        
        if dealerships:
            dealer_placeholders = ','.join(['?' for _ in dealerships])
            where_conditions.append(f"dealer_id IN ({dealer_placeholders})")
            query_params.extend(dealerships)
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM vehicles WHERE {where_clause}"
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(count_query, query_params)
            total_count = cursor.fetchone()[0]
        
        # Process in batches
        all_results = []
        offset = 0
        
        while offset < total_count:
            query = f"""
                SELECT * FROM vehicles 
                WHERE {where_clause}
                ORDER BY dealer_id, normalized_status, make, model
                LIMIT ? OFFSET ?
            """
            
            with sqlite3.connect(self.database_path) as conn:
                batch_df = pd.read_sql_query(query, conn, params=query_params + [batch_size, offset])
            
            all_results.append(batch_df)
            offset += batch_size
            
            self.logger.info(f"Processed batch: {offset}/{total_count}")
        
        # Combine all batches
        final_df = pd.concat(all_results, ignore_index=True)
        
        # Save results
        output_file = f"output_data/bulk_order_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        final_df.to_csv(output_file, index=False)
        
        # Record order items
        self._record_order_items(order_id, final_df['vin'].tolist())
        
        return {
            'order_id': order_id,
            'order_type': 'bulk',
            'total_vehicles': len(final_df),
            'dealerships_processed': final_df['dealer_id'].nunique(),
            'batches_processed': len(all_results),
            'output_file': output_file,
            'processed_at': datetime.now().isoformat()
        }
    
    def _record_order_items(self, order_id: str, vin_list: List[str]):
        """Record VINs associated with an order"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Insert order items
            order_items = [(order_id, vin) for vin in vin_list]
            cursor.executemany("""
                INSERT OR IGNORE INTO order_items (order_id, vin) VALUES (?, ?)
            """, order_items)
            
            conn.commit()
    
    def get_dealership_inventory_summary(self, dealer_id: str = None) -> Dict[str, Any]:
        """Get inventory summary with optimized queries"""
        where_clause = "WHERE dealer_id = ?" if dealer_id else ""
        params = [dealer_id] if dealer_id else []
        
        with sqlite3.connect(self.database_path) as conn:
            # Get counts by status
            status_query = f"""
                SELECT normalized_status, COUNT(*) as count
                FROM vehicles {where_clause}
                GROUP BY normalized_status
                ORDER BY count DESC
            """
            status_df = pd.read_sql_query(status_query, conn, params=params)
            
            # Get make/model distribution
            make_query = f"""
                SELECT make, model, COUNT(*) as count, AVG(price) as avg_price
                FROM vehicles {where_clause}
                WHERE price IS NOT NULL
                GROUP BY make, model
                ORDER BY count DESC
                LIMIT 20
            """
            make_df = pd.read_sql_query(make_query, conn, params=params)
            
            # Get overall stats
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_vehicles,
                    COUNT(DISTINCT dealer_id) as dealership_count,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price
                FROM vehicles 
                {where_clause}
                WHERE price IS NOT NULL
            """
            stats_df = pd.read_sql_query(stats_query, conn, params=params)
        
        return {
            'summary_for': dealer_id or 'all_dealerships',
            'status_distribution': status_df.to_dict('records'),
            'top_make_models': make_df.to_dict('records'),
            'overall_stats': stats_df.to_dict('records')[0],
            'generated_at': datetime.now().isoformat()
        }
    
    def search_vehicles(self, search_criteria: Dict[str, Any]) -> pd.DataFrame:
        """Advanced vehicle search with multiple criteria"""
        where_conditions = []
        query_params = []
        
        # Build dynamic WHERE clause
        if 'vin' in search_criteria:
            where_conditions.append("vin = ?")
            query_params.append(search_criteria['vin'])
        
        if 'make' in search_criteria:
            where_conditions.append("make LIKE ?")
            query_params.append(f"%{search_criteria['make']}%")
        
        if 'model' in search_criteria:
            where_conditions.append("model LIKE ?")
            query_params.append(f"%{search_criteria['model']}%")
        
        if 'year_range' in search_criteria:
            min_year, max_year = search_criteria['year_range']
            where_conditions.append("year BETWEEN ? AND ?")
            query_params.extend([min_year, max_year])
        
        if 'price_range' in search_criteria:
            min_price, max_price = search_criteria['price_range']
            where_conditions.append("price BETWEEN ? AND ?")
            query_params.extend([min_price, max_price])
        
        if 'dealerships' in search_criteria:
            dealer_placeholders = ','.join(['?' for _ in search_criteria['dealerships']])
            where_conditions.append(f"dealer_id IN ({dealer_placeholders})")
            query_params.extend(search_criteria['dealerships'])
        
        if 'status' in search_criteria:
            status_placeholders = ','.join(['?' for _ in search_criteria['status']])
            where_conditions.append(f"normalized_status IN ({status_placeholders})")
            query_params.extend(search_criteria['status'])
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        # Build query with sorting
        sort_order = search_criteria.get('sort_by', 'price ASC')
        limit = search_criteria.get('limit', 1000)
        
        query = f"""
            SELECT * FROM vehicles 
            WHERE {where_clause}
            ORDER BY {sort_order}
            LIMIT ?
        """
        
        query_params.append(limit)
        
        with sqlite3.connect(self.database_path) as conn:
            return pd.read_sql_query(query, conn, params=query_params)
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get detailed order status"""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Get order details
            cursor.execute("""
                SELECT * FROM orders WHERE order_id = ?
            """, (order_id,))
            
            order_row = cursor.fetchone()
            if not order_row:
                return {'error': f'Order {order_id} not found'}
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            order_dict = dict(zip(columns, order_row))
            
            # Get order items count
            cursor.execute("""
                SELECT COUNT(*) FROM order_items WHERE order_id = ?
            """, (order_id,))
            
            item_count = cursor.fetchone()[0]
            order_dict['item_count'] = item_count
            
        return order_dict
    
    def _get_order_dataframe(self, dealerships: List[str], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get DataFrame for order processing with Google Sheets compatibility"""
        where_conditions = []
        query_params = []
        
        if dealerships:
            dealer_placeholders = ','.join(['?' for _ in dealerships])
            where_conditions.append(f"dealer_id IN ({dealer_placeholders})")
            query_params.extend(dealerships)
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        query = f"""
            SELECT * FROM vehicles 
            WHERE {where_clause}
            ORDER BY dealer_id, normalized_status, make, model
        """
        
        with sqlite3.connect(self.database_path) as conn:
            return pd.read_sql_query(query, conn, params=query_params)
    
    def _process_list_order_with_sheets(self, order_id: str, dealerships: List[str], 
                                      filters: Dict[str, Any], sheets_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process list order using Google Sheets logic"""
        vin_list = filters.get('vin_list', [])
        if not vin_list:
            raise ValueError("List order requires vin_list in filters")
        
        # Use Google Sheets list processing logic
        df = pd.DataFrame(sheets_result['scrapeddata']['data'])
        processed_df = self.sheets_filters.apply_list_order_processing(df, vin_list)
        
        # Save with ORDER/VIN matrix format
        matrix_df = self.sheets_filters.create_order_vin_matrix(processed_df)
        
        output_file = f"output_data/list_order_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.makedirs('output_data', exist_ok=True)
        matrix_df.to_csv(output_file, index=False)
        
        # Record order items
        self._record_order_items(order_id, processed_df['vin'].dropna().tolist())
        
        return {
            'order_id': order_id,
            'order_type': 'list',
            'requested_vins': len(vin_list),
            'found_vehicles': len(processed_df[processed_df['status'] != 'not_found']),
            'missing_vins': len(processed_df[processed_df['status'] == 'not_found']),
            'output_file': output_file,
            'sheets_processing': True,
            'processed_at': datetime.now().isoformat()
        }
    
    def _process_comparative_order_with_sheets(self, order_id: str, dealerships: List[str],
                                             filters: Dict[str, Any], sheets_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparative order using Google Sheets logic"""
        comparative_groups = sheets_result['comparative_analysis']
        
        # Combine all comparative groups
        all_comparisons = []
        for group_name, group_df in comparative_groups.items():
            group_df['comparison_group'] = group_name
            all_comparisons.append(group_df)
        
        if all_comparisons:
            final_df = pd.concat(all_comparisons, ignore_index=True)
        else:
            final_df = pd.DataFrame()
        
        # Save with ORDER/VIN matrix format
        if len(final_df) > 0:
            matrix_df = self.sheets_filters.create_order_vin_matrix(final_df)
        else:
            matrix_df = pd.DataFrame()
        
        output_file = f"output_data/comparative_order_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        matrix_df.to_csv(output_file, index=False)
        
        # Generate comparison summary
        summary = {}
        for group_name, group_df in comparative_groups.items():
            summary[group_name] = {
                'vehicle_count': len(group_df),
                'dealership_count': group_df['dealer_id'].nunique(),
                'price_range': [group_df['price'].min(), group_df['price'].max()],
                'best_deal': group_df.iloc[0].to_dict() if len(group_df) > 0 else None
            }
        
        summary_file = output_file.replace('.csv', '_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Record order items
        if len(final_df) > 0:
            self._record_order_items(order_id, final_df['vin'].dropna().tolist())
        
        return {
            'order_id': order_id,
            'order_type': 'comparative',
            'comparison_groups': len(comparative_groups),
            'total_vehicles': len(final_df),
            'dealerships_compared': final_df['dealer_id'].nunique() if len(final_df) > 0 else 0,
            'output_file': output_file,
            'summary_file': summary_file,
            'sheets_processing': True,
            'processed_at': datetime.now().isoformat()
        }
    
    def _process_bulk_order_with_sheets(self, order_id: str, dealerships: List[str],
                                      filters: Dict[str, Any], sheets_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process bulk order using Google Sheets logic"""
        # Use the ORDERS view from sheets processing
        orders_data = sheets_result['orders']['data']
        matrix_df = pd.DataFrame(orders_data)
        
        # Apply dealership-specific views
        dealership_views = sheets_result['dealership_views']
        
        output_file = f"output_data/bulk_order_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        matrix_df.to_csv(output_file, index=False)
        
        # Save individual dealership files
        dealership_files = {}
        for dealership, view_data in dealership_views.items():
            if view_data['vehicle_count'] > 0:
                dealership_df = pd.DataFrame(view_data['data'])
                dealer_file = f"output_data/dealership_{dealership.lower()}_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                dealership_df.to_csv(dealer_file, index=False)
                dealership_files[dealership] = dealer_file
        
        # Record order items
        all_vins = matrix_df['VIN'].dropna().tolist()
        if all_vins:
            self._record_order_items(order_id, all_vins)
        
        return {
            'order_id': order_id,
            'order_type': 'bulk',
            'total_vehicles': len(matrix_df),
            'dealerships_processed': len(dealership_files),
            'dealership_files': dealership_files,
            'main_output_file': output_file,
            'order_summary': sheets_result['orders'].get('order_summary', {}),
            'sheets_processing': True,
            'processed_at': datetime.now().isoformat()
        }
    
    def generate_order_matrix_report(self, order_id: str = None) -> Dict[str, Any]:
        """Generate ORDER/VIN matrix report matching Google Sheets format"""
        # Get all vehicles
        with sqlite3.connect(self.database_path) as conn:
            df = pd.read_sql_query("SELECT * FROM vehicles", conn)
        
        if df.empty:
            return {'error': 'No vehicles found in database'}
        
        # Apply Google Sheets processing
        sheets_result = apply_all_google_sheets_filters(df)
        
        # Generate matrix report
        matrix_df = pd.DataFrame(sheets_result['orders']['data'])
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"output_data/order_matrix_report_{timestamp}.csv"
        os.makedirs('output_data', exist_ok=True)
        matrix_df.to_csv(report_file, index=False)
        
        return {
            'report_file': report_file,
            'matrix_data': sheets_result['orders'],
            'dealership_views': sheets_result['dealership_views'],
            'validation_results': sheets_result['validation'],
            'generated_at': datetime.now().isoformat()
        }

def create_order_processor(database_path: str = "data/order_processing.db") -> OrderProcessor:
    """Create a configured OrderProcessor instance"""
    return OrderProcessor(database_path)

def process_normalized_csv_to_orders(input_csv: str, output_dir: str = "output_data") -> Dict[str, Any]:
    """Convenience function to process normalized CSV into order-ready format"""
    processor = create_order_processor()
    
    # Import the data
    import_result = processor.import_normalized_data(input_csv)
    
    # Create a bulk order for all data
    order_config = OrderConfig(
        order_id=f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        order_type="bulk",
        dealerships=[],  # All dealerships
        filters={"batch_size": 1000}
    )
    
    processor.create_order(order_config)
    process_result = processor.process_order(order_config.order_id)
    
    return {
        'import_result': import_result,
        'process_result': process_result,
        'order_id': order_config.order_id
    }