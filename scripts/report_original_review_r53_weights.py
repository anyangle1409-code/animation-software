"""Require complete execution evidence; retain numerical failures without approval."""
from pathlib import Path
import sys,json,re
p=Path(sys.argv[1]);errors=[];results={}
for name in ('render','native','benchmarks','dense_motion'):
 f=p/(name+'_exit.txt');code=int(f.read_text()) if f.exists() else None
 results[name]=code
 if code!=0:errors.append(f'{name} execution exit={code}')
for name in ('native_final.json','benchmarks.json','dense_motion.json','native_check_status.json','projection_check_status.json','r53_weight_trial_review.json'):
 f=p/name
 if not f.exists():errors.append('Missing '+name)
 else:
  d=json.loads(f.read_text())
  if name.endswith('check_status.json'):
   for test,code in d['tests'].items():
    log=p/(test+'_test.txt')
    text=log.read_text() if log.exists() else ''
    completed_assertion_failure=bool(re.search(r'Ran [1-9][0-9]* tests?',text) and re.search(r'FAILED \(failures=[1-9][0-9]*\)',text) and 'FAIL:' in text)
    if not log.exists() or (code!=0 and not completed_assertion_failure):errors.append('Test execution error: '+test)
summary=dict(status='EVIDENCE_INCOMPLETE' if errors else 'EVIDENCE_COMPLETED_NOT_ACCEPTED',execution_exit_codes=results,execution_errors=errors,model_saved=False,approved=False,repair_complete=False,
 limitations=['Original projection tests only describe unchanged seven-knot R52 data; they do not certify this weight exception.','Original dense oscillation metric describes corrective increments, not additional weight-induced displacement.','Actual native83 geometry and161 back samples evaluate the patched mesh.','Owner visual acceptance and all numerical safety requirements remain outstanding.'])
(p/'r53_weight_execution.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary));raise SystemExit(bool(errors))
