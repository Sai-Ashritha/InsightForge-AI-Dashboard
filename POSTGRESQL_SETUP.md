# PostgreSQL Setup Guide for InsightForge Manufacturing Dashboard

## Overview
This guide walks you through setting up PostgreSQL and loading sample manufacturing data into the dashboard.

## Prerequisites
- PostgreSQL 12+ installed
- Windows 10/11 or Linux/macOS
- Python 3.9+ with venv activated
- 500 MB free disk space

---

## Step 1: Install PostgreSQL

### Windows
1. Download installer: https://www.postgresql.org/download/windows/
2. Run the installer and follow prompts
3. Remember the password you set for the `postgres` user
4. Default port: 5432
5. Accept all default options

### macOS (using Homebrew)
```bash
brew install postgresql
brew services start postgresql
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

---

## Step 2: Create Database

### Option A: Using pgAdmin (GUI)
1. Open pgAdmin (installed with PostgreSQL)
2. Right-click "Databases" → Create → Database
3. Name: `insightforge`
4. Owner: `postgres`
5. Click Create

### Option B: Using Command Line
```bash
# Windows CMD/PowerShell
psql -U postgres -c "CREATE DATABASE insightforge;"

# Linux/macOS
sudo -u postgres psql -c "CREATE DATABASE insightforge;"
```

---

## Step 3: Verify Connection

Test your PostgreSQL connection with these details:
- **Host**: 127.0.0.1
- **Port**: 5432
- **Database**: insightforge
- **User**: postgres
- **Password**: (your password)

```bash
# Test connection
psql -h 127.0.0.1 -U postgres -d insightforge -c "SELECT version();"
```

Expected output: PostgreSQL version information

---

## Step 4: Generate Sample Data

From the project root:

```bash
cd backend

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Generate sample CSV files
python scripts/generate_sample_data.py
```

Output:
```
✓ Exported 150 sales records to data/sample/sales.csv
✓ Exported 150 production records to data/sample/production.csv
✓ Exported 150 inventory records to data/sample/inventory.csv
✓ Exported 150 employee records to data/sample/employees.csv
✓ Exported 150 finance records to data/sample/finance.csv
```

---

## Step 5: Load Data into Database

```bash
# Still in backend folder with venv activated
python scripts/load_sample_data.py
```

Expected output:
```
======================================================================
Manufacturing Dashboard - Data Loader
======================================================================

1️⃣  Creating database tables...
✓ Tables created: {'status': 'tables_created'}

2️⃣  Loading sales.csv into 'sales' table...
   - Read 150 records
   - Normalized to 7 columns
✓ Inserted 150 rows into sales table

2️⃣  Loading production.csv into 'production' table...
   - Read 150 records
   - Normalized to 7 columns
✓ Inserted 150 rows into production table

... (inventory, employees, finance) ...

======================================================================
Data loading completed!
======================================================================
```

---

## Step 6: Verify Data in Database

```bash
# Connect to database
psql -h 127.0.0.1 -U postgres -d insightforge

# List tables
\dt

# Check record counts
SELECT COUNT(*) as total FROM sales;
SELECT COUNT(*) as total FROM production;
SELECT COUNT(*) as total FROM inventory;
SELECT COUNT(*) as total FROM employees;
SELECT COUNT(*) as total FROM finance;

# Exit
\q
```

---

## Step 7: Start Backend

```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

## Step 8: Test the API

Open your browser or use curl:

```bash
# Test dashboard with real data
curl http://127.0.0.1:8000/api/dashboard

# Expected response includes:
# - "revenue": (calculated from sales table)
# - "production": (calculated from production table)
# - "inventory": (calculated from inventory table)
# - "data_source": "live_database"
```

---

## Step 9: Start Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

Access at: http://localhost:5173

---

## Troubleshooting

### PostgreSQL Connection Refused
**Problem**: `psql: error: could not connect to server`

**Solution**:
- Ensure PostgreSQL service is running
- Windows: Check Services app for "postgresql-x64"
- Linux: `sudo systemctl status postgresql`
- Verify host/port/credentials

### Database Already Exists
**Problem**: `ERROR: database "insightforge" already exists`

**Solution**:
```bash
# Drop and recreate
psql -U postgres -c "DROP DATABASE IF EXISTS insightforge; CREATE DATABASE insightforge;"
```

### Data Not Inserting
**Problem**: Inserted rows = 0

**Solution**:
1. Check database connection works: `psql -h 127.0.0.1 -U postgres -d insightforge -c "\dt"`
2. Verify CSV files exist: `ls backend/data/sample/`
3. Check user permissions: `psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE insightforge TO postgres;"`

### PostgreSQL Won't Start
**Windows**: Use Services app (Win+R → services.msc)
**Linux**: `sudo systemctl restart postgresql`
**macOS**: `brew services restart postgresql`

---

## Environment Variables (Optional)

You can customize database connection with env vars:

```bash
# Set environment variables
export DB_HOST=127.0.0.1
export DB_PORT=5432
export DB_NAME=insightforge
export DB_USER=postgres
export DB_PASSWORD=your_password

# Then start backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## Next Steps

1. ✅ Database and data loaded
2. Upload manufacturing data via dashboard
3. Check anomalies and recommendations
4. Ask chatbot questions about your data
5. Monitor KPIs in real-time

---

## Support

For issues, check:
1. PostgreSQL logs: `C:\Program Files\PostgreSQL\15\data\log\` (Windows)
2. Backend logs: Console output from uvicorn
3. Browser console: F12 → Console tab

---

## Database Schema

### sales table
- id (PRIMARY KEY)
- date
- product
- category
- region
- quantity
- unit_price
- revenue

### production table
- id (PRIMARY KEY)
- date
- product
- department
- units_produced
- defective_units
- machine_hours
- downtime

### inventory table
- id (PRIMARY KEY)
- date
- product
- stock_available
- reorder_level
- warehouse

### employees table
- id (PRIMARY KEY)
- employee_id
- department
- date
- hours_worked
- units_completed
- productivity

### finance table
- id (PRIMARY KEY)
- date
- department
- expense
- profit
- revenue

---

Last updated: 2026-08-18
