# Complete CSV Import Workflow

## Overview
The database is designed to import your single `complete_data.csv` file that contains all dealership inventory data from your scraper system.

## Daily Import Process

### 1. Run Your Scraper System
```powershell
# Your existing scraper command that generates complete_data.csv
cd C:\silverfox_scraper_system
python main_scraper_orchestrator.py
```

This creates: `C:\silverfox_scraper_system\output_data\scraper_session_YYYYMMDD\complete_data.csv`

### 2. Import to Database
```powershell
# Navigate to database scripts
cd C:\dealership_database\scripts

# Import the complete CSV
python csv_importer_complete.py "C:\silverfox_scraper_system\output_data\scraper_session_20250724\complete_data.csv"
```

### 3. Verify Import
The import will show:
```
Importing C:\path\to\complete_data.csv...
Imported Audi Ranch Mirage: 50 vehicles
Imported BMW of West St. Louis: 75 vehicles
Imported Columbia BMW: 65 vehicles
... (all 39 dealerships)

============================================================
IMPORT SUMMARY
============================================================
Total Rows Processed: 2,574
Successfully Imported: 2,574
Skipped Rows: 0

Dealerships Processed: 40
----------------------------------------
Audi Ranch Mirage              | Imported:    50 | Skipped:   0
BMW of West St. Louis          | Imported:    75 | Skipped:   0
Columbia BMW                   | Imported:    65 | Skipped:   0
... etc
============================================================
```

## Export Options

### Export All Current Inventory
```powershell
python data_exporter.py --all --output "C:\exports\all_inventory.csv"
```

### Export Specific Dealership
```powershell
python data_exporter.py --dealership "BMW of West St. Louis" --output "C:\exports\bmw_inventory.csv"
```

### Export for QR Code Processing
```powershell
# This includes the QR code file paths needed for Adobe Illustrator
python data_exporter.py --all --qr-paths --output "C:\exports\qr_ready.csv"
```

### Check for Duplicate VINs
```powershell
python data_exporter.py --duplicates
```

### Generate Summary Report
```powershell
python data_exporter.py --summary
```

## Automation Setup

### Create Daily Import Script
Save this as `C:\dealership_database\daily_import.bat`:
```batch
@echo off
echo Starting Daily Import Process...
echo =============================

REM Set today's date
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "TODAY=%YYYY%%MM%%DD%"

REM Set paths
set SCRAPER_OUTPUT=C:\silverfox_scraper_system\output_data
set DB_SCRIPTS=C:\dealership_database\scripts
set EXPORT_DIR=C:\dealership_database\exports\%TODAY%

REM Create export directory
mkdir "%EXPORT_DIR%" 2>nul

REM Find today's complete_data.csv
echo Looking for today's scraper output...
set CSV_FILE=

for /d %%d in ("%SCRAPER_OUTPUT%\scraper_session_%TODAY%*") do (
    if exist "%%d\complete_data.csv" (
        set CSV_FILE=%%d\complete_data.csv
    )
)

if "%CSV_FILE%"=="" (
    echo ERROR: No complete_data.csv found for today!
    pause
    exit /b 1
)

echo Found: %CSV_FILE%

REM Import to database
echo.
echo Importing to database...
cd /d "%DB_SCRIPTS%"
python csv_importer_complete.py "%CSV_FILE%"

REM Export for processing
echo.
echo Exporting data for processing...
python data_exporter.py --all --qr-paths --output "%EXPORT_DIR%\complete_inventory.csv"

REM Generate reports
echo.
echo Generating reports...
python data_exporter.py --summary > "%EXPORT_DIR%\summary_report.txt"
python data_exporter.py --duplicates > "%EXPORT_DIR%\duplicate_vins.txt"

REM Backup database
echo.
echo Backing up database...
python database_maintenance.py --backup

echo.
echo =============================
echo Daily import process complete!
echo Exports saved to: %EXPORT_DIR%
echo =============================
pause
```

### Schedule Daily Import
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Silver Fox Daily Database Import"
4. Trigger: Daily at 9:00 AM (after scrapers run)
5. Action: Start `C:\dealership_database\daily_import.bat`

## Complete Data CSV Format

Your `complete_data.csv` should have these columns:
- `vin` - 17-character VIN (required)
- `stock_number` - Dealer stock number (required)
- `year` - Vehicle year
- `make` - Vehicle manufacturer
- `model` - Vehicle model
- `trim` - Trim level
- `price` - Current price
- `msrp` - Manufacturer suggested retail price
- `mileage` - Current mileage
- `exterior_color` - Exterior color
- `interior_color` - Interior color
- `fuel_type` - Gas, Electric, Hybrid, etc.
- `transmission` - Automatic, Manual, CVT
- `condition` - new, used, certified
- `url` - Vehicle detail page URL
- `dealer_name` - Dealership name (required)
- `scraped_at` - Timestamp when scraped

## Troubleshooting

### "Missing required field" errors
- Ensure your CSV has: vin, stock_number, dealer_name columns
- Check for blank values in required fields

### "Invalid VIN length" errors
- VINs must be exactly 17 characters
- Check for extra spaces or truncated VINs

### Import seems slow
- Normal import time: 1-2 minutes for 2,500 vehicles
- Run `python database_maintenance.py --vacuum` if slower

### Need to reimport same day
- The system will update existing records automatically
- Stock numbers, prices, and conditions will be updated
- VIN history will track all appearances