@echo off
setlocal
cd /d "%~dp0"

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"

if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do (
    if not defined BLENDER set "BLENDER=%%I"
  )
)

if not defined BLENDER (
  for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do (
    set "BLENDER=%%I"
  )
)

if not defined BLENDER (
  echo Blender not found. Set BLENDER_EXE to blender.exe.
  exit /b 1
)

echo Using Blender: %BLENDER%
"%BLENDER%" --background --factory-startup --python scripts\init_original_v1_blender.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo Clean-room ORIGINAL v1 workspace created under ORIGINAL_V1_WORK.
exit /b 0
