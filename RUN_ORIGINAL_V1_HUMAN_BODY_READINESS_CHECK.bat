@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "PYTHON=%PYTHON_EXE%"
if not defined PYTHON if exist "C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  set "PYTHON=C:\Users\Mark\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)
if not defined PYTHON (
  for /f "delims=" %%I in ('where python.exe 2^>nul') do (
    if not defined PYTHON set "PYTHON=%%I"
  )
)
if not defined PYTHON (
  echo ERROR: Python not found. Set PYTHON_EXE.
  exit /b 2
)

echo ============================================================
echo ORIGINAL v1 HUMAN BODY READINESS CHECK
echo Non-Blender authority/evidence validation only.
echo ============================================================

call :run scripts\validate_original_v1_human_body_master_plan.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_human_evidence.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_human_movement_sweeps.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_anatomical_coupling.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_joint_tissue_triggers.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_surface_visual_evidence_requirements.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_anatomical_coupling_capture_plan.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_first_party_deformation_architecture.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_defect_coupling_map.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_anatomical_repair_packages.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_deformation_diagnosis_tree.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_weights_only_contract.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_pose_evidence_planning.py
if errorlevel 1 exit /b 1
call :run scripts\validate_original_v1_candidate_comparison_template.py
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo PASS: HUMAN BODY READINESS CONTROL FILES ARE CONSISTENT
echo NOTE: This does NOT mean the body is anatomically accepted.
echo Blender candidate-bound coupling/motion evidence is still required.
echo ============================================================
exit /b 0

:run
echo.
echo ---- %~1 ----
"%PYTHON%" "%~1"
exit /b %ERRORLEVEL%
