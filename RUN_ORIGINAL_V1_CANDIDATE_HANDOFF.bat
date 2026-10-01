@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_CANDIDATE_HANDOFF.bat ^<rN^> [fresh-output-dir]
  exit /b 2
)
if "%~2"=="" (
  python scripts\original_v1_candidate_handoff.py "%~1"
) else (
  python scripts\original_v1_candidate_handoff.py "%~1" --out-dir "%~2"
)
exit /b %ERRORLEVEL%
