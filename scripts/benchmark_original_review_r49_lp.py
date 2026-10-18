"""Compare crossover modes on exactly the same captured R48 problem."""
import sys,json,time,warnings
from pathlib import Path
import numpy as np
import scipy
from scipy import sparse
from scipy.optimize import linprog,OptimizeWarning

def benchmark(directory,mode):
    root=Path(directory);A=sparse.load_npz(root/'A.npz');z=np.load(root/'arguments.npz')
    rhs=z['rhs'];relaxed=z['relaxed'];trust=float(z['trust'])
    active=np.unique(A.indices);local=A[:,active];n=len(active)
    scale=1/np.maximum(np.asarray(abs(local).sum(axis=1)).ravel(),1e-14)
    local=(sparse.diags(scale)@local).tocsr()
    matrix=sparse.hstack([local,-(relaxed*scale)[:,None]],format='csr')
    options=dict(time_limit=20.,disp=True,dual_feasibility_tolerance=1e-8,primal_feasibility_tolerance=1e-8)
    if mode!='default':options['run_crossover']=mode
    start=time.monotonic()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',category=OptimizeWarning,message='Unrecognized options detected.*')
        result=linprog(np.r_[np.zeros(n),1.],A_ub=matrix,b_ub=rhs*scale,bounds=[(-trust,trust)]*n+[(0,None)],method='highs-ipm',options=options)
    report=dict(mode=mode,scipy=scipy.__version__,numpy=np.__version__,elapsed_seconds=time.monotonic()-start,
        success=bool(result.success),status=int(result.status),message=result.message,iterations=result.nit,crossover_iterations=result.crossover_nit)
    if result.x is not None:
        movement=np.zeros(A.shape[1]);movement[active]=result.x[:-1];slack=max(0.,float(result.x[-1]))
        violation=float(np.max(A@movement-rhs-relaxed*slack,initial=0))
        report.update(slack_mm=slack,max_constraint_violation=violation,max_control_step_mm=float(abs(movement).max()))
        np.savez_compressed(root/f'{mode}_proposal.npz',movement=movement,slack=slack)
    (root/f'{mode}_timing.json').write_text(json.dumps(report,indent=2)+'\n')
    print('R49_LP_BENCHMARK',json.dumps(report),flush=True)

if __name__=='__main__':benchmark(*sys.argv[1:3])
