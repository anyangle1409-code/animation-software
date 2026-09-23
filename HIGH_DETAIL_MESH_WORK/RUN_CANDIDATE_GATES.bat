@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_CANDIDATE_GATES.bat v7_example
  exit /b 2
)
python scripts\run_candidate_gates.py --version %1
if errorlevel 1 exit /b %errorlevel%
python scripts\checkpoint_candidate.py --version %1
exit /b %errorlevel%
