"""Review-only plantar-envelope experiment; no skeletal or length change."""
import math


def expand_plantar(z, bottom, anchor=.022, blend=1):
    """Lower only the existing plantar envelope, preserving the dorsal anchor.

    The 22 mm anchor is an artist trial constraint, not an anatomical target.
    The caller must derive bottom from the actual source surface and check
    containment, topology, contact and motion independently.
    """
    if any(type(v) not in (float,int) or not math.isfinite(v)
           for v in (z,bottom,anchor,blend)):
        raise ValueError('Finite numeric envelope required')
    if anchor<=0 or bottom>=anchor or not 0<=blend<=1:
        raise ValueError('Invalid envelope or blend')
    if bottom<=0 or z>=anchor or blend==0:
        return z
    expanded=(z-bottom)*anchor/(anchor-bottom)
    return z+blend*(expanded-z)
