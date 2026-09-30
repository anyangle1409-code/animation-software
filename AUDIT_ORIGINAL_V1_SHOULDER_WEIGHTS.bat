@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call PREFLIGHT_CLAUDE_ORIGINAL_V1.bat
if errorlevel 1 exit /b %ERRORLEVEL%

set "CANDIDATE=%~1"
if "%CANDIDATE%"=="" set "CANDIDATE=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend"
if not exist "%CANDIDATE%" (
  echo ERROR: Candidate Blend not found: %CANDIDATE%
  exit /b 2
)

set "LABEL=%~2"
if "%LABEL%"=="" set "LABEL=r2_before_repair"
set "OUT_DIR=ORIGINAL_V1_WORK\candidates\repair_checks\weight_audits"
set "OUT=%OUT_DIR%\shoulder_weights_%LABEL%.json"

if exist "%OUT%" (
  echo ERROR: Evidence file already exists:
  echo   %OUT%
  echo Use a new label so before/after evidence is never overwritten.
  exit /b 2
)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

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
  echo ERROR: Blender not found. Set BLENDER_EXE to blender.exe.
  exit /b 2
)

echo ============================================================
echo ORIGINAL v1 O4 shoulder-weight audit
echo Candidate: %CANDIDATE%
echo Evidence:  %OUT%
echo This run is read-only and does not save the Blend.
echo ============================================================

"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\audit_original_v1_shoulder_weights_blender.py -- "%OUT%"
if errorlevel 1 (
  echo ERROR: Shoulder-weight audit failed.
  exit /b 1
)

if not exist "%OUT%" (
  echo ERROR: Expected audit report was not produced.
  exit /b 1
)

echo.
echo PASS: shoulder-weight evidence written to:
echo   %OUT%
exit /b 0
