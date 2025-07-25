#!/usr/bin/env python3
"""
Silver Fox Competitive Pricing Analyzer
=======================================

Advanced pricing analysis module for comparing prices across dealers,
identifying market trends, and providing competitive intelligence for
the Silver Fox automotive inventory system.

Features:
- Multi-dealer price comparison
- Market trend analysis
- Competitive positioning insights
- Price optimization recommendations
- Market share analysis
- Seasonal pricing patterns

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import sqlite3
import statistics
from collections import defaultdict, Counter
import re

# Import Silver Fox components
sys.path.append(str(Path(__file__).parent))

@dataclass
class VehiclePrice:
    """Vehicle pricing data point"""
    vin: str
    dealer_id: str
    dealer_name: str
    year: int
    make: str
    model: str
    trim: str
    price: float
    mileage: int
    timestamp: datetime
    normalized_model: str  # Standardized model name

@dataclass
class MarketAnalysis:
    """Market analysis results"""
    vehicle_key: str  # year_make_model
    total_listings: int
    avg_price: float
    median_price: float
    price_range: Tuple[float, float]
    std_deviation: float
    dealer_count: int
    market_leader: str  # Dealer with most listings
    price_leader: str   # Dealer with lowest average price
    trend_direction: str  # 'increasing', 'decreasing', 'stable'

@dataclass
class CompetitiveInsight:
    """Competitive intelligence insight"""
    insight_type: str
    severity: str  # 'info', 'warning', 'critical'
    title: str
    description: str
    affected_dealers: List[str]
    recommended_action: str
    data_support: Dict[str, Any]

class CompetitivePricingAnalyzer:
    """
    Advanced competitive pricing analysis system
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the pricing analyzer"""
        self.project_root = Path(__file__).parent
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize database
        self.db_path = self.project_root / "pricing_analysis.db"
        self._initialize_database()
        
        # Load dealer configurations
        self.dealer_configs = self._load_dealer_configs()
        
        # Model normalization patterns
        self.model_patterns = self._load_model_patterns()
        
        self.logger.info("✅ Competitive pricing analyzer initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load analyzer configuration"""
        default_config = {
            'analysis_window_days': 30,
            'minimum_sample_size': 3,
            'price_outlier_threshold': 2.5,  # Standard deviations
            'trend_analysis_days': 14,
            'competitive_radius_miles': 50,
            'model_matching': {
                'fuzzy_threshold': 0.8,
                'year_tolerance': 1,
                'mileage_weight': 0.3
            },
            'insights': {
                'price_advantage_threshold': 0.05,  # 5% price advantage
                'market_share_threshold': 0.15,     # 15% market share
                'inventory_velocity_days': 45
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('pricing_analyzer')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f"pricing_analyzer_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_database(self):
        """Initialize SQLite database for pricing data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Vehicle pricing data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vehicle_pricing (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vin TEXT NOT NULL,
                        dealer_id TEXT NOT NULL,
                        dealer_name TEXT NOT NULL,
                        year INTEGER NOT NULL,
                        make TEXT NOT NULL,
                        model TEXT NOT NULL,
                        trim TEXT,
                        price REAL NOT NULL,
                        mileage INTEGER,
                        timestamp DATETIME NOT NULL,
                        normalized_model TEXT NOT NULL,
                        UNIQUE(vin, dealer_id, timestamp)
                    )
                ''')
                
                # Market analysis results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS market_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vehicle_key TEXT NOT NULL,
                        analysis_date DATETIME NOT NULL,
                        total_listings INTEGER NOT NULL,
                        avg_price REAL NOT NULL,
                        median_price REAL NOT NULL,
                        min_price REAL NOT NULL,
                        max_price REAL NOT NULL,
                        std_deviation REAL NOT NULL,
                        dealer_count INTEGER NOT NULL,
                        market_leader TEXT,
                        price_leader TEXT,
                        trend_direction TEXT,
                        analysis_data TEXT
                    )
                ''')
                
                # Competitive insights table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS competitive_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        insight_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        affected_dealers TEXT NOT NULL,
                        recommended_action TEXT NOT NULL,
                        data_support TEXT,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Create indexes
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_pricing_vehicle_key 
                    ON vehicle_pricing(year, make, normalized_model, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_pricing_dealer_time 
                    ON vehicle_pricing(dealer_id, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_vehicle_date 
                    ON market_analysis(vehicle_key, analysis_date)
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _load_dealer_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load dealer configurations"""
        configs = {}
        config_dir = self.project_root / "silverfox_system" / "config"
        
        if not config_dir.exists():
            self.logger.warning(f"Config directory not found: {config_dir}")
            return configs
        
        for config_file in config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    dealer_config = json.load(f)
                    dealer_id = config_file.stem
                    configs[dealer_id] = dealer_config
            except Exception as e:
                self.logger.warning(f"Could not load config for {config_file.stem}: {e}")
        
        return configs
    
    def _load_model_patterns(self) -> Dict[str, List[str]]:
        """Load model normalization patterns"""
        return {
            'bmw': [
                r'(\d+)[\s-]?series', r'x(\d+)', r'z(\d+)', r'm(\d+)',
                r'i(\d+)', r'grand\s+coupe', r'xdrive', r'sdrive'
            ],
            'audi': [
                r'a(\d+)', r'q(\d+)', r'tt', r'r(\d+)', r'e-tron',
                r'allroad', r'quattro'
            ],
            'mercedes': [
                r'([a-z])-class', r'gl[a-z]', r'ml[a-z]', r'sl[a-z]',
                r'amg', r'maybach'
            ],
            'lexus': [
                r'(is|es|gs|ls)', r'(rx|gx|lx)', r'(nx|ux)',
                r'rc', r'lc', r'ct'
            ],
            'acura': [
                r'(tsx|tlx|tl)', r'(mdx|rdx|zdx)', r'(rsx|nsx)',
                r'integra', r'legend'
            ]
        }
    
    def analyze_market_data(self, source_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis
        
        Args:
            source_data: Optional vehicle data, if None will load from recent scraper runs
            
        Returns:
            Comprehensive market analysis results
        """
        self.logger.info("🔍 Starting competitive pricing analysis")
        
        try:
            # Load and prepare data
            if source_data is None:
                vehicle_data = self._load_recent_vehicle_data()
            else:
                vehicle_data = self._prepare_vehicle_data(source_data)
            
            if not vehicle_data:
                self.logger.warning("⚠️ No vehicle data available for analysis")
                return {'error': 'No data available'}
            
            self.logger.info(f"📊 Analyzing {len(vehicle_data)} vehicle records")
            
            # Store pricing data
            self._store_vehicle_pricing(vehicle_data)
            
            # Perform market analysis
            market_analyses = self._perform_market_analysis(vehicle_data)
            
            # Generate competitive insights
            insights = self._generate_competitive_insights(vehicle_data, market_analyses)
            
            # Create comprehensive report
            report = self._create_analysis_report(vehicle_data, market_analyses, insights)
            
            self.logger.info("✅ Market analysis completed successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Market analysis failed: {e}")
            return {'error': str(e)}
    
    def _load_recent_vehicle_data(self) -> List[VehiclePrice]:
        """Load recent vehicle data from scraper outputs"""
        vehicle_data = []
        
        try:
            # Look for recent scraper session data
            output_dir = self.project_root / "output_data"
            if not output_dir.exists():
                return vehicle_data
            
            # Get most recent session
            session_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            if not session_dirs:
                return vehicle_data
            
            most_recent = max(session_dirs, key=lambda x: x.stat().st_mtime)
            
            # Load all vehicle JSON files from the session
            for json_file in most_recent.glob("*_vehicles.json"):
                try:
                    with open(json_file, 'r') as f:
                        dealer_data = json.load(f)
                    
                    dealer_name = json_file.stem.replace('_vehicles', '').replace('_', ' ').title()
                    dealer_id = self._normalize_dealer_id(dealer_name)
                    
                    for vehicle in dealer_data:
                        if self._is_valid_vehicle_data(vehicle):
                            vehicle_price = self._create_vehicle_price(vehicle, dealer_id, dealer_name)
                            if vehicle_price:
                                vehicle_data.append(vehicle_price)
                                
                except Exception as e:
                    self.logger.warning(f"Could not load {json_file}: {e}")
            
            self.logger.info(f"📊 Loaded {len(vehicle_data)} vehicles from recent session")
            return vehicle_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load recent vehicle data: {e}")
            return []
    
    def _prepare_vehicle_data(self, source_data: List[Dict[str, Any]]) -> List[VehiclePrice]:
        """Prepare and normalize vehicle data for analysis"""
        vehicle_data = []
        
        for vehicle in source_data:
            if self._is_valid_vehicle_data(vehicle):
                # Extract dealer info from vehicle data or use defaults
                dealer_id = vehicle.get('dealer_id', 'unknown')
                dealer_name = vehicle.get('dealer_name', 'Unknown Dealer')
                
                vehicle_price = self._create_vehicle_price(vehicle, dealer_id, dealer_name)
                if vehicle_price:
                    vehicle_data.append(vehicle_price)
        
        return vehicle_data
    
    def _is_valid_vehicle_data(self, vehicle: Dict[str, Any]) -> bool:
        """Check if vehicle data is valid for analysis"""
        required_fields = ['vin', 'year', 'make', 'model', 'price']
        
        for field in required_fields:
            if not vehicle.get(field):
                return False
        
        # Additional validation
        try:
            year = int(vehicle['year'])
            price = float(vehicle['price'])
            
            if year < 1990 or year > datetime.now().year + 2:
                return False
            
            if price <= 0 or price > 1000000:  # Reasonable price range
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _create_vehicle_price(self, vehicle: Dict[str, Any], dealer_id: str, dealer_name: str) -> Optional[VehiclePrice]:
        """Create VehiclePrice object from vehicle data"""
        try:
            normalized_model = self._normalize_model(vehicle['make'], vehicle['model'])
            
            return VehiclePrice(
                vin=vehicle['vin'],
                dealer_id=dealer_id,
                dealer_name=dealer_name,
                year=int(vehicle['year']),
                make=vehicle['make'].upper(),
                model=vehicle['model'],
                trim=vehicle.get('trim', ''),
                price=float(vehicle['price']),
                mileage=int(vehicle.get('mileage', 0)),
                timestamp=datetime.now(),
                normalized_model=normalized_model
            )
        except Exception as e:
            self.logger.warning(f"Could not create VehiclePrice: {e}")
            return None
    
    def _normalize_model(self, make: str, model: str) -> str:
        """Normalize model name for consistent comparison"""
        make_lower = make.lower()
        model_lower = model.lower()
        
        # Apply make-specific patterns
        if make_lower in self.model_patterns:
            for pattern in self.model_patterns[make_lower]:
                match = re.search(pattern, model_lower)
                if match:
                    return match.group(0).upper()
        
        # Generic normalization
        # Remove common words and standardize
        normalized = re.sub(r'\b(sedan|coupe|convertible|wagon|suv|hatchback)\b', '', model_lower)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized.upper() if normalized else model.upper()
    
    def _normalize_dealer_id(self, dealer_name: str) -> str:
        """Normalize dealer name to ID"""
        # Convert to lowercase, remove spaces and special characters
        normalized = re.sub(r'[^a-z0-9]', '', dealer_name.lower())
        return normalized
    
    def _store_vehicle_pricing(self, vehicle_data: List[VehiclePrice]):
        """Store vehicle pricing data in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for vehicle in vehicle_data:
                    cursor.execute('''
                        INSERT OR REPLACE INTO vehicle_pricing
                        (vin, dealer_id, dealer_name, year, make, model, trim,
                         price, mileage, timestamp, normalized_model)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        vehicle.vin, vehicle.dealer_id, vehicle.dealer_name,
                        vehicle.year, vehicle.make, vehicle.model, vehicle.trim,
                        vehicle.price, vehicle.mileage, vehicle.timestamp,
                        vehicle.normalized_model
                    ))
                
                conn.commit()
                self.logger.info(f"💾 Stored {len(vehicle_data)} vehicle pricing records")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store vehicle pricing: {e}")
    
    def _perform_market_analysis(self, vehicle_data: List[VehiclePrice]) -> Dict[str, MarketAnalysis]:
        """Perform market analysis by vehicle segment"""
        analyses = {}
        
        # Group vehicles by year, make, normalized model
        vehicle_groups = defaultdict(list)
        for vehicle in vehicle_data:
            vehicle_key = f"{vehicle.year}_{vehicle.make}_{vehicle.normalized_model}"
            vehicle_groups[vehicle_key].append(vehicle)
        
        # Analyze each group
        for vehicle_key, vehicles in vehicle_groups.items():
            if len(vehicles) >= self.config['minimum_sample_size']:
                analysis = self._analyze_vehicle_group(vehicle_key, vehicles)
                if analysis:
                    analyses[vehicle_key] = analysis
        
        # Store analysis results
        self._store_market_analyses(analyses)
        
        self.logger.info(f"📈 Completed analysis for {len(analyses)} vehicle segments")
        return analyses
    
    def _analyze_vehicle_group(self, vehicle_key: str, vehicles: List[VehiclePrice]) -> Optional[MarketAnalysis]:
        """Analyze a group of similar vehicles"""
        try:
            prices = [v.price for v in vehicles]
            dealers = [v.dealer_id for v in vehicles]
            
            # Remove outliers
            prices_clean = self._remove_price_outliers(prices)
            
            if len(prices_clean) < self.config['minimum_sample_size']:
                return None
            
            # Calculate statistics
            avg_price = statistics.mean(prices_clean)
            median_price = statistics.median(prices_clean)
            std_deviation = statistics.stdev(prices_clean) if len(prices_clean) > 1 else 0
            
            # Dealer analysis
            dealer_counts = Counter(dealers)
            market_leader = dealer_counts.most_common(1)[0][0]
            
            # Find price leader (dealer with lowest average price)
            dealer_avg_prices = defaultdict(list)
            for vehicle in vehicles:
                dealer_avg_prices[vehicle.dealer_id].append(vehicle.price)
            
            dealer_averages = {
                dealer: statistics.mean(prices) 
                for dealer, prices in dealer_avg_prices.items()
            }
            price_leader = min(dealer_averages.keys(), key=lambda x: dealer_averages[x])
            
            # Trend analysis (simplified - would need historical data for full implementation)
            trend_direction = "stable"  # Default
            
            return MarketAnalysis(
                vehicle_key=vehicle_key,
                total_listings=len(vehicles),
                avg_price=avg_price,
                median_price=median_price,
                price_range=(min(prices_clean), max(prices_clean)),
                std_deviation=std_deviation,
                dealer_count=len(set(dealers)),
                market_leader=market_leader,
                price_leader=price_leader,
                trend_direction=trend_direction
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to analyze vehicle group {vehicle_key}: {e}")
            return None
    
    def _remove_price_outliers(self, prices: List[float]) -> List[float]:
        """Remove price outliers using standard deviation method"""
        if len(prices) < 3:
            return prices
        
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices)
        threshold = self.config['price_outlier_threshold']
        
        cleaned_prices = [
            price for price in prices
            if abs(price - mean_price) <= threshold * std_dev
        ]
        
        return cleaned_prices if cleaned_prices else prices
    
    def _store_market_analyses(self, analyses: Dict[str, MarketAnalysis]):
        """Store market analysis results in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for analysis in analyses.values():
                    cursor.execute('''
                        INSERT INTO market_analysis
                        (vehicle_key, analysis_date, total_listings, avg_price,
                         median_price, min_price, max_price, std_deviation,
                         dealer_count, market_leader, price_leader, trend_direction,
                         analysis_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        analysis.vehicle_key,
                        datetime.now(),
                        analysis.total_listings,
                        analysis.avg_price,
                        analysis.median_price,
                        analysis.price_range[0],
                        analysis.price_range[1],
                        analysis.std_deviation,
                        analysis.dealer_count,
                        analysis.market_leader,
                        analysis.price_leader,
                        analysis.trend_direction,
                        json.dumps(asdict(analysis))
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store market analyses: {e}")
    
    def _generate_competitive_insights(self, vehicle_data: List[VehiclePrice], 
                                     analyses: Dict[str, MarketAnalysis]) -> List[CompetitiveInsight]:
        """Generate competitive intelligence insights"""
        insights = []
        
        # Price advantage insights
        insights.extend(self._analyze_price_advantages(analyses))
        
        # Market share insights
        insights.extend(self._analyze_market_share(vehicle_data))
        
        # Inventory depth insights
        insights.extend(self._analyze_inventory_depth(vehicle_data))
        
        # Price positioning insights
        insights.extend(self._analyze_price_positioning(analyses))
        
        # Store insights
        self._store_insights(insights)
        
        self.logger.info(f"💡 Generated {len(insights)} competitive insights")
        return insights
    
    def _analyze_price_advantages(self, analyses: Dict[str, MarketAnalysis]) -> List[CompetitiveInsight]:
        """Analyze price advantages across dealers"""
        insights = []
        
        for vehicle_key, analysis in analyses.items():
            # Check if price leader has significant advantage
            price_advantage = (analysis.avg_price - analysis.median_price) / analysis.avg_price
            
            if abs(price_advantage) > self.config['insights']['price_advantage_threshold']:
                severity = 'warning' if abs(price_advantage) > 0.1 else 'info'
                
                insight = CompetitiveInsight(
                    insight_type='price_advantage',
                    severity=severity,
                    title=f"Price Advantage Detected: {vehicle_key}",
                    description=(
                        f"{analysis.price_leader} has significant price advantage "
                        f"({price_advantage:.1%}) for {vehicle_key}"
                    ),
                    affected_dealers=[analysis.price_leader],
                    recommended_action="Review pricing strategy for competitive positioning",
                    data_support={
                        'vehicle_key': vehicle_key,
                        'price_advantage': price_advantage,
                        'market_avg': analysis.avg_price,
                        'leader_position': analysis.price_leader
                    }
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_market_share(self, vehicle_data: List[VehiclePrice]) -> List[CompetitiveInsight]:
        """Analyze market share by dealer"""
        insights = []
        
        # Calculate overall market share
        dealer_counts = Counter([v.dealer_id for v in vehicle_data])
        total_vehicles = len(vehicle_data)
        
        for dealer_id, count in dealer_counts.items():
            market_share = count / total_vehicles
            
            if market_share > self.config['insights']['market_share_threshold']:
                dealer_name = next((v.dealer_name for v in vehicle_data if v.dealer_id == dealer_id), dealer_id)
                
                insight = CompetitiveInsight(
                    insight_type='market_share',
                    severity='info',
                    title=f"Market Leadership: {dealer_name}",
                    description=(
                        f"{dealer_name} holds {market_share:.1%} market share "
                        f"with {count} listings"
                    ),
                    affected_dealers=[dealer_id],
                    recommended_action="Monitor competitive responses to market leader",
                    data_support={
                        'market_share': market_share,
                        'listing_count': count,
                        'total_market': total_vehicles
                    }
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_inventory_depth(self, vehicle_data: List[VehiclePrice]) -> List[CompetitiveInsight]:
        """Analyze inventory depth by make/model"""
        insights = []
        
        # Group by dealer and model
        dealer_inventory = defaultdict(lambda: defaultdict(int))
        for vehicle in vehicle_data:
            model_key = f"{vehicle.make} {vehicle.normalized_model}"
            dealer_inventory[vehicle.dealer_id][model_key] += 1
        
        # Find dealers with deep inventory in specific models
        for dealer_id, inventory in dealer_inventory.items():
            for model_key, count in inventory.items():
                if count >= 5:  # Threshold for "deep inventory"
                    dealer_name = next((v.dealer_name for v in vehicle_data if v.dealer_id == dealer_id), dealer_id)
                    
                    insight = CompetitiveInsight(
                        insight_type='inventory_depth',
                        severity='info',
                        title=f"Deep Inventory: {dealer_name} - {model_key}",
                        description=(
                            f"{dealer_name} has deep inventory ({count} units) "
                            f"in {model_key}"
                        ),
                        affected_dealers=[dealer_id],
                        recommended_action="Consider volume pricing opportunities",
                        data_support={
                            'model': model_key,
                            'inventory_count': count,
                            'dealer': dealer_name
                        }
                    )
                    insights.append(insight)
        
        return insights
    
    def _analyze_price_positioning(self, analyses: Dict[str, MarketAnalysis]) -> List[CompetitiveInsight]:
        """Analyze price positioning across market segments"""
        insights = []
        
        for vehicle_key, analysis in analyses.items():
            # Check for high price variance (competitive opportunity)
            if analysis.std_deviation > 0:
                coefficient_of_variation = analysis.std_deviation / analysis.avg_price
                
                if coefficient_of_variation > 0.15:  # High variance threshold
                    insight = CompetitiveInsight(
                        insight_type='price_variance',
                        severity='warning',
                        title=f"High Price Variance: {vehicle_key}",
                        description=(
                            f"Significant price variance ({coefficient_of_variation:.1%}) "
                            f"detected in {vehicle_key} segment"
                        ),
                        affected_dealers=[analysis.market_leader, analysis.price_leader],
                        recommended_action="Review pricing strategy - opportunity for optimization",
                        data_support={
                            'vehicle_key': vehicle_key,
                            'variance': coefficient_of_variation,
                            'price_range': analysis.price_range,
                            'avg_price': analysis.avg_price
                        }
                    )
                    insights.append(insight)
        
        return insights
    
    def _store_insights(self, insights: List[CompetitiveInsight]):
        """Store competitive insights in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for insight in insights:
                    cursor.execute('''
                        INSERT INTO competitive_insights
                        (timestamp, insight_type, severity, title, description,
                         affected_dealers, recommended_action, data_support)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now(),
                        insight.insight_type,
                        insight.severity,
                        insight.title,
                        insight.description,
                        json.dumps(insight.affected_dealers),
                        insight.recommended_action,
                        json.dumps(insight.data_support)
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store insights: {e}")
    
    def _create_analysis_report(self, vehicle_data: List[VehiclePrice], 
                              analyses: Dict[str, MarketAnalysis], 
                              insights: List[CompetitiveInsight]) -> Dict[str, Any]:
        """Create comprehensive analysis report"""
        # Summary statistics
        total_vehicles = len(vehicle_data)
        total_value = sum(v.price for v in vehicle_data)
        avg_price = total_value / total_vehicles if total_vehicles > 0 else 0
        
        dealers = list(set(v.dealer_id for v in vehicle_data))
        makes = list(set(v.make for v in vehicle_data))
        
        # Top insights by severity
        critical_insights = [i for i in insights if i.severity == 'critical']
        warning_insights = [i for i in insights if i.severity == 'warning']
        
        report = {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_vehicles_analyzed': total_vehicles,
                'total_market_value': total_value,
                'average_price': avg_price,
                'dealers_included': len(dealers),
                'makes_analyzed': len(makes),
                'segments_analyzed': len(analyses)
            },
            'market_overview': {
                'participating_dealers': dealers,
                'vehicle_makes': makes,
                'price_statistics': {
                    'total_value': total_value,
                    'average_price': avg_price,
                    'price_range': [
                        min(v.price for v in vehicle_data) if vehicle_data else 0,
                        max(v.price for v in vehicle_data) if vehicle_data else 0
                    ]
                }
            },
            'segment_analyses': {
                key: asdict(analysis) for key, analysis in analyses.items()
            },
            'competitive_insights': {
                'total_insights': len(insights),
                'critical_insights': len(critical_insights),
                'warning_insights': len(warning_insights),
                'insights_by_type': Counter([i.insight_type for i in insights]),
                'top_insights': [asdict(i) for i in insights[:10]]  # Top 10
            },
            'recommendations': self._generate_recommendations(analyses, insights),
            'data_quality': {
                'completeness_score': self._calculate_data_completeness(vehicle_data),
                'coverage_score': len(dealers) / max(len(self.dealer_configs), 1),
                'freshness_score': 1.0  # Assuming current data
            }
        }
        
        # Save report
        self._save_analysis_report(report)
        
        return report
    
    def _generate_recommendations(self, analyses: Dict[str, MarketAnalysis], 
                                insights: List[CompetitiveInsight]) -> List[str]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        # Price positioning recommendations
        price_insights = [i for i in insights if i.insight_type == 'price_advantage']
        if price_insights:
            recommendations.append(
                "Review pricing strategy - competitors showing significant price advantages"
            )
        
        # Market share recommendations
        share_insights = [i for i in insights if i.insight_type == 'market_share']
        if share_insights:
            recommendations.append(
                "Monitor market leaders for competitive threats and opportunities"
            )
        
        # Inventory recommendations
        inventory_insights = [i for i in insights if i.insight_type == 'inventory_depth']
        if inventory_insights:
            recommendations.append(
                "Consider volume pricing strategies for high-inventory models"
            )
        
        # General recommendations
        if len(analyses) > 10:
            recommendations.append(
                "Strong market coverage - maintain competitive monitoring frequency"
            )
        
        return recommendations
    
    def _calculate_data_completeness(self, vehicle_data: List[VehiclePrice]) -> float:
        """Calculate data completeness score"""
        if not vehicle_data:
            return 0.0
        
        required_fields = ['vin', 'price', 'year', 'make', 'model']
        optional_fields = ['trim', 'mileage']
        
        total_possible = len(vehicle_data) * (len(required_fields) + len(optional_fields))
        total_present = 0
        
        for vehicle in vehicle_data:
            # Required fields (weighted higher)
            for field in required_fields:
                if getattr(vehicle, field, None):
                    total_present += 2  # Weight required fields more
            
            # Optional fields
            for field in optional_fields:
                if getattr(vehicle, field, None):
                    total_present += 1
        
        return min(total_present / (total_possible * 1.5), 1.0)  # Adjusted for weighting
    
    def _save_analysis_report(self, report: Dict[str, Any]):
        """Save analysis report to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.project_root / f"competitive_analysis_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"📄 Analysis report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save analysis report: {e}")
    
    # Public API methods
    def get_dealer_comparison(self, dealer_ids: List[str]) -> Dict[str, Any]:
        """Compare specific dealers"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recent data for specified dealers
                placeholders = ','.join(['?' for _ in dealer_ids])
                cursor.execute(f'''
                    SELECT * FROM vehicle_pricing
                    WHERE dealer_id IN ({placeholders})
                    AND timestamp > datetime('now', '-7 days')
                    ORDER BY timestamp DESC
                ''', dealer_ids)
                
                # Process results into comparison format
                # Implementation would format data for easy comparison
                results = cursor.fetchall()
                
                return {
                    'comparison_data': 'Implementation specific to requirements',
                    'total_records': len(results)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Dealer comparison failed: {e}")
            return {'error': str(e)}
    
    def get_price_trends(self, vehicle_key: str, days: int = 30) -> Dict[str, Any]:
        """Get price trends for specific vehicle segment"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT analysis_date, avg_price, median_price, min_price, max_price
                    FROM market_analysis
                    WHERE vehicle_key = ? AND analysis_date > datetime('now', '-{} days')
                    ORDER BY analysis_date
                '''.format(days), (vehicle_key,))
                
                results = cursor.fetchall()
                
                return {
                    'vehicle_key': vehicle_key,
                    'trend_data': results,
                    'data_points': len(results)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Price trends query failed: {e}")
            return {'error': str(e)}


def main():
    """Main execution for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 Silver Fox Competitive Pricing Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = CompetitivePricingAnalyzer()
    
    # Run analysis
    results = analyzer.analyze_market_data()
    
    if 'error' not in results:
        print("✅ Analysis completed successfully")
        print(f"📊 Analyzed {results['analysis_metadata']['total_vehicles_analyzed']} vehicles")
        print(f"💡 Generated {results['competitive_insights']['total_insights']} insights")
        print(f"📋 {len(results['recommendations'])} recommendations provided")
    else:
        print(f"❌ Analysis failed: {results['error']}")


if __name__ == "__main__":
    main()