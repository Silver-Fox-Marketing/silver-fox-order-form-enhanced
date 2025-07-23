# Silverfox Enhanced Scraper System

A comprehensive, modular scraping framework designed for dealership inventory monitoring with enhanced error handling, individual dealership customization, and a GUI for filter management.

## 🚀 Features

- **Individual Dealership Scrapers**: 42 unique scrapers preserving original filtering logic
- **Enhanced Error Handling**: Comprehensive retry mechanisms and graceful failure handling
- **Rate Limiting**: Built-in rate limiting to respect website resources
- **Data Validation**: Robust data validation with customizable rules
- **GUI Filter Editor**: Intuitive interface for editing dealership-specific filters
- **Configuration Management**: Centralized configuration with export/import capabilities
- **Performance Optimization**: Async support and efficient resource usage
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## 📁 Project Structure

```
silverfox_assistant/
├── scraper/                     # Core scraper framework
│   ├── __init__.py
│   ├── config.py               # Configuration classes
│   ├── dealership_base.py      # Base scraper class
│   ├── dealership_manager.py   # Dealership management
│   ├── validators.py           # Data validation
│   ├── exceptions.py           # Custom exceptions
│   ├── utils.py               # Utility functions
│   ├── scraper_generator.py   # Generator for updated scrapers
│   ├── dealerships/           # Individual dealership scrapers
│   └── ui/
│       └── filter_editor.py   # GUI for filter editing
├── dealership_configs/         # Dealership configurations
├── output_data/               # Scraped data output
├── logs/                      # Application logs
├── generate_all_scrapers.py   # Script to generate all scrapers
├── run_filter_editor.py       # Launch filter editor GUI
└── requirements.txt           # Python dependencies
```

## 🛠️ Installation

1. **Clone or extract the project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome WebDriver** (automatically managed by webdriver-manager)

## 🚦 Quick Start

### 1. Generate Updated Scrapers
Generate modern versions of all 42 dealership scrapers:

```bash
python generate_all_scrapers.py
```

This will:
- Analyze original scrapers from the source repository
- Preserve all existing conditional filtering logic
- Create enhanced versions with better error handling
- Generate configurations for each dealership

### 2. Edit Dealership Filters
Launch the GUI to customize filtering rules:

```bash
python run_filter_editor.py
```

The Filter Editor allows you to:
- Select any dealership
- Modify price ranges, year ranges, make/model filters
- Add custom conditional filters
- Export/import configurations
- Reset to default values

### 3. Run Individual Scrapers
```python
from scraper import DealershipManager

# Initialize manager
manager = DealershipManager()

# Get a specific scraper
scraper = manager.get_dealership_scraper('joe_machens_hyundai')

# Run scraping session
if scraper:
    results = scraper.run_scraping_session()
    print(f"Scraped {results['filtered_count']} vehicles")
```

## 🎯 Individual Dealership Scrapers

The system includes updated scrapers for all 42 dealerships:

- `audiranchomirage` - Audi Ranch Mirage
- `auffenberghyundai` - Auffenberg Hyundai  
- `bmwofweststlouis` - BMW of West St. Louis
- `columbiahonda` - Columbia Honda
- `joemachenshyundai` - Joe Machens Hyundai
- `suntrupfordkirkwood` - Suntrup Ford Kirkwood
- ... and 36 more

Each scraper preserves its original:
- API endpoints and scraping methods
- Conditional filtering rules
- Data extraction patterns
- Dealership-specific customizations

## ⚙️ Configuration

### Dealership Configuration Structure
```json
{
  "id": "dealership_id",
  "name": "Dealership Name",
  "base_url": "https://dealership.com",
  "scraper_type": "api",
  "filtering_rules": {
    "conditional_filters": {
      "price_range": {"min": 5000, "max": 100000},
      "year_range": {"min": 2010, "max": 2024},
      "allowed_conditions": ["new", "used"],
      "allowed_makes": ["Toyota", "Honda"],
      "custom_filters": {
        "fuel_type": {
          "required_values": ["gasoline", "hybrid"]
        }
      }
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
  }
}
```

### Available Filter Types

1. **Price Range**: Filter by minimum/maximum price
2. **Year Range**: Filter by model year range  
3. **Make/Model Filters**: Allow or exclude specific makes
4. **Condition Filters**: Filter by new/used/certified status
5. **Custom Filters**: Field-specific conditional filters
6. **Location Filters**: Filter by dealership location

## 🔧 Advanced Usage

### Custom Scraper Implementation
```python
from scraper.dealership_base import DealershipScraperBase

class CustomDealershipScraper(DealershipScraperBase):
    def scrape_inventory(self):
        # Implement scraping logic
        pass
    
    def extract_vehicle_data(self, raw_data):
        # Implement data extraction
        pass
```

### Batch Processing
```python
from scraper import DealershipManager

manager = DealershipManager()
dealerships = manager.list_dealerships()

for dealership in dealerships:
    if dealership['has_scraper']:
        scraper = manager.get_dealership_scraper(dealership['id'])
        results = scraper.run_scraping_session()
        print(f"{dealership['name']}: {results['filtered_count']} vehicles")
```

### Configuration Management
```python
from scraper import DealershipManager

manager = DealershipManager()

# Update filters for a specific dealership
filter_updates = {
    'conditional_filters': {
        'price_range': {'min': 10000, 'max': 75000}
    }
}
manager.update_dealership_filters('joe_machens_hyundai', filter_updates)

# Export configuration
manager.export_dealership_config('joe_machens_hyundai', 'backup.json')
```

## 📊 Monitoring and Logging

The system provides comprehensive logging:

- **Application Logs**: `logs/scraper_generation.log`
- **Dealership Logs**: `logs/{dealership_id}.log`
- **Manager Logs**: `logs/dealership_manager.log`

Log levels: DEBUG, INFO, WARNING, ERROR

## 🔒 Error Handling

The system includes robust error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Built-in rate limiting to avoid being blocked
- **Data Validation**: Comprehensive validation with customizable rules
- **Graceful Degradation**: Continue processing even if individual items fail
- **Detailed Logging**: Full error context for debugging

## 🎨 GUI Filter Editor

The Filter Editor provides:

- **Dealership Selection**: Choose from all configured dealerships
- **Visual Filter Editing**: Easy-to-use interface for each filter type
- **Real-time Validation**: Immediate feedback on filter configurations
- **Export/Import**: Save and load filter configurations
- **Reset Options**: Restore default filter settings

### Filter Editor Features:
- Price range sliders and inputs
- Year range selection
- Make/model text lists
- Condition checkboxes
- Custom JSON filter editor
- Configuration backup/restore

## 🚨 Important Notes

1. **Original Logic Preserved**: All original filtering logic and patterns are maintained
2. **Rate Limiting**: Respects website resources with built-in delays
3. **Error Recovery**: Automatically handles temporary failures
4. **Data Integrity**: Validates all scraped data before saving
5. **Deduplication**: Prevents duplicate vehicle entries
6. **Modular Design**: Easy to extend and customize individual scrapers

## 📝 Requirements

- Python 3.8+
- Chrome browser
- Internet connection for scraping
- Tkinter for GUI (usually included with Python)

## 🤝 Contributing

To add new dealerships or modify existing ones:

1. Create/modify dealership configuration
2. Implement/update scraper class
3. Register with DealershipManager
4. Test with Filter Editor

## 📞 Support

For issues or questions:
- Check logs in the `logs/` directory
- Use the Filter Editor for configuration issues
- Review original scraper patterns for reference

---

**Built for Silverfox Marketing** - Enhanced dealership inventory monitoring system