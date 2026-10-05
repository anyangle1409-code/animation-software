@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem One-command, READ-ONLY pre-repair diagnostic bundle.
rem Usage:
rem   RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat candidate.blend fresh-label [pose,pose,...]

set "CANDIDATE=%~1"
set "LABEL=%~2"
set "POSES=%~3"
if "%CANDIDATE%"=="" (echo ERROR: candidate Blend required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if not exist "%CANDIDATE%" (echo ERROR: candidate not found: %CANDIDATE%& exit /b 2)

set "ROOT=ORIGINAL_V1_WORK\candidates\repair_checks"
set "SKIN=%ROOT%\skinning_mode\%LABEL%\skinning_mode.json"
set "SCOPE=%ROOT%\pose_coupling_scope\%LABEL%\pose_coupling_scope.json"
set "PLAN=%ROOT%\pose_evidence_plans\%LABEL%\pose_capture_evidence_plan.json"
set "SHOULDER=%ROOT%\shoulder_layer_diagnostics\%LABEL%\shoulder_layer_diagnostic.json"
set "REV=%ROOT%\motion_reversibility\%LABEL%\motion_reversibility.json"
set "CONT=%ROOT%\motion_continuity\%LABEL%\motion_continuity.json"
set "BUNDLE_DIR=%ROOT%\pre_repair_bundle\%LABEL%"
set "BUNDLE=%BUNDLE_DIR%\pre_repair_diagnostic_bundle.json"

if exist "%BUNDLE%" (
  echo ERROR: bundle already exists. Use a fresh label:
  echo   %BUNDLE%
  exit /b 2
)

echo ============================================================
echo ORIGINAL v1 PRE-REPAIR DIAGNOSTIC BUNDLE
echo Candidate: %CANDIDATE%
echo Label:     %LABEL%
echo READ-ONLY: no Blend is saved or edited.
echo ============================================================

call RUN_ORIGINAL_V1_HUMAN_BODY_READINESS_CHECK.bat
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_SKINNING_MODE_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

if "%POSES%"=="" (
  call RUN_ORIGINAL_V1_POSE_COUPLING_SCOPE.bat "%CANDIDATE%" "%LABEL%"
) else (
  call RUN_ORIGINAL_V1_POSE_COUPLING_SCOPE.bat "%CANDIDATE%" "%LABEL%" "%POSES%"
)
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_POSE_EVIDENCE_PLAN.bat "%SCOPE%" "%LABEL%"
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_SHOULDER_LAYER_DIAGNOSTIC.bat "%CANDIDATE%" "%LABEL%" "press_top,pullup_hang" 13
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_MOTION_REVERSIBILITY_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_MOTION_CONTINUITY_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

if not exist "%BUNDLE_DIR%" mkdir "%BUNDLE_DIR%"

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

"%PYTHON%" scripts\build_original_v1_pre_repair_diagnostic_bundle.py ^
  --candidate "%CANDIDATE%" ^
  --label "%LABEL%" ^
  --skinning "%SKIN%" ^
  --pose-scope "%SCOPE%" ^
  --pose-plan "%PLAN%" ^
  --shoulder "%SHOULDER%" ^
  --reversibility "%REV%" ^
  --continuity "%CONT%" ^
  --out "%BUNDLE%"
if errorlevel 1 exit /b 1

echo.
echo PASS: immutable diagnostic bundle written:
echo   %BUNDLE%
echo Next: use ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json before any edit.
exit /b 0
