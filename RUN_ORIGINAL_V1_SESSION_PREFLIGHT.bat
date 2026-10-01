@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo STOP - Python unavailable. Install/enable the existing authoring Python.
  exit /b 2
)
python scripts\original_v1_session_preflight.py %*
exit /b %errorlevel%
