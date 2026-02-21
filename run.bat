@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Make sure Python is installed and the py launcher is available.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate .venv
    pause
    exit /b 1
)

python -c "import flet, google.cloud.firestore" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies from requirements.txt...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

set PYTHONPATH=src
flet run src/skoolplannr/app.py

endlocal
