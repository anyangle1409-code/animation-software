@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_DRESSED_RANGE.bat ^<rN^> ^<verified_static_dressed_evidence.json^> [trialN]
  exit /b 2
)
if "%~2"=="" (
  echo Usage: RUN_ORIGINAL_V1_DRESSED_RANGE.bat ^<rN^> ^<verified_static_dressed_evidence.json^> [trialN]
  exit /b 2
)
set "TRIAL=%~3"
if "%TRIAL%"=="" set "TRIAL=trial1"
rem Finite deterministic model-range samples only. Never saves/promotes the model.
python scripts\original_v1_dressed_range_evidence.py "%~1" --static-evidence "%~2" --trial "%TRIAL%" --capture
if errorlevel 1 exit /b 2
python scripts\build_original_v1_daily_status.py
exit /b %ERRORLEVEL%
