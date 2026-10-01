@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_RUNTIME_DISCOVERY.bat ^<path-to-separate-standalone-checkout^> [fresh-output.json]
  exit /b 2
)
set "OUT=%~2"
if "%OUT%"=="" set "OUT=ORIGINAL_V1_WORK\runtime_discovery\runtime_discovery.json"
rem Read-only comparison only. Does not edit the standalone checkout or activate assets.
python scripts\original_v1_runtime_discovery.py --runtime-root "%~1" --json-out "%OUT%"
exit /b %ERRORLEVEL%
