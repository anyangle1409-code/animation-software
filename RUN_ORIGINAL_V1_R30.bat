@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Deterministic r29 -> r30 helper for the current ORIGINAL-v1 Priority-2 hand work.
rem This does not alter thresholds, R2, promotion state, or any production asset.
rem It creates a NEW local r30 .blend, runs the complete evidence suite, compares
rem against r29 and r28, rebuilds the candidate summary, and collects a compact
rem visual review set that can be committed for phone/GitHub review.

set "EXPECTED_BRANCH=claude/original-v1-blender-o2-20260929"
set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="%EXPECTED_BRANCH%" (
  echo ERROR: Expected %EXPECTED_BRANCH%; found "%CURRENT_BRANCH%".
  exit /b 2
)

git diff --quiet HEAD -- scripts\optimize_original_v1_o4_shoulder_weights.py scripts\dump_original_v1_o4_pose_skinning_blender.py scripts\apply_original_v1_o4_weight_solution_blender.py scripts\pose_test_original_v1_o4_candidate_blender.py scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json
if errorlevel 1 (
  echo ERROR: r30 generation/validation code has uncommitted changes.
  echo Commit or discard those changes before producing evidence.
  exit /b 2
)

set "R29=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.blend"
set "R30=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend"
set "WS=ORIGINAL_V1_WORK\candidates\weight_solutions"
set "DUMP=%WS%\r29_for_o22_dump.npz"
set "INIT=%WS%\o21.npz"
set "SOL=%WS%\o22.npz"
set "R2=ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json"
set "RC=ORIGINAL_V1_WORK\candidates\repair_checks"

for %%F in ("%R29%" "%INIT%" "%R2%") do (
  if not exist "%%~F" (
    echo ERROR: Required input missing: %%~F
    exit /b 2
  )
)

set "R29_MANIFEST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json"
python scripts\verify_original_v1_local_candidate.py "%R29%" "%R29_MANIFEST%"
if errorlevel 1 (
  echo ERROR: Local r29 does not match its committed manifest. Do not run o22.
  exit /b 2
)

for %%F in ("%R30%" "%SOL%") do (
  if exist "%%~F" (
    echo ERROR: Refusing to overwrite existing r30 work: %%~F
    echo Inspect the existing file before deciding whether a new revision label is required.
    exit /b 2
  )
)
rem The pose dump is a disposable read-only derivative. Claude's battery-stop session
rem may have left one behind even though no o22 solution exists, so regenerate it.
if exist "%DUMP%" del /q "%DUMP%"

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
)
if not defined BLENDER (
  for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do (
    if not defined BLENDER set "BLENDER=%%I"
  )
)
if not defined BLENDER (
  echo ERROR: Blender not found. Set BLENDER_EXE to blender.exe.
  exit /b 2
)

echo ============================================================
echo ORIGINAL v1 r30 deterministic candidate run
echo Source: r29
echo Optimiser: o22, warm-start o21, pinned R2 comparator bounds
echo ============================================================

echo [1/7] Dump r29 pose skinning...
"%BLENDER%" --background --factory-startup "%R29%" --python-exit-code 1 ^
  --python scripts\dump_original_v1_o4_pose_skinning_blender.py -- "%DUMP%"
if errorlevel 1 exit /b 1

echo [2/7] Solve o22...
python scripts\optimize_original_v1_o4_shoulder_weights.py "%DUMP%" "%SOL%" ^
  --preset o22 --init "%INIT%" --r2-report "%R2%"
if errorlevel 1 exit /b 1

echo [3/7] Apply o22 to a NEW r30 candidate...
"%BLENDER%" --background --factory-startup "%R29%" --python-exit-code 1 ^
  --python scripts\apply_original_v1_o4_weight_solution_blender.py -- "%SOL%" "%R30%"
if errorlevel 1 exit /b 1

echo [4/7] Run full 15-pose evidence and compare with r29/R2...
call RUN_ORIGINAL_V1_FULL_EVIDENCE.bat r30 r29
if errorlevel 1 (
  echo ERROR: Full r30 evidence pipeline failed.
  exit /b 1
)

echo [5/7] Add explicit r30 comparison against r28...
python scripts\compare_original_v1_deformation_reports.py ^
  "%RC%\full_r28_merged_pose_report.json" ^
  "%RC%\full_r30_merged_pose_report.json" ^
  --baseline-grip-report "%RC%\full_r28_merged_pose_report.json" ^
  --candidate-grip-report "%RC%\full_r30_merged_pose_report.json" ^
  --profile development_blocker ^
  --json-out "%RC%\full_r30_comparison_vs_r28.json" ^
  --report-only
if errorlevel 1 exit /b 1

echo [6/7] Rebuild generated candidate review...
python scripts\build_original_v1_candidate_review.py
if errorlevel 1 exit /b 1

echo [7/7] Collect compact visual review images...
python scripts\collect_original_v1_review_images.py r30
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo r30 run complete.
echo DO NOT mark production approved automatically.
echo Review:
echo   %RC%\full_r30_deformation_acceptance.md
echo   %RC%\full_r30_comparison_vs_R2.json
echo   %RC%\full_r30_comparison_vs_r29.json
echo   %RC%\full_r30_comparison_vs_r28.json
echo   ORIGINAL_V1_WORK\candidates\review\visual_r30\
echo ============================================================
exit /b 0
