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
echo ORIGINAL v1 HUMAN BODY CONTRACT GATES
echo ============================================================

call :run scripts\validate_original_v1_human_evidence.py || exit /b 1
call :run scripts\validate_original_v1_human_body_master_plan.py || exit /b 1
call :run scripts\validate_original_v1_human_movement_sweeps.py || exit /b 1
call :run scripts\validate_original_v1_anatomical_coupling.py || exit /b 1
call :run scripts\validate_original_v1_first_party_deformation_architecture.py || exit /b 1
call :run scripts\validate_original_v1_surface_visual_evidence_requirements.py || exit /b 1
call :run scripts\validate_original_v1_joint_tissue_triggers.py || exit /b 1
call :run scripts\validate_original_v1_anatomical_coupling_capture_plan.py || exit /b 1
call :run scripts\validate_original_v1_defect_coupling_map.py || exit /b 1
call :run scripts\validate_original_v1_anatomical_repair_packages.py || exit /b 1
call :run scripts\validate_original_v1_deformation_diagnosis_tree.py || exit /b 1
call :run scripts\validate_original_v1_weights_only_contract.py || exit /b 1
call :run scripts\validate_original_v1_pose_evidence_planning.py || exit /b 1
call :run scripts\validate_original_v1_candidate_comparison_template.py || exit /b 1
call :run scripts\validate_original_v1_candidate_surface_visual_review_template.py || exit /b 1
call :run scripts\validate_original_v1_repair_execution_record_template.py || exit /b 1
call :run scripts\validate_original_v1_stage1_repair_execution_graph.py || exit /b 1
call :run scripts\validate_original_v1_stage1_progress.py || exit /b 1
call :run scripts\validate_original_v1_deformation_failure_signatures.py || exit /b 1

call :run scripts\test_validate_original_v1_surface_visual_evidence_requirements.py || exit /b 1
call :run scripts\test_original_v1_human_evidence.py || exit /b 1
call :run scripts\test_validate_original_v1_human_body_master_plan.py || exit /b 1
call :run scripts\test_validate_original_v1_human_movement_sweeps.py || exit /b 1
call :run scripts\test_validate_original_v1_anatomical_coupling.py || exit /b 1
call :run scripts\test_validate_original_v1_first_party_deformation_architecture.py || exit /b 1
call :run scripts\test_validate_original_v1_coupling_zone_declaration.py || exit /b 1
call :run scripts\test_validate_original_v1_anatomical_coupling_evidence.py || exit /b 1
call :run scripts\test_validate_original_v1_shoulder_layer_diagnostic.py || exit /b 1
call :run scripts\test_build_original_v1_pose_capture_evidence_plan.py || exit /b 1
call :run scripts\test_build_original_v1_candidate_comparison_report.py || exit /b 1
call :run scripts\test_validate_original_v1_anatomical_repair_packages.py || exit /b 1
call :run scripts\test_validate_original_v1_stage1_repair_execution_graph.py || exit /b 1
call :run scripts\test_validate_original_v1_stage1_progress.py || exit /b 1
call :run scripts\test_validate_original_v1_deformation_diagnosis_tree.py || exit /b 1
call :run scripts\test_validate_original_v1_weights_only_acceptance.py || exit /b 1
call :run scripts\test_validate_original_v1_candidate_surface_visual_review.py || exit /b 1
call :run scripts\test_validate_original_v1_repair_execution_record.py || exit /b 1
call :run scripts\test_create_original_v1_post_edit_evidence_bundle.py || exit /b 1
call :run scripts\test_build_original_v1_repair_regression_plan.py || exit /b 1

echo.
echo PASS: human-body contract, evidence, movement and coupling gates are internally consistent.
exit /b 0

:run
echo.
echo ^> %*
"%PYTHON%" %*
if errorlevel 1 (
  echo FAILED: %*
  exit /b 1
)
exit /b 0
