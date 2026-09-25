@echo off
setlocal
cd /d "%~dp0"
python scripts\start_v15_hand.py
exit /b %errorlevel%
