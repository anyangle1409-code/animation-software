@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: PRINT_CLAUDE_TASK_PROMPT.bat task description
  exit /b 2
)
python scripts\print_claude_task_prompt.py %*
exit /b %errorlevel%
