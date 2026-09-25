@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  python scripts\finish_v15_hand.py
) else (
  python scripts\finish_v15_hand.py --version %~1
)
exit /b %errorlevel%
