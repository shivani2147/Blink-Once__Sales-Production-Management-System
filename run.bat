@echo off
REM ProductionFlow CRM - Windows Startup Script

echo.
echo ╔════════════════════════════════════════╗
echo ║   ProductionFlow CRM - Start Server    ║
echo ║   Sales ^& Production Management        ║
echo ╚════════════════════════════════════════╝
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ⚠️  Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo 📦 Checking dependencies...
pip show fastapi > nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependencies not found. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start the application
echo.
echo ✓ All checks passed!
echo.
echo 🚀 Starting ProductionFlow CRM...
echo 📌 Server: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/api/docs
echo.
echo Press CTRL+C to stop the server
echo.

python main.py

REM Deactivate virtual environment on exit
deactivate

pause
