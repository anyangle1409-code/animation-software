@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Read-only shoulder/axilla deformation-layer diagnostic.
rem Usage:
rem   RUN_ORIGINAL_V1_SHOULDER_LAYER_DIAGNOSTIC.bat candidate.blend label [pose,pose,...] [samples]
rem
rem The candidate is NEVER saved. Output collision is refused.

set "CANDIDATE=%~1"
if "%CANDIDATE%"=="" (
  echo ERROR: candidate Blend is required.
  exit /b 2
)
if not exist "%CANDIDATE%" (
  echo ERROR: Candidate Blend not found: %CANDIDATE%
  exit /b 2
)

set "LABEL=%~2"
if "%LABEL%"=="" (
  echo ERROR: fresh evidence label is required.
  exit /b 2
)

set "POSES=%~3"
if "%POSES%"=="" set "POSES=press_top,pullup_hang"

set "SAMPLES=%~4"
if "%SAMPLES%"=="" set "SAMPLES=13"

set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\shoulder_layer_diagnostics\%LABEL%"
set "OUT=%OUT_DIR%\shoulder_layer_diagnostic.json"
if exist "%OUT%" (
  echo ERROR: Evidence output already exists:
  echo   %OUT%
  echo Use a new label. Existing evidence is immutable.
  exit /b 2
)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

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

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)
if not defined PYTHON (
  for /f "delims=" %%I in ('where python.exe 2^>nul') do (
    if not defined PYTHON set "PYTHON=%%I"
  )
)

echo ============================================================
echo ORIGINAL v1 shoulder/axilla layer diagnostic
echo Candidate: %CANDIDATE%
echo Poses:     %POSES%
echo Samples:   %SAMPLES%
echo Output:    %OUT%
echo READ-ONLY: source Blend will not be saved.
echo ============================================================

"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\audit_original_v1_shoulder_layer_diagnostic_blender.py -- ^
  "%OUT%" "%POSES%" "%SAMPLES%"
if errorlevel 1 (
  echo ERROR: layer diagnostic failed.
  exit /b 1
)

if not exist "%OUT%" (
  echo ERROR: expected diagnostic was not produced.
  exit /b 1
)

if defined PYTHON (
  "%PYTHON%" scripts\validate_original_v1_shoulder_layer_diagnostic.py "%OUT%"
) else (
  rem Fallback: Blender's embedded Python can validate the JSON without relying
  rem on the Windows Store python alias.
  "%BLENDER%" --background --factory-startup --python-exit-code 1 ^
    --python scripts\validate_original_v1_shoulder_layer_diagnostic.py -- "%OUT%"
)
if errorlevel 1 (
  echo ERROR: diagnostic output failed validation.
  exit /b 1
)

echo.
echo PASS: read-only shoulder-layer evidence written:
echo   %OUT%
exit /b 0
