@echo off
echo ========================================
echo Personal AI Research Assistant
echo ========================================
echo.

echo Starting API Server...
start "Research Assistant API" cmd /k "venv\Scripts\activate && python main.py"

echo Waiting for API to start...
timeout /t 5 /nobreak > nul

echo Starting Streamlit UI...
start "Research Assistant UI" cmd /k "venv\Scripts\activate && streamlit run app.py"

echo.
echo ========================================
echo Both servers are starting!
echo API: http://localhost:8000
echo UI: http://localhost:8501
echo ========================================
echo.
echo Press any key to exit...
pause > nul
