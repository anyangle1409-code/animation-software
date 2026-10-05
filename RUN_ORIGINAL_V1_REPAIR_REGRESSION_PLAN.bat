@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PACKAGES=%~1"
set "OUT=%~2"
if "%PACKAGES%"=="" (echo ERROR: comma-separated repair package ids required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh output json path required.& exit /b 2)
if exist "%OUT%" (echo ERROR: output exists; use a fresh path.& exit /b 2)
for %%D in ("%OUT%") do if not exist "%%~dpD" mkdir "%%~dpD"
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\build_original_v1_repair_regression_plan.py --packages "%PACKAGES%" --out "%OUT%"
exit /b %ERRORLEVEL%
