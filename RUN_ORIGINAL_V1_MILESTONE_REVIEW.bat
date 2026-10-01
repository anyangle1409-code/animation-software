@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat ^<rN^>
  exit /b 2
)
rem Actual Blender capture only; verified candidate, live branch, fresh output paths.
rem Pending owner review is non-blocking. Never saves/promotes the candidate.
python scripts\original_v1_milestone_review.py "%~1" --capture
if errorlevel 1 exit /b 2
python scripts\build_original_v1_daily_status.py
exit /b %ERRORLEVEL%
