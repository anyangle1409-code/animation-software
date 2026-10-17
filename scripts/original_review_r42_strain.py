"""R41 bounded strain goals. Canonical geometry and all older tests stay intact."""
import numpy as np

def eligible_vertices(rest):
 return (abs(rest[:,0])>.08)&(abs(rest[:,0])<.35)&(rest[:,2]>1.27)&(rest[:,2]<1.51)

def strain_metrics(data,delta):
 faces=data['faces'];p=data['rest'];tri=p[faces];a0=.5*np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
 stretch=[];collapse=[];severity=[]
 for s,base in enumerate(data['base']):
  p=base+np.einsum('nij,nj->ni',data['mat'][s],np.einsum('kn,knj->nj',data['weight'][s],delta))
  tri=p[faces];ar=.5*np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1);ratio=ar/np.maximum(a0,1e-20)
  stretch.append(int((ratio>2).sum()));collapse.append(int(((ratio<.1)&(a0>1e-12)).sum()));severity.append(float(ratio.max()))
 return dict(marked_stretch=stretch[25],top_stretch=stretch[40],benchmark_max_collapse=max(collapse[41:82]),
             max_material_delta_mm=float(np.linalg.norm(delta,axis=2).max()*1000),stretch=stretch,collapse=collapse,max_area_ratio=severity)

def goals(metrics):
 return (metrics['marked_stretch']<=40 and metrics['top_stretch']<=70 and metrics['benchmark_max_collapse']==0
         and metrics['max_material_delta_mm']<=45.)

def area_log_penalty(areas,reference,under_weight=20.):
    safe=np.maximum(areas,1e-20);ref=np.maximum(reference,1e-20)
    over=np.maximum(np.log(safe/(1.85*ref)),0);under=np.maximum(np.log(.2*ref/safe),0)
    valid=np.asarray(reference)>1e-12
    value=float(((over*over+under_weight*under*under)*valid).sum())
    return value,2*(over-under_weight*under)/safe*valid


def area_safety(points,parent,rest,faces):
 """Saved/native sample must retain count and maximum area severity gates."""
 def areas(p):
  t=np.asarray(p)[faces]
  return .5*np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
 a0=areas(rest);before=areas(parent);after=areas(points)
 def metrics(a):
  return dict(stretch=int((a>2*a0).sum()),collapse=int(((a<.1*a0)&(a0>1e-12)).sum()),max_area_ratio=float((a/np.maximum(a0,1e-20)).max()))
 b=metrics(before);a=metrics(after)
 return dict(current=a,parent=b,passed=bool(a['stretch']<=b['stretch'] and a['collapse']<=b['collapse'] and a['max_area_ratio']<=b['max_area_ratio']*1.01))

