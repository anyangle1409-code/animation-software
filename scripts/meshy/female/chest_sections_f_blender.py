"""FEMALE chest sections (read-only): segments of body, bra and her source cut by the planes z = 1.20 (horizontal,
through the bust), x = 0 (sagittal, sternum) and x = 0.085 (sagittal, through a breast), rest pose. Drawn by
chest_sections_draw.py. usage: python3.13 chest_sections_f_blender.py -- <candidate .blend> <out .json>
"""
import bpy,sys,json,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2],load_ui=False)
rig=bpy.data.objects['HGPT_FEMALE_RIG']; rig.data.pose_position='REST'; bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get()
def segs(n,axis,val,lim):
    o=bpy.data.objects[n]; m=o.evaluated_get(dg).to_mesh(); V=np.array([v.co[:] for v in m.vertices]); out=[]
    for p in m.polygons:
        vs=list(p.vertices); a=V[vs,axis]
        if a.min()>val or a.max()<val: continue
        c=V[vs].mean(0)
        if not lim(c): continue
        pts=[]
        for k in range(len(vs)):
            A,B=V[vs[k]],V[vs[(k+1)%len(vs)]]
            if (A[axis]-val)*(B[axis]-val)<0: t=(val-A[axis])/(B[axis]-A[axis]); pts.append((A+(B-A)*t).tolist())
        if len(pts)==2: out.append(pts)
    return out
res={}
names=['HGPT_Female_Body','HGPT_Female_Bra','HGPT_FEMALE_SOURCE_Mesh_0']
res['h']={n:segs(n,2,1.20,lambda c:c[1]<0.02 and abs(c[0])<0.2) for n in names}
res['s0']={n:segs(n,0,0.0,lambda c:c[1]<0.02 and 1.0<c[2]<1.4) for n in names}
res['s8']={n:segs(n,0,0.085,lambda c:c[1]<0.02 and 1.0<c[2]<1.4) for n in names}
json.dump(res,open(sys.argv[-1],'w'))
