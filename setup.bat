@echo off
chcp 65001 >nul
REM Hanhua Workbench - Setup (Windows)

echo [1/3] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create venv. Make sure Python is installed and in PATH.
    pause
    exit /b 1
)

echo [2/3] Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo ERROR: pip upgrade failed.
    pause
    exit /b 1
)

echo [3/3] Installing dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Setup complete! Run start.bat to launch the server.
echo.
pause
