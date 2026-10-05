@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "WORKSPACE=%~1"
set "FINAL_CANDIDATE=%~2"
if "%WORKSPACE%"=="" (echo ERROR: repair workspace directory required.& exit /b 2)
if "%FINAL_CANDIDATE%"=="" (echo ERROR: final repaired Blend required.& exit /b 2)
if not exist "%WORKSPACE%\workspace_manifest.json" (echo ERROR: workspace manifest missing.& exit /b 2)
if not exist "%FINAL_CANDIDATE%" (echo ERROR: final candidate not found.& exit /b 2)
if exist "%WORKSPACE%\workspace_finalization_manifest.json" (echo ERROR: workspace already finalized.& exit /b 2)
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\finalize_original_v1_repair_workspace.py --workspace "%WORKSPACE%" --final-candidate "%FINAL_CANDIDATE%"
exit /b %ERRORLEVEL%
