"""Read-only certificate: can the R46 fitting domain move its arm-root outline?
No Blender data or candidate is written. Arguments: source.npz solution.npz report.json.
"""
from pathlib import Path
import json,sys
import numpy as np

def audit(source, solution):
    with np.load(source) as z:
        data={k:z[k] for k in z.files}
    delta=np.load(solution)['delta']
    frame=25
    base=data['base'][frame]
    mat=data['mat'][frame]
    weights=data['weight'][frame]
    current=base+np.einsum('nij,nj->ni',mat,np.einsum('kn,knj->nj',weights,delta))
    faces=data['faces']
    edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
    up=np.array([0.,-.02,1.]);up/=np.linalg.norm(up)
    x=256+current[:,0]/1.15*512
    y=256-(current-np.array([0.,0.,1.45]))@up/1.15*512
    results=[]
    for row in range(180,361,10):
        a,b=edges.T
        selected=((y[a]<=row)&(y[b]>row))|((y[b]<=row)&(y[a]>row))
        a,b=a[selected],b[selected]
        t=(row-y[a])/(y[b]-y[a])
        xx=x[a]+t*(x[b]-x[a])
        for side,j in [('left',int(np.argmin(xx))),('right',int(np.argmax(xx)))]:
            vertices=np.array([a[j],b[j]])
            coefficients=weights[:,vertices]*data['free'][:,vertices]
            response=coefficients[:,:,None,None]*mat[vertices][None]
            fixed=bool(np.count_nonzero(response)==0)
            results.append(dict(side=side,screen_row=row,screen_x=float(xx[j]),
                vertices=vertices.tolist(),locked_at_this_pose=fixed,
                maximum_free_coordinate_response=float(abs(response).max()),
                current_increment_mm=float(np.linalg.norm(current[vertices]-base[vertices],axis=1).max()*1000)))
    locked_upper=[r for r in results if r['screen_row']<=230]
    assert len(locked_upper)==12
    assert all(r['locked_at_this_pose'] and r['maximum_free_coordinate_response']==0. and r['current_increment_mm']==0. for r in locked_upper)
    return dict(status='READ_ONLY_SCOPE_CERTIFICATE_NOT_A_MODEL',frame=frame,
        elevation_degrees=135.625,locked_upper_outline_records=len(locked_upper),
        explanation='At these outline edges every active source coordinate is fixed. Any change confined to the existing free mask has exactly zero response there.',
        records=results)

if __name__=='__main__':
    source,solution,dest=sys.argv[1:4]
    report=audit(source,solution)
    Path(dest).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
