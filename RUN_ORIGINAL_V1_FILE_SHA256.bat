@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "FILE=%~1"
if "%FILE%"=="" (echo ERROR: file required.& exit /b 2)
if not exist "%FILE%" (echo ERROR: file not found: %FILE%& exit /b 2)
set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)
"%PYTHON%" scripts\sha256_file.py "%FILE%"
exit /b %ERRORLEVEL%
