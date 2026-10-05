@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem One-command, READ-ONLY pre-repair diagnostic bundle.
rem Backward-compatible usage:
rem   RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat candidate.blend fresh-label
rem   RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat candidate.blend fresh-label pose,pose,...
rem Package-aware usage:
rem   RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat candidate.blend fresh-label RP-ID[,RP-ID...] [pose,pose,...]
rem If no package list is supplied, the current shoulder-yoke cluster is assumed.

set "CANDIDATE=%~1"
set "LABEL=%~2"
set "ARG3=%~3"
set "ARG4=%~4"
if "%CANDIDATE%"=="" (echo ERROR: candidate Blend required.& exit /b 2)
if "%LABEL%"=="" (echo ERROR: fresh label required.& exit /b 2)
if not exist "%CANDIDATE%" (echo ERROR: candidate not found: %CANDIDATE%& exit /b 2)

set "DEFAULT_PACKAGES=RP-PEC-AX-002,RP-POSTAX-003,RP-DELTOID-004,RP-NECK-TRAP-001"
set "PACKAGES=%DEFAULT_PACKAGES%"
set "POSES="

if not "%ARG3%"=="" (
  echo(%ARG3%| findstr /I /C:"RP-" >nul
  if errorlevel 1 (
    set "POSES=%ARG3%"
  ) else (
    set "PACKAGES=%ARG3%"
    set "POSES=%ARG4%"
  )
)

set "ROOT=ORIGINAL_V1_WORK\candidates\repair_checks"
set "SKIN=%ROOT%\skinning_mode\%LABEL%\skinning_mode.json"
set "SCOPE=%ROOT%\pose_coupling_scope\%LABEL%\pose_coupling_scope.json"
set "PLAN=%ROOT%\pose_evidence_plans\%LABEL%\pose_capture_evidence_plan.json"
set "SHOULDER=%ROOT%\shoulder_layer_diagnostics\%LABEL%\shoulder_layer_diagnostic.json"
set "REV=%ROOT%\motion_reversibility\%LABEL%\motion_reversibility.json"
set "CONT=%ROOT%\motion_continuity\%LABEL%\motion_continuity.json"
set "BUNDLE_DIR=%ROOT%\pre_repair_bundle\%LABEL%"
set "BUNDLE=%BUNDLE_DIR%\pre_repair_diagnostic_bundle.json"
set "SELECTION=%BUNDLE_DIR%\package_validation_selection.json"
set "POSES_FILE=%BUNDLE_DIR%\selected_pose_names.txt"

if exist "%BUNDLE_DIR%" (
  echo ERROR: pre-repair bundle directory already exists. Use a fresh label:
  echo   %BUNDLE_DIR%
  exit /b 2
)
mkdir "%BUNDLE_DIR%"

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON for /f "delims=" %%I in ('where python.exe 2^>nul') do if not defined PYTHON set "PYTHON=%%I"
if not defined PYTHON (echo ERROR: Python not found.& exit /b 2)

echo ============================================================
echo ORIGINAL v1 PRE-REPAIR DIAGNOSTIC BUNDLE
echo Candidate: %CANDIDATE%
echo Label:     %LABEL%
echo Packages:  %PACKAGES%
echo READ-ONLY: no Blend is saved or edited.
echo ============================================================

call RUN_ORIGINAL_V1_HUMAN_BODY_READINESS_CHECK.bat
if errorlevel 1 exit /b 1

if "%POSES%"=="" (
  "%PYTHON%" scripts\build_original_v1_package_validation_selection.py --packages "%PACKAGES%" --out "%SELECTION%" --poses-out "%POSES_FILE%"
  if errorlevel 1 exit /b 1
  set /p POSES=<"%POSES_FILE%"
) else (
  "%PYTHON%" scripts\build_original_v1_package_validation_selection.py --packages "%PACKAGES%" --out "%SELECTION%"
  if errorlevel 1 exit /b 1
  echo NOTE: caller supplied pose override "%POSES%"; package validation selection remains authoritative for sweep-only movement requirements.
)

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

"%PYTHON%" scripts\original_v1_workspace_requires_diagnostic.py --packages "%PACKAGES%" --diagnostic shoulder_layer
set "DIAG_RC=%ERRORLEVEL%"
if "%DIAG_RC%"=="2" exit /b 1
if "%DIAG_RC%"=="0" (
  call RUN_ORIGINAL_V1_SHOULDER_LAYER_DIAGNOSTIC.bat "%CANDIDATE%" "%LABEL%" "press_top,pullup_hang" 13
  if errorlevel 1 exit /b 1
) else (
  echo SKIP: shoulder-layer diagnostic is not required for the selected repair packages.
)

call RUN_ORIGINAL_V1_MOTION_REVERSIBILITY_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

call RUN_ORIGINAL_V1_MOTION_CONTINUITY_AUDIT.bat "%CANDIDATE%" "%LABEL%"
if errorlevel 1 exit /b 1

set "SHOULDER_ARG="
if "%DIAG_RC%"=="0" set "SHOULDER_ARG=--shoulder "%SHOULDER%""

"%PYTHON%" scripts\build_original_v1_pre_repair_diagnostic_bundle.py ^
  --candidate "%CANDIDATE%" ^
  --label "%LABEL%" ^
  --packages "%PACKAGES%" ^
  --selection "%SELECTION%" ^
  --skinning "%SKIN%" ^
  --pose-scope "%SCOPE%" ^
  --pose-plan "%PLAN%" ^
  %SHOULDER_ARG% ^
  --reversibility "%REV%" ^
  --continuity "%CONT%" ^
  --out "%BUNDLE%"
if errorlevel 1 exit /b 1

echo.
echo PASS: immutable diagnostic bundle written:
echo   %BUNDLE%
echo Next: use ORIGINAL_V1_DEFORMATION_DIAGNOSIS_TREE.json before any edit.
exit /b 0
