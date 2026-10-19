"""Read-only audit helpers. Diagnostic ablations are never repaired candidates."""
import numpy as np
MODES=('r41','r41_no_s5','r41_no_s7','r41_no_s5_s7','r52')

def muted_names(mode,names):
 if mode not in MODES:raise ValueError('Unknown diagnostic mode')
 prefixes={'r41_no_s5':('HGPT_S5_BAKE_',),'r41_no_s7':('HGPT_S7_DELT_',),'r41_no_s5_s7':('HGPT_S5_BAKE_','HGPT_S7_DELT_')}.get(mode,())
 return [n for n in names if n.startswith(prefixes)]

def pose_difference_mm(a,b):
 a,b=np.asarray(a),np.asarray(b)
 if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('Invalid pose comparison')
 return float(np.linalg.norm(a-b,axis=-1).max()*1000)

def temporal_metrics(a,b):
 a,b=np.asarray(a),np.asarray(b)
 if a.shape!=b.shape or a.ndim!=3 or len(a)!=161 or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('Expected matching finite161-pose arrays')
 def excess(x,y):return float((np.linalg.norm(np.diff(y,n=2,axis=0),axis=2)-np.linalg.norm(np.diff(x,n=2,axis=0),axis=2)).max()*1000)
 dense=excess(a,b)
 return dict(coarse41_excess_mm=excess(a[::4],b[::4]),dense161_excess_mm=dense,normalized_dense_excess_mm=dense*16,diagnostic_only=True,model_saved=False)
