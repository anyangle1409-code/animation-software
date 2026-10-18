"""Instrument the unchanged R46 feasibility/minimum-L1 proposal solver."""
import os,time,json
from pathlib import Path
import numpy as np
from scipy import sparse
from original_review_r46_lp import step as regularized_step

calls=0
def reset_cache():pass

def step(A,rhs,trust,relaxed=None,profile_opt_tolerance=1e-7):
    global calls
    calls+=1
    report=dict(call=calls,rows=A.shape[0],columns=A.shape[1],nnz=A.nnz,trust_mm=trust)
    folder=os.environ.get('HGPT_R49_LP_DIAGNOSTICS')
    if folder:
        p=Path(folder);p.mkdir(parents=True,exist_ok=True)
        sparse.save_npz(p/'latest_linear_matrix.npz',A,compressed=False)
        np.savez(p/'latest_linear_arguments.npz',rhs=rhs,trust=trust,relaxed=relaxed)
        (p/'latest_linear_status.json').write_text(json.dumps(dict(report,status='SOLVING'),indent=2)+'\n')
    print('R49_LINEAR_BEGIN',json.dumps(report),flush=True)
    start=time.monotonic()
    result=regularized_step(A,rhs,trust,relaxed,profile_opt_tolerance)
    report.update(status='SOLVED',seconds=time.monotonic()-start,slack_mm=result[1])
    if folder:(Path(folder)/'latest_linear_status.json').write_text(json.dumps(report,indent=2)+'\n')
    print('R49_LINEAR_END',json.dumps(report),flush=True)
    return result
