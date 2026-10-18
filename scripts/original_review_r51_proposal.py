"""Verified bounded search proposals; never claims an optimal or accepted model."""
import json,os
from pathlib import Path
import numpy as np
from original_review_r51_bounded import propose
calls=0

def step(A,rhs,trust,labels,scales):
 global calls
 calls+=1
 soft=np.flatnonzero([not name.startswith(('profile_','material_bound','dense_material_bound')) for name in labels])
 controls=np.unique(A.indices)
 units={'area_upper':1e-5,'area_lower':1e-5,'orientation':1e-5,'contact':.001,'front':1.,'posterior_normal_cone':1.,'back_motion':.001,'back_motion_cone':.001}
 weights=np.array([scales[j]/units.get(labels[j],1.) for j in soft]);weights/=max(float(np.median(weights[weights>0])),1e-15)
 report=dict(call=calls,stage=os.environ.get('HGPT_R51_FIT_STAGE','local'),proposal_optimal=False,model_saved=False,approved=False,status='PROPOSING')
 folder=os.environ.get('HGPT_R51_LP_DIAGNOSTICS')
 def record():
  if folder:
   p=Path(folder);p.mkdir(exist_ok=True,parents=True);(p/'latest_linear_status.json').write_text(json.dumps(report,indent=2)+'\n')
 record()
 try:x,result=propose(A[:,controls],rhs,weights,soft,trust,iterations=400)
 except Exception as error:
  report.update(status='FAILED_NO_PROPOSAL',error=str(error));record();raise
 report.update(result,status='HARD_FEASIBLE_SEARCH_PROPOSAL_NOT_OPTIMAL');record()
 if folder:
  with (Path(folder)/'linear_history.jsonl').open('a') as f:f.write(json.dumps(report)+'\n')
 print('R51_VERIFIED_BOUNDED_PROPOSAL',json.dumps(report),flush=True)
 movement=np.zeros(A.shape[1]);movement[controls]=x
 return movement,result['objective']
