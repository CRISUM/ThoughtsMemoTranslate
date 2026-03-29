@echo off
chcp 65001 >nul
REM Hanhua Workbench - Start (Windows)

if not exist ".venv" (
    echo ERROR: Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Hanhua Workbench...
echo Open in browser: http://localhost:8000
echo Press Ctrl+C to stop.
echo.

.venv\Scripts\python.exe server.py
pause
