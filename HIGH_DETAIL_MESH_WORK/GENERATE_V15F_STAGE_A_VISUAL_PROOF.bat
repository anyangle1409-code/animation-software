@echo off
setlocal
cd /d "%~dp0"
python scripts\generate_v15f_stage_a_visual_proof.py
exit /b %errorlevel%
