@echo off
setlocal
rem Full deformation evidence for one numbered O4 candidate (read-only; never saves the Blend).
rem Usage: RUN_ORIGINAL_V1_FULL_EVIDENCE.bat <rN> [prior rM]
rem Runs every repair group (shoulder, hand+grip, hip, pushup, row) with labels <group>_<rN>,
rem a neutral rest-pose control run (neutral_<rN>), then merges all 15 poses and runs the
rem committed evaluator, repair queue and comparator vs pinned R2 (and vs the prior candidate).
cd /d "%~dp0"
set "REV=%~1"
if "%REV%"=="" (
  echo Usage: RUN_ORIGINAL_V1_FULL_EVIDENCE.bat ^<rN^> [prior rM]
  exit /b 2
)
set "CANDIDATE=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.blend"
if not exist "%CANDIDATE%" (
  echo ERROR: Candidate Blend not found: %CANDIDATE%
  exit /b 2
)
for %%G in (shoulder hand hip pushup row) do (
  call RUN_ORIGINAL_V1_REPAIR_CHECK.bat %%G "%CANDIDATE%" %%G_%REV%
  if errorlevel 1 exit /b 1
)
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
)
if not defined BLENDER (
  echo ERROR: Blender not found. Set BLENDER_EXE to blender.exe.
  exit /b 2
)
set "NOUT=ORIGINAL_V1_WORK\candidates\repair_checks\neutral_%REV%"
if exist "%NOUT%" (
  echo ERROR: Output folder already exists: %NOUT%
  exit /b 2
)
mkdir "%NOUT%"
"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\pose_test_original_v1_o4_candidate_blender.py -- "%NOUT%" neutral
if errorlevel 1 exit /b 1
if "%~2"=="" (
  python scripts\merge_original_v1_repair_group_reports.py %REV%
) else (
  python scripts\merge_original_v1_repair_group_reports.py %REV% --prior %~2
)
