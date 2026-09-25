"""Start the project controller detached on the local laptop."""
from __future__ import annotations
import os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"project_controller.py"
LOCK=ROOT/"reports"/"project_controller.lock"

if LOCK.exists():
    age=time.time()-LOCK.stat().st_mtime
    if age < 120:
        print("PROJECT_CONTROLLER_ALREADY_ACTIVE",LOCK)
        raise SystemExit(0)
    print("PROJECT_CONTROLLER_LOCK_STALE_OR_UNHEALTHY",LOCK)
    # Do not delete a recent-ish unknown lock automatically. A stopped/crashed
    # controller can be recovered with STOP_PROJECT_CONTROLLER.bat then restart.
    if age < 12*3600:
        raise SystemExit(2)
    LOCK.unlink(missing_ok=True)

kwargs={"cwd":str(ROOT),"stdin":subprocess.DEVNULL,
        "stdout":subprocess.DEVNULL,"stderr":subprocess.DEVNULL}
if os.name=="nt":
    kwargs["creationflags"]=(
        getattr(subprocess,"DETACHED_PROCESS",0)
        | getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
    )
else:
    kwargs["start_new_session"]=True

p=subprocess.Popen([sys.executable,str(SCRIPT)],**kwargs)
print("PROJECT_CONTROLLER_STARTED",p.pid)
