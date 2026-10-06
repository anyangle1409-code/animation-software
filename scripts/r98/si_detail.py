import sys; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
from hgpt_pose import *
from mathutils.bvhtree import BVHTree
P=Poser(); P.set_correctives(0)
for m in P.body.modifiers:
    if m.type=='MASK': m.show_viewport=False
me=P.body.data; rest=P.evaluated(); me.calc_loop_triangles(); T=np.array([t.vertices[:] for t in me.loop_triangles])
faces=T[(rest[T][:,:,2]>1.25).any(1) & (rest[T][:,:,0]<-0.05).all(1)]
P.reset()
for s in 'lr': P.elevate(s,argv[1],float(argv[2]),axial=float(argv[3]))
X=P.evaluated()
tree=BVHTree.FromPolygons([tuple(p) for p in X],[tuple(f) for f in faces],all_triangles=True)
pr=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(faces[a])&set(faces[b])]
C=np.array([[rest[faces[a]].mean(0),rest[faces[b]].mean(0)] for a,b in pr])
print(len(pr))
from collections import Counter
cl=Counter((tuple(np.round(c[0],2)),tuple(np.round(c[1],2))) for c in C[:,:, :])
for k,v in cl.most_common(12): print(v,k)
