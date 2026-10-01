@echo off
setlocal
cd /d "%~dp0"
python scripts\original_v1_blender_smoke.py
exit /b %ERRORLEVEL%
