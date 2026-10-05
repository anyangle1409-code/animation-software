@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MANIFEST=%~1"
set "OUT=%~2"
if "%MANIFEST%"=="" (echo ERROR: candidate comparison manifest required.& exit /b 2)
if "%OUT%"=="" (echo ERROR: fresh output json path required.& exit /b 2)
if not exist "%MANIFEST%" (echo ERROR: manifest not found: %MANIFEST%& exit /b 2)
if exist "%OUT%" (echo ERROR: output exists; use a fresh path.& exit /b 2)
for %%D in ("%OUT%") do if not exist "%%~dpD" mkdir "%%~dpD"
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\build_original_v1_candidate_comparison_report.py "%MANIFEST%" "%OUT%"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" echo ELIGIBLE: %OUT%
if "%RC%"=="3" echo BLOCKED BY EVIDENCE: %OUT%
exit /b %RC%
