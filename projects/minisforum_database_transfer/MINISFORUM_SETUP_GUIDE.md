# 🚀 MINISFORUM DATABASE SETUP - COMPLETE GUIDE

## 📁 What to Transfer to Flash Drive

Copy this entire `minisforum_database_transfer` folder to your flash drive. It contains:
- `/sql/` - Database creation scripts
- `/scripts/` - Python management tools
- `/setup_instructions.md` - Detailed setup guide
- This guide

---

## 🖥️ MinisForum PC Setup Process

### **Phase 1: Install PostgreSQL** (30 minutes)

1. **Download PostgreSQL 16**
   - On the MinisForum, go to: https://www.postgresql.org/download/windows/
   - Download the Windows x86-64 installer
   - Run as Administrator

2. **Installation Settings** (IMPORTANT - Write these down!)
   ```
   Installation Directory: C:\Program Files\PostgreSQL\16
   Data Directory: C:\dealership_database\data
   Password: [Choose a strong password - WRITE IT DOWN]
   Port: 5432
   Locale: English, United States
   ```

3. **Uncheck Stack Builder** at the end (not needed)

### **Phase 2: Create Directory Structure** (5 minutes)

1. Open PowerShell as Administrator
2. Run these commands:
   ```powershell
   # Create all required directories
   mkdir C:\dealership_database
   mkdir C:\dealership_database\data
   mkdir C:\dealership_database\scripts
   mkdir C:\dealership_database\sql
   mkdir C:\dealership_database\backups
   mkdir C:\dealership_database\imports
   mkdir C:\dealership_database\exports
   mkdir C:\dealership_database\logs
   ```

### **Phase 3: Copy Files from Flash Drive** (5 minutes)

1. Insert your flash drive
2. Copy files to correct locations:
   - Copy all `.sql` files from flash drive `/sql/` to `C:\dealership_database\sql\`
   - Copy all `.py` files from flash drive `/scripts/` to `C:\dealership_database\scripts\`
   - Copy `requirements.txt` to `C:\dealership_database\scripts\`

### **Phase 4: Set Environment Variables** (5 minutes)

1. Still in PowerShell as Administrator:
   ```powershell
   # Add PostgreSQL to PATH
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\PostgreSQL\16\bin", [EnvironmentVariableTarget]::Machine)
   
   # Set database password (replace YOUR_PASSWORD with the one you chose)
   [Environment]::SetEnvironmentVariable("DEALERSHIP_DB_PASSWORD", "YOUR_PASSWORD", [EnvironmentVariableTarget]::User)
   
   # Close and reopen PowerShell for changes to take effect
   ```

### **Phase 5: Create Database** (10 minutes)

1. Open new PowerShell as Administrator
2. Navigate to SQL directory:
   ```powershell
   cd C:\dealership_database\sql
   ```

3. Create database (you'll be prompted for password):
   ```powershell
   psql -U postgres -f 01_create_database.sql
   ```

4. Create tables:
   ```powershell
   psql -U postgres -d dealership_db -f 02_create_tables.sql
   ```

5. Add dealership configurations:
   ```powershell
   psql -U postgres -d dealership_db -f 03_initial_dealership_configs.sql
   ```

6. Apply performance settings:
   ```powershell
   psql -U postgres -d dealership_db -f 04_performance_settings.sql
   ```

### **Phase 6: Install Python Dependencies** (10 minutes)

1. Ensure Python 3.8+ is installed. If not:
   - Download from https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation

2. In PowerShell:
   ```powershell
   cd C:\dealership_database\scripts
   pip install -r requirements.txt
   ```

### **Phase 7: Test Everything** (5 minutes)

1. Test database connection:
   ```powershell
   cd C:\dealership_database\scripts
   python database_connection.py
   ```
   
   You should see: `✓ Database connection successful`

2. Run health check:
   ```powershell
   python database_maintenance.py --health
   ```

---

## ✅ Setup Complete!

### **Daily Usage Commands**

**Import CSV files from scrapers:**
```powershell
cd C:\dealership_database\scripts
python csv_importer.py "C:\path\to\scraper\output" --update-counts
```

**Export for order processing:**
```powershell
python data_exporter.py --all --output "C:\exports\today"
```

**Check for duplicates:**
```powershell
python data_exporter.py --duplicates
```

**Backup database:**
```powershell
python database_maintenance.py --backup
```

---

## 🆘 Troubleshooting

**"psql not recognized"**
- Close and reopen PowerShell after setting PATH

**"Connection failed"**
- Check password in environment variable: `echo %DEALERSHIP_DB_PASSWORD%`
- Verify PostgreSQL service is running in Services

**"Import failed"**
- Ensure CSV has required columns (vin, stock_number)
- Check dealership name matches configuration

---

## 📞 Quick Reference

- Database name: `dealership_db`
- Default port: `5432`
- Scripts location: `C:\dealership_database\scripts`
- Backups location: `C:\dealership_database\backups`
- Import folder: `C:\dealership_database\imports`
- Export folder: `C:\dealership_database\exports`

---

**Setup typically takes 60-90 minutes total**