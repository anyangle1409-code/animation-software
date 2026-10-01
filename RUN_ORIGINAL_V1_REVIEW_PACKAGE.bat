@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_REVIEW_PACKAGE.bat ^<rN^> [fresh-output-dir]
  exit /b 2
)
if "%~2"=="" (
  python scripts\original_v1_review_package.py "%~1"
) else (
  python scripts\original_v1_review_package.py "%~1" --out-dir "%~2"
)
exit /b %ERRORLEVEL%
