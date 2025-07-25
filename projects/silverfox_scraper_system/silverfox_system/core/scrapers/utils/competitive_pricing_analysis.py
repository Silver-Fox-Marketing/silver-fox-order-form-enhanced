#!/usr/bin/env python3
"""
Competitive Pricing Analysis Module
Provides real-time competitive intelligence and pricing recommendations
Analyzes pricing strategies across dealership inventories for market positioning
"""

import logging
import json
import statistics
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re
import difflib

# Import alert system for pricing notifications
try:
    from realtime_inventory_alerts import (
        RealtimeInventoryAlertSystem,
        InventoryAlert,
        AlertType,
        AlertPriority,
        NotificationChannel
    )
except ImportError:
    from utils.realtime_inventory_alerts import (
        RealtimeInventoryAlertSystem,
        InventoryAlert,
        AlertType,
        AlertPriority,
        NotificationChannel
    )

class PricingPosition(Enum):
    """Market pricing position relative to competitors"""
    SIGNIFICANTLY_BELOW = "significantly_below"  # >15% below market
    BELOW_MARKET = "below_market"                # 5-15% below market
    MARKET_COMPETITIVE = "market_competitive"    # Within 5% of market
    ABOVE_MARKET = "above_market"               # 5-15% above market
    SIGNIFICANTLY_ABOVE = "significantly_above" # >15% above market

