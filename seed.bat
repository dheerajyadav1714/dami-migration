@echo off
echo ==============================================
echo D.A.M.I. Database Setup and Seeding Script
echo ==============================================

echo [1/2] Creating BigQuery Dataset and Tables...
.venv\Scripts\python.exe scripts\create_bq_tables.py

if %ERRORLEVEL% NEQ 0 (
    echo Error creating BigQuery tables. Exiting.
    exit /b %ERRORLEVEL%
)

echo [2/2] Seeding BigQuery Tables with Sample Dataset...
.venv\Scripts\python.exe scripts\seed_database.py

if %ERRORLEVEL% NEQ 0 (
    echo Error seeding BigQuery tables. Exiting.
    exit /b %ERRORLEVEL%
)

echo ==============================================
echo Setup Complete! Run run.bat to start the app.
echo ==============================================
pause
