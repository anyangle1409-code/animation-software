@echo off
setlocal EnableExtensions

for /f "delims=" %%B in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "HGPT_BRANCH=%%B"
if /I not "%HGPT_BRANCH%"=="claude/original-v1-blender-o2-20260929" (
  echo ERROR: Run this only on claude/original-v1-blender-o2-20260929.
  echo Current branch: %HGPT_BRANCH%
  exit /b 2
)

set "PROFILE=%~1"
if "%PROFILE%"=="" set "PROFILE=development_blocker"

if /I not "%PROFILE%"=="development_blocker" if /I not "%PROFILE%"=="production_target" (
  echo ERROR: profile must be development_blocker or production_target.
  exit /b 2
)

set "POSE_REPORT=ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json"
set "GRIP_REPORT=ORIGINAL_V1_WORK\candidates\grip_test_report_r1.json"
set "OUT_JSON=ORIGINAL_V1_WORK\candidates\deformation_acceptance_%PROFILE%.json"
set "OUT_MD=ORIGINAL_V1_WORK\candidates\deformation_acceptance_%PROFILE%.md"

if not exist "%POSE_REPORT%" (
  echo ERROR: Missing %POSE_REPORT%
  exit /b 2
)
echo [1/3] Testing deformation tooling...
python -m unittest discover -s scripts -p "test_*deformation*.py"
if errorlevel 1 exit /b %errorlevel%

echo [2/3] Verifying pinned R2 baseline...
python scripts\verify_original_v1_deformation_baseline.py
if errorlevel 1 exit /b %errorlevel%

echo [3/3] Evaluating ORIGINAL v1 candidate against %PROFILE%...
python scripts\evaluate_original_v1_deformation_report.py ^
  "%POSE_REPORT%" ^
  --grip-report "%GRIP_REPORT%" ^
  --profile "%PROFILE%" ^
  --require-group core_five ^
  --json-out "%OUT_JSON%" ^
  --markdown-out "%OUT_MD%"

set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
  echo PASS: %PROFILE% deformation gate.
) else (
  echo FAIL: %PROFILE% deformation gate. This is expected until the candidate is repaired.
  echo Review: %OUT_MD%
)
exit /b %RC%
