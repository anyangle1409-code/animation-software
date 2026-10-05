@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Package-aware sweep preparation pipeline.
rem Usage:
rem   RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PIPELINE.bat candidate.blend revision RP-ID[,RP-ID...] fresh-label
rem
rem This command PREPARES review evidence only. It never infers CALIBRATED,
rem engineering PASS, owner acceptance, or production approval.

set "CANDIDATE=%~1"
set "REV=%~2"
set "PACKAGES=%~3"
set "LABEL=%~4"
set "CALIBRATED=%~5"

if "%CANDIDATE%"=="" (echo ERROR: candidate Blend required.& exit /b 2)
if "%REV%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%PACKAGES%"=="" (echo ERROR: repair package ids required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if not exist "%CANDIDATE%" (echo ERROR: candidate not found: %CANDIDATE%& exit /b 2)

set "PIPE=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweep_pipeline\%LABEL%"
set "PLAN=%PIPE%\pipeline_plan.json"
set "SWEEPS_FILE=%PIPE%\required_sweeps.txt"
set "CONTACT_FILE=%PIPE%\contact_sweeps.txt"
set "CAL=%PIPE%\runner_calibration_IN_REVIEW.json"
set "REVIEW=%PIPE%\review_workspace"

if exist "%PIPE%" (
  echo ERROR: pipeline output exists. Use a fresh label:
  echo   %PIPE%
  exit /b 2
)
mkdir "%PIPE%"

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found. Set PYTHON_EXE.& exit /b 2)

"%PYTHON%" scripts\build_original_v1_human_movement_sweep_pipeline_plan.py ^
  --packages "%PACKAGES%" ^
  --out "%PLAN%" ^
  --sweeps-out "%SWEEPS_FILE%" ^
  --contact-out "%CONTACT_FILE%"
if errorlevel 1 exit /b 1

set "SWEEPS="
set /p SWEEPS=<"%SWEEPS_FILE%"
set "CONTACT_SWEEPS="
set /p CONTACT_SWEEPS=<"%CONTACT_FILE%"

if "%SWEEPS%"=="" (
  echo.
  echo PASS: selected repair packages have no sweep-only movements.
  echo No generic sweep pipeline run is required.
  echo Plan:
  echo   %PLAN%
  exit /b 0
)

set "RAW_LABEL=%LABEL%_all11"
set "VISUAL_LABEL=%LABEL%_visual"
set "CONTACT_LABEL=%LABEL%_contact"

set "RAW=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweeps\%RAW_LABEL%\human_movement_sweeps.json"
set "VISUAL_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweep_visuals\%VISUAL_LABEL%"
set "CONTACT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweep_contact\%CONTACT_LABEL%"

echo ============================================================
echo ORIGINAL v1 HUMAN MOVEMENT SWEEP PIPELINE
echo Candidate: %CANDIDATE%
echo Revision:  %REV%
echo Packages:  %PACKAGES%
echo Required sweep-only movements: %SWEEPS%
echo Contact-bearing subset: %CONTACT_SWEEPS%
echo ============================================================

if not "%CALIBRATED%"=="" (
  if not exist "%CALIBRATED%" (
    echo ERROR: supplied calibrated runner record not found:
    echo   %CALIBRATED%
    exit /b 2
  )
  "%PYTHON%" scripts\validate_original_v1_human_movement_sweep_runner_calibration.py "%CALIBRATED%" --require-calibrated
  if errorlevel 1 exit /b 1
  set "CAL=%CALIBRATED%"
  set "RAW_LABEL=%LABEL%_selected"
  set "RAW=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweeps\%RAW_LABEL%\human_movement_sweeps.json"
  call RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat "%CANDIDATE%" "%RAW_LABEL%" "%SWEEPS%"
  if errorlevel 1 exit /b 1
) else (
  rem First-time calibration is authority-wide, so raw execution runs all 11.
  call RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat "%CANDIDATE%" "%RAW_LABEL%"
  if errorlevel 1 exit /b 1

  call RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CALIBRATION.bat "%RAW%" "%REV%" "%CAL%"
  if errorlevel 1 exit /b 1
)

call RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUALS.bat "%CANDIDATE%" "%REV%" "%VISUAL_LABEL%" "%SWEEPS%"
if errorlevel 1 exit /b 1

set "CONTACT_ARG=-"
if not "%CONTACT_SWEEPS%"=="" (
  call RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW.bat "%CANDIDATE%" "%REV%" "%CONTACT_LABEL%" "%CONTACT_SWEEPS%"
  if errorlevel 1 exit /b 1
  set "CONTACT_ARG=%CONTACT_DIR%"
)

call RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_REVIEW_WORKSPACE.bat ^
  "%RAW%" "%REV%" "%CAL%" "%VISUAL_DIR%" "%CONTACT_ARG%" "%REVIEW%" "%SWEEPS%"
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo PREPARATION COMPLETE
echo Pipeline plan:
echo   %PLAN%
echo Calibration record:
echo   %CAL%
if not "%CALIBRATED%"=="" echo Reused existing validated CALIBRATED runner record.
echo Review workspace:
echo   %REVIEW%
echo.
echo IMPORTANT:
echo - Calibration is still IN_REVIEW.
echo - Per-sweep review/acceptance remains PENDING.
echo - Work must review human evidence, motion, visuals and contact as required.
echo - No model/anatomy PASS is inferred by this command.
echo ============================================================
exit /b 0
