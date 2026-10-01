@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  python scripts\original_v1_blend_inventory.py
) else (
  python scripts\original_v1_blend_inventory.py --json-out "%~1"
)
exit /b %ERRORLEVEL%
