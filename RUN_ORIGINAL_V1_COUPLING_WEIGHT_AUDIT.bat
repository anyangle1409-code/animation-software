@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Generic read-only anatomical coupling weight audit.
rem Usage:
rem   RUN_ORIGINAL_V1_COUPLING_WEIGHT_AUDIT.bat candidate.blend declaration.json fresh-label

set "CANDIDATE=%~1"
set "DECL=%~2"
set "LABEL=%~3"
if "%CANDIDATE%"=="" (
  echo ERROR: candidate Blend required.
  exit /b 2
)
if "%DECL%"=="" (
  echo ERROR: coupling-zone declaration required.
  exit /b 2
)
if "%LABEL%"=="" (
  echo ERROR: fresh label required.
  exit /b 2
)
if not exist "%CANDIDATE%" (
  echo ERROR: candidate not found: %CANDIDATE%
  exit /b 2
)
if not exist "%DECL%" (
  echo ERROR: declaration not found: %DECL%
  exit /b 2
)

set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\coupling_weights\%LABEL%"
set "OUT=%OUT_DIR%\coupling_weight_audit.json"
if exist "%OUT%" (
  echo ERROR: evidence exists; use a fresh label:
  echo   %OUT%
  exit /b 2
)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
)
if not defined BLENDER (
  for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
)
if not defined BLENDER (
  echo ERROR: Blender not found. Set BLENDER_EXE.
  exit /b 2
)

echo ============================================================
echo ORIGINAL v1 anatomical coupling weight audit
echo Candidate:    %CANDIDATE%
echo Declaration:  %DECL%
echo Output:       %OUT%
echo READ-ONLY: source Blend is never saved.
echo ============================================================

"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\audit_original_v1_coupling_zone_weights_blender.py -- ^
  "%DECL%" "%OUT%"
if errorlevel 1 exit /b 1

if not exist "%OUT%" (
  echo ERROR: expected output missing.
  exit /b 1
)

echo PASS: %OUT%
exit /b 0
