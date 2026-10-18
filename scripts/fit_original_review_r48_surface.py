"""Local nonlinear feasibility probe: direct crease and orientation penalties.

Starts from the safe parent, not a folded initialization. This is diagnostic
research, not a model-acceptance path; native gates remain mandatory.
"""
import sys,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'r47-audit/scripts'))
from original_review_r41_front import edge_pairs,angles
from original_review_r44_area import upper_bounds
from repair_original_review_r48 import contour_constraints

def outline_observations(points,edges,with_grad=False):
    a,b=points[edges[:,0]],points[edges[:,1]]
    values=[];vertices=[];gradients=[]
    for level in np.arange(1.18,1.62,.01):
        cross=((a[:,2]<=level)&(b[:,2]>level))|((b[:,2]<=level)&(a[:,2]>level))
        ee=edges[cross];aa,bb=a[cross],b[cross]
        t=(level-aa[:,2])/(bb[:,2]-aa[:,2]);p=aa+t[:,None]*(bb-aa)
        for side in (-1,1):
            for n in (np.array([side,0.,0.]),np.array([side,-1.,0.])/np.sqrt(2.)):
                support=np.where(p[:,0]*side>.08,p@n,-np.inf)
                j=int(np.argmax(support));values.append(support[j])
                if with_grad:
                    g=n.copy();g[2]-=((bb[j]-aa[j])@n)/(bb[j,2]-aa[j,2])
                    vertices.append(ee[j]);gradients.append([(1-t[j])*g,t[j]*g])
    if with_grad:return np.array(values),np.array(vertices),np.array(gradients)
    return np.array(values)

