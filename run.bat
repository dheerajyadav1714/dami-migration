@echo off
echo ==============================================
echo D.A.M.I. Application Launcher
echo ==============================================

echo Starting FastAPI Backend API on http://localhost:8000...
start "DAMI FastAPI Backend" cmd /k ".venv\Scripts\python.exe api\main.py"

echo Starting Streamlit UI on http://localhost:8501...
start "DAMI Streamlit UI" cmd /k ".venv\Scripts\streamlit.exe run ui\app.py"

echo ==============================================
echo App Launched! Opening logs in separate windows.
echo Press Ctrl+C in their respective windows to stop.
echo ==============================================
