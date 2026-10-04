@echo off
REM r83 low-usage helper. REVIEW paths before running. Does not run Blender automatically.
echo Home Gym PT r83 low-usage execution helper
echo.
echo 1. Fetch/reconcile live claude/original-v1-blender-o2-20260929 first.
echo 2. Preserve r81. Never use r82 as parent.
echo 3. Read docs\work_packages\CLAUDE_R83_LOW_USAGE_HANDOFF.md
echo.
echo First-pass restoration alphas: 0.10 0.20 0.35
echo Refinement only if earned: 0.05 0.15 0.25 0.50
echo.
echo Focused poses:
echo press_top,pullup_hang,pullup_hang_rhythm,squat_bottom,press_bottom,pullup_bar,pullup_top,press_top_rhythm,pushup_bottom
echo.
echo Do NOT launch a full 15-pose run until a focused candidate beats r81 without development or shoulder-intersection regression.
