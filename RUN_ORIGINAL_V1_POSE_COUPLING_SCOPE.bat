@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Read-only pose -> connected-tissue review-scope audit.
rem Usage:
rem   RUN_ORIGINAL_V1_POSE_COUPLING_SCOPE.bat candidate.blend fresh-label [pose,pose,...]

set "CANDIDATE=%~1"
set "LABEL=%~2"
set "POSES=%~3"
if "%CANDIDATE%"=="" (
  echo ERROR: candidate Blend required.
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

set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\pose_coupling_scope\%LABEL%"
set "OUT=%OUT_DIR%\pose_coupling_scope.json"
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
echo ORIGINAL v1 POSE -> CONNECTED TISSUE SCOPE
echo Candidate: %CANDIDATE%
echo Output:    %OUT%
if not "%POSES%"=="" echo Poses:     %POSES%
echo READ-ONLY: source Blend is never saved.
echo ============================================================

if "%POSES%"=="" (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\audit_original_v1_pose_coupling_scope_blender.py -- "%OUT%"
) else (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\audit_original_v1_pose_coupling_scope_blender.py -- "%OUT%" "%POSES%"
)
if errorlevel 1 exit /b 1

if not exist "%OUT%" (
  echo ERROR: expected output missing.
  exit /b 1
)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON (
  for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
)
if defined PYTHON (
  "%PYTHON%" scripts\validate_original_v1_pose_coupling_scope.py "%OUT%"
) else (
  "%BLENDER%" --background --factory-startup --python-exit-code 1 ^
    --python scripts\validate_original_v1_pose_coupling_scope.py -- "%OUT%"
)
if errorlevel 1 exit /b 1

echo PASS: %OUT%
exit /b 0
