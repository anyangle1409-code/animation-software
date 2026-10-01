@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_VISUAL_QA.bat ^<capture-manifest.json^> [reference-manifest.json] [fresh-output.json]
  exit /b 2
)
set "REF=%~2"
set "OUT=%~3"
if "%OUT%"=="" set "OUT=ORIGINAL_V1_WORK\visual_qa\visual_qa_report.json"
if "%REF%"=="" (
  python scripts\original_v1_visual_qa.py --capture-manifest "%~1" --json-out "%OUT%"
) else (
  python scripts\original_v1_visual_qa.py --capture-manifest "%~1" --reference-manifest "%REF%" --json-out "%OUT%"
)
exit /b %ERRORLEVEL%
