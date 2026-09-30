@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call PREFLIGHT_CLAUDE_ORIGINAL_V1.bat
if errorlevel 1 exit /b %ERRORLEVEL%

set "CANDIDATE=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend"
if not exist "%CANDIDATE%" (
  echo ERROR: Expected O4 candidate Blend is missing:
  echo   %CANDIDATE%
  exit /b 2
)

set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do (
    if not defined BLENDER set "BLENDER=%%I"
  )
)
if not defined BLENDER (
  for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do (
    if not defined BLENDER set "BLENDER=%%I"
  )
)
if not defined BLENDER (
  echo ERROR: Blender was not found. Set BLENDER_EXE to the full blender.exe path.
  exit /b 2
)

echo.
echo Opening guarded O4 candidate:
echo   %CANDIDATE%
echo.
echo IMPORTANT:
echo   - This is a candidate, not production.
echo   - Priority 1 is shoulder / upper torso.
echo   - Do not copy V8-V15f geometry, weights, bind data or calibration.
echo   - Save meaningful repairs as NEW numbered candidates/checkpoints.
echo.

start "" "%BLENDER%" "%CD%\%CANDIDATE%"
exit /b 0
