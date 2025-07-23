# Silverfox Complete Scraper System

## 🎯 System Overview

A comprehensive dealership inventory scraping system with:
- **42+ Individual Dealership Scrapers** with preserved original filtering logic
- **GUI Control Center** with rotary filter controls for each dealership
- **Data Normalization Pipeline** (Raw CSV → Normalized CSV → Database)
- **Add New Dealerships** via URL analysis
- **Real-time Monitoring** and logging

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure all 42 dealerships with their original rules
python configure_all_dealerships.py
```

### 2. Launch Control Center
```bash
# Start the comprehensive GUI
python run_scraper_control_center.py
```

### 3. Generate Individual Scrapers (Optional)
```bash
# Generate updated scraper code for all dealerships
python generate_all_scrapers.py
```

## 🎮 Control Center Features

### Main Interface
- **Dealership List**: All 42+ configured dealerships with status indicators
- **Search/Filter**: Find specific dealerships quickly
- **Bulk Operations**: Run multiple scrapers simultaneously
- **Real-time Status**: Monitor scraping progress and results

### Individual Dealership Controls
Each dealership has customizable filter controls:

#### 🎛️ Rotary Filter Knobs
- **Price Range**: Min/Max price with visual progress indicators
- **Year Range**: Model year filtering with rotary controls
- **Condition Checkboxes**: New, Used, Certified options

#### 📊 Dealership Information
- **Platform Detection**: Shows API type (Algolia, DealerOn, Custom, etc.)
- **Base URL**: Direct link to dealership website
- **Configuration Status**: Filter count and last updated

### Adding New Dealerships
1. Click **"➕ Add New"** in toolbar
2. Paste dealership website URL
3. Click **"🔍 Analyze Website"**
4. System automatically:
   - Detects platform type (Algolia, DealerOn Cosmos, etc.)
   - Finds API endpoints
   - Extracts dealership name and info
   - Suggests default filter settings
5. Customize filters and save

### Data Pipeline
**Complete 3-Step Process:**
1. **Raw Scraping**: Extract data with original filtering rules
2. **Raw CSV Export**: Save unprocessed data for database
3. **Normalized CSV**: Apply business normalization rules

**Status Normalization Example:**
```
Raw Status          → Normalized
"Certified Used"    → "cpo"
"In-transit"        → "offlot"
"Available"         → "onlot"
"Pre-Owned"         → "po"
```

## 🏪 Configured Dealerships

### High-Volume Dealerships
- **Joe Machens Group**: Hyundai, Toyota, Nissan, CDJR (Algolia API)
- **Suntrup Group**: Ford Kirkwood, Ford West, Buick GMC, Hyundai/Kia South
- **Bommarito Group**: Cadillac, West County (DealerOn Cosmos)

### Luxury Dealerships
- **Porsche St. Louis**: $50K-$500K price range
- **BMW of West St. Louis**: Premium vehicle filtering
- **Audi Ranch Mirage**: Luxury inventory management
- **Jaguar/Land Rover Ranch Mirage**: High-end filtering

### Regional Dealerships
- **Columbia Area**: Honda, BMW, Kia
- **Dave Sinclair Group**: Lincoln South, Lincoln St. Peters
- **Independent Dealers**: 15+ smaller operations

## ⚙️ Filter Configuration

### Price Range Filters
- **Economy Dealerships**: $5K-$50K (South County Autos, Stehouwer Auto)
- **Mainstream**: $8K-$120K (Most Ford, Honda, Toyota dealers)
- **Luxury**: $30K-$500K (Porsche, BMW, Jaguar, Land Rover)

### Platform-Specific Settings
- **Algolia Dealerships**: Facet filters, 20 items per page
- **DealerOn Cosmos**: Dealer ID-based API calls
- **Stellantis/DDC**: Feed-based extraction
- **Custom APIs**: Individualized endpoints

### Location-Based Filtering
Each dealership filters by exact location match to prevent cross-contamination between multi-location groups.

## 📊 Data Output Structure

### Raw CSV Fields
```csv
vin,stock_number,year,make,model,trim,price,msrp,mileage,
exterior_color,interior_color,body_style,fuel_type,
original_status,dealer_name,dealer_id,url,scraped_at
```

### Normalized CSV Fields
```csv
vin,stock_number,year,make,model,trim,price,msrp,mileage,
exterior_color,interior_color,body_style,fuel_type,
original_status,normalized_status,condition,
dealer_name,dealer_id,url,scraped_at
```

## 🔧 Advanced Configuration

### Adding Custom Filters
1. Select dealership in Control Center
2. Adjust rotary knobs for price/year ranges
3. Toggle condition checkboxes
4. Click **"💾 Save Filters"**

### Platform Detection Rules
- **Algolia**: `algolia.net` domains, `searchable_dealer_name` fields
- **DealerOn**: `vhcliaa` API endpoints, `cosmos` references
- **Stellantis/DDC**: Manufacturer-specific indicators
- **Custom**: Fallback for unique implementations

### API Configuration
Each platform has specific requirements:
```json
{
  "algolia": {
    "app_id": "YAUO1QHBQ9",
    "api_key": "c0b6c7faee6b9e27d4bd3b9ae5c5bb3e",
    "facet_filters": ["searchable_dealer_name:Dealer Name"]
  },
  "dealeron_cosmos": {
    "dealer_id": "65023",
    "endpoint": "/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles"
  }
}
```

## 📈 Monitoring & Logging

### Log Files
- `scraping_pipeline.log`: Complete pipeline execution
- `dealership_manager.log`: Configuration changes
- `data_normalizer.log`: Normalization process
- `{dealership_id}.log`: Individual scraper logs

### Status Indicators
- **✅ Ready**: Configured and ready to run
- **🔄 Running**: Currently scraping
- **✅ Complete**: Successfully finished
- **❌ Failed**: Error occurred
- **⚠️ No Scraper**: Configuration only

### Performance Metrics
- **Rate Limiting**: 30-120 requests/minute per dealership
- **Concurrent Workers**: 3 per dealership
- **Retry Logic**: 3-5 attempts with exponential backoff
- **Data Validation**: Required field checking and type conversion

## 🛠️ Maintenance

### Daily Operations
1. **Monitor Logs**: Check for failed scrapers
2. **Review Data Quality**: Validate normalized output
3. **Update Filters**: Adjust for new inventory patterns
4. **Database Sync**: Ensure raw and normalized data alignment

### Weekly Maintenance
1. **Performance Review**: Check scraping speeds and success rates
2. **Filter Optimization**: Adjust ranges based on market changes
3. **New Dealership Research**: Identify potential additions
4. **System Updates**: Apply any framework improvements

### Platform Updates
- **Algolia Changes**: Monitor API version updates
- **Website Redesigns**: Update selectors and endpoints
- **New Security Measures**: Adapt to anti-bot implementations

## 🔍 Troubleshooting

### Common Issues

**Scraper Not Starting**
- Check dealership configuration exists
- Verify API endpoints are accessible
- Review rate limiting settings

**No Data Returned**
- Validate filter settings aren't too restrictive
- Check website changes or API updates
- Review platform detection accuracy

**Normalization Errors**
- Verify required fields are present
- Check status mapping rules
- Review data type conversions

**Performance Issues**
- Adjust rate limiting settings
- Check concurrent worker counts
- Monitor system resources

### Support Resources
- **Control Center Logs**: Real-time error display
- **Individual Dealer Logs**: Detailed scraping information
- **Configuration Export**: Backup and restore settings
- **Platform Documentation**: API-specific guidance

## 🎯 Success Metrics

### Data Quality
- **99%+ VIN Accuracy**: Unique identifier reliability
- **95%+ Price Accuracy**: Correct price extraction
- **90%+ Status Normalization**: Proper condition mapping

### System Performance
- **42+ Dealerships**: Comprehensive coverage
- **< 5 Min Average**: Per-dealership scraping time
- **24/7 Availability**: Continuous monitoring capability

### Business Impact
- **Real-time Inventory**: Up-to-date vehicle availability
- **Normalized Data**: Consistent format for processing
- **Scalable Architecture**: Easy addition of new dealerships

---

**Built for Silverfox Marketing** - Complete dealership inventory monitoring solution