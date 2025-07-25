#!/usr/bin/env python3
"""
Grafana Dashboard Generator for Silver Fox Scraper System
========================================================

Automatically generates comprehensive Grafana dashboards for monitoring
the Silver Fox scraper system with business intelligence insights.

Author: Claude (Silver Fox Assistant)
Created: July 2025
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import os


class GrafanaDashboardGenerator:
    """Generates and manages Grafana dashboards"""
    
    def __init__(self, grafana_url: str, api_key: str):
        self.grafana_url = grafana_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.logger = logging.getLogger(f"{__name__}.GrafanaDashboardGenerator")
    
    def create_silverfox_system_dashboard(self) -> Dict[str, Any]:
        """Create the main Silver Fox system monitoring dashboard"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "Silver Fox Scraper System - Overview",
                "tags": ["silverfox", "scrapers", "overview"],
                "timezone": "browser",
                "panels": [
                    self._create_system_health_panel(),
                    self._create_scraper_status_panel(),
                    self._create_inventory_summary_panel(),
                    self._create_error_rate_panel(),
                    self._create_response_time_panel(),
                    self._create_resource_usage_panel(),
                    self._create_alert_summary_panel(),
                    self._create_dealership_performance_panel()
                ],
                "time": {
                    "from": "now-24h",
                    "to": "now"
                },
                "timepicker": {},
                "templating": {
                    "list": [
                        self._create_dealership_template(),
                        self._create_scraper_type_template()
                    ]
                },
                "annotations": {
                    "list": [
                        self._create_alert_annotations()
                    ]
                },
                "refresh": "30s",
                "schemaVersion": 27,
                "version": 1,
                "links": []
            },
            "folderId": 0,
            "overwrite": True
        }
        
        return dashboard
    
    def create_business_intelligence_dashboard(self) -> Dict[str, Any]:
        """Create business intelligence dashboard for executives"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "Silver Fox Business Intelligence",
                "tags": ["silverfox", "business", "intelligence"],
                "timezone": "browser",
                "panels": [
                    self._create_total_inventory_panel(),
                    self._create_inventory_by_dealership_panel(),
                    self._create_inventory_trends_panel(),
                    self._create_competitive_pricing_panel(),
                    self._create_price_alerts_panel(),
                    self._create_inventory_turnover_panel(),
                    self._create_market_share_panel(),
                    self._create_revenue_opportunity_panel()
                ],
                "time": {
                    "from": "now-7d",
                    "to": "now"
                },
                "timepicker": {},
                "templating": {
                    "list": [
                        self._create_dealership_template(),
                        self._create_vehicle_type_template()
                    ]
                },
                "refresh": "5m",
                "schemaVersion": 27,
                "version": 1,
                "links": []
            },
            "folderId": 0,
            "overwrite": True
        }
        
        return dashboard
    
    def create_technical_dashboard(self) -> Dict[str, Any]:
        """Create detailed technical dashboard for developers"""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "Silver Fox Technical Monitoring",
                "tags": ["silverfox", "technical", "monitoring"],
                "timezone": "browser",
                "panels": [
                    self._create_kubernetes_resources_panel(),
                    self._create_pod_status_panel(),
                    self._create_redis_metrics_panel(),
                    self._create_api_performance_panel(),
                    self._create_chrome_metrics_panel(),
                    self._create_network_metrics_panel(),
                    self._create_log_analysis_panel(),
                    self._create_custom_metrics_panel()
                ],
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "timepicker": {},
                "templating": {
                    "list": [
                        self._create_namespace_template(),
                        self._create_pod_template()
                    ]
                },
                "refresh": "15s",
                "schemaVersion": 27,
                "version": 1,
                "links": []
            },
            "folderId": 0,
            "overwrite": True
        }
        
        return dashboard
    
    def _create_system_health_panel(self) -> Dict[str, Any]:
        """Create system health overview panel"""
        return {
            "id": 1,
            "title": "System Health Overview",
            "type": "stat",
            "targets": [
                {
                    "expr": "up{job=~\"silverfox-.*\"}",
                    "legendFormat": "{{job}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "fieldConfig": {
                "defaults": {
                    "mappings": [
                        {"options": {"0": {"text": "DOWN"}}, "type": "value"},
                        {"options": {"1": {"text": "UP"}}, "type": "value"}
                    ],
                    "thresholds": {
                        "steps": [
                            {"color": "red", "value": 0},
                            {"color": "green", "value": 1}
                        ]
                    }
                }
            },
            "options": {
                "colorMode": "background",
                "graphMode": "none",
                "justifyMode": "center",
                "orientation": "horizontal"
            }
        }
    
    def _create_scraper_status_panel(self) -> Dict[str, Any]:
        """Create scraper status panel"""
        return {
            "id": 2,
            "title": "Scraper Status by Dealership",
            "type": "table",
            "targets": [
                {
                    "expr": "silverfox_scraper_last_success_timestamp",
                    "legendFormat": "{{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "displayMode": "table",
                        "filterable": True
                    }
                }
            },
            "transformations": [
                {
                    "id": "organize",
                    "options": {
                        "excludeByName": {},
                        "indexByName": {},
                        "renameByName": {
                            "dealership": "Dealership",
                            "Value": "Last Success"
                        }
                    }
                }
            ]
        }
    
    def _create_inventory_summary_panel(self) -> Dict[str, Any]:
        """Create inventory summary panel"""
        return {
            "id": 3,
            "title": "Total Inventory Count",
            "type": "stat",
            "targets": [
                {
                    "expr": "sum(silverfox_total_inventory_count)",
                    "legendFormat": "Total Vehicles"
                }
            ],
            "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
            "fieldConfig": {
                "defaults": {
                    "unit": "short",
                    "thresholds": {
                        "steps": [
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 100},
                            {"color": "green", "value": 500}
                        ]
                    }
                }
            },
            "options": {
                "colorMode": "value",
                "graphMode": "area",
                "justifyMode": "center",
                "orientation": "horizontal"
            }
        }
    
    def _create_error_rate_panel(self) -> Dict[str, Any]:
        """Create error rate panel"""
        return {
            "id": 4,
            "title": "Error Rate",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "rate(silverfox_scraper_errors_total[5m])",
                    "legendFormat": "{{dealership}} - {{error_type}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 6, "y": 8},
            "fieldConfig": {
                "defaults": {
                    "unit": "percentunit",
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "linear",
                        "lineWidth": 1,
                        "fillOpacity": 0.1,
                        "gradientMode": "none",
                        "spanNulls": False,
                        "insertNulls": False,
                        "showPoints": "auto",
                        "pointSize": 5,
                        "stacking": {"mode": "none", "group": "A"},
                        "axisPlacement": "auto",
                        "axisLabel": "",
                        "scaleDistribution": {"type": "linear"},
                        "hideFrom": {"legend": False, "tooltip": False, "vis": False},
                        "thresholdsStyle": {"mode": "off"}
                    },
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.05},
                            {"color": "red", "value": 0.1}
                        ]
                    }
                }
            }
        }
    
    def _create_response_time_panel(self) -> Dict[str, Any]:
        """Create response time panel"""
        return {
            "id": 5,
            "title": "Scraper Response Times",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "silverfox_scraper_duration_seconds",
                    "legendFormat": "{{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 18, "y": 8},
            "fieldConfig": {
                "defaults": {
                    "unit": "s",
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "linear",
                        "lineWidth": 1,
                        "fillOpacity": 0.1,
                        "gradientMode": "none"
                    },
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 60},
                            {"color": "red", "value": 300}
                        ]
                    }
                }
            }
        }
    
    def _create_total_inventory_panel(self) -> Dict[str, Any]:
        """Create total inventory panel for business dashboard"""
        return {
            "id": 10,
            "title": "Total Vehicle Inventory",
            "type": "stat",
            "targets": [
                {
                    "expr": "sum(silverfox_total_inventory_count) by (dealership)",
                    "legendFormat": "{{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
            "fieldConfig": {
                "defaults": {
                    "unit": "short",
                    "displayName": "Vehicles",
                    "thresholds": {
                        "steps": [
                            {"color": "red", "value": 0},
                            {"color": "yellow", "value": 50},
                            {"color": "green", "value": 200}
                        ]
                    }
                }
            },
            "options": {
                "colorMode": "value",
                "graphMode": "area",
                "justifyMode": "center"
            }
        }
    
    def _create_competitive_pricing_panel(self) -> Dict[str, Any]:
        """Create competitive pricing analysis panel"""
        return {
            "id": 11,
            "title": "Competitive Price Differences",
            "type": "bargauge",
            "targets": [
                {
                    "expr": "silverfox_competitive_price_difference_percent",
                    "legendFormat": "{{dealership}} - {{vehicle_model}}"
                }
            ],
            "gridPos": {"h": 8, "w": 16, "x": 8, "y": 0},
            "fieldConfig": {
                "defaults": {
                    "unit": "percent",
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": -10},
                            {"color": "yellow", "value": 0},
                            {"color": "red", "value": 10}
                        ]
                    }
                }
            },
            "options": {
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"],
                    "fields": ""
                },
                "orientation": "horizontal",
                "displayMode": "gradient"
            }
        }
    
    def _create_dealership_template(self) -> Dict[str, Any]:
        """Create dealership variable template"""
        return {
            "current": {
                "selected": False,
                "text": "All",
                "value": "$__all"
            },
            "datasource": "Prometheus",
            "definition": "label_values(silverfox_total_inventory_count, dealership)",
            "hide": 0,
            "includeAll": True,
            "label": "Dealership",
            "multi": True,
            "name": "dealership",
            "options": [],
            "query": {
                "query": "label_values(silverfox_total_inventory_count, dealership)",
                "refId": "Prometheus-dealership-Variable-Query"
            },
            "refresh": 1,
            "regex": "",
            "skipUrlSync": False,
            "sort": 1,
            "type": "query"
        }
    
    def _create_scraper_type_template(self) -> Dict[str, Any]:
        """Create scraper type variable template"""
        return {
            "current": {
                "selected": False,
                "text": "All",
                "value": "$__all"
            },
            "datasource": "Prometheus",
            "definition": "label_values(up{job=~\"silverfox-.*\"}, job)",
            "hide": 0,
            "includeAll": True,
            "label": "Scraper Type",
            "multi": True,
            "name": "scraper_type",
            "options": [],
            "query": {
                "query": "label_values(up{job=~\"silverfox-.*\"}, job)",
                "refId": "Prometheus-scraper-type-Variable-Query"
            },
            "refresh": 1,
            "regex": "",
            "skipUrlSync": False,
            "sort": 1,
            "type": "query"
        }
    
    def _create_vehicle_type_template(self) -> Dict[str, Any]:
        """Create vehicle type variable template"""
        return {
            "current": {
                "selected": False,
                "text": "All",
                "value": "$__all"
            },
            "datasource": "Prometheus",
            "definition": "label_values(silverfox_vehicles_by_type, vehicle_type)",
            "hide": 0,
            "includeAll": True,
            "label": "Vehicle Type",
            "multi": True,
            "name": "vehicle_type",
            "options": [],
            "query": {
                "query": "label_values(silverfox_vehicles_by_type, vehicle_type)",
                "refId": "Prometheus-vehicle-type-Variable-Query"
            },
            "refresh": 1,
            "regex": "",
            "skipUrlSync": False,
            "sort": 1,
            "type": "query"
        }
    
    def _create_namespace_template(self) -> Dict[str, Any]:
        """Create Kubernetes namespace template"""
        return {
            "current": {
                "selected": True,
                "text": "silverfox-scrapers",
                "value": "silverfox-scrapers"
            },
            "datasource": "Prometheus",
            "definition": "label_values(kube_namespace_created, namespace)",
            "hide": 0,
            "includeAll": False,
            "label": "Namespace",
            "multi": False,
            "name": "namespace",
            "options": [],
            "query": {
                "query": "label_values(kube_namespace_created, namespace)",
                "refId": "Prometheus-namespace-Variable-Query"
            },
            "refresh": 1,
            "regex": "silverfox.*",
            "skipUrlSync": False,
            "sort": 1,
            "type": "query"
        }
    
    def _create_pod_template(self) -> Dict[str, Any]:
        """Create Kubernetes pod template"""
        return {
            "current": {
                "selected": False,
                "text": "All",
                "value": "$__all"
            },
            "datasource": "Prometheus",
            "definition": "label_values(kube_pod_info{namespace=\"$namespace\"}, pod)",
            "hide": 0,
            "includeAll": True,
            "label": "Pod",
            "multi": True,
            "name": "pod",
            "options": [],
            "query": {
                "query": "label_values(kube_pod_info{namespace=\"$namespace\"}, pod)",
                "refId": "Prometheus-pod-Variable-Query"
            },
            "refresh": 1,
            "regex": "",
            "skipUrlSync": False,
            "sort": 1,
            "type": "query"
        }
    
    def _create_alert_annotations(self) -> Dict[str, Any]:
        """Create alert annotations"""
        return {
            "builtIn": 1,
            "datasource": "Prometheus",
            "enable": True,
            "hide": True,
            "iconColor": "rgba(0, 211, 255, 1)",
            "name": "Annotations & Alerts",
            "type": "dashboard"
        }
    
    def _create_resource_usage_panel(self) -> Dict[str, Any]:
        """Create resource usage panel"""
        return {
            "id": 6,
            "title": "Resource Usage",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "rate(container_cpu_usage_seconds_total{pod=~\"silverfox-.*\"}[5m])",
                    "legendFormat": "CPU - {{pod}}"
                },
                {
                    "expr": "container_memory_working_set_bytes{pod=~\"silverfox-.*\"} / 1024 / 1024",
                    "legendFormat": "Memory MB - {{pod}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "linear"
                    }
                }
            }
        }
    
    def _create_alert_summary_panel(self) -> Dict[str, Any]:
        """Create alert summary panel"""
        return {
            "id": 7,
            "title": "Active Alerts",
            "type": "table",
            "targets": [
                {
                    "expr": "ALERTS{alertstate=\"firing\"}",
                    "legendFormat": "{{alertname}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "displayMode": "table"
                    }
                }
            }
        }
    
    def _create_dealership_performance_panel(self) -> Dict[str, Any]:
        """Create dealership performance comparison panel"""
        return {
            "id": 8,
            "title": "Dealership Performance Comparison",
            "type": "barchart",
            "targets": [
                {
                    "expr": "silverfox_vehicles_scraped_total",
                    "legendFormat": "{{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24},
            "fieldConfig": {
                "defaults": {
                    "unit": "short",
                    "custom": {
                        "axisPlacement": "auto",
                        "axisLabel": "Vehicles Scraped",
                        "scaleDistribution": {"type": "linear"}
                    }
                }
            }
        }
    
    def _create_inventory_by_dealership_panel(self) -> Dict[str, Any]:
        """Create inventory by dealership panel"""
        return {
            "id": 12,
            "title": "Inventory by Dealership",
            "type": "piechart",
            "targets": [
                {
                    "expr": "silverfox_total_inventory_count",
                    "legendFormat": "{{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
            "fieldConfig": {
                "defaults": {
                    "unit": "short",
                    "custom": {
                        "hideFrom": {
                            "tooltip": False,
                            "vis": False,
                            "legend": False
                        }
                    }
                }
            },
            "options": {
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"]
                },
                "pieType": "pie",
                "tooltip": {"mode": "single"}
            }
        }
    
    def _create_inventory_trends_panel(self) -> Dict[str, Any]:
        """Create inventory trends panel"""
        return {
            "id": 13,
            "title": "Inventory Trends (7 Days)",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "silverfox_total_inventory_count",
                    "legendFormat": "{{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
            "fieldConfig": {
                "defaults": {
                    "unit": "short",
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "smooth",
                        "lineWidth": 2,
                        "fillOpacity": 0.1,
                        "gradientMode": "opacity"
                    }
                }
            }
        }
    
    def _create_kubernetes_resources_panel(self) -> Dict[str, Any]:
        """Create Kubernetes resources panel"""
        return {
            "id": 20,
            "title": "Kubernetes Resources",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "kube_pod_container_resource_requests{namespace=\"$namespace\", resource=\"cpu\"}",
                    "legendFormat": "CPU Requests - {{pod}}"
                },
                {
                    "expr": "kube_pod_container_resource_limits{namespace=\"$namespace\", resource=\"memory\"}",
                    "legendFormat": "Memory Limits - {{pod}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
        }
    
    def _create_pod_status_panel(self) -> Dict[str, Any]:
        """Create pod status panel"""
        return {
            "id": 21,
            "title": "Pod Status",
            "type": "table",
            "targets": [
                {
                    "expr": "kube_pod_status_phase{namespace=\"$namespace\"}",
                    "legendFormat": "{{pod}} - {{phase}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
        }
    
    def _create_redis_metrics_panel(self) -> Dict[str, Any]:
        """Create Redis metrics panel"""
        return {
            "id": 22,
            "title": "Redis Performance",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "redis_connected_clients",
                    "legendFormat": "Connected Clients"
                },
                {
                    "expr": "redis_memory_used_bytes / 1024 / 1024",
                    "legendFormat": "Memory Used (MB)"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
        }
    
    def _create_api_performance_panel(self) -> Dict[str, Any]:
        """Create API performance panel"""
        return {
            "id": 23,
            "title": "API Performance",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "silverfox_api_requests_total",
                    "legendFormat": "{{method}} {{endpoint}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
        }
    
    def _create_chrome_metrics_panel(self) -> Dict[str, Any]:
        """Create Chrome browser metrics panel"""
        return {
            "id": 24,
            "title": "Chrome Browser Metrics",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "silverfox_chrome_memory_usage_bytes / 1024 / 1024",
                    "legendFormat": "Chrome Memory (MB) - {{pod}}"
                },
                {
                    "expr": "silverfox_chrome_cpu_usage_percent",
                    "legendFormat": "Chrome CPU % - {{pod}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
        }
    
    def _create_network_metrics_panel(self) -> Dict[str, Any]:
        """Create network metrics panel"""
        return {
            "id": 25,
            "title": "Network Metrics",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "rate(container_network_receive_bytes_total{pod=~\"silverfox-.*\"}[5m])",
                    "legendFormat": "RX - {{pod}}"
                },
                {
                    "expr": "rate(container_network_transmit_bytes_total{pod=~\"silverfox-.*\"}[5m])",
                    "legendFormat": "TX - {{pod}}"
                }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
        }
    
    def _create_log_analysis_panel(self) -> Dict[str, Any]:
        """Create log analysis panel"""
        return {
            "id": 26,
            "title": "Log Analysis",
            "type": "logs",
            "targets": [
                {
                    "expr": "{namespace=\"silverfox-scrapers\"}",
                    "legendFormat": ""
                }
            ],
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24}
        }
    
    def _create_custom_metrics_panel(self) -> Dict[str, Any]:
        """Create custom Silver Fox metrics panel"""
        return {
            "id": 27,
            "title": "Custom Silver Fox Metrics",
            "type": "timeseries",
            "targets": [
                {
                    "expr": "silverfox_page_load_time_seconds",
                    "legendFormat": "Page Load Time - {{dealership}}"
                },
                {
                    "expr": "silverfox_anti_bot_delays_seconds",
                    "legendFormat": "Anti-bot Delays - {{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 32}
        }
    
    def _create_price_alerts_panel(self) -> Dict[str, Any]:
        """Create price alerts panel"""
        return {
            "id": 14,
            "title": "Price Alert Summary",
            "type": "stat",
            "targets": [
                {
                    "expr": "sum(silverfox_price_alerts_active)",
                    "legendFormat": "Active Price Alerts"
                }
            ],
            "gridPos": {"h": 4, "w": 6, "x": 0, "y": 16}
        }
    
    def _create_inventory_turnover_panel(self) -> Dict[str, Any]:
        """Create inventory turnover panel"""
        return {
            "id": 15,
            "title": "Inventory Turnover Rate",
            "type": "gauge",
            "targets": [
                {
                    "expr": "silverfox_inventory_turnover_rate",
                    "legendFormat": "{{dealership}}"
                }
            ],
            "gridPos": {"h": 8, "w": 8, "x": 6, "y": 16}
        }
    
    def _create_market_share_panel(self) -> Dict[str, Any]:
        """Create market share panel"""
        return {
            "id": 16,
            "title": "Market Share Analysis",
            "type": "bargauge",
            "targets": [
                {
                    "expr": "silverfox_market_share_percent",
                    "legendFormat": "{{dealership}} - {{vehicle_category}}"
                }
            ],
            "gridPos": {"h": 8, "w": 10, "x": 14, "y": 16}
        }
    
    def _create_revenue_opportunity_panel(self) -> Dict[str, Any]:
        """Create revenue opportunity panel"""
        return {
            "id": 17,
            "title": "Revenue Opportunities",
            "type": "table",
            "targets": [
                {
                    "expr": "silverfox_revenue_opportunity_dollars",
                    "legendFormat": "{{dealership}} - {{opportunity_type}}"
                }
            ],
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24}
        }
    
    def deploy_dashboard(self, dashboard: Dict[str, Any]) -> Optional[str]:
        """Deploy dashboard to Grafana"""
        try:
            url = f"{self.grafana_url}/api/dashboards/db"
            response = requests.post(url, headers=self.headers, json=dashboard)
            
            if response.status_code == 200:
                result = response.json()
                dashboard_url = f"{self.grafana_url}/d/{result['uid']}/{result['slug']}"
                self.logger.info(f"Dashboard deployed successfully: {dashboard_url}")
                return dashboard_url
            else:
                self.logger.error(f"Failed to deploy dashboard: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error deploying dashboard: {e}")
            return None
    
    def deploy_all_dashboards(self) -> Dict[str, Optional[str]]:
        """Deploy all Silver Fox dashboards"""
        dashboards = {
            "system_overview": self.create_silverfox_system_dashboard(),
            "business_intelligence": self.create_business_intelligence_dashboard(),
            "technical_monitoring": self.create_technical_dashboard()
        }
        
        results = {}
        for name, dashboard in dashboards.items():
            url = self.deploy_dashboard(dashboard)
            results[name] = url
            if url:
                self.logger.info(f"✅ {name} dashboard deployed: {url}")
            else:
                self.logger.error(f"❌ Failed to deploy {name} dashboard")
        
        return results


def main():
    """Example usage"""
    # Configuration
    grafana_url = "http://localhost:3000"  # Update with your Grafana URL
    api_key = "your_grafana_api_key"  # Update with your API key
    
    # Initialize dashboard generator
    generator = GrafanaDashboardGenerator(grafana_url, api_key)
    
    # Deploy all dashboards
    results = generator.deploy_all_dashboards()
    
    print("Dashboard deployment results:")
    for name, url in results.items():
        if url:
            print(f"✅ {name}: {url}")
        else:
            print(f"❌ {name}: Failed to deploy")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()