"""Intermediate material redistribution; final safety and native gates are mandatory."""
import json
import sys
from pathlib import Path
import numpy as np

def solve(data,epochs=180):
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
    reference=[]
    for p in data['base']:
        cross=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
        reference.append(cross/np.maximum(np.linalg.norm(cross,axis=1)[:,None],1e-20))
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
            delta=initial+difference*np.minimum(1,.008/np.maximum(length,1e-20))[:,:,None]
            delta[~free]=initial[~free]
            # Signed area against the parent's same-pose normals stops the
            # area-only solver from folding a small triangle through itself.
            p=position(s);tri=p[faces]
            cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
            signed=.5*(cross*reference[s]).sum(1)
            chosen=np.flatnonzero((signed<.2*baselines[s])&(baselines[s]>1e-12))
            if len(chosen):
                f=faces[chosen];tri=p[f];nn=reference[s][chosen]
                g=.5*np.stack([np.cross(tri[:,1]-tri[:,2],nn),np.cross(tri[:,2]-tri[:,0],nn),np.cross(tri[:,0]-tri[:,1],nn)],axis=1)
                material=np.einsum('nvji,nvj->nvi',data['mat'][s][f],g)
                gradients=[];denom=np.zeros(len(f))
                for k in range(len(delta)):
                    grad=material*data['weight'][s,k][f][:,:,None]
                    n=normals[k][f];grad-=n*(grad*n).sum(2)[:,:,None]
                    grad*=free[k][f][:,:,None];gradients.append(grad);denom+=(grad*grad).sum((1,2))
                scale=.8*(.2*baselines[s][chosen]-signed[chosen])/np.maximum(denom,1e-20)
                for k,grad in enumerate(gradients):
                    update=np.zeros_like(rest);count=np.zeros(len(rest))
                    for v in range(3):
                        np.add.at(update,f[:,v],scale[:,None]*grad[:,v]);np.add.at(count,f[:,v],free[k][f[:,v]]*(denom>1e-20))
                    delta[k]+=update/np.maximum(count[:,None],1)
                difference=delta-initial;length=np.linalg.norm(difference,axis=2)
                delta=initial+difference*np.minimum(1,.008/np.maximum(length,1e-20))[:,:,None]
                delta[~free]=initial[~free]

        if epoch%10==0 or epoch==epochs-1:
            if not np.isfinite(delta).all():raise ValueError('Nonfinite solved material delta')
            extra_stretch=extra_collapse=orientation_barriers=0;worst=0.
            rows=[]
            for s in range(len(baselines)):
                p=position(s);a=areas(p);b=baselines[s]
                tri=p[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
                signed=.5*(cross*reference[s]).sum(1)
                orientation_barriers+=int(((signed<.199*b)&(b>1e-12)).sum())
                st=int((a>2*a0).sum());co=int((a<.1*a0).sum())
                bs=int((b>2*a0).sum());bc=int((b<.1*a0).sum())
                extra_stretch+=st>bs;extra_collapse+=co>bc
                worst=max(worst,float((np.maximum(a-upper[s],0)/np.maximum(a0,1e-20)).max(initial=0)))
                rows.append({'sample':s,'stretch':st,'baseline_stretch':bs,'collapse':co,'baseline_collapse':bc})
            history.append({'epoch':epoch,'extra_stretch_samples':extra_stretch,'extra_collapse_samples':extra_collapse,'max_area_excess':worst,'orientation_barriers':orientation_barriers})
            print('R38_COUPLED_AREA',json.dumps(history[-1]),flush=True)
            if not extra_stretch and not extra_collapse and not orientation_barriers and worst<.005:break
    reversed_counts=[]
    for s in range(len(baselines)):
        p=position(s);tri=p[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        reversed_counts.append(int((((cross*reference[s]).sum(1)<0)&(baselines[s]>1e-12)).sum()))
    report={'normal_rotations_over_90_degrees':reversed_counts,'extra_stretch_samples':extra_stretch,'extra_collapse_samples':extra_collapse,
            'max_material_adjustment_mm':float(np.linalg.norm(delta-initial,axis=2).max()*1000),
            'history':history,'samples':rows,'frozen_vertices_unchanged':bool(np.array_equal(delta[~free],initial[~free]))}
    return delta,report

