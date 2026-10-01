@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage:
  echo   RUN_ORIGINAL_V1_FINAL_FREEZE_CHECK.bat --template ^<fresh-template.json^>
  echo   RUN_ORIGINAL_V1_FINAL_FREEZE_CHECK.bat ^<final-freeze-packet.json^> ^<fresh-receipt.json^>
  exit /b 2
)
if /I "%~1"=="--template" (
  if "%~2"=="" exit /b 2
  python scripts\verify_original_v1_final_freeze.py --template --json-out "%~2"
  exit /b %ERRORLEVEL%
)
if "%~2"=="" exit /b 2
rem Eligibility only. This command never promotes assets or changes production flags.
python scripts\verify_original_v1_final_freeze.py "%~1" --json-out "%~2"
exit /b %ERRORLEVEL%
