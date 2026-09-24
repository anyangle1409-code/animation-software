"""Measure the hand surface's seams, holes and folds, for V8, V10 and V11.

The hand and wrist are not one welded sheet: V8 is built from skin patches whose
edges meet other patches' edges or lie on their faces, unwelded. Whether those
seams are closed - in the bind pose and once the hand moves - is what decides
the wrist band, the palm outline and the thumb-index web wedge, and none of the
existing guards measures it. This does, per candidate:

* bind seams: every left-hand boundary vertex's distance to the nearest face it
  is not part of (0 is a closed seam, a few tenths of a millimetre a visible
  crack, several millimetres an open hole);
* posed seams: the same, on the equipment-free open-hand review pose written by
  the hand-studies harness (a seam can be closed at rest and open when posed if
  its two sides are weighted differently);
* fingertip holes: open boundary loops on the index to pinky tips;
* folds: left-hand edges whose two faces meet at more than 100 degrees.

Usage (Blender 5.2 Python):
    python scripts/audit_hand_seams.py v8_knee_anatomy v10_hand_retopology v11_hand_cleanup
Posed seams need reports/poses_<version>/open_hand_review_candidate.json, or for
the V8/V10 baselines the V11 board poses (see run_v11_pipeline.sh).
"""
from __future__ import annotations
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BANDS=((.05,'closed <0.05 mm'),(.5,'0.05-0.5 mm'),(1.5,'0.5-1.5 mm'),(4.,'1.5-4 mm'),(12.,'4-12 mm'))

def in_hand(co):return co.x>=.62 and 1.06<co.z<1.33
def band(mm):return next((label for limit,label in BANDS if mm<limit),'open >12 mm')

def seam_gaps(bm,select):
    bm.faces.ensure_lookup_table();tree=BVHTree.FromBMesh(bm);counts={label:0 for _,label in BANDS};counts['open >12 mm']=0
    for v in bm.verts:
        if not v.is_boundary or not select(v):continue
        own={f.index for f in v.link_faces}
        for x in [e.other_vert(v) for e in v.link_edges]:own|={f.index for f in x.link_faces}
        best=None
        for co,no,idx,d in tree.find_nearest_range(v.co,.012):
            if idx not in own and (best is None or d<best):best=d
        counts[band(best*1000 if best is not None else 1e9)]+=1
    return counts

def folds(bm,select):
    bm.normal_update()
    return sum(1 for e in bm.edges if len(e.link_faces)==2 and select(e.verts[0])
               and e.link_faces[0].normal.dot(e.link_faces[1].normal)<math.cos(math.radians(100)))

def tip_holes(bm,groups,dlay):
    digits={i for i,n in groups.items() if ('DEF-f_' in n and n.endswith('.03.L')) or n=='DEF-f_pinky.02.L'}
    return sum(1 for e in bm.edges if e.is_boundary and all(in_hand(x.co) and sum(w for g,w in x[dlay].items() if g in digits)>.5 for x in e.verts))

def posed(version):
    for path in (ROOT/f'reports/poses_{version}/open_hand_review_candidate.json',):
        if path.exists():return path
    board={'v10_hand_retopology':'baseline'}.get(version)
    if board:
        path=ROOT/f'reports/poses_v11_hand_cleanup/open_hand_review_{board}.json'
        if path.exists():return path
    return None

report={}
for version in sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend'))
    body=bpy.data.objects['Mike_Freeman'];bm=bmesh.new();bm.from_mesh(body.data)
    groups={g.index:g.name for g in body.vertex_groups};dlay=bm.verts.layers.deform.active
    entry={'bind_seams':seam_gaps(bm,lambda v:in_hand(v.co)),
           'fingertip_hole_edges':tip_holes(bm,groups,dlay),
           'folds_over_100deg':folds(bm,lambda v:in_hand(v.co))}
    bm.free()
    source=posed(version)
    if source:
        d=json.loads(source.read_text());m=d['meshes'][0]
        pm=bmesh.new();vs=[pm.verts.new(Vector((x,-z,y))) for x,y,z in m['positions']];I=m['indices']
        for i in range(0,len(I),3):
            try:pm.faces.new((vs[I[i]],vs[I[i+1]],vs[I[i+2]]))
            except ValueError:pass
        pm.verts.ensure_lookup_table()
        # The posed left hand: around the vertices the review renderer frames it
        # by (V8 GLB ids, which every candidate keeps as its prefix).
        ownership=json.loads((ROOT/'reports/sculpt_reference.json').read_text())['ownership']
        ids=[i for i,w in enumerate(ownership) if w['hand']>.8 and m['positions'][i][0]>0]
        centre=sum((vs[i].co for i in ids),Vector())/len(ids)
        reach=max((vs[i].co-centre).length for i in ids)*1.05
        entry['posed_open_hand_seams']=seam_gaps(pm,lambda v:(v.co-centre).length<reach)
        entry['posed_source']=str(source.relative_to(ROOT))
        pm.free()
    report[version]=entry
    print('HAND_SEAMS',version,json.dumps(entry),flush=True)
out=ROOT/'reports/hand_seam_audit.json'
out.write_text(json.dumps(report,indent=2))
print('WROTE',out)
