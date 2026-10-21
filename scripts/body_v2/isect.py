import sys, numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SP="/tmp/claude-0/-home-user-animation-software/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/scratchpad"
co=np.load(SP+"/r76/rest_co.npy"); F=np.load(SP+"/r76/faces.npy")
fs=[set(f) for f in F]
for p in sys.argv[1:]:
    P=co+np.load(p)["offsets"]
    t=BVHTree.FromPolygons([Vector(v) for v in P],[tuple(f) for f in F],all_triangles=True)
    pr=[(a,b) for a,b in t.overlap(t) if a<b and not(fs[a]&fs[b])]
    ca=np.array([P[F[a]].mean(0) for a,b in pr]); cb=np.array([P[F[b]].mean(0) for a,b in pr])
    print(p.split('/')[-2], len(pr))
    if len(pr):
        mid=(ca+cb)/2
        # cluster by rounding
        keys={}
        for m in mid:
            k=(round(abs(m[0]),2)//0.04*0.04, round(m[1],2)//0.04*0.04, round(m[2],2)//0.05*0.05); keys[k]=keys.get(k,0)+1
        for k,v in sorted(keys.items(), key=lambda kv:-kv[1])[:10]: print("   |x|~%.2f y~%.2f z~%.2f : %d"%(k[0],k[1],k[2],v))
