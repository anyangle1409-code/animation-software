"""Retain study evidence after timeout/failure; never save or accept a model."""
from pathlib import Path
import json,shutil,sys
root=Path(sys.argv[1]);code=int(sys.argv[2]);dest=root/'solved.npz'
if dest.exists():
 report=json.loads(Path(str(dest)+'.json').read_text());source='main_final_study'
elif Path(str(dest)+'.progress.npz').exists():
 shutil.copy2(Path(str(dest)+'.progress.npz'),dest);history=json.loads(Path(str(dest)+'.progress.json').read_text());retained=[r for r in history if r.get('retained')];row=retained[-1] if retained else history[-1];report=dict(history=history,**{k:v for k,v in row.items() if k not in ('history',)});source='main_progress_checkpoint'
else:
 shutil.copy2(root/'preflight.npz',dest);report=json.loads((root/'preflight.npz.json').read_text());source='preflight_only_fallback'
report.update(status='UNSAVED_TEMPORAL_STUDY_NOT_ACCEPTED',fit_exit_code=code,fit_timed_out=code==124,fit_process_completed=code==0,state_source=source,model_saved=False,approved=False,shape_repair_complete=False)
Path(str(dest)+'.json').write_text(json.dumps(report,indent=2)+'\n');(root/'fit_status.json').write_text(json.dumps({k:v for k,v in report.items() if k!='history'},indent=2)+'\n');print('R52_RETAINED_STATE',source,code,flush=True)
