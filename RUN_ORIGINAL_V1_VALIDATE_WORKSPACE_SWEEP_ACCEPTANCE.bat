@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "WORKSPACE=%~1"
if "%WORKSPACE%"=="" (echo ERROR: finalized repair workspace required.& exit /b 2)
if not exist "%WORKSPACE%\workspace_finalization_manifest.json" (echo ERROR: workspace is not finalized.& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

"%PYTHON%" scripts\validate_original_v1_workspace_sweep_acceptance.py "%WORKSPACE%"
if errorlevel 1 exit /b 1

echo.
echo PASS: every required sweep acceptance record is candidate-bound and engineering PASS.
echo Owner acceptance and production approval remain separate.
exit /b 0
