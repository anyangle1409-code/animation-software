"""Build the V11 hand cleanup candidate in Blender from the V10 checkpoint.

V10's visible defects were measured before this script was written
(`REVIEW_V10_TOPOLOGY_AUDIT.md`). Two of the four are topology, not shape, and
no sculpt field can remove them:

* The hand and wrist surface is not one welded sheet. V8 already carried about
  900 unwelded boundary vertices around each hand and wrist, almost all within
  0.5 mm of a partner edge: the "stepped" wrist band and the pale outline across
  the palm are those seams. V10's subdivision and sculpt moved one side of them,
  opening 335 boundary vertices into 0.5-2 mm cracks; the dark thumb-index web
  line is one of them.
* The index, middle, ring and pinky tips end in small open holes (8 to 13
  boundary vertices, up to 3.6 mm across) in both V8 and V10.

The other two - ring banding along the fingers and faceted tips - are shape. V10
added its joint pads, shaft narrowing and a 5.5 mm tip push on top of a
subdivided surface, which is where its folded (>120 degree) and flipped
triangles come from. Two strategies are built and measured:

* ``VARIANT=A`` keeps V10's sculpt and cleans it: constrained Taubin smoothing.
* ``VARIANT=B`` (the default, and V11) keeps V10's topology but returns the
  hand to V8's shape (originals to their V8 positions, added vertices to their
  interpolated V8 rest position) and smooths that denser surface. None of V10's
  sculpt fields are re-applied by default; see ``PALM_FIELDS``.

Both then fill the fingertip holes, close the seams and restore V10's posed
skin-interpolation correction. Seams are closed by moving vertices, never by
merging: every original V8 vertex keeps its ID (the packer depends on it), the
682 protected push-up contact vertices never move, and no vertex outside the
hand region moves. Where a seam runs between a hand vertex and a fixed one, only
the hand side moves.
"""
from __future__ import annotations
import bpy,bmesh,json,math,os,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_point_line

ROOT=Path(__file__).resolve().parents[1]
VARIANT=os.environ.get('VARIANT','B')
VERSION='v11_hand_cleanup'
SOURCE_BLEND=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology.blend'
V8_BLEND=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend'
V8_GLB=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb'
OUT=Path(os.environ.get('OUT',ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend'))
REPORT=Path(os.environ.get('REPORT',ROOT/f'reports/build_{VERSION}_blender.json'))
for protected in (SOURCE_BLEND,V8_BLEND):
    assert OUT.resolve()!=protected.resolve(),'Refusing to overwrite a preserved candidate'

# --- V8 reference: original positions, and which originals are protected ----
data=V8_GLB.read_bytes();n=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+n]);base=28+n;prim=doc['meshes'][0]['primitives'][0]
def view(ai):
    a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']]
    dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
    cols={'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']]
    return np.ndarray((a['count'],cols),dt,buffer=data,offset=base+v.get('byteOffset',0)+a.get('byteOffset',0),
                      strides=(v.get('byteStride',dt.itemsize*cols),dt.itemsize)).copy()
