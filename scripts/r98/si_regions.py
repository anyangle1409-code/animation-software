"""Classify protected-zone self-intersections by rest region across the matrix poses. usage: -- blend out.json"""
import sys, json; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
from hgpt_pose import *
from mathutils.bvhtree import BVHTree
P=Poser(); P.set_correctives(0)
for m in P.body.modifiers:
    if m.type=='MASK': m.show_viewport=False
me=P.body.data; rest=P.evaluated(); me.calc_loop_triangles(); T=np.array([t.vertices[:] for t in me.loop_triangles])
n=len(rest); names=[g.name for g in P.body.vertex_groups]; Wm=np.zeros((n,len(names)))
for v in me.vertices:
    for g in v.groups: Wm[v.index,g.group]=g.weight
gi={k:i for i,k in enumerate(names)}
def zone(s):
    g=sum(Wm[:,gi[b]] for b in (f"clavicle_{s}",f"scapula_{s}",f"upperarm_{s}"))
    side=rest[:,0]<0 if s=='l' else rest[:,0]>0
    return side&(g>0.02)&(rest[:,2]>1.25)
Z=zone('l')|zone('r'); faces=T[Z[T].any(1)]
def region(c):
    x,y,z=abs(c[0]),c[1],c[2]
    if z>1.47 and x<0.2: return 'superior_shoulder_trapezius'
    if x>0.2 and z>1.42: return 'deltoid_cap'
    if y<0: return 'anterior_axilla_pec'
    return 'posterior_axilla_back'
poses={}
for plane in ('abduction','flexion'):
    for th in (0,30,60,90,120,150,170):
        for an,av in {'internal':-40.0,'neutral':0.0,'external':40.0}.items():
            poses[f'{plane}_{th:03d}_{an}']=(plane,th,av if th<=120 else av*0.6,0,0)
extra={'horizontal_adduction_90':('flexion',90,0,20,35),'horizontal_abduction_90':('abduction',90,0,20,-25),'arm_behind_torso':(-90,40,-40,70,0),
 'bent_elbow_elevation_120':('scaption',120,30,100,0),'press_bottom_like':(20,85,60,95,0),'press_top_like':(15,165,25,15,0),'pullup_hang_like':(25,170,20,5,0),
 'pullup_top_like':(10,60,10,130,0),'bench_bottom_like':(5,80,55,90,-30),'pushup_bottom_like':(30,55,20,95,-20),'row_top_like':(-80,45,0,100,0)}
poses.update(extra)
tot={}; per={}
for k,(pl,th,ax,el,hz) in poses.items():
    P.reset()
    for s in 'lr': P.elevate(s,pl,th,axial=ax,elbow=el,horizontal=hz)
    X=P.evaluated()
    tree=BVHTree.FromPolygons([tuple(p) for p in X],[tuple(f) for f in faces],all_triangles=True)
    c={}
    for a,b in tree.overlap(tree):
        if a<b and not set(faces[a])&set(faces[b]):
            r=region(rest[faces[a]].mean(0)); c[r]=c.get(r,0)+1
    per[k]=c
    for r,v in c.items(): tot[r]=tot.get(r,0)+v
json.dump({'total':tot,'per_pose':per},open(argv[1],'w'),indent=1); print(json.dumps(tot))
