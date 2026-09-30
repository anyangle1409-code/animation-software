@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Read-only targeted deformation check for the current shoulder repair cycle.
rem Usage:
rem   RUN_ORIGINAL_V1_SHOULDER_CHECK.bat [candidate.blend] [label]
rem The Blender pose script never saves the candidate.

set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="claude/original-v1-blender-o2-20260929" (
  echo ERROR: Expected claude/original-v1-blender-o2-20260929; found "%CURRENT_BRANCH%".
  exit /b 2
)

set "CANDIDATE=%~1"
if "%CANDIDATE%"=="" set "CANDIDATE=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend"
if not exist "%CANDIDATE%" (
  echo ERROR: Candidate Blend not found: %CANDIDATE%
  exit /b 2
)

set "LABEL=%~2"
if "%LABEL%"=="" set "LABEL=shoulder_current"
set "OUT=ORIGINAL_V1_WORK\candidates\repair_checks\%LABEL%"
set "POSES=press_top,press_top_rhythm,pullup_hang,pullup_hang_rhythm,pullup_top"

git diff --quiet HEAD -- scripts\pose_test_original_v1_o4_candidate_blender.py scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json
if errorlevel 1 (
  echo ERROR: Validation scripts/spec have uncommitted changes. Commit or discard them first.
  exit /b 2
)

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do (
    if not defined BLENDER set "BLENDER=%%I"
  )
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

if exist "%OUT%" (
  echo ERROR: Output folder already exists: %OUT%
  echo Use a new label so evidence from different candidates is never mixed.
  exit /b 2
)
mkdir "%OUT%"
if errorlevel 1 exit /b 2

echo ============================================================
echo ORIGINAL v1 shoulder deformation repair check
echo Candidate: %CANDIDATE%
echo Output:    %OUT%
echo Poses:     %POSES%
echo ============================================================

"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\pose_test_original_v1_o4_candidate_blender.py -- "%OUT%" "%POSES%"
if errorlevel 1 (
  echo ERROR: Blender shoulder pose test failed.
  exit /b 1
)

if not exist "%OUT%\pose_test_report.json" (
  echo ERROR: Pose report was not produced.
  exit /b 1
)

python scripts\compare_original_v1_deformation_reports.py ^
  ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  "%OUT%\pose_test_report.json" ^
  --profile development_blocker ^
  --poses "%POSES%" ^
  --json-out "%OUT%\comparison_vs_R2.json"

set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
  echo.
  echo Shoulder subset did not regress against R2.
  echo Inspect renders and comparison_vs_R2.json before accepting the repair.
) else (
  echo.
  echo Shoulder subset REGRESSED against R2 or the comparison failed.
  echo Do not promote this candidate. Inspect %OUT%\comparison_vs_R2.json
)
exit /b %RC%
