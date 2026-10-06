"""Find closed quad edge rings crossing the left axillary apex; report extent. usage: -- blend"""
import sys, bpy, bmesh, numpy as np
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
bm=bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
co=np.array([v.co[:] for v in bm.verts])
def ring(e0):
    """walk across quads via opposite edges in both directions; return list of edges and closed flag"""
    out=[e0]; closed=False
    for start_face in list(e0.link_faces)[:2]:
        e=e0; f=start_face; seq=[]
        while True:
            if len(f.verts)!=4: break
            loops=[l for l in f.loops if l.edge==e][0]
            opp=loops.link_loop_next.link_loop_next.edge
            if opp==e0: closed=True; break
            seq.append(opp)
            nf=[x for x in opp.link_faces if x!=f]
            if not nf or len(seq)>400: break
            e,f=opp,nf[0]
        if closed: out+=seq; break
        out=list(reversed(seq))+out if start_face==list(e0.link_faces)[0] else out+seq
    return out,closed
# apex: torso-wall/arm-wall top of slit; pick verts near target points
for tgt in [(-0.165,0.02,1.41),(-0.165,-0.03,1.40),(-0.165,0.06,1.41),(-0.16,0.0,1.38),(-0.17,0.0,1.43)]:
    vi=int(np.argmin(np.linalg.norm(co-np.array(tgt),axis=1))); v=bm.verts[vi]
    for e in v.link_edges:
        d=np.array(e.other_vert(v).co)-np.array(v.co); d/=np.linalg.norm(d)
        if abs(d[1])>0.7: continue   # skip edges running along the crease (front-back)
        r,closed=ring(e)
        mids=np.array([(np.array(x.verts[0].co)+np.array(x.verts[1].co))/2 for x in r])
        print(f"seed v{vi} {np.round(co[vi],3)} edge dir {np.round(d,2)} ring len {len(r)} closed {closed} x[{mids[:,0].min():.3f},{mids[:,0].max():.3f}] y[{mids[:,1].min():.3f},{mids[:,1].max():.3f}] z[{mids[:,2].min():.3f},{mids[:,2].max():.3f}]")
