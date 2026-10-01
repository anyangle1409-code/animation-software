@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Read-only focused diagnostics for the remaining ORIGINAL-v1 blockers.
rem Usage: RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat <rN>
rem Requires the local git-ignored candidate .blend. Produces small JSON/Markdown
rem diagnostics only; the temporary NPZ dump is deleted before exit.

set "REV=%~1"
if "%REV%"=="" (
  echo Usage: RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat ^<rN^>
  exit /b 2
)

set "EXPECTED_BRANCH=claude/original-v1-blender-o2-20260929"
set "CURRENT_BRANCH="
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="%EXPECTED_BRANCH%" (
  echo ERROR: Expected %EXPECTED_BRANCH%; found "%CURRENT_BRANCH%".
  exit /b 2
)

git diff --quiet HEAD -- scripts\pose_test_original_v1_o4_candidate_blender.py scripts\dump_original_v1_o4_pose_skinning_blender.py scripts\analyze_original_v1_pose_dump.py scripts\probe_original_v1_grip_penetration_blender.py ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json
if errorlevel 1 (
  echo ERROR: Diagnostic scripts/spec have uncommitted changes.
  exit /b 2
)

set "CANDIDATE=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.blend"
set "MANIFEST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.json"
if not exist "%CANDIDATE%" (
  echo ERROR: Candidate Blend not found: %CANDIDATE%
  exit /b 2
)
if not exist "%MANIFEST%" (
  echo ERROR: Candidate manifest not found: %MANIFEST%
  exit /b 2
)
python scripts\verify_original_v1_local_candidate.py "%CANDIDATE%" "%MANIFEST%"
if errorlevel 1 (
  echo ERROR: Local candidate does not match its committed manifest.
  exit /b 2
)

set "OUT=ORIGINAL_V1_WORK\candidates\repair_checks\remaining_diagnostics_%REV%"
if exist "%OUT%" (
  echo ERROR: Output folder already exists: %OUT%
  exit /b 2
)
mkdir "%OUT%"
if errorlevel 1 exit /b 2

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

set "DUMP=%TEMP%\hgpt_%REV%_remaining_pose_dump.npz"
if exist "%DUMP%" del /q "%DUMP%"

echo ============================================================
echo ORIGINAL v1 remaining-blocker diagnostics
echo Candidate: %REV%
echo No model changes will be made.
echo ============================================================

echo [1/3] Dump exact push-up/lunge skinning...
"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\dump_original_v1_o4_pose_skinning_blender.py -- "%DUMP%" "pushup_bottom,lunge"
if errorlevel 1 goto :fail

echo [2/3] Locate exact extreme edges and current bone weights...
python scripts\analyze_original_v1_pose_dump.py "%DUMP%" ^
  --json-out "%OUT%\edge_extremes.json" ^
  --markdown-out "%OUT%\edge_extremes.md"
if errorlevel 1 goto :fail

echo [3/3] Probe grip penetration before and after finger closing...
"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\probe_original_v1_grip_penetration_blender.py -- "%OUT%\grip_penetration.json"
if errorlevel 1 goto :fail

if exist "%DUMP%" del /q "%DUMP%"
echo.
echo Diagnostics complete: %OUT%
echo Evidence only: no mesh, rig, weights, gates or baseline were changed.
exit /b 0

:fail
if exist "%DUMP%" del /q "%DUMP%"
echo ERROR: remaining-blocker diagnostics failed.
exit /b 1
