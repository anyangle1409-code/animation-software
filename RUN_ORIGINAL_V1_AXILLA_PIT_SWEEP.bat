@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_SWEEP.bat <source-rN> <target-rN>
rem One Blender dump, then 0.25x/1x/4x pure-Python area-barrier trials. No candidate is created.
set "SOURCE_REV=%~1"
set "TARGET_REV=%~2"
if "%SOURCE_REV%"=="" goto :usage
if "%TARGET_REV%"=="" goto :usage
if /I "%SOURCE_REV%"=="%TARGET_REV%" ( echo ERROR: source and target must differ & exit /b 2 )
for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="claude/original-v1-blender-o2-20260929" ( echo ERROR: wrong branch & exit /b 2 )
git diff --quiet HEAD -- scripts\pose_test_original_v1_o4_candidate_blender.py scripts\dump_original_v1_arc_skinning_blender.py scripts\optimize_original_v1_shoulder_corrective.py scripts\run_original_v1_axilla_trial_sweep.py
if errorlevel 1 ( echo ERROR: sweep inputs have uncommitted changes & exit /b 2 )
python scripts\test_original_v1_shoulder_corrective_area_gradient.py || exit /b 2
set "BLEND=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.blend"
set "MANIFEST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%SOURCE_REV%.json"
set "PREP=ORIGINAL_V1_WORK\candidates\repair_preparation\%TARGET_REV%_axilla_pit_declared"
set "DECL=%PREP%\axilla_pit_mask_declared_before_edit.json"
set "TRIALS=%PREP%\numeric_trials"
set "SOL=%PREP%\incremental_corrective_solution.npz"
set "REPORT=%PREP%\incremental_corrective_solution_report.json"
if not exist "%BLEND%" ( echo ERROR: missing source blend & exit /b 2 )
if not exist "%DECL%" ( echo ERROR: run AXILLA_PIT_PREP first & exit /b 2 )
if exist "%TRIALS%" ( echo ERROR: refusing to overwrite trial directory & exit /b 2 )
if exist "%SOL%" ( echo ERROR: canonical solution already exists & exit /b 2 )
if exist "%REPORT%" ( echo ERROR: canonical report already exists & exit /b 2 )
python scripts\verify_original_v1_local_candidate.py "%BLEND%" "%MANIFEST%" || exit /b 2
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER ( echo ERROR: Blender not found & exit /b 2 )
rem Optional denser arc training (default unchanged): AXILLA_PIT_ARC_FRACTIONS="0.0625,0.125,..." so the solver sees the same samples the face audit measures.
set "ARC_FRACTIONS=0.25,0.375,0.5,0.625,0.75,0.875"
if not "%AXILLA_PIT_ARC_FRACTIONS%"=="" set "ARC_FRACTIONS=%AXILLA_PIT_ARC_FRACTIONS%"
set "DUMP=%TEMP%\hgpt_%SOURCE_REV%_%TARGET_REV%_axilla_sweep.npz"
if exist "%DUMP%" del /q "%DUMP%"
"%BLENDER%" --background --factory-startup "%BLEND%" --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "%DUMP%" "%ARC_FRACTIONS%"
if errorlevel 1 goto :fail
set "HOLD_ARG="
if not "%AXILLA_PIT_HOLD_REGION_MIN%"=="" set "HOLD_ARG=--hold-region-min %AXILLA_PIT_HOLD_REGION_MIN%"
if not "%AXILLA_PIT_HOLD_REGION_MIN%"=="" if /I "%AXILLA_PIT_CONTACT_GUARD%"=="1" set "HOLD_ARG=%HOLD_ARG% --contact-guard"
if not "%AXILLA_PIT_HOLD_REGION_MIN%"=="" if not "%AXILLA_PIT_HOLD_REGION_MAX%"=="" set "HOLD_ARG=%HOLD_ARG% --hold-region-max %AXILLA_PIT_HOLD_REGION_MAX%"
if not "%AXILLA_PIT_HOLD_REGION_MIN%"=="" if not "%AXILLA_PIT_HOLD_WEIGHT%"=="" set "HOLD_ARG=%HOLD_ARG% --w-hold %AXILLA_PIT_HOLD_WEIGHT%"
if not "%AXILLA_PIT_HOLD_REGION_MIN%"=="" if not "%AXILLA_PIT_HOLD_SCOPE%"=="" set "HOLD_ARG=%HOLD_ARG% --hold-scope %AXILLA_PIT_HOLD_SCOPE%"
python scripts\run_original_v1_axilla_trial_sweep.py "%DUMP%" "%DECL%" "%TRIALS%" --canonical-solution "%SOL%" --canonical-report "%REPORT%" %HOLD_ARG%
if errorlevel 1 goto :fail
if exist "%DUMP%" del /q "%DUMP%"
echo SWEEP COMPLETE. Selection: %TRIALS%\selection.json
echo No Blend created. Inspect selection, then run AXILLA_PIT_APPLY.
exit /b 0
:usage
echo Usage: %~nx0 ^<source-rN^> ^<target-rN^>
exit /b 2
:fail
if exist "%DUMP%" del /q "%DUMP%"
echo No candidate created. Trial reports are preserved.
exit /b 1
