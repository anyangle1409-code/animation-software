@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="--template" (
  if "%~2"=="" goto usage
  if "%~3"=="" goto usage
  python scripts\original_v1_phase5_anatomy.py --region "%~2" --template --json-out "%~3"
  exit /b %ERRORLEVEL%
)
if "%~1"=="" goto usage
if "%~2"=="" goto usage
if "%~3"=="" goto usage
python scripts\original_v1_phase5_anatomy.py "%~2" --region "%~1" --json-out "%~3"
exit /b %ERRORLEVEL%

:usage
echo Usage:
echo   RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat --template ^<5A-5G^> ^<fresh-template.json^>
echo   RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat ^<5A-5G^> ^<actual-region-report.json^> ^<fresh-receipt.json^>
exit /b 2
