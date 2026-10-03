@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_SOLVE.bat <source-rN> <target-rN> <w-area> [area-min] [w-fold] [w-prox]
set "SOURCE_REV=%~1"
set "TARGET_REV=%~2"
set "W_AREA=%~3"
set "AREA_MIN=%~4"
set "W_FOLD=%~5"
set "W_PROX=%~6"
if "%SOURCE_REV%"=="" goto :usage
if "%TARGET_REV%"=="" goto :usage
if "%W_AREA%"=="" goto :usage
if "%AREA_MIN%"=="" set "AREA_MIN=0.20"
if "%W_FOLD%"=="" set "W_FOLD=0"
if "%W_PROX%"=="" set "W_PROX=0"
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="claude/original-v1-blender-o2-20260929" ( echo ERROR: wrong branch & exit /b 2 )
git diff --quiet HEAD -- scripts\pose_test_original_v1_o4_candidate_blender.py scripts\dump_original_v1_arc_skinning_blender.py scripts\optimize_original_v1_shoulder_corrective.py
if errorlevel 1 ( echo ERROR: solve inputs have uncommitted changes & exit /b 2 )
set "BLEND=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.blend"
set "MANIFEST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.json"
set "PREP=ORIGINAL_V1_WORK\candidates\repair_preparation\%TARGET_REV%_axilla_pit_declared"
set "DECL=%PREP%\axilla_pit_mask_declared_before_edit.json"
set "SOL=%PREP%\incremental_corrective_solution.npz"
set "REPORT=%PREP%\incremental_corrective_solution_report.json"
if not exist "%BLEND%" ( echo ERROR: missing source blend & exit /b 2 )
if not exist "%DECL%" ( echo ERROR: run AXILLA_PIT_PREP first & exit /b 2 )
if exist "%SOL%" ( echo ERROR: refusing to overwrite solution & exit /b 2 )
if exist "%REPORT%" ( echo ERROR: refusing to overwrite solve report & exit /b 2 )
python scripts\verify_original_v1_local_candidate.py "%BLEND%" "%MANIFEST%" || exit /b 2
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER ( echo ERROR: Blender not found & exit /b 2 )
set "DUMP=%TEMP%\hgpt_%SOURCE_REV%_%TARGET_REV%_axilla_arc.npz"
if exist "%DUMP%" del /q "%DUMP%"
"%BLENDER%" --background --factory-startup "%BLEND%" --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "%DUMP%" "0.25,0.375,0.5,0.625,0.75,0.875"
if errorlevel 1 goto :fail
python scripts\optimize_original_v1_shoulder_corrective.py "%DUMP%" "%SOL%" --mask-file "%DECL%" --hi 3.6 --lo 0.30 --w-trunk 3000000 --w-area "%W_AREA%" --area-min "%AREA_MIN%" --w-fold "%W_FOLD%" --w-prox "%W_PROX%" --rounds 3 --w-smooth 300 --w-mag 2 --iters 300 --json-out "%REPORT%"
if errorlevel 1 goto :fail
if exist "%DUMP%" del /q "%DUMP%"
echo SOLVE COMPLETE: %SOL%
echo REPORT: %REPORT%
echo Incremental delta only; DO NOT pass corr_v8 as --init.
exit /b 0
:usage
echo Usage: %~nx0 ^<source-rN^> ^<target-rN^> ^<w-area^> [area-min] [w-fold] [w-prox]
exit /b 2
:fail
if exist "%DUMP%" del /q "%DUMP%"
exit /b 1