class TrendDirection(Enum):
    """Price trend direction"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

class AnalysisType(Enum):
    """Type of competitive analysis"""
    VEHICLE_SPECIFIC = "vehicle_specific"
    BRAND_ANALYSIS = "brand_analysis"
    DEALERSHIP_COMPARISON = "dealership_comparison"
    MARKET_OVERVIEW = "market_overview"
    TREND_ANALYSIS = "trend_analysis"

@dataclass
class VehicleMatch:
    """Represents a matched vehicle across dealerships"""
    primary_vin: str
    primary_dealership: str
    matches: List[Dict[str, Any]]
    similarity_scores: List[float]
    match_criteria: Dict[str, Any]
    confidence: float

@dataclass
class PricingAnalysis:
    """Pricing analysis results for a vehicle or group"""
    vehicle_identifier: str  # VIN or group identifier
    market_price_stats: Dict[str, float]  # min, max, mean, median, std
    pricing_position: PricingPosition
    competitive_vehicles: List[Dict[str, Any]]
    price_recommendations: Dict[str, Any]
    market_context: Dict[str, Any]
    analysis_timestamp: datetime

@dataclass
class MarketTrend:
    """Market trend analysis"""
    trend_period: str
    direction: TrendDirection
    price_change_percentage: float
    volume_change_percentage: float
    key_factors: List[str]
    confidence: float

@dataclass
class CompetitiveDashboard:
    """Comprehensive competitive analysis dashboard"""
    dealership_name: str
    analysis_date: datetime
    market_position_summary: Dict[str, Any]
    pricing_opportunities: List[Dict[str, Any]]
    competitor_insights: List[Dict[str, Any]]
    market_trends: List[MarketTrend]
    recommendations: List[str]
    
class CompetitivePricingAnalyzer:
    """
    Advanced competitive pricing analysis system
    Provides market intelligence and pricing recommendations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("CompetitivePricingAnalyzer")
        
        # Analysis parameters
        self.similarity_threshold = config.get('similarity_threshold', 0.85)
        self.price_variance_threshold = config.get('price_variance_threshold', 0.05)  # 5%
        self.trend_analysis_days = config.get('trend_analysis_days', 30)
        self.min_market_samples = config.get('min_market_samples', 3)
        
        # Vehicle matching weights
        self.matching_weights = {
            'make': 0.25,
            'model': 0.25,
            'year': 0.20,
            'trim': 0.15,
            'mileage': 0.10,
            'condition': 0.05
        }
        
        # Data storage
        self.vehicle_database = {}  # VIN -> vehicle data with history
        self.pricing_history = {}   # VIN -> [price records]
        self.market_analysis_cache = {}
        self.competitive_matches = {}
        
        # Initialize alert system integration
        self.alert_system = None
        if config.get('enable_alerts', True):
            self._initialize_alert_integration()
    
    def _initialize_alert_integration(self):
        """Initialize integration with alert system"""
        try:
            alert_config = self.config.get('alert_config', {})
            if alert_config:
                from utils.realtime_inventory_alerts import create_alert_system
                self.alert_system = create_alert_system(alert_config)
        except Exception as e:
            self.logger.warning(f"Could not initialize alert integration: {str(e)}")
    
    def analyze_dealership_inventory(self, 
                                   dealership_id: str,
                                   dealership_name: str,
                                   inventory: List[Dict[str, Any]],
                                   market_data: Dict[str, List[Dict[str, Any]]]) -> CompetitiveDashboard:
        """
        Comprehensive competitive analysis for dealership inventory
        Returns dashboard with market positioning and recommendations
        """
        
        self.logger.info(f"Starting competitive analysis for {dealership_name}")
        
        # Update vehicle database
        self._update_vehicle_database(dealership_id, inventory)
        
        # Analyze market position
        market_position_summary = self._analyze_market_position(
            dealership_id, dealership_name, inventory, market_data
        )
        
        # Identify pricing opportunities
        pricing_opportunities = self._identify_pricing_opportunities(
            dealership_id, inventory, market_data
        )
        
        # Generate competitor insights
        competitor_insights = self._generate_competitor_insights(
            dealership_id, dealership_name, market_data
        )
        
        # Analyze market trends
        market_trends = self._analyze_market_trends(market_data)
        
        # Generate recommendations
        recommendations = self._generate_pricing_recommendations(
            market_position_summary, pricing_opportunities, market_trends
        )
        
        # Create dashboard
        dashboard = CompetitiveDashboard(
            dealership_name=dealership_name,
            analysis_date=datetime.now(),
            market_position_summary=market_position_summary,
            pricing_opportunities=pricing_opportunities,
            competitor_insights=competitor_insights,
            market_trends=market_trends,
            recommendations=recommendations
        )
        
        # Generate alerts for significant findings
        self._generate_pricing_alerts(dealership_id, dealership_name, dashboard)
        
        self.logger.info(f"Competitive analysis complete for {dealership_name}")
        return dashboard
    
    def _update_vehicle_database(self, dealership_id: str, inventory: List[Dict[str, Any]]):
        """Update internal vehicle database with current inventory"""
        
        for vehicle in inventory:
            vin = vehicle.get('vin', '')
            if not vin:
                continue
            
            # Create unique key
            vehicle_key = f"{dealership_id}:{vin}"
            
            # Store vehicle data with timestamp
            vehicle_record = {
                **vehicle,
                'dealership_id': dealership_id,
                'last_updated': datetime.now(),
                'price_history': []
            }
            
            # Update price history
            if vehicle_key in self.vehicle_database:
                existing = self.vehicle_database[vehicle_key]
                vehicle_record['price_history'] = existing.get('price_history', [])
                
                # Add price record if changed
                current_price = vehicle.get('price')
                if current_price and (not existing.get('price') or existing['price'] != current_price):
                    vehicle_record['price_history'].append({
                        'price': current_price,
                        'timestamp': datetime.now()
                    })
            else:
                # First time seeing this vehicle
                current_price = vehicle.get('price')
                if current_price:
                    vehicle_record['price_history'] = [{
                        'price': current_price,
                        'timestamp': datetime.now()
                    }]
            
            self.vehicle_database[vehicle_key] = vehicle_record
    
    def _analyze_market_position(self, 
                               dealership_id: str,
                               dealership_name: str,
                               inventory: List[Dict[str, Any]],
                               market_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze dealership's overall market position"""
        
        # Flatten market data
        all_market_vehicles = []
        for dealer_id, vehicles in market_data.items():
            if dealer_id != dealership_id:  # Exclude self
                all_market_vehicles.extend(vehicles)
        
        if not all_market_vehicles:
            return {'error': 'Insufficient market data for analysis'}
        
        # Analyze pricing position
        pricing_positions = []
        analyzed_vehicles = 0
        
        for vehicle in inventory:
            if not vehicle.get('price'):
                continue
            
            matches = self._find_competitive_matches(vehicle, all_market_vehicles)
            if len(matches) >= self.min_market_samples:
                market_prices = [m['price'] for m in matches if m.get('price')]
                if market_prices:
                    position = self._calculate_pricing_position(vehicle['price'], market_prices)
                    pricing_positions.append(position)
                    analyzed_vehicles += 1
        
        # Calculate summary statistics
        position_counts = defaultdict(int)
        for pos in pricing_positions:
            position_counts[pos.value] += 1
        
        # Overall market position
        if not pricing_positions:
            overall_position = "insufficient_data"
        else:
            # Determine dominant position
            most_common_position = max(position_counts.items(), key=lambda x: x[1])
            overall_position = most_common_position[0]
        
        # Calculate average price vs market
        dealership_prices = [v['price'] for v in inventory if v.get('price')]
        market_prices = [v['price'] for v in all_market_vehicles if v.get('price')]
        
        avg_dealership_price = statistics.mean(dealership_prices) if dealership_prices else 0
        avg_market_price = statistics.mean(market_prices) if market_prices else 0
        
        price_variance = 0
        if avg_market_price > 0:
            price_variance = ((avg_dealership_price - avg_market_price) / avg_market_price) * 100
        
        return {
            'dealership_name': dealership_name,
            'overall_position': overall_position,
            'position_distribution': dict(position_counts),
            'analyzed_vehicles': analyzed_vehicles,
            'total_inventory': len(inventory),
            'analysis_coverage': (analyzed_vehicles / len(inventory)) * 100 if inventory else 0,
            'average_price_variance': price_variance,
            'dealership_avg_price': avg_dealership_price,
            'market_avg_price': avg_market_price,
            'competitive_dealers': len(market_data) - 1
        }
    
    def _identify_pricing_opportunities(self,
                                     dealership_id: str,
                                     inventory: List[Dict[str, Any]],
                                     market_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Identify specific pricing opportunities in inventory"""
        
        opportunities = []
        
        # Flatten market data (excluding self)
        all_market_vehicles = []
        for dealer_id, vehicles in market_data.items():
            if dealer_id != dealership_id:
                all_market_vehicles.extend(vehicles)
        
        for vehicle in inventory:
            if not vehicle.get('price') or not vehicle.get('vin'):
                continue
            
            # Find competitive matches
            matches = self._find_competitive_matches(vehicle, all_market_vehicles)
            
            if len(matches) >= self.min_market_samples:
                market_prices = [m['price'] for m in matches if m.get('price')]
                
                if market_prices:
                    # Calculate market statistics
                    market_stats = self._calculate_market_statistics(market_prices)
                    current_price = vehicle['price']
                    
                    # Determine opportunity type
                    opportunity = self._classify_pricing_opportunity(
                        vehicle, current_price, market_stats, matches
                    )
                    
                    if opportunity:
                        opportunities.append(opportunity)
        
        # Sort by potential impact (revenue opportunity)
        opportunities.sort(key=lambda x: x.get('revenue_impact', 0), reverse=True)
        
        return opportunities[:20]  # Top 20 opportunities
    
    def _find_competitive_matches(self, 
                                target_vehicle: Dict[str, Any], 
                                market_vehicles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find competitive vehicle matches using similarity scoring"""
        
        matches = []
        
        for market_vehicle in market_vehicles:
            similarity = self._calculate_vehicle_similarity(target_vehicle, market_vehicle)
            
            if similarity >= self.similarity_threshold:
                match_data = {
                    **market_vehicle,
                    'similarity_score': similarity
                }
                matches.append(match_data)
        
        # Sort by similarity score
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return matches
    
    def _calculate_vehicle_similarity(self, 
                                    vehicle1: Dict[str, Any], 
                                    vehicle2: Dict[str, Any]) -> float:
        """Calculate similarity score between two vehicles"""
        
        total_score = 0.0
        
        # Make comparison
        make1 = str(vehicle1.get('make', '')).upper()
        make2 = str(vehicle2.get('make', '')).upper()
        if make1 == make2:
            total_score += self.matching_weights['make']
        elif self._is_similar_string(make1, make2):
            total_score += self.matching_weights['make'] * 0.8
        
        # Model comparison
        model1 = str(vehicle1.get('model', '')).upper()
        model2 = str(vehicle2.get('model', '')).upper()
        if model1 == model2:
            total_score += self.matching_weights['model']
        elif self._is_similar_string(model1, model2):
            total_score += self.matching_weights['model'] * 0.9
        
        # Year comparison
        year1 = vehicle1.get('year', 0)
        year2 = vehicle2.get('year', 0)
        if year1 and year2:
            year_diff = abs(year1 - year2)
            if year_diff == 0:
                total_score += self.matching_weights['year']
            elif year_diff == 1:
                total_score += self.matching_weights['year'] * 0.8
            elif year_diff == 2:
                total_score += self.matching_weights['year'] * 0.6
        
        # Trim comparison
        trim1 = str(vehicle1.get('trim', '')).upper()
        trim2 = str(vehicle2.get('trim', '')).upper()
        if trim1 == trim2:
            total_score += self.matching_weights['trim']
        elif self._is_similar_string(trim1, trim2):
            total_score += self.matching_weights['trim'] * 0.7
        
        # Mileage comparison
        mileage1 = vehicle1.get('mileage', 0)
        mileage2 = vehicle2.get('mileage', 0)
        if mileage1 and mileage2:
            mileage_diff_pct = abs(mileage1 - mileage2) / max(mileage1, mileage2)
            if mileage_diff_pct <= 0.1:  # Within 10%
                total_score += self.matching_weights['mileage']
            elif mileage_diff_pct <= 0.25:  # Within 25%
                total_score += self.matching_weights['mileage'] * 0.7
            elif mileage_diff_pct <= 0.5:  # Within 50%
                total_score += self.matching_weights['mileage'] * 0.4
        
        # Condition comparison
        condition1 = str(vehicle1.get('condition', '')).upper()
        condition2 = str(vehicle2.get('condition', '')).upper()
        if condition1 == condition2:
            total_score += self.matching_weights['condition']
        
        return min(1.0, total_score)
    
    def _is_similar_string(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are similar using difflib"""
        if not str1 or not str2:
            return False
        
        similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
        return similarity >= threshold
    
    def _calculate_pricing_position(self, vehicle_price: float, market_prices: List[float]) -> PricingPosition:
        """Determine pricing position relative to market"""
        
        if not market_prices:
            return PricingPosition.MARKET_COMPETITIVE
        
        market_median = statistics.median(market_prices)
        
        if market_median == 0:
            return PricingPosition.MARKET_COMPETITIVE
        
        variance = ((vehicle_price - market_median) / market_median) * 100
        
        if variance < -15:
            return PricingPosition.SIGNIFICANTLY_BELOW
        elif variance < -5:
            return PricingPosition.BELOW_MARKET
        elif variance <= 5:
            return PricingPosition.MARKET_COMPETITIVE
        elif variance <= 15:
            return PricingPosition.ABOVE_MARKET
        else:
            return PricingPosition.SIGNIFICANTLY_ABOVE
    
    def _calculate_market_statistics(self, prices: List[float]) -> Dict[str, float]:
        """Calculate comprehensive market statistics"""
        
        if not prices:
            return {}
        
        return {
            'min': min(prices),
            'max': max(prices),
            'mean': statistics.mean(prices),
            'median': statistics.median(prices),
            'std': statistics.stdev(prices) if len(prices) > 1 else 0,
            'q1': np.percentile(prices, 25),
            'q3': np.percentile(prices, 75),
            'count': len(prices)
        }
    
    def _classify_pricing_opportunity(self,
                                    vehicle: Dict[str, Any],
                                    current_price: float,
                                    market_stats: Dict[str, float],
                                    competitive_matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Classify and quantify pricing opportunity"""
        
        if not market_stats:
            return None
        
        market_median = market_stats['median']
        market_mean = market_stats['mean']
        
        # Calculate potential adjustments
        variance_from_median = ((current_price - market_median) / market_median) * 100
        variance_from_mean = ((current_price - market_mean) / market_mean) * 100
        
        opportunity = None
        
        # Overpriced vehicle - opportunity to reduce for faster sale
        if variance_from_median > 10:
            recommended_price = market_median * 1.02  # 2% above median for competitive edge
            potential_reduction = current_price - recommended_price
            
            opportunity = {
                'type': 'price_reduction',
                'vehicle': {
                    'vin': vehicle.get('vin'),
                    'year': vehicle.get('year'),
                    'make': vehicle.get('make'),
                    'model': vehicle.get('model'),
                    'trim': vehicle.get('trim')
                },
                'current_price': current_price,
                'recommended_price': recommended_price,
                'price_adjustment': -potential_reduction,
                'adjustment_percentage': (potential_reduction / current_price) * 100,
                'market_position': 'above_market',
                'justification': f"Vehicle priced {variance_from_median:.1f}% above market median",
                'expected_outcome': 'faster_turnover',
                'revenue_impact': -potential_reduction,  # Revenue reduction but faster sale
                'market_stats': market_stats,
                'competitive_count': len(competitive_matches)
            }
        
        # Underpriced vehicle - opportunity to increase margin
        elif variance_from_median < -5:
            recommended_price = market_median * 0.98  # 2% below median for competitive pricing
            potential_increase = recommended_price - current_price
            
            if potential_increase > 500:  # Only if meaningful increase
                opportunity = {
                    'type': 'price_increase',
                    'vehicle': {
                        'vin': vehicle.get('vin'),
                        'year': vehicle.get('year'),
                        'make': vehicle.get('make'),
                        'model': vehicle.get('model'),
                        'trim': vehicle.get('trim')
                    },
                    'current_price': current_price,
                    'recommended_price': recommended_price,
                    'price_adjustment': potential_increase,
                    'adjustment_percentage': (potential_increase / current_price) * 100,
                    'market_position': 'below_market',
                    'justification': f"Vehicle priced {abs(variance_from_median):.1f}% below market median",
                    'expected_outcome': 'increased_margin',
                    'revenue_impact': potential_increase,
                    'market_stats': market_stats,
                    'competitive_count': len(competitive_matches)
                }
        
        # Market anomaly - significantly different from competition
        elif market_stats['std'] > 0 and abs(variance_from_mean) > 20:
            opportunity = {
                'type': 'market_anomaly',
                'vehicle': {
                    'vin': vehicle.get('vin'),
                    'year': vehicle.get('year'),
                    'make': vehicle.get('make'),
                    'model': vehicle.get('model'),
                    'trim': vehicle.get('trim')
                },
                'current_price': current_price,
                'market_position': 'anomaly',
                'variance_from_mean': variance_from_mean,
                'justification': f"Vehicle pricing significantly different from market average",
                'expected_outcome': 'review_required',
                'revenue_impact': 0,
                'market_stats': market_stats,
                'competitive_count': len(competitive_matches)
            }
        
        return opportunity
    
    def _generate_competitor_insights(self,
                                    dealership_id: str,
                                    dealership_name: str,
                                    market_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate insights about competitor strategies"""
        
        insights = []
        
        for competitor_id, competitor_inventory in market_data.items():
            if competitor_id == dealership_id:
                continue
            
            # Get competitor name
            competitor_name = "Unknown Competitor"
            if competitor_inventory:
                competitor_name = competitor_inventory[0].get('dealer_name', competitor_id)
            
            # Analyze competitor's pricing strategy
            competitor_prices = [v['price'] for v in competitor_inventory if v.get('price')]
            
            if competitor_prices:
                insight = {
                    'competitor_id': competitor_id,
                    'competitor_name': competitor_name,
                    'inventory_size': len(competitor_inventory),
                    'price_statistics': self._calculate_market_statistics(competitor_prices),
                    'pricing_strategy': self._analyze_pricing_strategy(competitor_inventory),
                    'brand_focus': self._analyze_brand_focus(competitor_inventory),
                    'competitive_threat_level': self._assess_competitive_threat(
                        dealership_id, competitor_inventory, market_data
                    )
                }
                insights.append(insight)
        
        # Sort by competitive threat level
        insights.sort(key=lambda x: x['competitive_threat_level'], reverse=True)
        
        return insights
    
    def _analyze_pricing_strategy(self, inventory: List[Dict[str, Any]]) -> str:
        """Analyze a competitor's pricing strategy"""
        
        prices = [v['price'] for v in inventory if v.get('price')]
        
        if not prices:
            return "unknown"
        
        # Calculate price distribution
        mean_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        
        # Categorize based on price range
        if mean_price > 50000:
            if median_price / mean_price > 0.9:
                return "premium_consistent"
            else:
                return "premium_mixed"
        elif mean_price > 25000:
            return "mid_market"
        else:
            return "value_focused"
    
    def _analyze_brand_focus(self, inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze competitor's brand focus"""
        
        brand_counts = defaultdict(int)
        total_vehicles = len(inventory)
        
        for vehicle in inventory:
            make = vehicle.get('make', 'Unknown')
            brand_counts[make] += 1
        
        # Calculate brand distribution
        brand_distribution = {
            brand: count / total_vehicles * 100
            for brand, count in brand_counts.items()
        }
        
        # Identify primary brands (>20% of inventory)
        primary_brands = [
            brand for brand, percentage in brand_distribution.items()
            if percentage > 20
        ]
        
        return {
            'brand_distribution': dict(brand_distribution),
            'primary_brands': primary_brands,
            'brand_diversity': len(brand_counts),
            'specialization_level': max(brand_distribution.values()) if brand_distribution else 0
        }
    
    def _assess_competitive_threat(self,
                                 dealership_id: str,
                                 competitor_inventory: List[Dict[str, Any]],
                                 market_data: Dict[str, List[Dict[str, Any]]]) -> float:
        """Assess competitive threat level (0-1 scale)"""
        
        # Get our inventory
        our_inventory = market_data.get(dealership_id, [])
        
        if not our_inventory or not competitor_inventory:
            return 0.0
        
        threat_score = 0.0
        
        # Factor 1: Inventory size comparison
        size_ratio = len(competitor_inventory) / len(our_inventory)
        threat_score += min(size_ratio * 0.2, 0.3)  # Max 0.3 points
        
        # Factor 2: Price competition
        our_prices = [v['price'] for v in our_inventory if v.get('price')]
        competitor_prices = [v['price'] for v in competitor_inventory if v.get('price')]
        
        if our_prices and competitor_prices:
            our_avg = statistics.mean(our_prices)
            competitor_avg = statistics.mean(competitor_prices)
            
            if competitor_avg < our_avg:  # They're cheaper
                price_advantage = (our_avg - competitor_avg) / our_avg
                threat_score += min(price_advantage * 0.4, 0.4)  # Max 0.4 points
        
        # Factor 3: Vehicle overlap
        overlap_score = self._calculate_inventory_overlap(our_inventory, competitor_inventory)
        threat_score += overlap_score * 0.3  # Max 0.3 points
        
        return min(1.0, threat_score)
    
    def _calculate_inventory_overlap(self, 
                                   inventory1: List[Dict[str, Any]], 
                                   inventory2: List[Dict[str, Any]]) -> float:
        """Calculate overlap between two inventories"""
        
        # Create sets of vehicle signatures
        def create_signature(vehicle):
            return f"{vehicle.get('make', '')}_{vehicle.get('model', '')}_{vehicle.get('year', '')}"
        
        signatures1 = set(create_signature(v) for v in inventory1)
        signatures2 = set(create_signature(v) for v in inventory2)
        
        if not signatures1:
            return 0.0
        
        overlap = len(signatures1.intersection(signatures2))
        return overlap / len(signatures1)
    
    def _analyze_market_trends(self, market_data: Dict[str, List[Dict[str, Any]]]) -> List[MarketTrend]:
        """Analyze market trends across all dealerships"""
        
        trends = []
        
        # Flatten all market data
        all_vehicles = []
        for vehicles in market_data.values():
            all_vehicles.extend(vehicles)
        
        # Overall market trend
        overall_trend = self._calculate_overall_trend(all_vehicles)
        if overall_trend:
            trends.append(overall_trend)
        
        # Brand-specific trends
        brand_trends = self._calculate_brand_trends(all_vehicles)
        trends.extend(brand_trends)
        
        # Price range trends
        price_range_trends = self._calculate_price_range_trends(all_vehicles)
        trends.extend(price_range_trends)
        
        return trends
    
    def _calculate_overall_trend(self, vehicles: List[Dict[str, Any]]) -> Optional[MarketTrend]:
        """Calculate overall market trend"""
        
        # For now, analyze current vs historical data if available
        # This would be enhanced with actual historical data storage
        
        current_prices = [v['price'] for v in vehicles if v.get('price')]
        current_inventory_size = len(vehicles)
        
        if not current_prices:
            return None
        
        avg_price = statistics.mean(current_prices)
        
        # Placeholder trend analysis
        # In a real implementation, this would compare against historical data
        return MarketTrend(
            trend_period="30_days",
            direction=TrendDirection.STABLE,
            price_change_percentage=0.0,
            volume_change_percentage=0.0,
            key_factors=["Insufficient historical data for trend analysis"],
            confidence=0.3
        )
    
    def _calculate_brand_trends(self, vehicles: List[Dict[str, Any]]) -> List[MarketTrend]:
        """Calculate brand-specific trends"""
        
        # Group by brand
        brand_data = defaultdict(list)
        for vehicle in vehicles:
            make = vehicle.get('make', 'Unknown')
            if vehicle.get('price'):
                brand_data[make].append(vehicle)
        
        trends = []
        
        for brand, brand_vehicles in brand_data.items():
            if len(brand_vehicles) >= 5:  # Minimum sample size
                brand_prices = [v['price'] for v in brand_vehicles]
                avg_price = statistics.mean(brand_prices)
                
                # Placeholder brand trend
                trend = MarketTrend(
                    trend_period=f"{brand}_current",
                    direction=TrendDirection.STABLE,
                    price_change_percentage=0.0,
                    volume_change_percentage=0.0,
                    key_factors=[f"{len(brand_vehicles)} vehicles available", f"Average price: ${avg_price:,.0f}"],
                    confidence=0.5
                )
                trends.append(trend)
        
        return trends[:5]  # Top 5 brands
    
    def _calculate_price_range_trends(self, vehicles: List[Dict[str, Any]]) -> List[MarketTrend]:
        """Calculate trends by price range"""
        
        price_ranges = {
            'budget': (0, 20000),
            'mid_market': (20000, 50000),
            'premium': (50000, 100000),
            'luxury': (100000, float('inf'))
        }
        
        trends = []
        
        for range_name, (min_price, max_price) in price_ranges.items():
            range_vehicles = [
                v for v in vehicles 
                if v.get('price') and min_price <= v['price'] < max_price
            ]
            
            if range_vehicles:
                trend = MarketTrend(
                    trend_period=f"{range_name}_segment",
                    direction=TrendDirection.STABLE,
                    price_change_percentage=0.0,
                    volume_change_percentage=0.0,
                    key_factors=[f"{len(range_vehicles)} vehicles in ${min_price:,}-${max_price:,} range"],
                    confidence=0.4
                )
                trends.append(trend)
        
        return trends
    
    def _generate_pricing_recommendations(self,
                                        market_position: Dict[str, Any],
                                        opportunities: List[Dict[str, Any]],
                                        trends: List[MarketTrend]) -> List[str]:
        """Generate actionable pricing recommendations"""
        
        recommendations = []
        
        # Market position recommendations
        overall_position = market_position.get('overall_position', '')
        
        if overall_position == 'significantly_above':
            recommendations.append(
                "🔴 CRITICAL: Overall pricing is significantly above market. "
                "Consider strategic price reductions to improve competitiveness."
            )
        elif overall_position == 'above_market':
            recommendations.append(
                "🟡 WARNING: Pricing is above market average. "
                "Review high-priority vehicles for potential price adjustments."
            )
        elif overall_position == 'significantly_below':
            recommendations.append(
                "💰 OPPORTUNITY: Pricing is significantly below market. "
                "Consider selective price increases to improve margins."
            )
        
        # Coverage recommendations
        coverage = market_position.get('analysis_coverage', 0)
        if coverage < 60:
            recommendations.append(
                f"📊 DATA: Only {coverage:.0f}% of inventory has competitive data. "
                "Consider expanding market data collection for better insights."
            )
        
        # Opportunity-based recommendations
        if opportunities:
            high_impact_opportunities = [o for o in opportunities[:5] if abs(o.get('revenue_impact', 0)) > 1000]
            
            if high_impact_opportunities:
                total_impact = sum(o.get('revenue_impact', 0) for o in high_impact_opportunities)
                recommendations.append(
                    f"💡 PRIORITY: {len(high_impact_opportunities)} high-impact pricing opportunities "
                    f"identified with potential ${abs(total_impact):,.0f} revenue impact."
                )
        
        # Trend-based recommendations
        for trend in trends[:3]:  # Top 3 trends
            if trend.confidence > 0.7:
                if trend.direction == TrendDirection.DECREASING:
                    recommendations.append(
                        f"📉 TREND: {trend.trend_period} shows declining prices. "
                        "Consider adjusting pricing strategy accordingly."
                    )
                elif trend.direction == TrendDirection.INCREASING:
                    recommendations.append(
                        f"📈 TREND: {trend.trend_period} shows rising prices. "
                        "Opportunity to increase margins on similar vehicles."
                    )
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append(
                "✅ STABLE: Current pricing appears competitive with market conditions. "
                "Continue monitoring for changes."
            )
        
        return recommendations
    
    def analyze_dealership_pricing(self, dealership_name: str, vehicles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Simplified method for analyzing dealership pricing against market
        Returns list of competitive insights
        """
        
        try:
            insights = []
            
            for vehicle in vehicles[:10]:  # Limit to first 10 vehicles for performance
                try:
                    # Generate basic competitive insight
                    insight = {
                        'vin': vehicle.get('vin', 'Unknown'),
                        'vehicle_info': f"{vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}",
                        'current_price': vehicle.get('price', 0),
                        'market_position': 'competitive',  # Default
                        'insight_text': f"Competitive analysis for {vehicle.get('make', 'Unknown')} {vehicle.get('model', 'Unknown')}",
                        'priority': 'medium',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Simulate market comparison (in real implementation would compare against actual market data)
                    base_price = vehicle.get('price', 50000)
                    if base_price > 75000:
                        insight['market_position'] = 'above_market'
                        insight['insight_text'] = f"High-value vehicle - monitor luxury market positioning"
                        insight['priority'] = 'high'
                    elif base_price < 25000:
                        insight['market_position'] = 'below_market'
                        insight['insight_text'] = f"Value-priced vehicle - competitive advantage"
                    
                    insights.append(insight)
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing vehicle {vehicle.get('vin', 'Unknown')}: {str(e)}")
                    continue
            
            self.logger.info(f"Generated {len(insights)} competitive insights for {dealership_name}")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error in dealership pricing analysis: {str(e)}")
            return []
    
    def analyze_cross_dealership_competition(self, dealership_id: str, vehicles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze competition across multiple dealerships
        Returns cross-dealership competitive insights
        """
        
        return self.analyze_dealership_pricing(f"Dealership {dealership_id}", vehicles)
    
    def _generate_pricing_alerts(self,
                               dealership_id: str,
                               dealership_name: str,
                               dashboard: CompetitiveDashboard):
        """Generate pricing alerts based on analysis results"""
        
        if not self.alert_system:
            return
        
        # Critical pricing position alert
        overall_position = dashboard.market_position_summary.get('overall_position', '')
        
        if overall_position in ['significantly_above', 'significantly_below']:
            priority = AlertPriority.HIGH if overall_position == 'significantly_above' else AlertPriority.MEDIUM
            
            alert = InventoryAlert(
                alert_id=f"pricing_{dealership_id}_{int(datetime.now().timestamp())}",
                alert_type=AlertType.COMPETITOR_ALERT,
                priority=priority,
                dealership_name=dealership_name,
                dealership_id=dealership_id,
                title=f"Pricing Position Alert: {overall_position.replace('_', ' ').title()}",
                message=f"Dealership pricing is {overall_position.replace('_', ' ')} compared to market",
                details={
                    'market_position': dashboard.market_position_summary,
                    'top_opportunities': dashboard.pricing_opportunities[:5],
                    'analysis_timestamp': dashboard.analysis_date.isoformat()
                },
                created_at=datetime.now(),
                channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD]
            )
            
            # Process alert through existing alert system
            self.alert_system._process_alerts([alert])
    
    def export_competitive_report(self, dashboard: CompetitiveDashboard, format: str = 'json') -> str:
        """Export competitive analysis report in specified format"""
        
        if format == 'json':
            return json.dumps({
                'dealership_name': dashboard.dealership_name,
                'analysis_date': dashboard.analysis_date.isoformat(),
                'market_position_summary': dashboard.market_position_summary,
                'pricing_opportunities': dashboard.pricing_opportunities,
                'competitor_insights': dashboard.competitor_insights,
                'market_trends': [
                    {
                        'trend_period': t.trend_period,
                        'direction': t.direction.value,
                        'price_change_percentage': t.price_change_percentage,
                        'volume_change_percentage': t.volume_change_percentage,
                        'key_factors': t.key_factors,
                        'confidence': t.confidence
                    } for t in dashboard.market_trends
                ],
                'recommendations': dashboard.recommendations
            }, indent=2)
        
        elif format == 'csv':
            # Export opportunities as CSV
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'VIN', 'Year', 'Make', 'Model', 'Current_Price', 
                'Recommended_Price', 'Adjustment', 'Opportunity_Type', 'Revenue_Impact'
            ])
            
            # Write opportunities
            for opp in dashboard.pricing_opportunities:
                vehicle = opp.get('vehicle', {})
                writer.writerow([
                    vehicle.get('vin', ''),
                    vehicle.get('year', ''),
                    vehicle.get('make', ''),
                    vehicle.get('model', ''),
                    opp.get('current_price', ''),
                    opp.get('recommended_price', ''),
                    opp.get('price_adjustment', ''),
                    opp.get('type', ''),
                    opp.get('revenue_impact', '')
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Factory functions

def create_competitive_analyzer(config: Dict[str, Any]) -> CompetitivePricingAnalyzer:
    """Create configured competitive pricing analyzer"""
    
    default_config = {
        'similarity_threshold': 0.85,
        'price_variance_threshold': 0.05,
        'trend_analysis_days': 30,
        'min_market_samples': 3,
        'enable_alerts': True,
        'alert_config': {}
    }
    
    merged_config = {**default_config, **config}
    return CompetitivePricingAnalyzer(merged_config)

def analyze_market_competition(dealership_inventories: Dict[str, List[Dict[str, Any]]],
                             config: Optional[Dict[str, Any]] = None) -> Dict[str, CompetitiveDashboard]:
    """Analyze competition across multiple dealerships"""
    
    analyzer = create_competitive_analyzer(config or {})
    dashboards = {}
    
    for dealership_id, inventory in dealership_inventories.items():
        dealership_name = inventory[0].get('dealer_name', dealership_id) if inventory else dealership_id
        
        # Create market data excluding current dealership
        market_data = {k: v for k, v in dealership_inventories.items()}
        
        dashboard = analyzer.analyze_dealership_inventory(
            dealership_id, dealership_name, inventory, market_data
        )
        
        dashboards[dealership_id] = dashboard
    
    return dashboards