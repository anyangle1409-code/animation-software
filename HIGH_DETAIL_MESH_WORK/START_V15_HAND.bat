@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  python scripts\start_v15_hand.py
) else (
  python scripts\start_v15_hand.py --version %~1
)
exit /b %errorlevel%
