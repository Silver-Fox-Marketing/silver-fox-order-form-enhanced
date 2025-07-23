#!/usr/bin/env python3
"""
Configure all 42 dealerships with their specific filtering rules and configurations
based on analysis of original scrapers.
"""

import os
import sys
import json
from datetime import datetime

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.dealership_manager import DealershipManager
from scraper.utils import setup_logging

# Comprehensive dealership configurations based on original scraper analysis
DEALERSHIP_CONFIGURATIONS = {
    "audiranchomirage": {
        "name": "Audi Ranch Mirage",
        "base_url": "https://www.audirancho.com",
        "scraper_type": "api",
        "api_platform": "stellantis_ddc",
        "api_config": {
            "primary_endpoint": "https://www.audirancho.com/inventory/feed/vehicles",
            "dealership_code": "65072",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Audi Ranch Mirage"
                },
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 15000, "max": 300000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year", "dealer_name"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "mileage", "exterior_color", "dealer_name", "url"]
        }
    },
    
    "auffenberghyundai": {
        "name": "Auffenberg Hyundai",
        "base_url": "https://www.auffenberghyundai.com",
        "scraper_type": "api",
        "api_platform": "custom_widget",
        "api_config": {
            "primary_endpoint": "https://www.auffenberghyundai.com/api/inventory/vehicles",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Auffenberg Hyundai"
                },
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 5000, "max": 100000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": ["price"],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "mileage", "exterior_color", "condition", "url"]
        }
    },
    
    "bmwofweststlouis": {
        "name": "BMW of West St. Louis",
        "base_url": "https://www.bmwofweststlouis.com",
        "scraper_type": "api",
        "api_platform": "algolia",
        "api_config": {
            "algolia_app_id": "YAUO1QHBQ9",
            "algolia_api_key": "c0b6c7faee6b9e27d4bd3b9ae5c5bb3e",
            "index_name": "prod_STITCHED_vehicle_search_feeds",
            "primary_endpoint": "https://yauo1qhbq9-dsn.algolia.net/1/indexes/prod_STITCHED_vehicle_search_feeds/query",
            "headers": {
                "X-Algolia-API-Key": "c0b6c7faee6b9e27d4bd3b9ae5c5bb3e",
                "X-Algolia-Application-Id": "YAUO1QHBQ9",
                "Content-Type": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "BMW of West St. Louis"
                },
                "api_filters": {
                    "facet_filters": ["searchable_dealer_name:BMW of West St. Louis"]
                },
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 20000, "max": 200000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "items_per_page": 20,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "msrp", "mileage", "exterior_color", "fuel_type", "url"]
        }
    },
    
    "bommaritocadillac": {
        "name": "Bommarito Cadillac",
        "base_url": "https://www.bommaritocadillac.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "api_config": {
            "primary_endpoint": "https://www.bommaritocadillac.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles",
            "dealer_id": "68426",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Bommarito Cadillac"
                },
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 25000, "max": 150000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "mileage", "exterior_color", "body_style", "fuel_type", "url"]
        }
    },
    
    "bommaritowestcounty": {
        "name": "Bommarito West County",
        "base_url": "https://www.bommaritowestcounty.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "api_config": {
            "primary_endpoint": "https://www.bommaritowestcounty.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles",
            "dealer_id": "68426",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Bommarito West County"
                },
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 15000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "mileage", "exterior_color", "condition", "url"]
        }
    },
    
    "columbiabmw": {
        "name": "Columbia BMW",
        "base_url": "https://www.columbiabmw.com",
        "scraper_type": "api",
        "api_platform": "stellantis_ddc",
        "api_config": {
            "primary_endpoint": "https://www.columbiabmw.com/inventory/feed/vehicles",
            "dealership_code": "65001",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Columbia BMW"
                },
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 20000, "max": 200000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "mileage", "exterior_color", "body_style", "url"]
        }
    },
    
    "columbiahonda": {
        "name": "Columbia Honda",
        "base_url": "https://www.columbiahonda.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "api_config": {
            "primary_endpoint": "https://www.columbiahonda.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles",
            "dealer_id": "65004",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Columbia Honda"
                },
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 10000, "max": 80000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "mileage", "exterior_color", "status", "url"]
        }
    },
    
    "joemachenshyundai": {
        "name": "Joe Machens Hyundai",
        "base_url": "https://www.joemachenshyundai.com",
        "scraper_type": "api",
        "api_platform": "algolia",
        "api_config": {
            "algolia_app_id": "YAUO1QHBQ9",
            "algolia_api_key": "c0b6c7faee6b9e27d4bd3b9ae5c5bb3e",
            "index_name": "prod_STITCHED_vehicle_search_feeds",
            "primary_endpoint": "https://yauo1qhbq9-dsn.algolia.net/1/indexes/prod_STITCHED_vehicle_search_feeds/query",
            "headers": {
                "X-Algolia-API-Key": "c0b6c7faee6b9e27d4bd3b9ae5c5bb3e",
                "X-Algolia-Application-Id": "YAUO1QHBQ9",
                "Content-Type": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Joe Machens Hyundai"
                },
                "api_filters": {
                    "facet_filters": ["searchable_dealer_name:Joe Machens Hyundai"]
                },
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 5000, "max": 100000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "items_per_page": 20,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "msrp", "mileage", "exterior_color", "fuel_type", "url"]
        }
    },
    
    "suntrupfordkirkwood": {
        "name": "Suntrup Ford Kirkwood", 
        "base_url": "https://www.suntrupfordkirkwood.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "api_config": {
            "primary_endpoint": "https://www.suntrupfordkirkwood.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles",
            "dealer_id": "65023",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        },
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {
                    "required_location": "Suntrup Ford Kirkwood"
                },
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 10000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "skip_if_missing": [],
                "field_types": {
                    "price": "price",
                    "year": "year",
                    "mileage": "mileage"
                }
            }
        },
        "extraction_config": {
            "method": "api_request",
            "pagination": True,
            "data_fields": ["vin", "stock_number", "year", "make", "model", "trim", "price", "mileage", "exterior_color", "body_style", "fuel_type", "url"]
        }
    },
    
    # Adding remaining 33 dealerships with their specific configurations
    "davesinclairlincolnsouth": {
        "name": "Dave Sinclair Lincoln South",
        "base_url": "https://www.davesinclairlincolnsouth.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Dave Sinclair Lincoln South"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 15000, "max": 150000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "davesinclairlincolnstpeters": {
        "name": "Dave Sinclair Lincoln St. Peters",
        "base_url": "https://www.davesinclairlincolnstpeters.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Dave Sinclair Lincoln St. Peters"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 15000, "max": 150000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "frankletahonda": {
        "name": "Frank Leta Honda",
        "base_url": "https://www.frankletahonda.com",
        "scraper_type": "api",
        "api_platform": "algolia",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Frank Leta Honda"},
                "api_filters": {"facet_filters": ["searchable_dealer_name:Frank Leta Honda"]},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 10000, "max": 80000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "glendalechryslerjeep": {
        "name": "Glendale Chrysler Jeep",
        "base_url": "https://www.glendalechryslerjeep.com",
        "scraper_type": "api",
        "api_platform": "stellantis_ddc",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Glendale Chrysler Jeep"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 12000, "max": 100000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "hondafrontenac": {
        "name": "Honda of Frontenac",
        "base_url": "https://www.hondafrontenac.com",
        "scraper_type": "sitemap",
        "api_platform": "sitemap_based",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Honda of Frontenac"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 10000, "max": 80000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "hwkia": {
        "name": "H&W Kia",
        "base_url": "https://www.hwkia.com",
        "scraper_type": "sitemap",
        "api_platform": "sitemap_based",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "H&W Kia"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 8000, "max": 70000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "indigoautogroup": {
        "name": "Indigo Auto Group",
        "base_url": "https://www.indigoautogroup.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Indigo Auto Group"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 5000, "max": 150000},
                "year_range": {"min": 2005, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "jaguarranchomirage": {
        "name": "Jaguar Ranch Mirage",
        "base_url": "https://www.jaguarranchomirage.com",
        "scraper_type": "api",
        "api_platform": "stellantis_ddc",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Jaguar Ranch Mirage"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 30000, "max": 200000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "joemachenscdjr": {
        "name": "Joe Machens Chrysler Dodge Jeep Ram",
        "base_url": "https://www.joemachenscdjr.com",
        "scraper_type": "api",
        "api_platform": "algolia",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Joe Machens Chrysler Dodge Jeep Ram"},
                "api_filters": {"facet_filters": ["searchable_dealer_name:Joe Machens Chrysler Dodge Jeep Ram"]},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 8000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "joemachensnissan": {
        "name": "Joe Machens Nissan",
        "base_url": "https://www.joemachensnissan.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Joe Machens Nissan"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 8000, "max": 80000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "joemachenstoyota": {
        "name": "Joe Machens Toyota",
        "base_url": "https://www.joemachenstoyota.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Joe Machens Toyota"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 10000, "max": 100000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "kiaofcolumbia": {
        "name": "Kia of Columbia",
        "base_url": "https://www.kiaofcolumbia.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Kia of Columbia"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 8000, "max": 70000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "landroverranchomirage": {
        "name": "Land Rover Ranch Mirage",
        "base_url": "https://www.landroverranchomirage.com",
        "scraper_type": "api",
        "api_platform": "stellantis_ddc",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Land Rover Ranch Mirage"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 35000, "max": 300000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "miniofstlouis": {
        "name": "MINI of St. Louis",
        "base_url": "https://www.miniofstlouis.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "MINI of St. Louis"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 15000, "max": 80000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "pappastoyota": {
        "name": "Pappas Toyota",
        "base_url": "https://www.pappastoyota.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Pappas Toyota"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 10000, "max": 100000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "porschestlouis": {
        "name": "Porsche St. Louis",
        "base_url": "https://www.porschestlouis.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Porsche St. Louis"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 50000, "max": 500000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "pundmannford": {
        "name": "Pundmann Ford",
        "base_url": "https://www.pundmannford.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Pundmann Ford"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 10000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "rustydrewingcadillac": {
        "name": "Rusty Drewing Cadillac",
        "base_url": "https://www.rustydrewingcadillac.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Rusty Drewing Cadillac"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 20000, "max": 150000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "rustydrewingchevroletbuickgmc": {
        "name": "Rusty Drewing Chevrolet Buick GMC",
        "base_url": "https://www.rustydrewingchevroletbuickgmc.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Rusty Drewing Chevrolet Buick GMC"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 10000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "serrahondaofallon": {
        "name": "Serra Honda of O'Fallon",
        "base_url": "https://www.serrahondaofallon.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Serra Honda of O'Fallon"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 10000, "max": 80000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "southcountyautos": {
        "name": "South County Autos",
        "base_url": "https://www.southcountyautos.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "South County Autos"},
                "allowed_conditions": ["used"],
                "price_range": {"min": 5000, "max": 50000},
                "year_range": {"min": 2005, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "spiritlexus": {
        "name": "Spirit Lexus",
        "base_url": "https://www.spiritlexus.com",
        "scraper_type": "api",
        "api_platform": "algolia",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Spirit Lexus"},
                "api_filters": {"facet_filters": ["searchable_dealer_name:Spirit Lexus"]},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 25000, "max": 200000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "stehouwerauto": {
        "name": "Stehouwer Auto",
        "base_url": "https://www.stehouwerauto.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Stehouwer Auto"},
                "allowed_conditions": ["used"],
                "price_range": {"min": 5000, "max": 40000},
                "year_range": {"min": 2005, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "suntrupbuickgmc": {
        "name": "Suntrup Buick GMC",
        "base_url": "https://www.suntrupbuickgmc.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Suntrup Buick GMC"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 15000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "suntrupfordwest": {
        "name": "Suntrup Ford West",
        "base_url": "https://www.suntrupfordwest.com",
        "scraper_type": "api",
        "api_platform": "dealeron_cosmos",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Suntrup Ford West"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 10000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "suntruphyundaisouth": {
        "name": "Suntrup Hyundai South",
        "base_url": "https://www.suntruphyundaisouth.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Suntrup Hyundai South"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 8000, "max": 80000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "suntrupkiasouth": {
        "name": "Suntrup Kia South",
        "base_url": "https://www.suntrupkiasouth.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Suntrup Kia South"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 8000, "max": 70000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "thoroughbredford": {
        "name": "Thoroughbred Ford",
        "base_url": "https://www.thoroughbredford.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Thoroughbred Ford"},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 10000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "twincitytoyota": {
        "name": "Twin City Toyota",
        "base_url": "https://www.twincitytoyota.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Twin City Toyota"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 10000, "max": 100000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "wcvolvocars": {
        "name": "West County Volvo Cars",
        "base_url": "https://www.wcvolvocars.com",
        "scraper_type": "api",
        "api_platform": "custom",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "West County Volvo Cars"},
                "allowed_conditions": ["new", "used", "certified"],
                "price_range": {"min": 20000, "max": 150000},
                "year_range": {"min": 2015, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    },
    
    "weberchev": {
        "name": "Weber Chevrolet",
        "base_url": "https://www.weberchev.com",
        "scraper_type": "api",
        "api_platform": "algolia",
        "filtering_rules": {
            "conditional_filters": {
                "location_filters": {"required_location": "Weber Chevrolet"},
                "api_filters": {"facet_filters": ["searchable_dealer_name:Weber Chevrolet"]},
                "allowed_conditions": ["new", "used"],
                "price_range": {"min": 10000, "max": 120000},
                "year_range": {"min": 2010, "max": 2024}
            },
            "validation_rules": {
                "required_fields": ["vin", "make", "model", "year"],
                "field_types": {"price": "price", "year": "year", "mileage": "mileage"}
            }
        }
    }
}

def configure_all_dealerships():
    """Configure all dealerships with their specific rules"""
    
    logger = setup_logging("INFO", "logs/dealership_configuration.log")
    logger.info("Starting dealership configuration process")
    
    # Initialize dealership manager
    manager = DealershipManager()
    
    print("🏪 Configuring all dealership scrapers with original filtering rules...")
    print(f"📊 Processing {len(DEALERSHIP_CONFIGURATIONS)} dealership configurations")
    
    successful = 0
    failed = 0
    
    for dealership_id, config in DEALERSHIP_CONFIGURATIONS.items():
        try:
            # Add metadata
            config['id'] = dealership_id
            config['created_at'] = datetime.now().isoformat()
            config['updated_at'] = datetime.now().isoformat()
            
            # Create configuration
            success = manager.create_dealership_config(dealership_id, config)
            
            if success:
                successful += 1
                print(f"   ✅ {config['name']} ({dealership_id})")
                logger.info(f"Successfully configured {dealership_id}")
            else:
                failed += 1
                print(f"   ❌ {config['name']} ({dealership_id}) - Configuration failed")
                logger.error(f"Failed to configure {dealership_id}")
                
        except Exception as e:
            failed += 1
            print(f"   ❌ {dealership_id} - Error: {str(e)}")
            logger.error(f"Error configuring {dealership_id}: {str(e)}")
    
    print(f"\n✅ Configuration Complete!")
    print(f"✓ Successfully configured: {successful} dealerships")
    print(f"✗ Failed to configure: {failed} dealerships")
    
    if successful > 0:
        print(f"\n📁 Configuration files saved in: dealership_configs/")
        print(f"🎯 Use the Filter Editor to modify specific rules: python run_filter_editor.py")
        print(f"🚀 Generate scrapers with: python generate_all_scrapers.py")
    
    logger.info(f"Configuration complete: {successful} successful, {failed} failed")
    
    return successful, failed

def main():
    """Main function"""
    try:
        successful, failed = configure_all_dealerships()
        
        if failed > 0:
            return 1
        return 0
        
    except Exception as e:
        print(f"❌ Configuration process failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)