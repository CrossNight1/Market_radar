@echo off
echo ========================================
echo     Market Radar Launcher (Windows)
echo ========================================

if not exist .venv (
    echo Error: .venv not found. Creating it...
    python -m venv .venv
    call .venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo Activating virtual environment...
    call .venv\Scripts\activate
)

echo Starting Market Radar Shiny App on Port 8001...
python -m shiny run app.py --reload --port 8001 --launch-browser
pause
