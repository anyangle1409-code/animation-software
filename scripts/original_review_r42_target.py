"""Owner-confirmed body-side restoration; upper arm and elbow remain fixed."""
import numpy as np
from scipy.interpolate import PchipInterpolator
from original_review_r42_line import frame, profile, guide
STATIONS=np.array([-.40,-.36,-.32,-.28,-.24,-.20,-.16,-.14,-.12,-.10,-.08,-.06,-.04,-.02,0.])
EXCESS_MM=np.array([0,0,22,33,39,38,35,32,28,20,12,6,2,0,0])
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def target(p,faces,bones,rest,gain=.85):
 change=np.zeros_like(p);constraint=np.zeros(len(p),bool)
 curve=PchipInterpolator(STATIONS,EXCESS_MM/1000)
 region=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.35)&(rest[:,2]>1.20)&(rest[:,2]<1.51)
 for side,(gh,el) in bones.items():
  axis,normal=frame(gh,el,side);d=p-gh;s=d@axis;r=d@normal
  levels=np.arange(-.30,.18001,.002);outline=profile(p,faces,gh,el,side,levels)
  local=np.interp(s,levels,outline);line=guide(p,faces,gh,el,side)
  desired=np.polyval(line,s)+curve(np.clip(s,STATIONS[0],STATIONS[-1]))
  gap=np.maximum(desired-local,0);outer=smooth((r-local+.065)/.05);rear=smooth((d[:,1]+.055)/.055)
  longitudinal=smooth((s+.40)/.05)*smooth(-s/.025);same=p[:,0]*(1 if side=='r' else -1)>0
  amount=gap*outer*rear*longitudinal*same*region*gain;amount[(s>=0)|(s<=-.40)]=0
  change+=amount[:,None]*normal
  # Lock only the visible three-millimetre contour band. Locking a nineteen-
  # millimetre band in trial 1 prevented redistribution and increased stretch.
  constraint|=same&region&(r>local-.003)&(rear>.98)&(s>-.32)&(s<-.035)&(amount>.001)
 mirror=int(np.argmin(np.linalg.norm(rest-rest[18633]*[-1,1,1],axis=1)))
 distance=np.minimum(np.linalg.norm(p-p[18633],axis=1),np.linalg.norm(p-p[mirror],axis=1));fade=smooth((distance-.008)/.018)
 change*=fade[:,None];constraint&=fade>.999
 change[[18633,mirror]]=0;constraint[[18633,mirror]]=False
 return change,constraint
