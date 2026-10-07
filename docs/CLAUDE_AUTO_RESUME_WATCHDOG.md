# Claude auto-resume watchdog

This watchdog queues the Home Gym PT continuation prompt into the existing Claude Code cloud session when Claude usage becomes available again.

Target session:
https://claude.ai/code/session_01EPKohHG29Xe8qKuNMT5Fv9

## Windows setup

From the repository, run once:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_claude_auto_resume.ps1
```

Default schedule: 12:50 local time every day.

If usage is not available yet, the watcher retries every 5 minutes for up to 3 hours. It exits immediately after one successful continuation message is queued.

To change the start time:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_claude_auto_resume.ps1 -DailyStart "12:40"
```

## Linux / WSL

Run `scripts/claude_auto_resume.sh` from cron or systemd at the expected reset window.

Example cron:

```
50 12 * * * /absolute/path/to/animation-software/scripts/claude_auto_resume.sh
```

## Log

`ORIGINAL_V1_WORK/anatomy/automation/claude_auto_resume.log`

Status meanings:
- WAIT — usage appears unavailable; retrying.
- SUCCESS — continuation prompt queued; watcher exits.
- WARN / ERROR — CLI, authentication or path problem.

## Requirements

- Claude Code CLI installed and signed in on the laptop.
- `claude` available in PATH for the scheduled task.
- Laptop awake, or Windows Task Scheduler able to run the missed task when it becomes available.
- Existing Claude cloud session still accessible.

## Safety

The watcher itself does not modify Git, Blender, or the model. It only queues the continuation prompt. The prompt requires Claude to inspect live HEAD, preserve newer work, avoid destructive Git operations, stay on the anatomical-audit branch, and leave production geometry, weights and drivers unchanged until the audit gates permit production work.
