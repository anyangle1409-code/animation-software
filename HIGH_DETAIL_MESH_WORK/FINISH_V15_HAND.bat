@echo off
setlocal
cd /d "%~dp0"
python scripts\finish_v15_hand.py
exit /b %errorlevel%
