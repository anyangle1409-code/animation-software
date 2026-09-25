@echo off
setlocal
cd /d "%~dp0"
python scripts\audit_v15f_stage_a.py
if errorlevel 1 exit /b %errorlevel%
python scripts\generate_v15f_stage_a_visual_proof.py
if errorlevel 1 exit /b %errorlevel%
python scripts\write_v15f_handoff.py
exit /b %errorlevel%
