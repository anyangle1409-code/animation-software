@echo off
setlocal
cd /d "%~dp0"

echo === 1/3 Export V15 dressed GLB ===
python scripts\export_v15_hand_glb.py
if errorlevel 1 exit /b %errorlevel%

echo === 2/3 Frozen validation and V13e matched review ===
python scripts\finish_v15_hand.py
if errorlevel 1 exit /b %errorlevel%

echo === 3/3 Latest-source integration validation ===
python scripts\run_v15_latest_source_validation.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo V15 POST-EDIT PIPELINE COMPLETE
echo Review the generated V13e/V15 comparison boards before any grip refit or promotion.
exit /b 0
