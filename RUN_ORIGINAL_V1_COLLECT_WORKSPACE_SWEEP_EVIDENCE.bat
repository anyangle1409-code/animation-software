@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "WORKSPACE=%~1"
set "RAW=%~2"
set "VISUAL=%~3"
set "CAL=%~4"
set "CONTACT=%~5"

if "%WORKSPACE%"=="" (echo ERROR: finalized workspace required.& exit /b 2)
if "%RAW%"=="" (echo ERROR: raw sweep report required.& exit /b 2)
if "%VISUAL%"=="" (echo ERROR: sweep visual directory required.& exit /b 2)
if "%CAL%"=="" (echo ERROR: calibrated runner record required.& exit /b 2)
if not exist "%WORKSPACE%\workspace_finalization_manifest.json" (echo ERROR: workspace not finalized.& exit /b 2)
if not exist "%RAW%" (echo ERROR: raw sweep report missing.& exit /b 2)
if not exist "%VISUAL%" (echo ERROR: visual directory missing.& exit /b 2)
if not exist "%CAL%" (echo ERROR: calibration record missing.& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

if "%CONTACT%"=="" (
  "%PYTHON%" scripts\collect_original_v1_workspace_sweep_evidence.py ^
    --workspace "%WORKSPACE%" ^
    --raw-sweep-report "%RAW%" ^
    --visual-dir "%VISUAL%" ^
    --calibration-record "%CAL%"
) else (
  if not exist "%CONTACT%" (echo ERROR: contact directory missing.& exit /b 2)
  "%PYTHON%" scripts\collect_original_v1_workspace_sweep_evidence.py ^
    --workspace "%WORKSPACE%" ^
    --raw-sweep-report "%RAW%" ^
    --visual-dir "%VISUAL%" ^
    --calibration-record "%CAL%" ^
    --contact-dir "%CONTACT%"
)
exit /b %ERRORLEVEL%
