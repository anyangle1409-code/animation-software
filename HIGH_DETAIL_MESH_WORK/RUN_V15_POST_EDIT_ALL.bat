@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set VERSION=%~1
if "%VERSION%"=="" set VERSION=v15a_deep_hand_rebuild

echo Candidate: %VERSION%
echo === 1/5 Export dressed GLB ===
python scripts\export_v15_hand_glb.py --version %VERSION%
if errorlevel 1 goto :failed

echo === 2/5 Frozen validation and V13e matched review ===
python scripts\finish_v15_hand.py --version %VERSION%
if errorlevel 1 goto :failed

echo === 3/5 Latest-source integration validation ===
python scripts\run_v15_latest_source_validation.py --version %VERSION%
if errorlevel 1 goto :failed

echo === 4/5 Consolidated report ===
python scripts\summarize_v15_results.py --version %VERSION%
if errorlevel 1 goto :failed

echo === 5/5 Review dashboard and difference maps ===
python scripts\make_v15_review_dashboard.py --version %VERSION%
if errorlevel 1 goto :failed

echo.
echo V15 POST-EDIT PIPELINE COMPLETE: %VERSION%
echo Read V15_POST_EDIT_REPORT_%VERSION%.md and V15_REVIEW_%VERSION%.html.
echo Do not refit grips or promote automatically.
exit /b 0

:failed
set CODE=!ERRORLEVEL!
echo.
echo V15 pipeline stopped at a failing stage. Building the best partial report available...
python scripts\summarize_v15_results.py --version %VERSION%
python scripts\make_v15_review_dashboard.py --version %VERSION%
echo Follow V15_FAILURE_RECOVERY.md from the first failed stage.
exit /b !CODE!
