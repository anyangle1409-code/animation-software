"""Coupled area constraints in material coordinates across both native paths."""
import json
import sys
from pathlib import Path
import numpy as np

def solve(data,epochs=120):
    for key in ('rest','base','mat','weight','delta','normal'):
        if not np.isfinite(data[key]).all():raise ValueError(f'Nonfinite response array: {key}')
    rest=np.asarray(data['rest'],float)
    all_faces=np.asarray(data['faces'],int)
    delta=np.asarray(data['delta'],float).copy()
    initial=delta.copy()
    free=np.asarray(data['free'],bool)
    normals=np.asarray(data['normal'],float)
    touched=free.any(0)
    faces=all_faces[touched[all_faces].any(1)]
    def areas(p):
        return .5*np.linalg.norm(np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]]),axis=1)
    a0=areas(rest)
    baselines=[areas(p) for p in data['base']]
    upper=[np.maximum(1.8*a0,a*.99) for a in baselines]
    lower=.2*a0
    def position(s):
        dr=np.einsum('kn,knj->nj',data['weight'][s],delta)
        return data['base'][s]+np.einsum('nij,nj->ni',data['mat'][s],dr)
    history=[]
    for epoch in range(epochs):
        # Alternate traversal to avoid privileging the final pose in a pass.
        order=range(len(baselines)) if epoch%2==0 else range(len(baselines)-1,-1,-1)
        for s in order:
            if not np.any(data['weight'][s]):continue
            p=position(s)
            ar=areas(p)
            error=np.maximum(ar-upper[s],0)+np.minimum(ar-lower,0)
            chosen=np.flatnonzero(np.abs(error)>np.maximum(a0*1e-5,1e-15))
            if not len(chosen):continue
            f=faces[chosen];tri=p[f]
            nn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
            nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-20)
            g=.5*np.stack([np.cross(tri[:,1]-tri[:,2],nn),np.cross(tri[:,2]-tri[:,0],nn),np.cross(tri[:,0]-tri[:,1],nn)],axis=1)
            material=np.einsum('nvji,nvj->nvi',data['mat'][s][f],g)
            gradients=[];denom=np.zeros(len(f))
            for k in range(len(delta)):
                grad=material*data['weight'][s,k][f][:,:,None]
                n=normals[k][f]
                grad-=n*(grad*n).sum(2)[:,:,None]
                grad*=free[k][f][:,:,None]
                gradients.append(grad)
                denom+=(grad*grad).sum((1,2))
            scale=-.8*error[chosen]/np.maximum(denom,1e-20)
            for k,grad in enumerate(gradients):
                update=np.zeros_like(rest);count=np.zeros(len(rest))
                changes=scale[:,None,None]*grad
                for v in range(3):
                    np.add.at(update,f[:,v],changes[:,v])
                    np.add.at(count,f[:,v],free[k][f[:,v]]*(denom>1e-20))
                delta[k]+=update/np.maximum(count[:,None],1)
            difference=delta-initial
            length=np.linalg.norm(difference,axis=2)
            delta=initial+difference*np.minimum(1,.015/np.maximum(length,1e-20))[:,:,None]
            delta[~free]=initial[~free]
        if epoch%10==0 or epoch==epochs-1:
            if not np.isfinite(delta).all():raise ValueError('Nonfinite solved material delta')
            extra_stretch=extra_collapse=0;worst=0.
            rows=[]
            for s in range(len(baselines)):
                a=areas(position(s));b=baselines[s]
                st=int((a>2*a0).sum());co=int((a<.1*a0).sum())
                bs=int((b>2*a0).sum());bc=int((b<.1*a0).sum())
                extra_stretch+=st>bs;extra_collapse+=co>bc
                worst=max(worst,float((np.maximum(a-upper[s],0)/np.maximum(a0,1e-20)).max(initial=0)))
                rows.append({'sample':s,'stretch':st,'baseline_stretch':bs,'collapse':co,'baseline_collapse':bc})
            history.append({'epoch':epoch,'extra_stretch_samples':extra_stretch,'extra_collapse_samples':extra_collapse,'max_area_excess':worst})
            print('R37_COUPLED_AREA',json.dumps(history[-1]),flush=True)
            if not extra_stretch and not extra_collapse and worst<.005:break
    report={'extra_stretch_samples':extra_stretch,'extra_collapse_samples':extra_collapse,
            'max_material_adjustment_mm':float(np.linalg.norm(delta-initial,axis=2).max()*1000),
            'history':history,'samples':rows,'frozen_vertices_unchanged':bool(np.array_equal(delta[~free],initial[~free]))}
    return delta,report

if __name__=='__main__':
    source,dest=sys.argv[1:3]
    with np.load(source) as z:
        data={key:z[key] for key in z.files}
    delta,report=solve(data)
    np.savez_compressed(dest,delta=delta)
    Path(dest+'.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['extra_stretch_samples'] or report['extra_collapse_samples']:
        raise SystemExit('Coupled constraints still fail; no candidate will be built')

