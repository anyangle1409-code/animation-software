"""Candidate-only distal finger shape refinement from the V12c checkpoint."""
from __future__ import annotations
import bpy,bmesh,json,math,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
VERSION='v13e_fingertip_retopology'
SRC=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v12c_palm_volume.blend'
OUT=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend'
REPORT=ROOT/f'reports/build_{VERSION}_blender.json'
assert SRC.is_file() and not OUT.exists()
g=(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb').read_bytes()
n=struct.unpack_from('<I',g,12)[0];doc=json.loads(g[20:20+n]);base=28+n
a=doc['accessors'][doc['meshes'][0]['primitives'][0]['indices']];view=doc['bufferViews'][a['bufferView']]
indices=np.ndarray(a['count'],dtype=np.dtype({5125:'<u4',5123:'<u2'}[a['componentType']]),buffer=g,offset=base+view.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,3)
protected_glb=set(json.loads((ROOT/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids'])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend'))
v8=bpy.data.objects['Mike_Freeman'].data;mapping=[set() for _ in v8.vertices]
for i,p in enumerate(v8.polygons):
    for j,li in enumerate(p.loop_indices):mapping[v8.loops[li].vertex_index].add(int(indices[i,j]))
protected_ids={i for i,ids in enumerate(mapping) if ids&protected_glb}
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body=bpy.data.objects['Mike_Freeman'];mesh=body.data
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bm.normal_update()
idlay=bm.verts.layers.int['v8_source_id'];dlay=bm.verts.layers.deform.active
groups={x.index:x.name for x in body.vertex_groups}
def source_id(v):return v[idlay]-1
def protected(v):return source_id(v) in protected_ids if source_id(v)>=0 else False
def influence(v,select):return sum(w for gid,w in v[dlay].items() if gid in select)
def fade(x,a,b):
    t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3.-2.*t)
def closest_chain(p,chain):
    best=None;length=0.
    for a,b in zip(chain[:-1],chain[1:]):
        ab=b-a;seg=ab.length;t=max(0.,min(1.,(p-a).dot(ab)/(seg*seg)))
        q=a+t*ab;item=((p-q).length,q,length+t*seg)
        if best is None or item[0]<best[0]:best=item
        length+=seg
    return best

# Add true local fingertip loops before sculpting. No edge incident to a
# protected floor vertex or an unwelded patch boundary is split.
bones=bpy.data.objects['HomeGymPT_Male_Rig'].data.bones
distal_edges=set()
for side in ('L','R'):
    for digit in ('index','middle','ring','pinky'):
        prefix='DEF-f_'+digit+'.'
        chain_bones=[bones[prefix+f'{i:02d}.'+side] for i in (1,2,3)]
        chain=[chain_bones[0].head_local.copy()]+[b.tail_local.copy() for b in chain_bones]
        select={gid for gid,name in groups.items() if prefix in name and name.endswith('.'+side)}
        owned=[v for v in bm.verts if (v.co.x>0)==(side=='L') and influence(v,select)>.5]
        endpoint=max(closest_chain(v.co,chain)[2] for v in owned)
        for e in bm.edges:
            if e.is_boundary or any(protected(v) or v.is_boundary for v in e.verts):continue
            if (e.verts[0].co-e.verts[1].co).length<.0018:continue
            if all(influence(v,select)>.5 and closest_chain(v.co,chain)[2]>endpoint-.012 for v in e.verts):
                distal_edges.add(e)
before_vertices=len(bm.verts);before_faces=len(bm.faces)
if distal_edges:
    bmesh.ops.subdivide_edges(bm,edges=list(distal_edges),cuts=1,use_grid_fill=True)
    bm.verts.ensure_lookup_table();bm.normal_update()
    for v in bm.verts[before_vertices:]:v[idlay]=0
new_vertices=len(bm.verts)-before_vertices

# Pin every original floor-contact vertex, every unwelded patch boundary,
# every non-digit vertex and a tapering neighbourhood around the anchors.
fixed={v for v in bm.verts if protected(v) or v.is_boundary}
ring={v:0 for v in fixed};front=fixed
for depth in range(1,5):
    nxt={e.other_vert(v) for v in front for e in v.link_edges if e.other_vert(v) not in ring}
    for v in nxt:ring[v]=depth
    front=nxt
ring_weight={0:0.,1:.08,2:.35,3:.7,4:1.}
start={v:v.co.copy() for v in bm.verts}
arm=bpy.data.objects['HomeGymPT_Male_Rig'];bones=arm.data.bones
updates={}
per_digit={}
for side in ('L','R'):
    for digit in ('index','middle','ring','pinky'):
        prefix='DEF-f_'+digit+'.'
        chain_bones=[bones[prefix+f'{i:02d}.'+side] for i in (1,2,3)]
        chain=[chain_bones[0].head_local.copy()]+[b.tail_local.copy() for b in chain_bones]
        direction=(chain[-1]-chain[-2]).normalized()
        select={gid for gid,name in groups.items() if prefix in name and name.endswith('.'+side)}
        samples=[]
        for v in bm.verts:
            if (v.co.x>0)!=(side=='L'):continue
            w=min(1.,influence(v,select))
            if w<.5:continue
            distance,q,arc=closest_chain(v.co,chain)
            if distance>.025:continue
            samples.append((v,w,distance,q,arc))
        # Bone tails run 9-20 mm beyond this source mesh. Locate the distal
        # surface itself; otherwise a tail-relative field misses the index.
        effective_end=max(x[4] for x in samples)
        moved=0
        for v,w,distance,q,arc in samples:
            if v in fixed or arc<effective_end-.018:continue
            radial=v.co-q
            if radial.length<1e-8:continue
            taper=fade(arc,effective_end-.018,effective_end-.006)
            anchor=ring_weight.get(ring.get(v,5),1.)
            s=w*anchor*taper
            # A small distal dome and taper. Unlike V10, the cap advances at
            # most 1.1 mm and is never touched on the floor-contact anchors.
            local_gain=.5 if digit in ('ring','pinky') else 1.
            cap=.0011*s*local_gain*max(0.,1.-(distance/.018)**2)
            pinch=.00045*s*local_gain
            updates[v]=v.co+cap*direction-pinch*radial.normalized()
            moved+=1
        per_digit[side+'_'+digit]=moved
for v,p in updates.items():v.co=p

# Preserve exact bilateral shape with mirrored source-position pairing.
right=[v for v in bm.verts if v in updates and v.co.x<0]
left=[v for v in bm.verts if v in updates and v.co.x>0]
tree=KDTree(len(right))
for i,v in enumerate(right):p=start[v];tree.insert(Vector((-p.x,p.y,p.z)),i)
tree.balance();pairs=0
for v in left:
    _,i,d=tree.find(start[v])
    if d>.00025:continue
    other=right[i];avg=(v.co+Vector((-other.co.x,other.co.y,other.co.z)))*.5
    v.co=avg;other.co=Vector((-avg.x,avg.y,avg.z));pairs+=1

# Subdivision plus dome shaping can sharpen one triangle at the ring/pinky
# tip and one at the index. Relax only those distal patches, keeping contact
# and patch-boundary vertices pinned; inherited folds elsewhere are untouched.
def new_distal_folds():
    bm.normal_update()
    result=[]
    for e in bm.edges:
        if len(e.link_faces)!=2:continue
        p=(e.verts[0].co+e.verts[1].co)*.5
        if abs(p.x)<.8 or not (p.z<1.10 or (p.y<-.24 and p.z<1.17)):continue
        if e.link_faces[0].normal.dot(e.link_faces[1].normal)<math.cos(math.radians(100)):
            result.append(e)
    return result
folds_before=len(new_distal_folds());repair_rounds=0
for repair_rounds in range(1,25):
    folded=new_distal_folds()
    if not folded:break
    zone={v for e in folded for f in e.link_faces for v in f.verts}
    zone|={e.other_vert(v) for v in list(zone) for e in v.link_edges}
    changes={}
    for v in zone:
        if protected(v) or v.is_boundary or len(v.link_edges)<3:continue
        avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
        shift=.32*(avg-v.co)
        if shift.length>.00035:shift.length=.00035
        changes[v]=v.co+shift
    for v,p in changes.items():v.co=p
folds_after=len(new_distal_folds())

protected_max=max((v.co-start[v]).length for v in bm.verts if protected(v))
boundary_max=max((v.co-start[v]).length for v in bm.verts if v.is_boundary)
outside_max=max(((v.co-start[v]).length for v in bm.verts if abs(v.co.x)<.62 or not 1.06<v.co.z<1.33),default=0.)
max_move=max((v.co-start[v]).length for v in bm.verts)
assert protected_max<1e-9 and boundary_max<1e-9 and outside_max<1e-9
bm.normal_update();bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update()
body['v13_fingertip_note']='V12c source; distal finger dome/taper only; protected contacts and seam boundaries fixed.'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
report={'source':SRC.name,'blend':OUT.name,'subdivided_edges':len(distal_edges),'new_vertices':new_vertices,
        'new_distal_folds_before_repair':folds_before,'new_distal_folds_after_repair':folds_after,'fold_repair_rounds':repair_rounds,
        'faces_before':before_faces,'faces_after':len(mesh.polygons),'moved_vertices':len(updates),'per_digit':per_digit,
        'mirrored_pairs':pairs,'max_move_mm':max_move*1000,'protected_max_move_mm':protected_max*1000,
        'boundary_max_move_mm':boundary_max*1000,'outside_hand_max_move_mm':outside_max*1000,
        'body_vertices':len(mesh.vertices),'body_faces':len(mesh.polygons)}
REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2))
print('V13_FINGERTIPS',json.dumps(report),flush=True)
