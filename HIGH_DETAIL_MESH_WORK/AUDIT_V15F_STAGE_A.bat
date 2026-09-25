@echo off
setlocal
cd /d "%~dp0"
python scripts\audit_v15f_stage_a.py
exit /b %errorlevel%
