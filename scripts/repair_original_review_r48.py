"""Experimental ARAP surface extension of the owner-approved R47 contour.

All Dirichlet boundaries retain the authorized scope. No Blender save here.
"""
import json,sys
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

def contour_constraints(points,allowed):
    constraints={}
    for side in (-1,1):
        for direction in (np.array([side,0.,0.]),np.array([side,-1.,0.])/np.sqrt(2.)):
            height=points[:,2]
            width=points@direction
            for level in np.arange(1.15,1.62,.004):
                ids=np.flatnonzero((points[:,0]*side>.08)&(abs(height-level)<.003))
                if len(ids):
                    j=ids[np.argmax(width[ids])]
                    if allowed[j]:constraints[(int(j),tuple(direction))]=True
    return [(j,np.array(direction)) for j,direction in constraints]

def arap(base,faces,target,allowed,constraints,iterations=60):
    n=len(base)
    edges=np.unique(np.sort(np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1),axis=0)
    a,b=edges.T
    e=base[a]-base[b]
    weight=1./np.maximum(np.linalg.norm(e,axis=1),.002)**2
    weight/=np.median(weight)
    L=sparse.coo_matrix((np.r_[weight,weight,-weight,-weight],
        (np.r_[a,b,a,b],np.r_[a,b,b,a])),shape=(n,n)).tocsr()
    fixed=~allowed
    fi=np.flatnonzero(fixed);free=np.flatnonzero(~fixed)
    p=base.copy();p[allowed]=target[allowed]
    p[fixed]=base[fixed]
    local=np.full(n,-1,int);local[free]=np.arange(len(free))
    ids=np.array([j for j,_ in constraints]);directions=np.array([v for _,v in constraints])
    row=np.repeat(np.arange(len(ids)),3);col=(local[ids,None]*3+np.arange(3)).ravel()
    C=sparse.coo_matrix((directions.ravel(),(row,col)),shape=(len(ids),len(free)*3)).tocsr()
    H=sparse.kron(L[free][:,free],sparse.eye(3),format='csc')
    system=sparse.bmat([[H,C.T],[C,None]],format='csc')
    solve=splu(system)
    constraint_rhs=np.einsum('ni,ni->n',directions,target[ids])
    boundary=L[free][:,fi]@p[fi]
    for iteration in range(iterations):
        pe=p[a]-p[b]
        outer=weight[:,None,None]*pe[:,:,None]*e[:,None,:]
        covariance=np.zeros((n,3,3))
        np.add.at(covariance,a,outer);np.add.at(covariance,b,outer)
        u,_,vh=np.linalg.svd(covariance)
        sign=np.linalg.det(u@vh)
        u[:,:,2]*=sign[:,None]
        rotation=u@vh
        rhs_edge=weight[:,None]*np.einsum('nij,nj->ni',(rotation[a]+rotation[b])*.5,e)
        rhs=np.zeros((n,3));np.add.at(rhs,a,rhs_edge);np.add.at(rhs,b,-rhs_edge)
        result=solve.solve(np.r_[(rhs[free]-boundary).ravel(),constraint_rhs])
        p[free]=result[:len(free)*3].reshape(-1,3)
    return p

def repair(d,original,iterations=60):
    delta=np.zeros_like(original);logs=[];handle_masks=[]
    for k in range(7):
        allowed=d['r47_allowed'][k]
        if not allowed.any():
            handle_masks.append(np.zeros(len(allowed),bool));continue
        base=d['key_base'][k]
        matrix=d['key_mat'][k]*d['key_weight'][k,k,:,None,None]
        target=base+np.einsum('nij,nj->ni',matrix,original[k])
        constraints=contour_constraints(target,allowed)
        handles=np.zeros(len(allowed),bool)
        handles[[j for j,_ in constraints]]=True
        p=arap(base,d['faces'],target,allowed,constraints,iterations)
        delta[k,allowed]=np.einsum('nij,nj->ni',np.linalg.pinv(matrix[allowed],rcond=1e-4),p[allowed]-base[allowed])
        handle_masks.append(handles)
        logs.append(dict(key=k,handles=int(handles.sum()),max_material_mm=float(np.linalg.norm(delta[k],axis=1).max()*1000)))
        print(json.dumps(logs[-1]),flush=True)
    return delta,np.array(handle_masks),logs

if __name__=='__main__':
    source,previous,output=sys.argv[1:4]
    with np.load(source) as z:d={k:z[k] for k in z.files}
    old=np.load(previous)['delta']
    delta,handles,logs=repair(d,old,int(sys.argv[4]) if len(sys.argv)>4 else 60)
    np.savez_compressed(output,delta=delta,contour_handles=handles)
    Path(output+'.json').write_text(json.dumps(dict(status='EXPERIMENT_NOT_ACCEPTED',keys=logs),indent=2)+'\n')
