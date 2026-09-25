@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set VERSION=%~1
if "%VERSION%"=="" set VERSION=v15a_deep_hand_rebuild

echo Candidate: %VERSION%
echo === 1/4 Export dressed GLB ===
python scripts\export_v15_hand_glb.py --version %VERSION%
if errorlevel 1 (
  set CODE=!ERRORLEVEL!
  python scripts\summarize_v15_results.py --version %VERSION%
  exit /b !CODE!
)

echo === 2/4 Frozen validation and V13e matched review ===
python scripts\finish_v15_hand.py --version %VERSION%
if errorlevel 1 (
  set CODE=!ERRORLEVEL!
  python scripts\summarize_v15_results.py --version %VERSION%
  exit /b !CODE!
)

echo === 3/4 Latest-source integration validation ===
python scripts\run_v15_latest_source_validation.py --version %VERSION%
if errorlevel 1 (
  set CODE=!ERRORLEVEL!
  python scripts\summarize_v15_results.py --version %VERSION%
  exit /b !CODE!
)

echo === 4/4 Consolidated report ===
python scripts\summarize_v15_results.py --version %VERSION%
if errorlevel 1 exit /b %errorlevel%

echo.
echo V15 POST-EDIT PIPELINE COMPLETE: %VERSION%
echo Read V15_POST_EDIT_REPORT_%VERSION%.md and inspect the matched V13e/candidate boards.
echo Do not refit grips or promote automatically.
exit /b 0
