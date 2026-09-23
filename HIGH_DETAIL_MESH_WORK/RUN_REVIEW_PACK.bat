@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_REVIEW_PACK.bat v7_example
  exit /b 2
)
python scripts\prepare_review_pack.py --version %1
exit /b %errorlevel%
