import sys; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np, json
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
from hgpt_pose import *
from mathutils.bvhtree import BVHTree
P=Poser(); P.set_correctives(0)
for m in P.body.modifiers:
    if m.type=='MASK': m.show_viewport=False
me=P.body.data; E=np.array([e.vertices[:] for e in me.edges]); rest=P.evaluated()
rl=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1)
me.calc_loop_triangles(); T=np.array([t.vertices[:] for t in me.loop_triangles])
L=rest[:,0]<0
zone=L&(rest[:,2]>1.2)&(rest[:,2]<1.6)&(rest[:,0]<-0.08)
ez=zone[E].all(1)
print('median edge len zone', np.median(rl[ez]))
for spec in ['flexion:170','abduction:150','abduction:170','flexion:060:40']:
    parts=spec.split(':'); P.reset()
    for s in 'lr': P.elevate(s,parts[0],float(parts[1]),axial=float(parts[2]) if len(parts)>2 else 0)
    X=P.evaluated(); r=np.linalg.norm(X[E[:,0]]-X[E[:,1]],axis=1)/rl
    m=ez&(r>2.5)
    print('==',spec,'edges>2.5:',int(m.sum()),'their rest len median',np.median(rl[m]) if m.any() else 0, 'centroid', rest[E[m]].mean((0,1)).round(3) if m.any() else None)
    # bin by region: anterior (y<0) vs posterior
    mid=rest[E[:,0]]
    print('   anterior',int((m&(mid[:,1]<0)).sum()),'posterior',int((m&(mid[:,1]>=0)).sum()))
    # self intersections in zone
    tz=np.nonzero(zone[T].all(1))[0]; faces=T[tz]
    tree=BVHTree.FromPolygons([tuple(p) for p in X],[tuple(f) for f in faces],all_triangles=True)
    pr=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(faces[a])&set(faces[b])]
    if pr:
        c=np.array([rest[faces[a]].mean(0) for a,b in pr]+[rest[faces[b]].mean(0) for a,b in pr])
        print('   SI pairs',len(pr),'rest centroid',c.mean(0).round(3),'y<0 frac',round(float((c[:,1]<0).mean()),2),'z range',c[:,2].min().round(3),c[:,2].max().round(3))
