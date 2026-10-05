@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "CANDIDATE=%~1"
set "REV=%~2"
set "LABEL=%~3"
set "SWEEPS=%~4"
if "%CANDIDATE%"=="" (echo ERROR: candidate Blend required.& exit /b 2)
if "%REV%"=="" (echo ERROR: candidate revision required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if not exist "%CANDIDATE%" (echo ERROR: candidate not found: %CANDIDATE%& exit /b 2)
set "OUT=ORIGINAL_V1_WORK\candidates\repair_checks\human_movement_sweep_visuals\%LABEL%"
if exist "%OUT%" (echo ERROR: visual output directory exists. Use a fresh label.& exit /b 2)
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER (echo ERROR: Blender not found. Set BLENDER_EXE.& exit /b 2)
if "%SWEEPS%"=="" (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\capture_original_v1_human_movement_sweep_visual_blender.py -- "%OUT%" "%REV%"
) else (
  "%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
    --python scripts\capture_original_v1_human_movement_sweep_visual_blender.py -- "%OUT%" "%REV%" "%SWEEPS%"
)
if errorlevel 1 exit /b 1
echo PASS: raw visual sweep captures written:
echo   %OUT%
echo NOTE: engineering_review remains PENDING until Work reviews the images.
exit /b 0
