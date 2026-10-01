@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo [Gravpool] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY=python
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PY=py
    ) else (
        echo [ERROR] Python not found.
        echo Please install Python 3.9+ from https://www.python.org/downloads/
        echo IMPORTANT: Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

echo [Gravpool] Running setup bundle...
%PY% bundle.py
if %errorlevel% neq 0 (
    echo [ERROR] Setup bundle failed.
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo [SUCCESS] Gravpool setup completed!
echo.
echo Next steps:
echo 1. Login Account:  %PY% -m gravpool.cli add-account --auth-dir auth
echo    (Do this once, or use the Add Account button in Dashboard)
echo 2. Start GravPool: %PY% -m gravpool.cli gui --auth-dirs auth
echo    (Dashboard at http://127.0.0.1:8390)
echo    (API at       http://127.0.0.1:8390/v1 with key sk-local)
echo ========================================================
echo.
pause
