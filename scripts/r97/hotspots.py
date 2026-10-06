import sys; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
from hgpt_pose import *
P=Poser(); P.set_correctives(0)
for m in P.body.modifiers:
    if m.type=='MASK': m.show_viewport=False; m.show_render=False
me=P.body.data; edges=np.array([e.vertices[:] for e in me.edges]); rest=P.evaluated()
rl=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
names=[g.name for g in P.body.vertex_groups]
def wrow(i): return {names[g.group]:round(g.weight,2) for g in me.vertices[i].groups if g.weight>0.01}
for spec in argv[1:]:
    plane,th,ax,el,hz=spec.split(':'); 
    try: plane=float(plane)
    except: pass
    P.reset()
    for s in 'lr': P.elevate(s,plane,float(th),axial=float(ax),elbow=float(el),horizontal=float(hz))
    X=P.evaluated(); r=np.linalg.norm(X[edges[:,0]]-X[edges[:,1]],axis=1)/rl
    L=rest[edges[:,0],0]<0
    top=np.argsort(-(r*L))[:5]
    print('==',spec)
    for k in top:
        a,b=edges[k]; print(f'  ratio {r[k]:.1f} rest {rest[a].round(3)} w_a {wrow(a)} w_b {wrow(b)}')
