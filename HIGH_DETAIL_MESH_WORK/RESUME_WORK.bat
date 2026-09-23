@echo off
setlocal
cd /d "%~dp0"
python scripts\audit_prep_workspace.py
if errorlevel 1 exit /b %errorlevel%
python scripts\preflight_resume.py
if errorlevel 1 exit /b %errorlevel%
python scripts\prepare_rig55_validation.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo Read CURRENT_STATE.md and RIG_55_BASELINE.md.
echo Rig baseline: hgpt_canonical_v2 / 55 bones / c2372c1.
echo Start a fresh candidate with START_CANDIDATE.bat version.
echo After editing/exporting, use FINISH_CANDIDATE.bat version task.
echo Ready: knee retopology, hand geometry, materials, shoulder topology planning.
echo Hold final hand weights and scapular rhythm until their remaining decisions are settled.
