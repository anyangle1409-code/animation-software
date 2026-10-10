@echo off
setlocal
cd /d "%~dp0"
set "CT_HOME=%USERPROFILE%\HomeGymPT_Private_Original_CT_Review"
echo.
echo HOME GYM PT - PRIVATE BLENDER CT REVIEW SCENE
echo =============================================
echo This creates a NEW isolated CT inspection .blend.
echo Your existing Blender model, active branch and production assets remain untouched.
echo Anatomical bone identity and scanner-to-HGPT registration remain UNVERIFIED.
echo.

where py >nul 2>nul
if not errorlevel 1 goto PY_PREP
where python >nul 2>nul
if not errorlevel 1 goto PYTHON_PREP
echo ERROR: Python 3 not found. Run start_private_ct_review.cmd after enabling Python 3.
pause
exit /b 1

:PY_PREP
py -3 scripts\anatomy_fit\nlm_ct_blender_six_source_prep.py
goto CHECK_PREP

:PYTHON_PREP
python scripts\anatomy_fit\nlm_ct_blender_six_source_prep.py

:CHECK_PREP
if errorlevel 1 (
  echo ERROR: Source pin preflight failed. No Blender file created.
  pause
  exit /b 1
)

set "BLENDER_EXE="
for /f "delims=" %%F in ('where blender.exe 2^>nul') do if not defined BLENDER_EXE set "BLENDER_EXE=%%F"
if not defined BLENDER_EXE (
  for /d %%D in ("%ProgramFiles%\Blender Foundation\Blender*") do (
    if exist "%%~fD\blender.exe" set "BLENDER_EXE=%%~fD\blender.exe"
  )
)
if not defined BLENDER_EXE (
  echo ERROR: Blender executable not found on PATH or standard Program Files.
  echo Original source PNGs and GE headers have still been safely prepared.
  echo Use Blender's own executable with the script shown in:
  echo docs\PRIVATE_CT_LAPTOP_NO_CLAUDE_HANDOFF_20261010.md
  pause
  exit /b 1
)

if not exist "%CT_HOME%" mkdir "%CT_HOME%"
echo.
echo Building separate CT source scene, without opening production skeleton...
"%BLENDER_EXE%" --background --python scripts\anatomy_fit\ct_pelvis_review_scene_blender.py -- --ct-dir "%CT_HOME%\original_NLM_CT_sources" --cache-dir "%CT_HOME%\BLENDER_DISPLAY_CACHE" --report-out "%CT_HOME%\BLENDER_CT_REVIEW_REPORT.json" --save-as "%CT_HOME%\BLENDER_CT_REVIEW_ONLY.blend" --fresh
set "RESULT=%ERRORLEVEL%"
if "%RESULT%"=="0" (
  echo.
  echo SUCCESS: Private CT display-only Blender scene:
  echo "%CT_HOME%\BLENDER_CT_REVIEW_ONLY.blend"
  echo No accepted skeleton or production Blender file changed.
) else (
  echo.
  echo ERROR: CT Blender scene could not be verified; do not use partial output.
)
pause
exit /b %RESULT%
