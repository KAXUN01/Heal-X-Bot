@echo off
REM Healing-bot: Simple Windows Launcher
REM This script provides an easy way to start the healing-bot system

echo.
echo ========================================
echo    🛡️  HEALING-BOT SYSTEM LAUNCHER  🛡️
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if the main script exists
if not exist "run-healing-bot.py" (
    echo ❌ ERROR: run-healing-bot.py not found
    echo Please run this script from the healing-bot project directory
    pause
    exit /b 1
)

echo 🚀 Starting Healing-bot System...
echo.

REM Run the main launcher script
python run-healing-bot.py %*

REM If we get here, the script has finished
echo.
echo 🛑 Healing-bot has stopped
pause
