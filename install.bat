@echo off
setlocal
chcp 65001 >nul
title GravPool installer

echo.
echo  ==========================================
echo  GravPool - quick setup
echo  ==========================================
echo.

where python >nul 2>nul
if %errorlevel%==0 goto :python_ok

where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py
  goto :python_ok
)

echo  [!] Python not found.
echo      Install Python 3.9+ from https://www.python.org/downloads/
echo      and tick "Add Python to PATH", then run this again.
pause
exit /b 1

:python_ok
if "%PY%"=="" set PY=python
%PY% --version
echo.
echo  Account login will open in your browser.
echo  Repeat this installer for every account you want to add.
echo.
%PY% -m gravpool.cli add-account --auth-dir auth
if %errorlevel% neq 0 (
  echo.
  echo  [!] Login failed or cancelled.
  pause
  exit /b 1
)
echo.
echo  Account added. Dashboard: python -m gravpool.cli gui
echo  Open http://127.0.0.1:8390
pause
