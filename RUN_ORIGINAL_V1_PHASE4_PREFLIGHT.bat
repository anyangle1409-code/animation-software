@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem Read-only gate before executing the Phase 4 development-freeze package.
call RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
if errorlevel 1 exit /b 1
python scripts\original_v1_phase4_preflight.py --require-local-blend
exit /b %ERRORLEVEL%
