@echo off
setlocal
cd /d "%~dp0"
python scripts\generate_v15f_ring_visual_proof.py
exit /b %errorlevel%
