"""Measure the owner-approved line in the unchanged native rear camera."""
import numpy as np

def frame(gh,elbow,side):
    view=np.array([0.,1.,.02]);view/=np.linalg.norm(view)
    axis=elbow-gh;axis=axis-view*(axis@view);axis/=np.linalg.norm(axis)
    normal=np.cross(axis,view);normal/=np.linalg.norm(normal)
    if normal[0]*(1 if side=='r' else -1)<0:normal=-normal
    return axis,normal

def profile(points,faces,gh,elbow,side,levels):
    axis,normal=frame(gh,elbow,side)
    a=faces[:,[0,1,2]].ravel();b=faces[:,[1,2,0]].ravel()
    aa=(points[a]-gh)@axis;bb=(points[b]-gh)@axis
    out=[]
    for s in levels:
        choose=((aa<=s)&(bb>s))|((bb<=s)&(aa>s))
        pp=points[a[choose]]+((s-aa[choose])/(bb[choose]-aa[choose]))[:,None]*(points[b[choose]]-points[a[choose]])
        keep=(np.linalg.norm(pp-gh,axis=1)<.36)&(pp[:,0]*(1 if side=='r' else -1)>0)
        out.append(float(((pp[keep]-gh)@normal).max()) if keep.any() else float('nan'))
    out=np.array(out)
    if not np.isfinite(out).all():raise ValueError('Incomplete approved-line profile')
    return out

def guide(points,faces,gh,elbow,side):
    levels=np.arange(.06,.16001,.02)
    return np.polyfit(levels,profile(points,faces,gh,elbow,side,levels),1)

def errors(current,parent,side):
    ht='135.625';gh=parent[f'gh_{side}_{ht}'];el=parent[f'elbow_{side}_{ht}'];faces=parent['faces']
    fit=guide(parent['all_'+ht],faces,gh,el,side)
    arm=np.arange(0,.16001,.005);join=np.arange(-.14,.00001,.005)
    a=profile(current['all_'+ht],faces,gh,el,side,arm)
    j=profile(current['all_'+ht],faces,gh,el,side,join)
    return float(abs(a-np.polyval(fit,arm)).max()*1000),float(np.maximum(np.polyval(fit,join)-j,0).max()*1000)
