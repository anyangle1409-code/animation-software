@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Full post-repair validation bundle. READ-ONLY with respect to the Blend.
rem Usage:
rem   RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat rN prior_rM workspace_dir fresh-label
rem prior_rM may be "-" to omit predecessor comparison.

set "REV=%~1"
set "PRIOR=%~2"
set "WORKSPACE=%~3"
set "LABEL=%~4"
if "%REV%"=="" (echo ERROR: revision rN required.& exit /b 2)
if "%PRIOR%"=="" (echo ERROR: prior revision or - required.& exit /b 2)
if "%WORKSPACE%"=="" (echo ERROR: finalized repair workspace required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)

set "CANDIDATE=ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_%REV%.blend"
if not exist "%CANDIDATE%" (echo ERROR: candidate Blend not found: %CANDIDATE%& exit /b 2)
if not exist "%WORKSPACE%\workspace_finalization_manifest.json" (echo ERROR: workspace is not finalized.& exit /b 2)

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

echo ============================================================
echo ORIGINAL v1 POST-REPAIR VALIDATION BUNDLE
echo Revision:  %REV%
echo Candidate: %CANDIDATE%
echo Workspace: %WORKSPACE%
echo Label:     %LABEL%
echo READ-ONLY: candidate Blend is never saved by this bundle.
echo ============================================================

call RUN_ORIGINAL_V1_HUMAN_BODY_READINESS_CHECK.bat
if errorlevel 1 exit /b 1

"%PYTHON%" scripts\validate_original_v1_repair_workspace_identity.py --workspace "%WORKSPACE%" --candidate "%CANDIDATE%"
if errorlevel 1 exit /b 1

if "%PRIOR%"=="-" (
  call RUN_ORIGINAL_V1_FULL_EVIDENCE.bat %REV%
) else (
  call RUN_ORIGINAL_V1_FULL_EVIDENCE.bat %REV% %PRIOR%
)
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat %REV%
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_SKINNING_MODE_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_POSE_COUPLING_SCOPE.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

set "SCOPE=ORIGINAL_V1_WORK\candidates\repair_checks\pose_coupling_scope\%LABEL%\pose_coupling_scope.json"
call RUN_ORIGINAL_V1_POSE_EVIDENCE_PLAN.bat "%SCOPE%" "%LABEL%"
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_SHOULDER_LAYER_DIAGNOSTIC.bat "%CANDIDATE%" "%LABEL%" "press_top,pullup_hang" 13
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_MOTION_REVERSIBILITY_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_MOTION_CONTINUITY_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

set "REVIEW_OUT=ORIGINAL_V1_WORK\candidates\review\package_%REV%_%LABEL%"
call RUN_ORIGINAL_V1_REVIEW_PACKAGE.bat %REV% "%REVIEW_OUT%"
if errorlevel 1 exit /b 1

if "%PRIOR%"=="-" (
  "%PYTHON%" scripts\collect_original_v1_post_repair_evidence.py --workspace "%WORKSPACE%" --revision "%REV%" --label "%LABEL%"
) else (
  "%PYTHON%" scripts\collect_original_v1_post_repair_evidence.py --workspace "%WORKSPACE%" --revision "%REV%" --label "%LABEL%" --prior "%PRIOR%"
)
if errorlevel 1 exit /b 1

echo.
echo PASS: post-repair evidence has been run and collected.
echo NOTE: engineering statuses remain PENDING until evidence is reviewed and final records are populated.
exit /b 0
