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

set "BLEND=ORIGINAL_V1_WORK\HomeGymPT_Male_ORIGINAL_v1.blend"
if not exist "%BLEND%" (
  echo Missing %BLEND%
  echo Run GENERATE_ORIGINAL_V1_CLEAN_SCAFFOLD.bat first.
  exit /b 1
)

"%BLENDER%" --background "%BLEND%" --python scripts\audit_original_v1_blender.py
if errorlevel 1 (
  echo.
  echo ORIGINAL v1 clean-room audit FAILED.
  exit /b 1
)

echo.
echo ORIGINAL v1 clean-room audit PASS.
exit /b 0
