@echo off
setlocal
cd /d "%~dp0"
python scripts\write_v15f_handoff.py
exit /b %errorlevel%
