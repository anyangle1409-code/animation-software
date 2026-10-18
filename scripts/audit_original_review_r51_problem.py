"""Capture R50's stalled third LP exactly, without solving or saving a model.

Usage: python scripts/audit_original_review_r51_problem.py RESPONSE SEED CONTACTS OUT
Use the immutable R49 response and R50 retained delta; set HGPT_R43_MATERIAL_FIELD=1.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy import sparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))

def capture(source,seed,contacts,directory):
 text=(ROOT/'scripts/solve_original_review_r50.py').read_text()
 if text.count('trust=.5')!=1:raise RuntimeError('Parent solver trust initialization changed')
 namespace={'__name__':'r51_capture_only'}
 exec(compile(text.replace('trust=.5','trust=1.125'),'immutable_R50_third_problem','exec'),namespace)
 out=Path(directory);out.mkdir(parents=True,exist_ok=False)
 class Captured(Exception):pass
 def intercept(A,rhs,trust,labels,scales):
  sparse.save_npz(out/'A.npz',A)
  np.savez_compressed(out/'arguments.npz',rhs=rhs,trust=trust,labels=np.array(labels),scales=scales)
  report=dict(rows=A.shape[0],columns=A.shape[1],nnz=A.nnz,active_controls=len(np.unique(A.indices)),trust_mm=trust,
   hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},model_saved=False,solved=False)
  (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
  if report['rows']!=49211 or report['active_controls']!=6606 or trust!=1.125:raise RuntimeError('Capture differs from immutable third problem')
  print(json.dumps(report),flush=True);raise Captured()
 namespace['linear_step']=intercept
 with np.load(source) as z:data={k:z[k] for k in z.files}
 with np.load(seed) as z:delta=z['delta']
 try:namespace['solve'](data,delta,{},json.loads(Path(contacts).read_text())['contacts'],str(out/'NOT_A_SOLUTION'),epochs=1)
 except Captured:return
 raise RuntimeError('No LP was captured')

if __name__=='__main__':capture(*sys.argv[1:5])
