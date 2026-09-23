@echo off
setlocal
cd /d "%~dp0"
python scripts\audit_prep_workspace.py
if errorlevel 1 exit /b %errorlevel%
python scripts\preflight_resume.py
if errorlevel 1 exit /b %errorlevel%
python scripts\prepare_rig63_validation.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo Read CURRENT_STATE.md and RIG_63_FREEZE.md.
echo Rig baseline: hgpt_canonical_v3 / 63 bones / frozen at 19ca602.
echo Start a fresh candidate with START_CANDIDATE.bat version.
echo After editing/exporting, use FINISH_CANDIDATE.bat version task.
echo Ready: knee retopology, hand geometry, materials, shoulder topology planning.
echo Runtime validation: 614033b with mirrored-hand roll fixed. Keep scapular rhythm off; treat grip refit/palm export as asset work.
