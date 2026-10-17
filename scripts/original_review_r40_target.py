"""Continue the owner-approved upper-arm line into the torso, S7 only."""
import numpy as np
from original_review_r40_line import frame,profile,guide

def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)

def target(p,faces,bones,rest,gain=1.):
    offset=np.zeros_like(p)
    for side,(gh,elbow) in bones.items():
        axis,normal=frame(gh,elbow,side);d=p-gh;s=d@axis;r=d@normal
        levels=np.arange(-.24,.20001,.002)
        outline=profile(p,faces,gh,elbow,side,levels)
        fit=guide(p,faces,gh,elbow,side)
        local=np.interp(s,levels,outline)
        desired=np.polyval(fit,s)
        gap=np.maximum(desired-local,0)
        outer=smooth((r-local+.065)/.05)
        longitudinal=smooth((s+.24)/.06)*smooth((.085-s)/.025)
        rear=smooth((d[:,1]+.065)/.04)
        same=p[:,0]*(1 if side=='r' else -1)>0
        amount=np.minimum(gap,.035)*outer*longitudinal*rear*same
        offset+=amount[:,None]*normal
    mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
    distance=np.minimum(np.linalg.norm(p-p[18633],axis=1),np.linalg.norm(p-p[mirror],axis=1))
    offset*=smooth((distance-.008)/.018)[:,None]*gain
    return offset
