"""Exact projected clearance of two planes over a caller-supplied XY ellipse.

This is a planar geometric invariant, not a disc-height measurement protocol
or a validator of curved anatomical endplates. +Z is superior. Both normals
are represented superior-facing, irrespective of the bone's outward normal.
Caller must establish that the footprint lies within BOTH endplate domains.
"""
import math
from numbers import Real

def _vector(value,n):
 try:v=list(value)
 except TypeError:raise ValueError('finite vector required')
 if len(v)!=n or not all(isinstance(x,Real) and not isinstance(x,bool) and math.isfinite(x) for x in v):raise ValueError('finite numeric vector required')
 return v

def _plane(origin,normal,xy):
 o=_vector(origin,3);n=_vector(normal,3)
 length=math.hypot(*n)
 if not math.isfinite(length) or length==0 or n[2]/length<=1e-8:raise ValueError('superior-facing, nonvertical plane required')
 slopes=[-n[0]/n[2],-n[1]/n[2]]
 z=o[2]+sum(s*(x-c) for s,x,c in zip(slopes,xy,o))
 return z,slopes

def clearance(upper_origin_mm,upper_normal,lower_origin_mm,lower_normal,footprint_centre_xy_mm,footprint_radii_xy_mm):
 xy=_vector(footprint_centre_xy_mm,2);r=_vector(footprint_radii_xy_mm,2)
 if min(r)<=0:raise ValueError('positive footprint radii required')
 uz,us=_plane(upper_origin_mm,upper_normal,xy);lz,ls=_plane(lower_origin_mm,lower_normal,xy)
 g=[a-b for a,b in zip(us,ls)];d=uz-lz
 amplitude=math.hypot(g[0]*r[0],g[1]*r[1])
 witness=xy if amplitude==0 else [xy[i]-g[i]*r[i]**2/amplitude for i in range(2)]
 minimum=d-amplitude;maximum=d+amplitude
 if not all(math.isfinite(x) for x in [d,minimum,maximum,*witness]):raise ValueError('nonfinite clearance result')
 return {'centre_projected_gap_mm':d,'minimum_projected_gap_mm':minimum,'maximum_projected_gap_mm':maximum,'minimum_witness_xy_mm':witness,'separated_everywhere':minimum>0,'measurement':'HGPT +Z projected clearance, not shortest Euclidean or endplate-normal distance','scope':'planar surfaces over supplied common elliptical footprint only'}
