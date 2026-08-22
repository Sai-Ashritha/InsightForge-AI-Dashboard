#!/usr/bin/env python3
"""
Quick start script for InsightForge Manufacturing Dashboard.
Sets up the project and provides next steps.
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step_num, text):
    """Print formatted step."""
    print(f"\n{step_num}️⃣  {text}")
    print("-" * 70)


def check_files():
    """Verify all required project files exist."""
    print_step(1, "Checking project structure")

    required_files = [
        "backend/app/main.py",
        "backend/app/database/db.py",
        "backend/scripts/generate_sample_data.py",
        "backend/scripts/load_sample_data.py",
        "backend/data/sample/sales.csv",
        "backend/data/sample/production.csv",
        "backend/data/sample/inventory.csv",
        "backend/data/sample/employees.csv",
        "backend/data/sample/finance.csv",
        "frontend/src/App.jsx",
        "POSTGRESQL_SETUP.md",
    ]

    missing = []
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path}")
            missing.append(file_path)

    if missing:
        print(f"\n⚠️  Missing {len(missing)} files. Run generate_sample_data.py first.")
        return False

    print(f"\n✅ All {len(required_files)} required files present!")
    return True


def check_python_packages():
    """Check if required Python packages are installed."""
    print_step(2, "Checking Python packages")

    required_packages = [
        "fastapi",
        "uvicorn",
        "pandas",
        "numpy",
        "scikit-learn",
        "psycopg2-binary",
        "openpyxl",
    ]

    import importlib

    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)

    if missing:
        print(f"\n⚠️  Missing {len(missing)} packages.")
        print(f"   Install with: pip install {' '.join(missing)}")
        return False

    print(f"\n✅ All {len(required_packages)} packages installed!")
    return True


def print_setup_instructions():
    """Print PostgreSQL setup instructions."""
    print_step(3, "PostgreSQL Setup Instructions")

    instructions = """
🔧 Database Setup Steps:

1. INSTALL PostgreSQL
   ├─ Windows: Download from https://www.postgresql.org/download/windows/
   ├─ macOS: brew install postgresql && brew services start postgresql
   └─ Linux: sudo apt install postgresql && sudo systemctl start postgresql

2. CREATE DATABASE
   ├─ pgAdmin GUI: Right-click Databases → Create → Name: insightforge
   └─ CLI: psql -U postgres -c "CREATE DATABASE insightforge;"

3. VERIFY CONNECTION
   └─ psql -h 127.0.0.1 -U postgres -d insightforge -c "SELECT version();"

4. LOAD SAMPLE DATA
   └─ python scripts/load_sample_data.py

5. START BACKEND
   └─ python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

6. START FRONTEND
   └─ cd frontend && npm run dev

7. ACCESS DASHBOARD
   └─ http://localhost:5173
"""

    print(instructions)


def print_api_endpoints():
    """Print available API endpoints."""
    print_step(4, "Available API Endpoints")

    endpoints = """
📍 Core Endpoints:
  GET  /api/dashboard              - KPI metrics (now from real DB)
  POST /api/upload                 - Upload & classify data
  GET  /api/forecast               - Revenue trend prediction
  GET  /api/db-status              - Database connection status

📊 Analytics Endpoints:
  GET  /api/analytics              - Data quality & anomalies
  GET  /api/anomalies              - Outlier detection details
  GET  /api/recommendations        - Business recommendations

💬 AI & Insights Endpoints:
  POST /api/chat                   - Interactive chatbot
  GET  /api/insights/executive-summary - Auto-generated summary
  GET  /api/insights/health-check  - Operation health score

🏥 Health Endpoints:
  GET  /                           - API status
  GET  /api/health                 - Full health report
  GET  /tables                     - Database table contents

📌 Base URL: http://127.0.0.1:8000
"""

    print(endpoints)


def print_sample_curl_commands():
    """Print curl command examples."""
    print_step(5, "Sample API Requests")

    commands = """
🔗 Test Commands (after backend is running):

