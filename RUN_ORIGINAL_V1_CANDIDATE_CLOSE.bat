@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_CANDIDATE_CLOSE.bat ^<rN^> [fresh-output.json]
  exit /b 2
)
if "%~2"=="" (
  python scripts\original_v1_candidate_closure.py "%~1"
) else (
  python scripts\original_v1_candidate_closure.py "%~1" --json-out "%~2"
)
exit /b %ERRORLEVEL%
