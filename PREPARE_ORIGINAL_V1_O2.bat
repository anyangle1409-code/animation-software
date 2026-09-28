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
  echo Missing O1 Blend. Run PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat on the laptop first.
  exit /b 1
)

node scripts\export-original-v4-rig.mjs --check
if errorlevel 1 exit /b 1
"%BLENDER%" --background "%BLEND%" --python scripts\materialize_original_v4_blender.py
if errorlevel 1 exit /b 1
"%BLENDER%" --background "%BLEND%" --python scripts\audit_original_v4_blender.py
if errorlevel 1 exit /b 1

echo O2 v4 rig ready. Open %BLEND% in Blender.
exit /b 0
