@echo off
setlocal
set "ROOT=%~dp0"
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
set "CANDIDATE=%ROOT%ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r95.blend"
set "OUTPUT=%ROOT%ORIGINAL_V1_WORK\candidates\repair_checks\deformation_layers_r95\deformation_layers_r95.json"
if not "%~1"=="" set "OUTPUT=%~f1"
if not exist "%BLENDER%" (
  echo STOP - Blender 5.2 is unavailable at the expected path.
  exit /b 2
)
if not exist "%CANDIDATE%" (
  echo STOP - exact local r95 Blend is unavailable: %CANDIDATE%
  exit /b 2
)
"%BLENDER%" --background --factory-startup "%CANDIDATE%" --python-exit-code 2 --python "%ROOT%scripts\diagnose_original_v1_deformation_layers_blender.py" -- "%OUTPUT%"
exit /b %ERRORLEVEL%
