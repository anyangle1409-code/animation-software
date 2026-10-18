"""Exact affine diagnostics; does not replace native Blender/contact checks."""
import json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'r47-audit/scripts'))
from original_review_r41_front import edge_pairs,angles

def measure(source,solution):
    with np.load(source) as archive:z={k:archive[k] for k in archive.files}
    delta=np.load(solution)['delta'];rest=z['rest'];faces=z['faces']
    e,ff=edge_pairs(faces);r=rest[e].mean(1)
    sel=(abs(r[:,0])>.08)&(abs(r[:,0])<.35)&(r[:,1]>.025)&(r[:,2]>1.20)&(r[:,2]<1.51)&z['free'].any(0)[e].any(1)
    tri=faces[ff[sel]]
    mask=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025)
    now=[];reversals=[];creases=[]
    for i,b in enumerate(z['base']):
        p=b+np.einsum('nij,nj->ni',z['mat'][i],np.einsum('kn,knj->nj',z['weight'][i],delta))
        def normals(v):
            t=v[faces];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
        reversals.append(int(((normals(b)*normals(p)).sum(1)<=0).sum()))
        creases.append(float((angles(p,tri)-angles(b,tri)).max()))
        if i<41:now.append(p[mask])
    old=z['base'][:41,mask]
    motion=(np.linalg.norm(np.diff(np.array(now),n=2,axis=0),axis=2)-np.linalg.norm(np.diff(old,n=2,axis=0),axis=2)).max()*1000
    report=dict(status='LOCAL_AFFINE_DIAGNOSTIC_NOT_NATIVE_ACCEPTANCE',
        marked_reversals=reversals[25],max_reversals=max(reversals),reversals=reversals,
        marked_crease_excess_deg=creases[25],max_crease_excess_deg=max(creases),
        back_motion_excess_mm=float(motion),source_max_mm=float(np.linalg.norm(delta,axis=2).max()*1000),
        dense_max_mm=float(np.linalg.norm(np.einsum('dk,knj->dnj',z['sampling_basis'],delta),axis=2).max()*1000),
        outside_authorized_max_mm=float(np.abs(delta[~z['r47_allowed']]).max()*1000))
    return report

if __name__=='__main__':
    report=measure(*sys.argv[1:3]);print(json.dumps(report,indent=2))
    Path(sys.argv[2]+'.metrics.json').write_text(json.dumps(report,indent=2)+'\n')
