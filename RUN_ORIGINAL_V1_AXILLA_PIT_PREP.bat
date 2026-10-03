@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Read-only r55+ axilla face-collapse audit and pre-edit local mask declaration.
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_PREP.bat <source-rN> <target-rN>
rem Example: RUN_ORIGINAL_V1_AXILLA_PIT_PREP.bat r55 r56
rem Never saves the Blend and never creates a candidate.

set "SOURCE_REV=%~1"
set "TARGET_REV=%~2"
if "%SOURCE_REV%"=="" (
  echo Usage: RUN_ORIGINAL_V1_AXILLA_PIT_PREP.bat ^<source-rN^> ^<target-rN^>
  exit /b 2
)
if "%TARGET_REV%"=="" (
  echo Usage: RUN_ORIGINAL_V1_AXILLA_PIT_PREP.bat ^<source-rN^> ^<target-rN^>
  exit /b 2
)
if /I "%SOURCE_REV%"=="%TARGET_REV%" (
  echo ERROR: Source and target revisions must differ.
  exit /b 2
)

set "EXPECTED_BRANCH=claude/original-v1-blender-o2-20260929"
set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="%EXPECTED_BRANCH%" (
  echo ERROR: Expected %EXPECTED_BRANCH%; found "%CURRENT_BRANCH%".
  exit /b 2
)

git diff --quiet HEAD -- scripts\pose_test_original_v1_o4_candidate_blender.py scripts\audit_original_v1_axilla_pit_blender.py scripts\verify_original_v1_local_candidate.py
if errorlevel 1 (
  echo ERROR: Axilla diagnostic inputs have uncommitted changes.
  exit /b 2
)

rem Optional override (default 1 ring, safety cap unchanged): set AXILLA_PIT_RINGS=0 for a tighter mask.
if "%AXILLA_PIT_RINGS%"=="" set "AXILLA_PIT_RINGS=1"
set "SOURCE_BLEND=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.blend"
set "SOURCE_MANIFEST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.json"
set "TARGET_BLEND=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%TARGET_REV%.blend"
set "TARGET_MANIFEST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%TARGET_REV%.json"
set "OUT=ORIGINAL_V1_WORK\candidates\repair_preparation\%TARGET_REV%_axilla_pit_declared"

if not exist "%SOURCE_BLEND%" (
  echo ERROR: Source candidate Blend not found: %SOURCE_BLEND%
  exit /b 2
)
if not exist "%SOURCE_MANIFEST%" (
  echo ERROR: Source candidate manifest not found: %SOURCE_MANIFEST%
  exit /b 2
)
if exist "%TARGET_BLEND%" (
  echo ERROR: Target candidate already exists: %TARGET_BLEND%
  exit /b 2
)
if exist "%TARGET_MANIFEST%" (
  echo ERROR: Target manifest already exists: %TARGET_MANIFEST%
  exit /b 2
)
if exist "%OUT%" (
  echo ERROR: Target prep folder already exists: %OUT%
  exit /b 2
)

python scripts\verify_original_v1_local_candidate.py "%SOURCE_BLEND%" "%SOURCE_MANIFEST%"
if errorlevel 1 (
  echo ERROR: Local source candidate does not match its committed manifest.
  exit /b 2
)

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

mkdir "%OUT%"
if errorlevel 1 exit /b 2

echo ============================================================
echo ORIGINAL v1 axilla-pit pre-edit diagnostic
echo Source: %SOURCE_REV%
echo Planned target: %TARGET_REV%
echo No model changes will be made.
echo ============================================================

"%BLENDER%" --background --factory-startup "%SOURCE_BLEND%" --python-exit-code 1 ^
  --python scripts\audit_original_v1_axilla_pit_blender.py -- ^
  "%OUT%\face_collapse_audit.json" ^
  "%OUT%\face_collapse_audit.md" ^
  "%OUT%\axilla_pit_mask_declared_before_edit.json" ^
  "%TARGET_REV%" 17 12 %AXILLA_PIT_RINGS% 0.20 0.20 0.30
if errorlevel 1 goto :fail

echo.
echo PREP COMPLETE: %OUT%
echo The declaration was created before any model edit.
echo Next: use the declared mask only; keep rig, P3a poses, gates and baselines locked.
exit /b 0

:fail
echo ERROR: axilla-pit preparation failed.
echo The source Blend was not saved or modified.
exit /b 1
