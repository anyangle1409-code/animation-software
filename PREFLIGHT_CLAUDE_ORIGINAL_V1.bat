@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "EXPECTED_BRANCH=claude/original-v1-blender-o2-20260929"
set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"

echo ============================================================
echo ORIGINAL v1 Claude laptop preflight
echo ============================================================
echo Branch: %CURRENT_BRANCH%

if /I not "%CURRENT_BRANCH%"=="%EXPECTED_BRANCH%" (
  echo ERROR: Expected %EXPECTED_BRANCH%.
  echo Do not run Blender work on another branch.
  exit /b 2
)

echo.
echo [1/5] Working tree...
git status --short
if errorlevel 1 exit /b 2

echo.
echo [2/5] Exact HEAD...
git rev-parse HEAD
if errorlevel 1 exit /b 2

echo.
echo [3/5] Candidate status contract...
python scripts\verify_original_v1_candidate_status.py
if errorlevel 1 (
  echo ERROR: Candidate status no longer matches repository evidence.
  exit /b 1
)

echo.
echo [4/5] Pinned R2 baseline integrity...
python scripts\verify_original_v1_deformation_baseline.py
if errorlevel 1 (
  echo ERROR: Pinned R2 baseline is not reproducible.
  exit /b 1
)

echo.
echo [5/5] Current deterministic repair queue...
python scripts\build_original_v1_repair_queue.py ^
  ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  --profile development_blocker ^
  --require-complete-ownership ^
  --expect-next-priority 1
if errorlevel 1 (
  echo ERROR: Repair queue is not in the expected guarded state.
  exit /b 1
)

echo.
echo ============================================================
echo PREFLIGHT PASS
echo Read docs\CLAUDE_LAPTOP_HANDOFF_20260930.md
echo Then read docs\ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md
echo Next Blender task: Priority 1 - shoulder / upper torso.
echo After a repair, use a NEW evidence label, for example:
echo   RUN_ORIGINAL_V1_REPAIR_CHECK.bat shoulder path\to\candidate.blend shoulder_r3
echo ============================================================
exit /b 0
