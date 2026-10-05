@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "SCOPE=%~1"
set "LABEL=%~2"
if "%SCOPE%"=="" (echo ERROR: pose_coupling_scope.json required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if not exist "%SCOPE%" (echo ERROR: scope report not found: %SCOPE%& exit /b 2)
set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\pose_evidence_plans\%LABEL%"
set "OUT=%OUT_DIR%\pose_capture_evidence_plan.json"
if exist "%OUT%" (echo ERROR: evidence plan exists; use a fresh label.& exit /b 2)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\build_original_v1_pose_capture_evidence_plan.py "%SCOPE%" "%OUT%"
if errorlevel 1 exit /b 1
echo PASS: %OUT%
exit /b 0
