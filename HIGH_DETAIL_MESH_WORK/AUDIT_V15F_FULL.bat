@echo off
setlocal
cd /d "%~dp0"
python scripts\audit_v15f_full.py
if errorlevel 1 exit /b %errorlevel%
python scripts\write_v15f_handoff.py
exit /b %errorlevel%
