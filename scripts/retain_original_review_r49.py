"""Retain the latest accepted fit state and record failures before any raise."""
import sys,json,shutil
from pathlib import Path

def retain(directory,code):
    p=Path(directory);destination=p/'solved.npz'
    options=[(destination,'completed_fit'),(p/'solved.npz.progress.npz','accepted_main_fit_progress'),(p/'preflight.npz','accepted_preflight_only')]
    chosen=next(((path,name) for path,name in options if path.exists()),None)
    report=dict(fit_exit_code=code,fit_completed=code==0,fit_timed_out=code==124,
        has_accepted_state=chosen is not None,state_source=chosen[1] if chosen else None,
        model_saved=False,approved=False,native_validation='PENDING')
    if not chosen:report.update(status='NO_ACCEPTED_STATE',blocker='Neither main fit nor verified preflight produced an accepted checkpoint.')
    else:report['status']='FIT_COMPLETED_NATIVE_VALIDATION_PENDING' if code==0 else 'PARTIAL_FIT_NATIVE_VALIDATION_PENDING'
    (p/'fit_status.json').write_text(json.dumps(report,indent=2)+'\n')
    if not chosen:raise RuntimeError(report['blocker'])
    source,name=chosen
    if source!=destination:shutil.copy2(source,destination)
    if not (p/'solved.npz.json').exists():
        history=[]
        candidate=p/'solved.npz.progress.json' if name=='accepted_main_fit_progress' else p/'preflight.npz.json'
        if candidate.exists():
            data=json.loads(candidate.read_text());history=data.get('history',[]) if isinstance(data,dict) else data
        (p/'solved.npz.json').write_text(json.dumps(dict(report,history=history),indent=2)+'\n')
    return report

if __name__=='__main__':print(json.dumps(retain(sys.argv[1],int(sys.argv[2]))),flush=True)
