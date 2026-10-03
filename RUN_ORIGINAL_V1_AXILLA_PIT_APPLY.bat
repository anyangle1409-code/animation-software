@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_APPLY.bat <source-rN> <target-rN>
set "SOURCE_REV=%~1"
set "TARGET_REV=%~2"
if "%SOURCE_REV%"=="" goto :usage
if "%TARGET_REV%"=="" goto :usage
if /I "%SOURCE_REV%"=="%TARGET_REV%" ( echo ERROR: source and target must differ & exit /b 2 )
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="claude/original-v1-blender-o2-20260929" ( echo ERROR: wrong branch & exit /b 2 )
git diff --quiet HEAD -- scripts\apply_original_v1_axilla_delta_blender.py scripts\verify_original_v1_local_candidate.py
if errorlevel 1 ( echo ERROR: apply scripts have uncommitted changes & exit /b 2 )
set "SRC=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.blend"
set "SRC_MAN=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.json"
set "DST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%TARGET_REV%.blend"
set "PREP=ORIGINAL_V1_WORK\candidates\repair_preparation\%TARGET_REV%_axilla_pit_declared"
set "DECL=%PREP%\axilla_pit_mask_declared_before_edit.json"
set "SOL=%PREP%\incremental_corrective_solution.npz"
set "PARENT_SPEC=ORIGINAL_V1_WORK\shoulder_corrective_%SOURCE_REV%.json"
set "NEW_SPEC=ORIGINAL_V1_WORK\shoulder_corrective_%TARGET_REV%.json"
if not exist "%SRC%" ( echo ERROR: missing source blend & exit /b 2 )
if not exist "%DECL%" ( echo ERROR: missing declaration & exit /b 2 )
if not exist "%SOL%" ( echo ERROR: missing solution & exit /b 2 )
if exist "%DST%" ( echo ERROR: refusing to overwrite target blend & exit /b 2 )
if exist "%NEW_SPEC%" ( echo ERROR: refusing to overwrite target spec & exit /b 2 )
python scripts\verify_original_v1_local_candidate.py "%SRC%" "%SRC_MAN%" || exit /b 2
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER ( echo ERROR: Blender not found & exit /b 2 )
"%BLENDER%" --background --factory-startup "%SRC%" --python-exit-code 1 --python scripts\apply_original_v1_axilla_delta_blender.py -- "%SOL%" "%DECL%" "%PARENT_SPEC%" "%DST%" "%NEW_SPEC%"
if errorlevel 1 exit /b 1
echo APPLY COMPLETE: %DST%
echo Experimental only. Run full evidence before continuation/freeze decisions.
exit /b 0
:usage
echo Usage: %~nx0 ^<source-rN^> ^<target-rN^>
exit /b 2
