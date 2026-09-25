@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo === 1/4 Export V15 dressed GLB ===
python scripts\export_v15_hand_glb.py
if errorlevel 1 (
  set CODE=!ERRORLEVEL!
  python scripts\summarize_v15_results.py
  exit /b !CODE!
)

echo === 2/4 Frozen validation and V13e matched review ===
python scripts\finish_v15_hand.py
if errorlevel 1 (
  set CODE=!ERRORLEVEL!
  python scripts\summarize_v15_results.py
  exit /b !CODE!
)

echo === 3/4 Latest-source integration validation ===
python scripts\run_v15_latest_source_validation.py
if errorlevel 1 (
  set CODE=!ERRORLEVEL!
  python scripts\summarize_v15_results.py
  exit /b !CODE!
)

echo === 4/4 Consolidated report ===
python scripts\summarize_v15_results.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo V15 POST-EDIT PIPELINE COMPLETE
echo Read V15_POST_EDIT_REPORT.md and inspect the three matched V13e/V15 boards.
echo Do not refit grips or promote automatically.
exit /b 0