def fit(d,old,key,iterations=500,initial=None,outline_target=False):
    b=d['key_base'][key];faces=d['faces'];mask=d['r47_allowed'][key];ids=np.flatnonzero(mask)
    M=d['key_mat'][key]*d['key_weight'][key,key,:,None,None]
    inv=np.linalg.pinv(M[ids],rcond=1e-4)
    target=b+np.einsum('nij,nj->ni',M,old[key])
    constraints=contour_constraints(target,mask)
    ci=np.array([j for j,_ in constraints]);cv=np.array([v for _,v in constraints])
    ct=np.einsum('ni,ni->n',target[ci],cv)
    edges=np.unique(np.sort(np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1),axis=0)
    outline_target_values=outline_observations(target,edges)
    edge_vertices,pairs=edge_pairs(faces)
    centre=d['rest'][edge_vertices].mean(1)
    posterior=(abs(centre[:,0])>.08)&(abs(centre[:,0])<.35)&(centre[:,1]>.025)&(centre[:,2]>1.20)&(centre[:,2]<1.51)&d['free'].any(0)[edge_vertices].any(1)
    pair_tri=faces[pairs];choose=mask[pair_tri].any((1,2))
    pair_tri=pair_tri[choose]
    t0=b[pair_tri];cr0=np.cross(t0[:,:,1]-t0[:,:,0],t0[:,:,2]-t0[:,:,0]);len0=np.linalg.norm(cr0,axis=2)
    n0=cr0/np.maximum(len0[:,:,None],1e-15)
    # Exactly the existing posterior domain gets the tight crease margin.
    # Elsewhere use a research regularizer; native front gates remain separate.
    extra=np.where(posterior[choose],1.5,20.)
    radius=2*np.sin(np.radians(np.minimum(angles(b,pair_tri)+extra,179.9))/2)
    ff=faces[mask[faces].any(1)]
    t0=b[ff];cross0=np.cross(t0[:,1]-t0[:,0],t0[:,2]-t0[:,0]);length0=np.linalg.norm(cross0,axis=1)
    normal0=cross0/np.maximum(length0[:,None],1e-15)
    r=d['rest'][ff];restarea=.5*np.linalg.norm(np.cross(r[:,1]-r[:,0],r[:,2]-r[:,0]),axis=1)
    all_t=b[faces];all_r=d['rest'][faces]
    all_a=.5*np.linalg.norm(np.cross(all_t[:,1]-all_t[:,0],all_t[:,2]-all_t[:,0]),axis=1)
    all_ra=.5*np.linalg.norm(np.cross(all_r[:,1]-all_r[:,0],all_r[:,2]-all_r[:,0]),axis=1)
    maxratio=(all_a/np.maximum(all_ra,1e-20)).max()
    upper=upper_bounds(restarea,(length0*.5)[None],np.array([maxratio]))[0]
    lower=np.minimum(.1001*restarea,length0*.5)
    start=time.time();calls=0;latest={}
    def loss(x):
        nonlocal calls,latest
        p=b.copy();p[ids]+=.001*x.reshape(-1,3)
        g=np.zeros_like(p)
        if outline_target:
            observations,ov,og=outline_observations(p,edges,True)
            residual=observations-outline_target_values
            value=float(10*np.sum((residual*1000)**2))
            np.add.at(g,ov.ravel(),(2e7*residual[:,None,None]*og).reshape(-1,3))
        else:
            residual=(p[ci]*cv).sum(1)-ct
            value=float(np.sum((residual*1000)**2))
            np.add.at(g,ci,2e6*residual[:,None]*cv)
        # Weak positional preference only; contour is the owner-approved target.
        residual_all=p[ids]-target[ids]
        value+=float(.0001*np.sum((residual_all*1000)**2));g[ids]+=.0002e6*residual_all
        t=p[pair_tri];cr=np.cross(t[:,:,1]-t[:,:,0],t[:,:,2]-t[:,:,0]);length=np.maximum(np.linalg.norm(cr,axis=2),1e-15);n=cr/length[:,:,None]
        difference=n[:,0]-n[:,1];norm=np.maximum(np.linalg.norm(difference,axis=1),1e-15)
        excess=np.maximum(norm-radius,0)
        weight=1e6
        value+=float(weight*np.sum(excess**2))
        v=2*weight*(excess/norm)[:,None]*difference
        gn=np.stack((v,-v),axis=1)
        gc=(gn-n*np.sum(n*gn,axis=2)[:,:,None])/length[:,:,None]
        tg=np.stack((np.cross(t[:,:,1]-t[:,:,2],gc),np.cross(t[:,:,2]-t[:,:,0],gc),np.cross(t[:,:,0]-t[:,:,1],gc)),axis=2)
        np.add.at(g,pair_tri.ravel(),tg.reshape(-1,3))
        t=p[ff];cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);length=np.maximum(np.linalg.norm(cr,axis=1),1e-15)
        area=length*.5;signed=(cr*normal0).sum(1)/np.maximum(length0,1e-15)
        orient=np.maximum(.1-signed,0)
        under=np.maximum((lower-area)/np.maximum(restarea,1e-15),0)
        over=np.maximum((area-upper)/np.maximum(restarea,1e-15),0)
        value+=float(weight*np.sum(orient**2+under**2+over**2))
        gc=(-2*weight*orient/np.maximum(length0,1e-15))[:,None]*normal0
        gc+=(weight*(over-under)/np.maximum(restarea,1e-15))[:,None]*cr/length[:,None]
        tg=np.stack((np.cross(t[:,1]-t[:,2],gc),np.cross(t[:,2]-t[:,0],gc),np.cross(t[:,0]-t[:,1],gc)),axis=1)
        np.add.at(g,ff.ravel(),tg.reshape(-1,3))
        source=np.einsum('nij,nj->ni',inv,p[ids]-b[ids]);slength=np.maximum(np.linalg.norm(source,axis=1),1e-15)
        excess_cap=np.maximum(slength-.0449,0)
        value+=float(1e10*np.sum(excess_cap**2))
        g[ids]+=np.einsum('nji,nj->ni',inv,(2e10*excess_cap/slength)[:,None]*source)
        calls+=1
        crease_changes=angles(p,pair_tri)-angles(b,pair_tri)
        latest=dict(value=value,crease_excess_deg=float(crease_changes.max()),posterior_crease_excess_deg=float(crease_changes[posterior[choose]].max()),contour_projection_max_mm=float(abs(residual).max()*1000),source_max_mm=float(slength.max()*1000),elapsed_s=time.time()-start)
        if calls%50==0:print(json.dumps(dict(calls=calls,**latest)),flush=True)
        return value,.001*g[ids].ravel()
    x=np.zeros(len(ids)*3) if initial is None else (1000*np.einsum('nij,nj->ni',M[ids],initial[key,ids])).ravel()
    # Verify the analytic gradient away from the zero-penalty kink.
    testx=np.random.default_rng(48).normal(0,.05,len(x));value,grad=loss(testx)
    check=np.random.default_rng(49).choice(len(x),6,replace=False);errors=[]
    for j in check:
        xp=testx.copy();xm=testx.copy();xp[j]+=1e-4;xm[j]-=1e-4
        numerical=(loss(xp)[0]-loss(xm)[0])/(2e-4)
        errors.append(abs(numerical-grad[j])/max(1,abs(numerical),abs(grad[j])))
    assert max(errors)<1e-4,errors
    result=minimize(loss,x,jac=True,method='L-BFGS-B',options=dict(maxiter=iterations,ftol=1e-12,gtol=1e-6,maxls=35,maxcor=15))
    output=np.zeros_like(old);output[key,ids]=np.einsum('nij,nj->ni',inv,.001*result.x.reshape(-1,3))
    loss(result.x)
    return output,dict(**latest,success=bool(result.success),message=str(result.message),iterations=int(result.nit),gradient_relative_error=max(errors))

if __name__=='__main__':
    source,previous,output=sys.argv[1:4]
    with np.load(source) as z:d={k:z[k] for k in z.files}
    old=np.load(previous)['delta']
    delta,report=fit(d,old,int(sys.argv[4]) if len(sys.argv)>4 else 3,int(sys.argv[5]) if len(sys.argv)>5 else 500,np.load(sys.argv[6])['delta'] if len(sys.argv)>6 else None,len(sys.argv)>7 and sys.argv[7]=='outline')
    np.savez_compressed(output,delta=delta)
    Path(output+'.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
