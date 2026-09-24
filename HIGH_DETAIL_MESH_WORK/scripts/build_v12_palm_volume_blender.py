"""Candidate-only, seam-aware palm-volume refinement of the V11 hand mesh."""
from __future__ import annotations
import bpy,bmesh,json,math,struct
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v11_hand_cleanup.blend'
OUT=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v12c_palm_volume.blend'
REPORT=ROOT/'reports/build_v12c_palm_volume_blender.json'
assert SRC.is_file() and not OUT.exists(), 'Source missing or output already exists'

# The protected contacts are identified using the V8 GLB vertex IDs, exactly as
# in the V11 builder. No original contact vertex can move.
glb=(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb').read_bytes()
n=struct.unpack_from('<I',glb,12)[0];doc=json.loads(glb[20:20+n]);base=28+n
a=doc['accessors'][doc['meshes'][0]['primitives'][0]['indices']]
v=doc['bufferViews'][a['bufferView']]
import numpy as np
dt=np.dtype({5125:'<u4',5123:'<u2'}[a['componentType']])
indices=np.ndarray(a['count'],dtype=dt,buffer=glb,offset=base+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,3)
protected_glb=set(json.loads((ROOT/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids'])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend'))
v8mesh=bpy.data.objects['Mike_Freeman'].data
glb_ids=[set() for _ in v8mesh.vertices]
for i,p in enumerate(v8mesh.polygons):
    for c,li in enumerate(p.loop_indices):glb_ids[v8mesh.loops[li].vertex_index].add(int(indices[i,c]))
protected_v8={i for i,ids in enumerate(glb_ids) if ids&protected_glb}
v8co=[v.co.copy() for v in v8mesh.vertices]

bpy.ops.wm.open_mainfile(filepath=str(SRC))
body=bpy.data.objects['Mike_Freeman'];mesh=body.data
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bm.normal_update()
idlay=bm.verts.layers.int['v8_source_id'];dlay=bm.verts.layers.deform.active
groups={g.index:g.name for g in body.vertex_groups}
hand_groups={i for i,n in groups.items() if any(s in n for s in ('DEF-hand.','DEF-palm.','DEF-thumb.','DEF-f_'))}
def influence(x):return sum(w for g,w in x[dlay].items() if g in hand_groups)
def sid(x):return x[idlay]-1
def protected(x):return sid(x) in protected_v8 if sid(x)>=0 else False
def in_hand(x):return abs(x.co.x)>=.62 and 1.06<x.co.z<1.33 and influence(x)>0
def fade(x,a,b):
    t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def gauss(x,mu,sigma):return math.exp(-.5*((x-mu)/sigma)**2)
start={x:x.co.copy() for x in bm.verts}

# Hold every open skin-patch edge and the protected floor contacts fixed. Fade
# over four graph rings into the interior so the sculpt cannot pull a patch
# away from its neighbour or create the V10 thumb-web wedge.
fixed={x for x in bm.verts if x.is_boundary or protected(x) or not in_hand(x)}
ring={x:0 for x in fixed};front=fixed
for depth in range(1,9):
    nxt={e.other_vert(x) for x in front for e in x.link_edges if e.other_vert(x) not in ring}
    for x in nxt:ring[x]=depth
    front=nxt
weights={0:0.,1:.02,2:.08,3:.18,4:.32,5:.5,6:.7,7:.88,8:1.}
updates={}
for x in bm.verts:
    if x in fixed:continue
    side=abs(x.co.x);y=x.co.y;z=x.co.z
    if not (.685<side<.825 and -.21<y<-.035 and 1.155<z<1.245):continue
    thenar=gauss(side,.749,.034)*gauss(y,-.145,.040)*gauss(z,1.195,.038)
    hypothenar=gauss(side,.745,.029)*gauss(y,-.070,.030)*gauss(z,1.188,.041)
    arch=gauss(side,.768,.043)*gauss(y,-.115,.058)*gauss(z,1.177,.043)
    wrist=gauss(side,.702,.023)*gauss(y,-.112,.052)*gauss(z,1.194,.054)
    # Roughly half the original V10 volume. The V11 surface is the source,
    # so this changes no topology, UV, material, skin influence or rig data.
    amplitude=(.00125*thenar+.0009*hypothenar+.00055*arch+.00025*wrist)
    strength=(weights.get(ring.get(x,9),1.)*min(1.,influence(x))*fade(side,.685,.705)
              *fade(z,1.155,1.17)*(1.-fade(z,1.225,1.245))
              *fade(y,-.21,-.18)*(1.-fade(y,-.06,-.035)))
    shift=x.normal*(amplitude*strength)
    if shift.length>1e-7:updates[x]=x.co+shift
for x,p in updates.items():x.co=p

# Numeric symmetry is a geometry guarantee, with V11 vertex pairing recovered
# from the unchanged source positions.
right=[x for x in bm.verts if x.co.x<-.62 and x not in fixed]
left=[x for x in bm.verts if x.co.x>.62 and x not in fixed]
tree=KDTree(len(right))
for i,x in enumerate(right):p=start[x];tree.insert(Vector((-p.x,p.y,p.z)),i)
tree.balance();pairs=0
for x in left:
    _,idx,d=tree.find(start[x])
    if d>.00025:continue
    other=right[idx];avg=(x.co+Vector((-other.co.x,other.co.y,other.co.z)))*.5
    x.co=avg;other.co=Vector((-avg.x,avg.y,avg.z));pairs+=1

protected_max=max((x.co-start[x]).length for x in bm.verts if protected(x))
boundary_max=max((x.co-start[x]).length for x in bm.verts if x.is_boundary)
outside_max=max((x.co-start[x]).length for x in bm.verts if not in_hand(x))
max_move=max((x.co-start[x]).length for x in bm.verts)
max_original_v8=max((x.co-v8co[sid(x)]).length for x in bm.verts if sid(x)>=0 and in_hand(x))
assert protected_max<1e-9 and boundary_max<1e-9 and outside_max<1e-9
assert max_original_v8<.0045, max_original_v8
bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update()
body['v12_palm_note']='V11 hand topology and seam cleanup preserved; interior palm volume only; no rig or grip edits.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
report={'source':SRC.name,'candidate':OUT.name,'vertices':len(mesh.vertices),'faces':len(mesh.polygons),
        'moved_vertices':len(updates),'symmetric_pairs':pairs,'protected_max_move_mm':protected_max*1000,
        'boundary_max_move_mm':boundary_max*1000,'outside_hand_max_move_mm':outside_max*1000,
        'max_move_v11_mm':max_move*1000,'max_original_hand_move_v8_mm':max_original_v8*1000}
REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2))
print('V12_PALM_BUILD',json.dumps(report),flush=True)