faces=view(prim['indices']).reshape(-1,3).astype(int)
protected_glb=set(json.loads((ROOT/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids'])
bpy.ops.wm.open_mainfile(filepath=str(V8_BLEND))
v8mesh=bpy.data.objects['Mike_Freeman'].data
assert len(v8mesh.vertices)==33059 and len(v8mesh.polygons)==len(faces)
v8_co=[v.co.copy() for v in v8mesh.vertices]
glb_ids=[set() for _ in v8mesh.vertices]
for i,poly in enumerate(v8mesh.polygons):
    for corner,loopid in enumerate(poly.loop_indices):
        glb_ids[v8mesh.loops[loopid].vertex_index].add(int(faces[i,corner]))
protected_v8=[bool(ids&protected_glb) for ids in glb_ids]
assert sum(protected_v8)>0

# --- V10 checkpoint ------------------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
body=bpy.data.objects['Mike_Freeman'];mesh=body.data
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
dlay=bm.verts.layers.deform.active
idlay=bm.verts.layers.int['v8_source_id']
floorlay=bm.verts.layers.float['v8_floor_clearance']
restlay=bm.verts.layers.float_vector['v8_interpolated_rest']
posedlay=bm.verts.layers.float_vector['v8_interpolated_curl_pose']
uv0=bm.loops.layers.uv[0];uv1=bm.loops.layers.uv[1]
# Made before any vertex is used as a key: adding a layer later re-creates them.
seamlay=bm.verts.layers.int.new('v11_seam_weights')
before_verts=len(bm.verts);before_faces=len(bm.faces)
start={v:v.co.copy() for v in bm.verts}

groups={g.index:g.name for g in body.vertex_groups}
hand_groups={i for i,n in groups.items() if any(s in n for s in ('DEF-hand.','DEF-palm.','DEF-thumb.','DEF-f_'))}
digit_groups={i for i,n in groups.items() if any(s in n for s in ('DEF-thumb.','DEF-f_'))}
def influence(v,selected):return sum(w for g,w in v[dlay].items() if g in selected)
def fade(v,a,b):
    t=max(0.,min(1.,(v-a)/(b-a)));return t*t*(3.-2.*t)
def gauss(v,mu,sigma):return math.exp(-.5*((v-mu)/sigma)**2)
# Identical to V10's hand mask, so V11 edits exactly the region V10 did.
def local_strength(v,margin=.016):
    p=v.co
    if abs(p.x)<.62 or p.z<1.06 or p.z>1.33:return 0.
    return min(1.,influence(v,hand_groups))*fade(v[floorlay],margin,margin+.025)*fade(abs(p.x),.63,.69)
def sid(v):return v[idlay]-1
def is_protected(v):return sid(v)>=0 and protected_v8[sid(v)]
def in_hand(v):
    p=v.co
    return abs(p.x)>=.62 and 1.06<p.z<1.33 and influence(v,hand_groups)>0.
# May move: any hand vertex but the protected push-up contact. V10's fade near
# the push-up floor is not used - it kept the palm side of the fingers and the
# palm-side wrist crease from being smoothed or closed at all.
def movable(v):return not is_protected(v) and in_hand(v)

# The hand, without V10's fade near the push-up floor. The protected contact
# vertices are what hold the push-up; the fade also kept the palm side of the
# fingers from ever being smoothed, which is where their ridges are.
# Smoothing eases in over the three rings around each protected vertex: those
# stay exactly where they are, and a neighbour smoothed right up to one leaves it
# standing proud as a star-shaped point.
protected_ring={}
frontier=[v for v in bm.verts if is_protected(v)]
for v in frontier:protected_ring[v]=0
for ring in (1,2,3):
    frontier=[e.other_vert(v) for v in frontier for e in v.link_edges]
    frontier=[v for v in frontier if v not in protected_ring]
    for v in frontier:protected_ring[v]=ring
RING_WEIGHT={0:0.,1:.2,2:.5,3:.8}
def hand_weight(v):
    if not in_hand(v):return 0.
    return RING_WEIGHT.get(protected_ring.get(v,4),1.)*min(1.,influence(v,hand_groups))*fade(abs(v.co.x),.63,.69)

# --- V10's posed skin-interpolation correction, taken off and put back --------
# The correction adds a fixed bind offset to each added vertex (it depends only
# on the V8 rest and curl interpolants and the vertex weights), so it is removed
# before any reshaping and restored at the end.
ref=json.loads((ROOT/'reports/v10_actual_curl_skin_matrices.json').read_text())
T=np.array(ref['matrices'],dtype=float).reshape(-1,4,4).transpose(0,2,1)
names=[doc['nodes'][i].get('name','') for i in doc['skins'][0]['joints']]
joint_by_name={name:i for i,name in enumerate(names)}
group_to_joint={g.index:joint_by_name[g.name] for g in body.vertex_groups if g.name in joint_by_name}
def to_glb(v):return np.array((v[0],v[2],-v[1]),dtype=float)
def to_blender(v):return Vector((float(v[0]),float(-v[2]),float(v[1])))
correction={}
for v in bm.verts:
    if sid(v)>=0:continue
    pairs=[(group_to_joint[g],w) for g,w in v[dlay].items() if g in group_to_joint and w>0]
    total=sum(w for _,w in pairs)
    M=sum(T[j]*(w/total) for j,w in pairs)
    offset=np.linalg.solve(M[:3,:3],to_glb(v[posedlay])-M[:3,3])-to_glb(v[restlay])
    correction[v]=to_blender(offset)
    v.co-=correction[v]

# --- Shape ---------------------------------------------------------------------
if VARIANT=='B':
    for v in bm.verts:
        if not movable(v):continue
        v.co=v8_co[sid(v)].copy() if sid(v)>=0 else Vector(v[restlay])

# --- Fingertip holes -------------------------------------------------------------
bm.edges.ensure_lookup_table()
tip_edges=[e for e in bm.edges if e.is_boundary and all(influence(x,digit_groups)>.5 and movable(x) for x in e.verts)]
filled=bmesh.ops.holes_fill(bm,edges=tip_edges,sides=16)['faces']
for f in filled:
    for loop in f.loops:
        # A cap face takes each corner's existing UVs from the surface around it,
        # so the packer finds the original vertex records unchanged.
        other=next(l for l in loop.vert.link_loops if l.face not in filled)
        loop[uv0].uv=other[uv0].uv.copy();loop[uv1].uv=other[uv1].uv.copy()
bmesh.ops.triangulate(bm,faces=filled)
bm.normal_update()

# --- Smoothing -------------------------------------------------------------------
# Taubin (shrink-free) smoothing inside the hand mask. Seam vertices are held
# here and closed afterwards; the mask's own falloff blends into the fixed wrist.
def taubin(rounds,cap,weight):
    for _ in range(rounds):
        for coefficient in (.5,-.53):
            updates={}
            for v in bm.verts:
                if is_protected(v) or v.is_boundary or len(v.link_edges)<3:continue
                s=weight(v)
                if s<.02:continue
                avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
                shift=coefficient*s*(avg-v.co)
                if shift.length>cap:shift.length=cap
                updates[v]=v.co+shift
            for v,p in updates.items():v.co=p
rounds=int(os.environ.get('ROUNDS','14'))
taubin(rounds,.0012,hand_weight)
# The fingers again, longer: V8's phalanges are a few long flat facets each.
finger_rounds=int(os.environ.get('FINGER_ROUNDS','24'))
taubin(finger_rounds,.0008,lambda v:hand_weight(v)*min(1.,influence(v,digit_groups)))
bm.normal_update()

# Off by default: pushed along vertex normals, which differ on the two sides of
# an unwelded seam, V10's thenar and web fields lift the thenar patch edge into
# the overhang that reads as the dark thumb-index web wedge. V11's palm is V8's
# accepted palm, smoothed. PALM_FIELDS=1 restores V10's volume and the wedge.
PALM_FIELDS=os.environ.get('PALM_FIELDS','0')=='1'
if VARIANT=='B' and PALM_FIELDS:
    # V10's broad palm, thenar, web and wrist volume fields, unchanged. Its
    # finger joint pads, shaft narrowing and tip push are left out: they are the
    # ring bands.
    for v in bm.verts:
        s=local_strength(v,.015)
        if s<.02 or is_protected(v):continue
        x=abs(v.co.x);y=v.co.y;z=v.co.z
        thenar=gauss(x,.749,.035)*gauss(y,-.145,.041)*gauss(z,1.196,.040)
        web=gauss(x,.759,.026)*gauss(y,-.191,.026)*gauss(z,1.197,.029)
        hypothenar=gauss(x,.745,.031)*gauss(y,-.069,.033)*gauss(z,1.188,.044)
        arch=gauss(x,.768,.044)*gauss(y,-.115,.062)*gauss(z,1.176,.046)
        wrist=gauss(x,.702,.026)*gauss(y,-.112,.055)*gauss(z,1.194,.057)
        height=(.004*thenar+.0026*web+.0032*hypothenar+.0022*arch+.0012*wrist)
        if height>.00001:v.co+=s*height*v.normal
    bm.normal_update()
    taubin(2,.0006,hand_weight)

for v,offset in correction.items():v.co+=offset

# --- Folds -----------------------------------------------------------------------
# The mask above fades to nothing near the push-up floor, so the finger bases and
# palm - where V10's folds are - were barely smoothed. The 682 protected contact
# vertices are what hold the push-up contact; everything else in the hand may
# move, so folded faces are relaxed locally until none are left.
def fold_edges():
    bm.normal_update()
    return [e for e in bm.edges if len(e.link_faces)==2 and any(in_hand(x) for x in e.verts)
            and e.link_faces[0].normal.dot(e.link_faces[1].normal)<-.17]  # beyond 100 degrees
fold_rounds=0;folds_before=len(fold_edges())
for fold_rounds in range(1,41):
    folded=fold_edges()
    if not folded:break
    ring={x for e in folded for f in e.link_faces for x in f.verts}
    ring|={e.other_vert(x) for x in list(ring) for e in x.link_edges}
    for coefficient in (.5,-.53):
        updates={}
        for v in ring:
            if is_protected(v) or v.is_boundary or not in_hand(v) or len(v.link_edges)<3:continue
            avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
            updates[v]=v.co+coefficient*(avg-v.co)
        for v,p in updates.items():v.co=p
folds_after=len(fold_edges())

# --- Symmetry, as V10 ------------------------------------------------------------
right=[v for v in bm.verts if v.co.x<-.62 and movable(v)]
left=[v for v in bm.verts if v.co.x>.62 and movable(v)]
tree=KDTree(len(right))
for i,v in enumerate(right):p=start[v];tree.insert(Vector((-p.x,p.y,p.z)),i)
tree.balance();paired=0
for v in left:
    _,ri,d=tree.find(start[v])
    if d>.00025:continue
    r=right[ri];avg=(v.co+Vector((-r.co.x,r.co.y,r.co.z)))*.5
    v.co=avg;r.co=Vector((-avg.x,avg.y,avg.z));paired+=1
bm.normal_update()

# --- Seams -----------------------------------------------------------------------
# Every boundary vertex with a partner edge within 2.5 mm is moved onto it, if it
# may move. Repeated so pairs that both move settle on each other.
bm.edges.ensure_lookup_table()
boundary=[e for e in bm.edges if e.is_boundary and any(local_strength(x)>0 or abs(x.co.x)>.55 for x in e.verts)]
mid=KDTree(len(boundary))
for i,e in enumerate(boundary):mid.insert((e.verts[0].co+e.verts[1].co)*.5,i)
mid.balance()
seam_moves=0;worst_seam=0.
for sweep in range(10):
    moved=0
    # In index order: vertices move one at a time, so the order must not vary.
    for v in sorted({x for e in boundary for x in e.verts},key=lambda x:x.index):
        if not movable(v):continue
        best=None
        # The vertex's own side of the seam: anything within two edges of it.
        near={v}
        for _ in range(2):near|={e.other_vert(x) for x in list(near) for e in x.link_edges}
        for _,i,_ in mid.find_range(v.co,.02):
            e=boundary[i]
            if e.verts[0] in near or e.verts[1] in near:continue
            a,b=e.verts[0].co,e.verts[1].co
            _,t=intersect_point_line(v.co,a,b);t=max(0.,min(1.,t));q=a+(b-a)*t
            d=(v.co-q).length
            if d<.0025 and (best is None or d<best[0]):best=(d,q,e)
        if best is None or best[0]<1e-7:continue
        d,q,e=best
        # Meet a movable partner half way; a fixed one, all the way.
        partner_moves=all(movable(x) for x in e.verts)
        target=(v.co+q)*.5 if partner_moves and sweep<2 else q
        worst_seam=max(worst_seam,d);v.co=target.copy();moved+=1
    seam_moves+=moved
    mid=KDTree(len(boundary))
    for i,e in enumerate(boundary):mid.insert((e.verts[0].co+e.verts[1].co)*.5,i)
    mid.balance()
    if moved==0:break
bm.normal_update()

# --- Seams against faces -----------------------------------------------------------
# Much of V8's hand is separate skin patches whose edges lie on another patch's
# face rather than meeting an edge (826 of 862 hand boundary vertices sit within
# 1.5 mm of another face). Where such an edge has lifted off - the dark wedge at
# the thumb-index web - the vertex is laid back onto the nearest face.
bm.faces.ensure_lookup_table();bm.normal_update()
tree=BVHTree.FromBMesh(bm)
face_snaps=0;worst_face_gap=0.
for v in [v for v in bm.verts if v.is_boundary and movable(v)]:
    own={f.index for f in v.link_faces}
    for x in [e.other_vert(v) for e in v.link_edges]:own|={f.index for f in x.link_faces}
    best=None
    for co,no,idx,d in tree.find_nearest_range(v.co,.003):
        if idx in own:continue
        if best is None or d<best[1]:best=(co,d)
    if best is None or best[1]<2e-5:continue
    worst_face_gap=max(worst_face_gap,best[1]);v.co=best[0].copy();face_snaps+=1
bm.normal_update()

# --- Seam weights -------------------------------------------------------------------
# A seam closed in the bind pose opens again as soon as the hand moves if its two
# sides are weighted differently: the dark wedge at the thumb-index web is V10's
# thenar patch edge carrying interpolated weights its partner surface does not.
# Each closed seam vertex takes the weights of the surface point it lies on, so
# both sides skin identically in every pose. Marked for the packer, which
# otherwise keeps every original vertex's V8 weights.
from mathutils.geometry import barycentric_transform
bm.faces.ensure_lookup_table();tree=BVHTree.FromBMesh(bm)
def deform_groups(v):return {g:w for g,w in v[dlay].items() if groups[g].startswith('DEF-')}
reweighted=0;largest_weight_change=0.
for v in [v for v in bm.verts if v.is_boundary and movable(v)]:
    own={f.index for f in v.link_faces}
    for x in [e.other_vert(v) for e in v.link_edges]:own|={f.index for f in x.link_faces}
    best=None
    for co,no,idx,d in tree.find_nearest_range(v.co,.0001):
        if idx in own:continue
        if best is None or d<best[1]:best=(idx,d)
    if best is None:continue
    face=bm.faces[best[0]];corners=[x.co for x in face.verts[:3]]
    if len(face.verts)!=3:continue
    # Barycentric coordinates of the vertex in the partner triangle.
    a,b,c=corners
    v0,v1,v2=b-a,c-a,v.co-a
    d00,d01,d11,d20,d21=v0.dot(v0),v0.dot(v1),v1.dot(v1),v2.dot(v0),v2.dot(v1)
    den=d00*d11-d01*d01
    if abs(den)<1e-18:continue
    wb=(d11*d20-d01*d21)/den;wc=(d00*d21-d01*d20)/den;wa=1.-wb-wc
    bary=[max(0.,x) for x in (wa,wb,wc)];total=sum(bary)
    if total<=0:continue
    partner={}
    for x,f in zip(face.verts,bary):
        for g,w in deform_groups(x).items():partner[g]=partner.get(g,0.)+w*f/total
    mine=deform_groups(v)
    change=sum(abs(partner.get(g,0.)-mine.get(g,0.)) for g in set(partner)|set(mine))
    if change<.01:continue
    for g in mine:
        if g not in partner:del v[dlay][g]
    for g,w in partner.items():v[dlay][g]=w
    v[seamlay]=1;reweighted+=1;largest_weight_change=max(largest_weight_change,change)

# --- Guarantees ------------------------------------------------------------------
survivors=[v for v in bm.verts if sid(v)>=0]
assert len(survivors)==33059 and len({sid(v) for v in survivors})==33059
protected_max=max((v.co-start[v]).length for v in survivors if protected_v8[sid(v)])
fixed_max=max(((v.co-start[v]).length for v in bm.verts if not in_hand(v)),default=0.)
assert protected_max<1e-9,protected_max
assert fixed_max<1e-9,fixed_max
assert len(bm.verts)==before_verts,'V11 adds no vertices'

bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update()
body['hand_cleanup_note']=f'V11 variant {VARIANT}: V10 seams closed, fingertip holes filled, hand smoothed; no rig edits.'
bpy.context.preferences.filepaths.save_version=0
OUT.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
report={'variant':VARIANT,'palm_fields':PALM_FIELDS,'source':SOURCE_BLEND.name,'blend':OUT.name,
        'vertices':len(mesh.vertices),'faces_before':before_faces,'faces_after':len(mesh.polygons),
        'fingertip_cap_faces':len(filled),'taubin_rounds':rounds,'finger_taubin_rounds':finger_rounds,
        'seam_vertices_moved':seam_moves,'largest_seam_closed_mm':worst_seam*1000,
        'seam_vertices_reweighted':reweighted,'largest_seam_weight_change':largest_weight_change,
        'seam_vertices_laid_on_faces':face_snaps,'largest_face_gap_closed_mm':worst_face_gap*1000,
        'folded_edges_before_repair':folds_before,'folded_edges_after_repair':folds_after,'fold_repair_rounds':fold_rounds,
        'mirrored_pairs':paired,'protected_original_max_move_mm':protected_max*1000,
        'outside_hand_max_move_mm':fixed_max*1000,
        'skin_correction_restored_vertices':len(correction)}
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(report,indent=2))
print('V11_HAND_BLENDER',json.dumps(report),flush=True)
