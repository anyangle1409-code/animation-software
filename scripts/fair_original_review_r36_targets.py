"""Create broader fair skin targets from R34 poses for R36; no assets are imported.

Thin-plate surface energy with position anchors and a fixed boundary. This
changes posed S7 targets only, not the skeleton, basis, weights or other keys.
"""
import json
import sys
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

def smooth(u):
    u=np.clip(u,0,1)
    return u*u*(3-2*u)

def targets(source, destination):
    z=np.load(source)
    faces=z['faces'];rest=z['rest'];n=len(rest)
    edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
    i,j=edges.T
    a=sparse.coo_matrix((np.ones(2*len(i)),(np.r_[i,j],np.r_[j,i])),shape=(n,n)).tocsr()
    lap=sparse.eye(n)-sparse.diags(1/np.asarray(a.sum(1)).ravel())@a
    mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*np.array([-1,1,1]),axis=1)))
    data={};report={}
    for ht,gain in ((120.,1.),(130.,1.),(145.,1.),(156.,.4),(166.,0.)):
        p=z[f'all_{ht}'];w=np.zeros(n)
        for side in ('l','r'):
            d=p-z[f'gh_{side}_{ht}']
            q=np.sqrt(((d[:,0]-(.035 if side=='r' else -.035))/.19)**2+(d[:,1]/.20)**2+((d[:,2]+.015)/.28)**2)
            w=np.maximum(w,smooth((1-q)/.35))
        distance=np.minimum(np.linalg.norm(p-p[18633],axis=1),np.linalg.norm(p-p[mirror],axis=1))
        w*=smooth((distance-.015)/.03)
        active=np.flatnonzero(w>1e-6)
        c=lap[:,active]
        h=c.T@c+sparse.diags(.001/np.maximum(w[active],1e-6)**2)
        delta=np.zeros_like(p)
        if gain:
            delta[active]=gain*spsolve(h.tocsc(),-c.T@(lap@p))
        data[str(ht)]=delta
        report[str(ht)]={'gain':gain,'support_vertices':int(len(active)),
                         'max_offset_mm':float(np.linalg.norm(delta,axis=1).max()*1000),
                         'front_sentinel_offset_mm':float(np.linalg.norm(delta[18633])*1000)}
    np.savez_compressed(destination,**data)
    Path(str(destination)+'.json').write_text(json.dumps(report,indent=2)+'\n')
    print('R36_FAIR_TARGETS',json.dumps(report),flush=True)

if __name__=='__main__':
    targets(*sys.argv[1:])
