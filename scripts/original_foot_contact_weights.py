"""Reversible shared-toe-control weight candidate; no anatomical shape claim."""
import math

def redistribute(weights,toe_name,foot_name,forward_m,pivot_forward_m,blend_m):
    if not isinstance(weights,dict) or not weights or toe_name==foot_name:
        raise ValueError('Distinct controls and nonempty weight mapping required')
    if any(type(v) not in (float,int) or not math.isfinite(v) or v<0 for v in weights.values()):
        raise ValueError('Finite nonnegative weights required')
    if any(type(v) not in (float,int) or not math.isfinite(v) for v in (forward_m,pivot_forward_m,blend_m)) or blend_m<=0:
        raise ValueError('Finite coordinates and positive blend width required')
    result=dict(weights)
    w=weights.get(toe_name,0)
    if w==0:return result
    u=min(1,max(0,(forward_m-pivot_forward_m)/blend_m))
    retained=u*u*(3-2*u)
    transferred=w*(1-retained)
    result[toe_name]=w*retained
    result[foot_name]=result.get(foot_name,0)+transferred
    if not math.isfinite(result[foot_name]):raise ValueError('Weight overflow')
    return result
