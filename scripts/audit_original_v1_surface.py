#!/usr/bin/env python3
"""Raw snapshot surface evidence. No mesh repair, phase PASS or production approval."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import subprocess
import sys
from audit_original_v1_changes import validate
from original_v1_production_control import ROOT,digest,evidence
from verify_original_v1_production_promotion import safe_path


def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def norm(a):return math.hypot(*a)


def cycle(face):
    # Face order matters: only cyclic rotation, never arbitrary sorting.
    index=face.index(min(face));return tuple(face[index:]+face[:index])


def components(nodes,adjacency):
    unseen=set(nodes);result=[]
    for seed in sorted(unseen):
        if seed not in unseen:continue
        unseen.remove(seed);stack=[seed];part=[]
        while stack:
            node=stack.pop();part.append(node)
            neighbors=adjacency.get(node,set())&unseen
            unseen.difference_update(neighbors);stack.extend(sorted(neighbors,reverse=True))
        result.append(sorted(part))
    return result


def audit_surface(snapshot,area_epsilon_m2=1e-12,planarity_epsilon_m=1e-6,mirror_quantum_m=1e-6):
    for value in (area_epsilon_m2,planarity_epsilon_m,mirror_quantum_m):
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise ValueError('finite nonnegative diagnostic precision required')
    if mirror_quantum_m==0:raise ValueError('mirror quantization must be positive')
    validate(snapshot)
    vertices=snapshot['vertices'];faces=snapshot['faces'];regions=snapshot['regions']
    if any(any(type(x) not in (int,float) for x in p) for p in vertices):raise ValueError('numeric coordinates required')
    if any(not isinstance(r,str) or not r for r in regions):raise ValueError('named vertex regions required')
    if not faces:raise ValueError('snapshot has no surface faces')
    edges=defaultdict(list);incident=defaultdict(list);face_groups=defaultdict(list)
    repeated=[];zero=[];near=[];zero_fans=[];nonplanar=[];metrics=[];valid=[]
    for fid,face in enumerate(faces):
        if len(set(face))!=len(face):repeated.append(fid);continue
        valid.append(fid);face_groups[min(cycle(face),cycle(list(reversed(face))))].append(fid)
        for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))].append((fid,a,b))
        for index,v in enumerate(face):incident[v].append((fid,face[index-1],face[(index+1)%len(face)]))
        p=[vertices[v] for v in face]
        fans=[cross(sub(p[i],p[0]),sub(p[i+1],p[0])) for i in range(1,len(p)-1)]
        area_vector=tuple(math.fsum(t[axis] for t in fans) for axis in range(3))
        vector_area=norm(area_vector)*0.5;fan_area=math.fsum(norm(t)*0.5 for t in fans)
        fan_zero=any(norm(t)==0 for t in fans)
        distance=max(abs(dot(sub(q,p[0]),area_vector))/norm(area_vector) for q in p) if vector_area else None
        if vector_area==0:zero.append(fid)
        elif vector_area<=area_epsilon_m2:near.append(fid)
        if fan_zero:zero_fans.append(fid)
        if distance is not None and distance>planarity_epsilon_m:nonplanar.append(fid)
        volume=math.fsum(dot(p[0],cross(p[i],p[i+1]))/6 for i in range(1,len(p)-1))
        metrics.append({'face_id':fid,'vertices':face,'regions':sorted({regions[v] for v in face}),
            'area_vector_m2':[x*0.5 for x in area_vector],'vector_area_m2':vector_area,
            'fan_area_sum_m2':fan_area,'fan_signed_volume_m3':volume,'max_plane_distance_m':distance})
    duplicate=[ids for _,ids in sorted(face_groups.items()) if len(ids)>1]
    boundary=[];nonmanifold=[];winding=[];face_adjacency=defaultdict(set)
    for edge,rows in sorted(edges.items()):
        record={'vertices':list(edge),'face_ids':sorted(r[0] for r in rows),'regions':sorted({regions[v] for v in edge})}
        if len(rows)==1:boundary.append(record)
        elif len(rows)>2:nonmanifold.append(record)
        elif rows[0][1:]==rows[1][1:]:winding.append(record)
        # Star connection avoids quadratic storage for a many-face invalid edge.
        for row in rows[1:]:
            face_adjacency[rows[0][0]].add(row[0]);face_adjacency[row[0]].add(rows[0][0])
    bad_vertices=[];vertex_links=[]
    for vid,rows in sorted(incident.items()):
        links=defaultdict(set);degrees=Counter()
        for _,a,b in rows:links[a].add(b);links[b].add(a);degrees[a]+=1;degrees[b]+=1
        parts=components(degrees,links);is_cycle=len(parts)==1 and all(d==2 for d in degrees.values())
        is_path=len(parts)==1 and sorted(degrees.values()).count(1)==2 and all(d in (1,2) for d in degrees.values())
        bad_edges=any(len(edges[tuple(sorted((vid,n)))])>2 for n in degrees)
        bad=bad_edges or not (is_cycle or is_path)
        if bad:bad_vertices.append(vid)
        vertex_links.append({'vertex_id':vid,'region':regions[vid],'link_component_count':len(parts),
            'link_neighbor_count':len(degrees),'link_kind':'NONMANIFOLD' if bad else 'CYCLE' if is_cycle else 'BOUNDARY_PATH'})
    by_face={row['face_id']:row for row in metrics};shells=[]
    bad_face_ids=set(repeated+zero+near+zero_fans+nonplanar)|{f for group in duplicate for f in group}
    parts=components(valid,face_adjacency);face_component={fid:i for i,ids in enumerate(parts) for fid in ids}
    component_edges=defaultdict(list)
    for edge,rows in edges.items():component_edges[face_component[rows[0][0]]].append((edge,rows))
    conflict_faces={r['face_ids'][0] for r in winding};bad_vertex_set=set(bad_vertices)
    for cid,ids in enumerate(parts):
        members=set(ids);used=sorted({v for f in ids for v in faces[f]})
        shell_edges=component_edges[cid]
        closed=all(len(rows)==2 for _,rows in shell_edges)
        coherent=not (members&conflict_faces)
        volume=math.fsum(by_face[f]['fan_signed_volume_m3'] for f in ids)
        orientation_available=closed and coherent and not (members&bad_face_ids) and not (set(used)&bad_vertex_set)
        shells.append({'component_id':len(shells),'face_ids':ids,'vertex_count':len(used),
            'regions':dict(sorted(Counter(regions[v] for v in used).items())),
            'closed_edge_incidence':closed,'consistent_shared_edge_winding':coherent,
            'signed_volume_m3':volume,'orientation_hint':('POSITIVE_SIGNED_VOLUME' if volume>0 else 'NEGATIVE_SIGNED_VOLUME' if volume<0 else 'ZERO_SIGNED_VOLUME') if orientation_available else None,
            'orientation_is_approval':False})
    coordinates=defaultdict(list)
    for i,p in enumerate(vertices):coordinates[tuple(p)].append(i)
    coincident=[ids for _,ids in sorted(coordinates.items()) if len(ids)>1]
    quantized=defaultdict(list)
    quant=lambda p:tuple(round(x/mirror_quantum_m) for x in p)
    for i,p in enumerate(vertices):quantized[quant(p)].append(i)
    mirror={};ambiguous=[];unpaired=[]
    for i,p in enumerate(vertices):
        own=quantized[quant(p)];twins=quantized.get(quant((-p[0],p[1],p[2])),[])
        if len(own)>1 or len(twins)>1:ambiguous.append(i)
        elif len(twins)==1:mirror[i]=twins[0]
        else:unpaired.append(i)
    directed={cycle(faces[f]) for f in valid};unmatched=[];uncovered=[]
    for fid in valid:
        if any(v not in mirror for v in faces[fid]):uncovered.append(fid)
        elif cycle(list(reversed([mirror[v] for v in faces[fid]]))) not in directed:unmatched.append(fid)
    errors=[math.dist((-vertices[i][0],vertices[i][1],vertices[i][2]),vertices[j])*1000 for i,j in sorted(mirror.items()) if i<=j]
    result={'schema_version':1,'candidate_sha256':snapshot['candidate_sha256'],'status':'EVIDENCE_ONLY',
        'coordinate_space':snapshot['coordinate_space'],'vertex_count':len(vertices),'face_count':len(faces),
        'edge_count':len(edges),'analysed_face_count':len(valid),'excluded_face_ids':repeated,
        'precision':{'area_epsilon_m2':area_epsilon_m2,'planarity_epsilon_m':planarity_epsilon_m,'mirror_quantum_m':mirror_quantum_m,
            'purpose':'declared diagnostic precision only; not a deformation gate or exception waiver'},
        'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'winding_conflict_edges':winding,
        'nonmanifold_vertex_ids':bad_vertices,'vertex_links':vertex_links,'components':shells,
        'isolated_vertex_ids':sorted(set(range(len(vertices)))-{v for f in faces for v in f}),
        'vertices_only_in_excluded_faces':sorted({v for f in faces for v in f}-set(incident)),
        'repeated_vertex_face_ids':repeated,'duplicate_face_groups':duplicate,
        'exact_zero_area_face_ids':zero,'near_degenerate_face_ids':near,'zero_area_fan_face_ids':zero_fans,
        'nonplanar_face_ids':nonplanar,'face_metrics':metrics,'coincident_coordinate_groups':coincident,
        'symmetry':{'coverage_vertex_count':len(mirror),'full_vertex_coverage':len(mirror)==len(vertices),
            'unpaired_vertex_ids':unpaired,'ambiguous_vertex_ids':ambiguous,
            'uncovered_face_ids':uncovered,'unmatched_face_ids':unmatched,
            'max_position_error_mm':max(errors,default=None),
            'mapping':'this candidate own unique quantized reflected coordinates; no nearest-surface transfer'},
        'phase_complete':False,'production_approved':False,
        'unresolved_domain_checks':['joint_support','actual_shading_normals','self_intersections','posed_deformation','owner_anatomy_review'],
        'limits':['Raw body snapshot only; clothing, modifiers and evaluated/custom shading normals are not inspected.',
            'Polygon fan triangulation is diagnostic, not proof of Blender/export triangulation for concave or nonplanar polygons.',
            'Signed volume is an orientation hint for closed coherent components, not proof of an intersection-free outward surface.',
            'No self-intersection, joint-support, anatomy, runtime or production acceptance is inferred.',
            'Repeated-index faces are excluded from incidence/link/component calculations and remain explicit defects.',
            'Diagnostic precision and quantized symmetry coverage cannot waive defects or change frozen gates.']}
    # Arithmetic overflow must not produce non-finite evidence.
    from original_v1_production_control import ensure_finite
    ensure_finite(result);return result


def markdown(result):
    lines=['# ORIGINAL v1 raw surface audit','',
        'Candidate SHA-256: `'+result['candidate_sha256']+'`','',
        'EVIDENCE ONLY. No phase completion or production approval.','',
        '| Finding | Count |','|---|---:|']
    fields=('boundary_edges','nonmanifold_edges','winding_conflict_edges','nonmanifold_vertex_ids',
        'isolated_vertex_ids','repeated_vertex_face_ids','duplicate_face_groups','exact_zero_area_face_ids',
        'near_degenerate_face_ids','zero_area_fan_face_ids','nonplanar_face_ids','coincident_coordinate_groups')
    lines += [f'| {name} | {len(result[name])} |' for name in fields]
    sym=result['symmetry'];lines += ['',f"Symmetry coverage: {sym['coverage_vertex_count']} / {result['vertex_count']} vertices; {len(sym['unmatched_face_ids'])} unmatched faces; {len(sym['uncovered_face_ids'])} uncovered faces.",
        '', 'Exact defect/region/face/vertex IDs and precision are in the JSON. Zero counts do not complete Phase 6.',
        '', 'Unresolved domain checks: '+', '.join(result['unresolved_domain_checks'])+'.','',
        *['- '+s for s in result['limits']],'']
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('snapshot',type=Path)
    ap.add_argument('--candidate-manifest',required=True,type=Path);ap.add_argument('--json-out',required=True,type=Path)
    ap.add_argument('--markdown-out',type=Path);ap.add_argument('--area-epsilon-m2',type=float,default=1e-12)
    ap.add_argument('--planarity-epsilon-m',type=float,default=1e-6);ap.add_argument('--mirror-quantum-m',type=float,default=1e-6)
    args=ap.parse_args()
    try:
        inputs=[safe_path(ROOT,p.resolve().relative_to(ROOT).as_posix()) for p in (args.snapshot,args.candidate_manifest)]
        outputs=[safe_path(ROOT,p.resolve().relative_to(ROOT).as_posix()) for p in (args.json_out,args.markdown_out) if p]
        if len(outputs)!=len(set(outputs)) or any(p.exists() for p in outputs):raise ValueError('audit output already exists or aliases another output; preserve evidence')
        snapshot,manifest=[json.loads(p.read_text(encoding='utf-8-sig')) for p in inputs]
        if not isinstance(snapshot,dict) or not isinstance(manifest,dict):raise ValueError('snapshot and manifest must be JSON objects')
        if snapshot.get('candidate_sha256')!=manifest.get('candidate_sha256'):raise ValueError('snapshot candidate differs from supplied manifest')
        result=audit_surface(snapshot,args.area_epsilon_m2,args.planarity_epsilon_m,args.mirror_quantum_m)
        result['source_evidence']=[evidence(ROOT,p.relative_to(ROOT).as_posix()) for p in inputs]+[evidence(ROOT,'scripts/audit_original_v1_surface.py'),evidence(ROOT,'scripts/audit_original_v1_changes.py')]
        result['command']=['python',*sys.argv];result['source_git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        result['evidence_timestamp']=datetime.now(timezone.utc).isoformat()
        for p in outputs:p.parent.mkdir(parents=True,exist_ok=True)
        outputs[0].write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        if len(outputs)>1:outputs[1].write_text(markdown(result),encoding='utf-8')
        print('SURFACE EVIDENCE WRITTEN — inspect findings and unresolved checks; no gate PASS');return 0
    except (OSError,ValueError,KeyError,TypeError,ArithmeticError,subprocess.SubprocessError) as exc:
        print('STOP — '+str(exc));return 2

if __name__=='__main__':raise SystemExit(main())
