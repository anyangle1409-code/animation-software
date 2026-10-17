"""Retain only the safe portion of the local authored skin target.

Couple all82poses. Safety can attenuate a local target but cannot slide vertices
in a new direction, the failure mode of the first rejected tangent solve.
"""
import json,sys
from pathlib import Path
import numpy as np
from scipy import sparse

def solve(data,epochs=180):
    for key in ('rest','base','mat','weight','delta','normal'):
        if not np.isfinite(data[key]).all():raise ValueError(f'Nonfinite response array: {key}')
    rest=np.asarray(data['rest'],float);initial=np.asarray(data['delta'],float).copy()
    free=np.asarray(data['free'],bool);all_faces=np.asarray(data['faces'],int)
    touched=free.any(0);faces=all_faces[touched[all_faces].any(1)]
    edges=np.unique(np.sort(np.concatenate([all_faces[:,[0,1]],all_faces[:,[1,2]],all_faces[:,[2,0]]]),axis=1),axis=0)
    i,j=edges.T;n=len(rest)
    adj=sparse.coo_matrix((np.ones(len(i)*2),(np.r_[i,j],np.r_[j,i])),shape=(n,n)).tocsr()
    lap=sparse.diags(1/np.maximum(np.asarray(adj.sum(1)).ravel(),1))@adj
    def crosses(p):return np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
    a0=.5*np.linalg.norm(crosses(rest),axis=1)
    references=[crosses(p) for p in data['base']]
    base_area=[.5*np.linalg.norm(v,axis=1) for v in references]
    scale=np.ones(initial.shape[:2]);delta=initial.copy();history=[]
    for epoch in range(epochs):
        badness=np.zeros_like(scale);rows=[];reversed_counts=[];extra_stretch=extra_collapse=0
        for s,b in enumerate(base_area):
            dr=np.einsum('kn,knj->nj',data['weight'][s],delta)
            p=data['base'][s]+np.einsum('nij,nj->ni',data['mat'][s],dr)
            cross=crosses(p);area=.5*np.linalg.norm(cross,axis=1)
            ref=references[s];dot=(cross*ref).sum(1)
            norm2=(ref*ref).sum(1)
            st=int((area>2*a0).sum());co=int((area<.1*a0).sum())
            bs=int((b>2*a0).sum());bc=int((b<.1*a0).sum())
            extra_stretch+=st>bs;extra_collapse+=co>bc
            rev=int(((dot<0)&(b>1e-12)).sum());reversed_counts.append(rev)
            rows.append({'sample':s,'stretch':st,'baseline_stretch':bs,'collapse':co,'baseline_collapse':bc})
            bad=((dot<.02*norm2)&(b>1e-12))
            if st>bs:bad|=(area>2*a0)&(b<=2*a0)
            if co>bc:bad|=(area<.1*a0)&(b>=.1*a0)
            vertices=np.unique(faces[bad])
            for k in range(len(delta)):
                badness[k,vertices]=np.maximum(badness[k,vertices],(data['weight'][s,k,vertices]>0)*free[k,vertices])
        if epoch%10==0 or epoch==epochs-1 or not badness.any():
            row={'epoch':epoch,'extra_stretch_samples':int(extra_stretch),'extra_collapse_samples':int(extra_collapse),'normal_rotations':int(sum(reversed_counts)),'unsafe_vertices':int((badness>0).sum())}
            history.append(row);print('R38_LOCAL_ATTENUATION',json.dumps(row),flush=True)
        if not badness.any():break
        if epoch==epochs-1:break
        # Spread the cutback over adjacent material vertices to avoid a small
        # hard boundary. The authored target direction itself remains fixed.
        for k in range(len(delta)):
            for _ in range(3):badness[k]=np.maximum(badness[k],.8*(lap@badness[k]))
        scale*=1-.25*badness
        delta=initial*scale[:,:,None]
        delta[~free]=initial[~free]
    if not np.isfinite(delta).all():raise ValueError('Nonfinite attenuated target')
    report={'extra_stretch_samples':int(extra_stretch),'extra_collapse_samples':int(extra_collapse),
            'normal_rotations_over_90_degrees':reversed_counts,'unsafe_vertices':int((badness>0).sum()),
            'max_material_adjustment_mm':float(np.linalg.norm(delta-initial,axis=2).max()*1000),
            'min_retained_target_fraction':float(scale.min()),'history':history,'samples':rows,
            'frozen_vertices_unchanged':bool(np.array_equal(delta[~free],initial[~free]))}
    return delta,report

def staged_solve(data):
    from redistribute_original_review_r38 import solve as redistribute
    data=dict(data);data['delta']=np.asarray(data['delta'],float)*.45
    authored=data['delta'].copy()
    result,intermediate=redistribute(data,epochs=180)
    data['delta']=result
    result,first_safety=solve(data)
    # Preserve flow in the other camera: a small smooth posterior shift through
    # the lower junction blends the three-quarter outline into the torso.
    p=data['base'][25];w=np.zeros(len(p))
    for side,gh in zip(('l','r'),data['marked_gh']):
        d=p-gh;d[:,0]*=1 if side=='r' else -1
        radius=np.sqrt(((d[:,0]-.04)/.04)**2+((d[:,1]+.02)/.04)**2+((d[:,2]+.045)/.03)**2)
        t=np.clip((2-radius)/.5,0,1)
        w=np.maximum(w,np.exp(-.5*radius**2)*t*t*(3-2*t))
    offset=np.zeros_like(p);offset[:,1]=.00075*w
    change=np.einsum('nij,nj->ni',np.linalg.pinv(data['mat'][25],rcond=1e-4),offset)
    data['delta']=result+change[None]*data['free'][:,:,None]
    result,report=solve(data)
    report.update(target_gain=.45,three_quarter_continuity_shift_mm=.75,
                  intermediate_redistribution=intermediate,first_safety=first_safety,
                  max_total_material_change_from_authored_mm=float(np.linalg.norm(result-authored,axis=2).max()*1000))
    return result,report

if __name__=='__main__':
    source,dest=sys.argv[1:3]
    with np.load(source) as z:data={key:z[key] for key in z.files}
    delta,report=staged_solve(data)
    np.savez_compressed(dest,delta=delta)
    Path(dest+'.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['extra_stretch_samples'] or report['extra_collapse_samples'] or report['unsafe_vertices'] or any(report['normal_rotations_over_90_degrees']):
        raise SystemExit('Coupled constraints still fail; no candidate will be built')
