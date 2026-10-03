@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "REGION=%~1"
set "REV=%~2"
if "%REGION%"=="" goto :usage
if "%REV%"=="" goto :usage
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="claude/original-v1-blender-o2-20260929" ( echo ERROR: wrong branch & exit /b 2 )
set "CAND=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.blend"
set "MAN=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.json"
set "RAW=ORIGINAL_V1_WORK\candidates\repair_checks\phase5_%REGION%_%REV%"
if not exist "%CAND%" ( echo ERROR: candidate Blend missing & exit /b 2 )
if exist "%RAW%" ( echo ERROR: refusing to overwrite raw capture folder & exit /b 2 )
python scripts\verify_original_v1_local_candidate.py "%CAND%" "%MAN%" || exit /b 2
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER ( echo ERROR: Blender not found & exit /b 2 )
"%BLENDER%" --background --factory-startup "%CAND%" --python-exit-code 1 --python scripts\capture_original_v1_phase5_region_blender.py -- "%REGION%" "%RAW%"
if errorlevel 1 exit /b 1
python scripts\original_v1_phase5_region_review.py "%REGION%" "%REV%"
if errorlevel 1 exit /b 1
echo PHASE 5 REGION REVIEW READY. owner_review pending; no region/phase completion inferred.
exit /b 0
:usage
echo Usage: %~nx0 ^<5A-5G^> ^<rN^>
exit /b 2
