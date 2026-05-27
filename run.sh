#!/bin/bash
# ProductionFlow CRM - Unix/Linux/Mac Startup Script

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   ProductionFlow CRM - Start Server    ║"
echo "║   Sales & Production Management        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies not found. Installing..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Start the application
echo ""
echo "✓ All checks passed!"
echo ""
echo "🚀 Starting ProductionFlow CRM..."
echo "📌 Server: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

python main.py

# Deactivate virtual environment on exit
deactivate