# Check API health
curl http://127.0.0.1:8000/api/health

# Get dashboard KPIs (from real database)
curl http://127.0.0.1:8000/api/dashboard

# Get business recommendations
curl http://127.0.0.1:8000/api/recommendations

# Get operation health score
curl http://127.0.0.1:8000/api/insights/health-check

# Ask the chatbot
curl -X POST http://127.0.0.1:8000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"question": "What is our revenue?"}'

# Get executive summary
curl http://127.0.0.1:8000/api/insights/executive-summary

# Check database status
curl http://127.0.0.1:8000/api/db-status
"""

    print(commands)


def print_feature_summary():
    """Print complete feature list."""
    print_step(6, "Complete Feature Checklist")

    features = """
✅ COMPLETED FEATURES:

📊 Data Pipeline:
   ✓ File upload (CSV, Excel, JSON)
   ✓ Automatic data classification (5 table types)
   ✓ Data cleaning & normalization
   ✓ Quality scoring
   ✓ PostgreSQL persistence

📈 Analytics Engine:
   ✓ Real-time KPI calculation from database
   ✓ Anomaly detection (IsolationForest)
   ✓ Column-level statistics
   ✓ Trend forecasting (polynomial regression)

🤖 Business Intelligence:
   ✓ Automatic recommendations (rule-based)
   ✓ Health scoring system
   ✓ Natural language explanations
   ✓ Interactive chatbot
   ✓ Executive summary generation

🎨 Frontend:
   ✓ React dashboard with Vite
   ✓ Real-time data display
   ✓ Chat interface with message history
   ✓ Responsive dark theme UI
   ✓ File upload panel

🔧 Backend:
   ✓ FastAPI with CORS
   ✓ 12+ REST endpoints
   ✓ Error handling & validation
   ✓ Database connection pooling

🗄️ Database:
   ✓ PostgreSQL schema (5 tables)
   ✓ Sample data generator (750 records)
   ✓ Data loader script
   ✓ Automatic table creation
"""

    print(features)


def print_next_steps():
    """Print immediate next steps."""
    print_step(7, "Next Steps to Run Live")

    steps = """
🚀 QUICK START (5 minutes):

Step 1: Install PostgreSQL
   → https://www.postgresql.org/download/

Step 2: Create database
   → psql -U postgres -c "CREATE DATABASE insightforge;"

Step 3: Generate and load sample data
   → cd backend
   → python scripts/load_sample_data.py

Step 4: Start backend
   → python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   → Look for: "Uvicorn running on http://127.0.0.1:8000"

Step 5: Start frontend (new terminal)
   → cd frontend
   → npm run dev
   → Look for: "Local: http://localhost:5173"

Step 6: Open browser
   → http://localhost:5173

✅ Dashboard will now show:
   • Real revenue/production/inventory from database
   • Anomalies detected in your data
   • AI-generated recommendations
   • Chat interface for asking questions

🎯 Try these first:
   1. Upload a CSV file (or use uploaded sample data)
   2. Check dashboard KPIs (now from real DB!)
   3. Ask chatbot: "What is our current revenue?"
   4. View anomalies and recommendations
"""

    print(steps)


def main():
    """Run all checks and print setup info."""
    print_header("InsightForge Manufacturing Dashboard - Setup Guide")

    # Run checks
    has_files = check_files()
    has_packages = check_python_packages()

    if has_files and has_packages:
        print_header("✅ System Ready!")
    else:
        print_header("⚠️  System Not Fully Ready")

    # Print guidance
    print_setup_instructions()
    print_api_endpoints()
    print_sample_curl_commands()
    print_feature_summary()
    print_next_steps()

    print_header("Questions?")
    print("""
📖 Documentation: See POSTGRESQL_SETUP.md
🔗 API Docs: http://127.0.0.1:8000/docs (after backend starts)
💬 Chatbot: Ask questions through the dashboard UI
📊 Example queries on /api/dashboard endpoint
""")


if __name__ == "__main__":
    main()
