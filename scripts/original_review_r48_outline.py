"""Exact horizontal silhouette and derivative in fixed rear/three-quarter views."""
import numpy as np

def silhouette(points,faces,side,normal,height):
    a=faces[:,[0,1,2]].ravel();b=faces[:,[1,2,0]].ravel()
    za=points[a,2];zb=points[b,2]
    crossing=((za<=height)&(zb>height))|((zb<=height)&(za>height))
    a,b,za,zb=a[crossing],b[crossing],za[crossing],zb[crossing]
    t=(height-za)/(zb-za);p=(1-t[:,None])*points[a]+t[:,None]*points[b]
    sign=-1 if side=='l' else 1
    keep=p[:,0]*sign>.08
    a,b,za,zb,t,p=[v[keep] for v in (a,b,za,zb,t,p)]
    support=p@normal;j=int(np.argmax(support))
    i0,i1=int(a[j]),int(b[j])
    g=normal.copy();g[2]-=((points[i1]-points[i0])@normal)/(zb[j]-za[j])
    return float(support[j]),np.array([i0,i1]),np.array([(1-t[j])*g,t[j]*g])
