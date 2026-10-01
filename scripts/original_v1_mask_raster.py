#!/usr/bin/env python3
"""Small first-party z-buffer triangle rasterizer for ORIGINAL-v1 QA masks."""
from __future__ import annotations

import math
from pathlib import Path


def _finite_point(point):
    return (
        isinstance(point,(list,tuple)) and len(point)==3
        and all(type(v) in (int,float) and math.isfinite(v) for v in point)
        and point[2]>0
    )


def rasterize(triangles,width,height):
    if type(width) is not int or type(height) is not int or width<=0 or height<=0:
        raise ValueError("positive integer mask dimensions required")
    if not isinstance(triangles,list):
        raise ValueError("triangle list required")
    z=[math.inf]*(width*height)
    visible=[None]*(width*height)
    roles=set()
    for row in triangles:
        if not isinstance(row,dict):raise ValueError("triangle row must be object")
        pts=row.get("points");labels=row.get("roles")
        if not isinstance(pts,list) or len(pts)!=3 or not all(_finite_point(p) for p in pts):
            raise ValueError("triangle points must be finite x/y/depth with positive depth")
        if not isinstance(labels,list) or not labels or any(not isinstance(x,str) or not x for x in labels):
            raise ValueError("triangle roles required")
        labels=tuple(sorted(set(labels)));roles.update(labels)
        (x0,y0,d0),(x1,y1,d1),(x2,y2,d2)=pts
        area=(x1-x0)*(y2-y0)-(y1-y0)*(x2-x0)
        if abs(area)<=1e-12:continue
        xmin=max(0,int(math.floor(min(x0,x1,x2))));xmax=min(width-1,int(math.ceil(max(x0,x1,x2))))
        ymin=max(0,int(math.floor(min(y0,y1,y2))));ymax=min(height-1,int(math.ceil(max(y0,y1,y2))))
        for py in range(ymin,ymax+1):
            sy=py+0.5
            for px in range(xmin,xmax+1):
                sx=px+0.5
                w0=((x1-sx)*(y2-sy)-(y1-sy)*(x2-sx))/area
                w1=((x2-sx)*(y0-sy)-(y2-sy)*(x0-sx))/area
                w2=1.0-w0-w1
                if min(w0,w1,w2)<-1e-9:continue
                inv=w0/d0+w1/d1+w2/d2
                if inv<=0:continue
                depth=1.0/inv
                idx=py*width+px
                if depth<z[idx]-1e-12:
                    z[idx]=depth;visible[idx]=labels
                elif abs(depth-z[idx])<=1e-12 and visible[idx] is not None:
                    visible[idx]=tuple(sorted(set(visible[idx])|set(labels)))
    masks={role:bytearray(width*height) for role in sorted(roles)}
    for idx,labels in enumerate(visible):
        if labels is None:continue
        for role in labels:masks[role][idx]=255
    return {"width":width,"height":height,"masks":masks,"visible_pixel_count":sum(x is not None for x in visible)}


def write_p5(path:Path,width:int,height:int,pixels):
    data=bytes(pixels)
    if len(data)!=width*height:raise ValueError("mask byte length differs from dimensions")
    if path.exists():raise ValueError("mask output collision")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as handle:
        handle.write(f"P5\n{width} {height}\n255\n".encode("ascii"));handle.write(data)


def read_png_dimensions(path:Path):
    data=path.read_bytes()[:24]
    if len(data)<24 or data[:8]!=b"\x89PNG\r\n\x1a\n" or data[12:16]!=b"IHDR":
        raise ValueError("source image must be PNG with IHDR")
    width=int.from_bytes(data[16:20],"big");height=int.from_bytes(data[20:24],"big")
    if width<=0 or height<=0:raise ValueError("invalid PNG dimensions")
    return width,height
