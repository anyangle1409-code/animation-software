"""Local R37 skin targets for the two owner marks; no skeleton edits."""
import numpy as np
from original_review_contour import section_profile

def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)

def target(p,faces,ghs,rest,gain=1.):
    offset=np.zeros_like(p)
    for side,gh in ghs.items():
        sign=1 if side=='r' else -1
        d=p-gh;x=d[:,0]*sign;v=d[:,2];y=d[:,1]
        levels,h=section_profile(p,faces,gh,'back',side,np.arange(-.14,.08001,.002))
        if not np.isfinite(h).all():raise ValueError('Incomplete target outline')
        line=np.interp(levels,[-.12,.06],np.interp([-.12,.06],levels,h))
        # Smooth correction to the broad bow, with zero change at both anchors.
        residual=np.interp(v,levels,line-h)
        current=np.interp(v,levels,h)
        envelope=smooth((v+.14)/.025)*smooth((.08-v)/.025)
        outer=smooth((x-current+.065)/.04)
        posterior=smooth((y+.065)/.04)
        dx=np.clip(.85*residual,-.012,.012)*envelope*outer*posterior
        dx*=smooth((x+.015)/.025)
        # Fit a gentle posterior surface through the marked patch. This removes
        # the small surface lobe independently of the rear silhouette.
        selected=(abs(x-.045)<.055)&(abs(v-.03)<.05)&(y>.02)
        q=d[selected]
        if len(q)<30:raise ValueError("Missing marked posterior target patch")
        qx=q[:,0]*sign;qv=q[:,2]
        a=np.column_stack((np.ones(len(q)),qx,qv,qx*qx,qx*qv,qv*qv))
        coeff=np.linalg.lstsq(a,q[:,1],rcond=None)[0]
        all_a=np.column_stack((np.ones(len(p)),x,v,x*x,x*v,v*v))
        fitted=all_a@coeff
        patch=smooth((.085-abs(x-.045))/.035)*smooth((.075-abs(v-.03))/.03)*smooth((y-.005)/.02)
        dy=np.clip(fitted-y,-.006,.006)*patch*.9
        keep=p[:,0]*sign>0
        offset[keep,0]+=sign*dx[keep];offset[keep,1]+=dy[keep]
    mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
    # Broad spatial fade keeps the protected front sentinel and its immediate
    # neighbors fixed without creating a small hard-edged protected island.
    distance=np.minimum(np.linalg.norm(p-p[18633],axis=1),np.linalg.norm(p-p[mirror],axis=1))
    offset*=smooth((distance-.025)/.04)[:,None]*gain
    return offset
