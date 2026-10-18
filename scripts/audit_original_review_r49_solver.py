"""Capture an unchanged R48 linear problem before solving it.

Read-only model diagnostic. No candidate geometry or acceptance test changes.
"""
import os,sys,json,time
from pathlib import Path
import numpy as np
from scipy import sparse
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'r48-work/scripts'),str(ROOT/'r47-audit/scripts')]
import solve_original_review_r48 as previous

class Captured(Exception):pass

def capture(source,contacts,destination):
    out=Path(destination);out.mkdir(parents=True,exist_ok=True)
    with np.load(source) as z:d={k:z[k] for k in z.files}
    start=time.monotonic()
    def snapshot(A,rhs,trust,relaxed=None,**kwargs):
        sparse.save_npz(out/'A.npz',A)
        np.savez_compressed(out/'arguments.npz',rhs=rhs,trust=trust,relaxed=relaxed)
        report=dict(status='UNCHANGED_R48_LINEAR_PROBLEM_CAPTURED',shape=list(A.shape),nnz=A.nnz,
            capture_seconds=time.monotonic()-start,trust_mm=trust,model_saved=False)
        (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
        raise Captured()
    previous.linear_step=snapshot
    os.environ['HGPT_R43_MATERIAL_FIELD']='1'
    try:previous.solve(d,np.zeros_like(d['delta']),{},json.loads(Path(contacts).read_text())['contacts'],str(out/'unused.npz'),epochs=1)
    except Captured:pass

if __name__=='__main__':capture(*sys.argv[1:4])
