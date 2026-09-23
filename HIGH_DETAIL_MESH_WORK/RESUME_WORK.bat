@echo off
setlocal
cd /d "%~dp0"
python scripts\preflight_resume.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo Read CURRENT_STATE.md and WORK_START_HERE.md.
echo Current reviewed geometry baseline: V6 knee seam.
echo Ready work: knee retopology, hand anatomy, skin/materials.
echo Hold final shoulder weights until the canonical scapula rig is confirmed.
