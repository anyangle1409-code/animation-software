@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Complete read-only evidence/review pass for a fresh local axilla candidate.
rem Usage: RUN_ORIGINAL_V1_AXILLA_PIT_VALIDATE.bat <candidate-rN> [prior-rN]
rem Default predecessor is r55. No acceptance or production promotion is performed.

set "REV=%~1"
set "PRIOR=%~2"
if "%REV%"=="" goto :usage
if "%PRIOR%"=="" set "PRIOR=r55"
if /I "%REV%"=="%PRIOR%" ( echo ERROR: candidate and predecessor must differ & exit /b 2 )

for /f "delims=" %%I in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%I"
if /I not "%CURRENT_BRANCH%"=="claude/original-v1-blender-o2-20260929" (
  echo ERROR: wrong branch "%CURRENT_BRANCH%"
  exit /b 2
)

git diff --quiet HEAD -- scripts\pose_test_original_v1_o4_candidate_blender.py scripts\audit_original_v1_axilla_candidate_blender.py scripts\original_v1_production_control.py ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json
if errorlevel 1 (
  echo ERROR: validation inputs have uncommitted changes.
  exit /b 2
)

set "CANDIDATE=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.blend"
set "MANIFEST=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.json"
set "DECL=ORIGINAL_V1_WORK\candidates\repair_preparation\%REV%_axilla_pit_declared\axilla_pit_mask_declared_before_edit.json"
set "AXOUT=ORIGINAL_V1_WORK\candidates\repair_checks\axilla_%REV%"

if not exist "%CANDIDATE%" ( echo ERROR: candidate Blend missing & exit /b 2 )
if not exist "%MANIFEST%" ( echo ERROR: candidate manifest missing & exit /b 2 )
if not exist "%DECL%" ( echo ERROR: candidate declaration missing & exit /b 2 )
if exist "%AXOUT%" ( echo ERROR: axilla validation output already exists & exit /b 2 )

python scripts\verify_original_v1_local_candidate.py "%CANDIDATE%" "%MANIFEST%"
if errorlevel 1 exit /b 2

echo ============================================================
echo ORIGINAL v1 axilla candidate validation
echo Candidate: %REV%
echo Predecessor: %PRIOR%
echo No candidate mutation or promotion will occur.
echo ============================================================

echo [1/6] Full 15-pose evidence and comparisons...
call RUN_ORIGINAL_V1_FULL_EVIDENCE.bat %REV% %PRIOR%
if errorlevel 1 exit /b 1

echo [2/6] Remaining focused diagnostics...
call RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat %REV%
if errorlevel 1 exit /b 1

echo [3/6] Declared axilla face audit...
set "BLENDER="
if defined BLENDER_EXE if exist "%BLENDER_EXE%" set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER for /f "delims=" %%I in ('dir /b /s "C:\Program Files\Blender Foundation\Blender *\blender.exe" 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER ( echo ERROR: Blender not found & exit /b 2 )
mkdir "%AXOUT%" || exit /b 2
"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 1 ^
  --python scripts\audit_original_v1_axilla_candidate_blender.py -- ^
  "%DECL%" "%AXOUT%\post_edit_face_audit.json" "%AXOUT%\post_edit_face_audit.md" 17
if errorlevel 1 exit /b 1

echo [4/6] Regenerate evidence-led status/ledger...
python scripts\build_original_v1_daily_status.py
if errorlevel 1 exit /b 1

echo [5/6] Capture verified milestone review images...
call RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat %REV%
if errorlevel 1 exit /b 1

echo [6/6] Verify candidate evidence closure...
call RUN_ORIGINAL_V1_CANDIDATE_CLOSE.bat %REV% "%AXOUT%\candidate_closure.json"
if errorlevel 1 (
  echo NOTE: Candidate evidence is not closed yet. Preserve outputs and inspect the closure report.
  exit /b 1
)

echo.
echo VALIDATION COMPLETE: %REV%
echo Inspect:
echo   ORIGINAL_V1_WORK\candidates\repair_checks\full_%REV%_comparison_vs_%PRIOR%.json
echo   %AXOUT%\post_edit_face_audit.json
echo   ORIGINAL_V1_WORK\candidates\review\milestone_%REV%\
echo No acceptance or production promotion was inferred.
exit /b 0

:usage
echo Usage: %~nx0 ^<candidate-rN^> [prior-rN]
exit /b 2
