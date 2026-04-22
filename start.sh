#!/bin/bash

echo "========================================"
# shellcheck disable=SC2164
echo "    Market Radar Launcher"
echo "========================================"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Error: .venv not found. Please create it first."
    exit 1
fi

echo "Starting Market Radar Shiny App on Port 8001..."
python -m shiny run app.py --reload --port 8001 --launch-browser
