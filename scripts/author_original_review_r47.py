"""R47 direct S7 shape study, after owner approval of the whole-outline scope.
Project-authored inward side-cap envelope; no private photo or traced contour input.
No optimizer, model save, skeleton/weights/Basis/HGPT edits.
"""
from pathlib import Path
import json,sys
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
KEYS=(110.,120.,130.,136.,145.,156.,166.)
GAINS=(0.,.55,.95,1.,.70,.20,0.)
Q=np.array([-.34,-.28,-.22,-.16,-.10,-.055,-.01,.04,.09,.13])
INWARD=np.array([0.,.002,.010,.026,.041,.045,.032,.016,.004,0.])

def smoothstep(v):
    v=np.clip(v,0.,1.)
    return v*v*(3.-2.*v)

def author(d):
    rest=d['rest'];n=len(rest);delta=np.zeros((7,n,3));allowed=np.zeros((7,n),bool)
    mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
    anchors=np.array([18633,mirror])
    distal_any=np.zeros(n,bool)
    for k in range(7):
        for side,(gh,el) in zip((-1,1),d['key_bones'][k]):
            axis=el-gh;axis/=np.linalg.norm(axis)
            p=d['key_base'][k]
            distal_any|=(p[:,0]*side>0)&((p-gh)@axis>=.16)
    region=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.44)&(rest[:,2]>1.15)&(rest[:,2]<1.56)
    up=np.array([0.,-.02,1.]);up/=np.linalg.norm(up)
    envelope=PchipInterpolator(Q,INWARD,extrapolate=False)
    logs=[]
    for k,gain in enumerate(GAINS):
        if not gain:continue
        p=d['key_base'][k];world=np.zeros((n,3))
        for side,(gh,el) in zip((-1,1),d['key_bones'][k]):
            axis=el-gh;axis/=np.linalg.norm(axis)
            station=(p-gh)@axis
            q=(p-gh)@up
            same=(rest[:,0]*side>0)&(p[:,0]*side>0)
            mask=same&region&~distal_any&(station<.16)&(q>Q[0])&(q<Q[-1])
            mask[anchors]=False
            allowed[k]|=mask
            # Local cross-sectional side envelope; avoid moving the centre of the back.
            bins=np.arange(Q[0]-.01,Q[-1]+.015,.005)
            width=np.full(len(bins),np.nan)
            for j,level in enumerate(bins):
                near=same&(abs(q-level)<.009)
                if near.any():width[j]=abs(p[near,0]).max()
            good=np.isfinite(width)
            width=np.interp(bins,bins[good],width[good])
            width=gaussian_filter1d(width,1.)
            outer=np.interp(q,bins,width)
            lateral=smoothstep((abs(p[:,0])-(outer-.11))/.11)
            distal=1.-smoothstep((station-.12)/.04)
            distance=np.linalg.norm(p[:,None]-p[anchors][None],axis=2).min(1)
            anchor_fade=smoothstep(distance/.04)
            amplitude=np.nan_to_num(envelope(q))*gain*lateral*distal*anchor_fade
            world[mask,0]=-side*amplitude[mask]
        coeff=d['key_weight'][k,k]
        active=allowed[k]&(coeff>.95)
        allowed[k]&=coeff>.95
        delta[k,active]=np.einsum('nij,nj->ni',np.linalg.pinv(d['key_mat'][k,active],rcond=1e-4),world[active]/coeff[active,None])
        logs.append(dict(key=KEYS[k],allowed=int(active.sum()),requested_world_max_mm=float(np.linalg.norm(world,axis=1).max()*1000)))
    # One global scale preserves smoothness while retaining BOTH existing45mm caps.
    dense=np.einsum('dk,knj->dnj',d['sampling_basis'],delta)
    maximum=max(float(np.linalg.norm(delta,axis=2).max()),float(np.linalg.norm(dense,axis=2).max()))
    factor=min(1.,.044999/max(maximum,1e-20))
    delta*=factor
    return delta,allowed,dict(status='DIRECT_SHAPE_STUDY_NOT_ACCEPTED',keys=logs,
        global_cap_scale=factor,unscaled_max_material_mm=maximum*1000,
        source_max_mm=float(np.linalg.norm(delta,axis=2).max()*1000),
        max_dense_mm=float(np.linalg.norm(np.einsum('dk,knj->dnj',d['sampling_basis'],delta),axis=2).max()*1000),
        distal_protection_from_m=.16,distal_fade_from_m=.12,anchors=anchors.tolist(),
        owner_scope_approved='2026-10-18 19:05 Europe/London',
        target_policy='inward whole-outline side cap; old R42 outward target retained only as legacy diagnostic')

if __name__=='__main__':
    source,destination,solution=sys.argv[1:4]
    with np.load(source) as z:d={k:z[k] for k in z.files}
    delta,allowed,report=author(d)
    d.update(r46_original_free=d['free'],free=d['free']|allowed,r47_allowed=allowed)
    np.savez_compressed(destination,**d)
    np.savez_compressed(solution,delta=delta)
    Path(solution+'.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
