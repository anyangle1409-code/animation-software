@echo off
setlocal
cd /d "%~dp0"
python scripts\start_v15f_local_patch.py
exit /b %errorlevel%
