"""Start the V15f safe runner detached on the local machine."""
from __future__ import annotations
import os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"v15f_safe_runner.py"
REPORTS=ROOT/"reports"
LOCK=REPORTS/"v15f_safe_runner.lock"

if LOCK.exists():
    age=time.time()-LOCK.stat().st_mtime
    if age < 10*3600:
        print("V15F_SAFE_RUNNER_ALREADY_LOCKED",LOCK)
        raise SystemExit(0)
    print("V15F_SAFE_RUNNER_REMOVING_STALE_LOCK",LOCK)
    LOCK.unlink(missing_ok=True)

kwargs={"cwd":str(ROOT)}
if os.name=="nt":
    kwargs["creationflags"]=(
        getattr(subprocess,"DETACHED_PROCESS",0)
        | getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
    )
    kwargs["stdin"]=subprocess.DEVNULL
    kwargs["stdout"]=subprocess.DEVNULL
    kwargs["stderr"]=subprocess.DEVNULL
else:
    kwargs["start_new_session"]=True
    kwargs["stdin"]=subprocess.DEVNULL
    kwargs["stdout"]=subprocess.DEVNULL
    kwargs["stderr"]=subprocess.DEVNULL

p=subprocess.Popen([sys.executable,str(SCRIPT),"--max-hours","8"],**kwargs)
print("V15F_SAFE_RUNNER_STARTED",p.pid)
