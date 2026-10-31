"""Four fixed mesh-edge trajectories; not anatomical tissue strain."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from elbow_edge_endpoint_audit import TARGETS
from forearm_pose_state_probe import W8_SHA256, R57_SHA, _number, _vector

LIMITATIONS=(
    'Four historical mesh edges are diagnostic samples, not a complete or anatomically certified elbow region',
    'Lengths and ratios describe mesh edges, not tissue strain or safety',
    'The evaluated neutral baseline and historical press ratios have a different reference and are not declared comparable',
    'The coupled row is measured with plain corrective keys zero, not driven corrective skin',
    'Vertex names and suffixes do not certify anatomical laterality',
    'No anatomical movement, joint-frame, muscle-continuity or return-to-neutral approval follows',
)


def topology(vertices_count,faces):
    if type(vertices_count) is not int or vertices_count<=0:
        raise ValueError('invalid vertex count')
    canonical=[];present=set()
    for face in faces:
        if (len(face)!=3 or any(type(i) is not int or not 0<=i<vertices_count for i in face)
            or len(set(face))!=3):
            raise ValueError('invalid triangle indices')
        face=list(face);canonical.append(face)
        for a,b in zip(face,face[1:]+face[:1]):present.add(tuple(sorted((a,b))))
    if not canonical or any(tuple(sorted(pair)) not in present for _,pair,*_ in TARGETS):
        raise ValueError('pinned edge absent from topology')
    return hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()


def _points(vertices,pair):
    try:return [_vector(list(vertices[i]),3) for i in pair]
    except (IndexError,KeyError,TypeError):raise ValueError('missing pinned endpoint') from None


def _length_mm(points):
    value=math.dist(*points)*1000.
    if not math.isfinite(value):raise ValueError('nonfinite length')
    return value


def reference(vertices,faces,source_count,source_faces):
    count=len(vertices)
    digest=topology(count,faces)
    if type(source_count) is not int or source_count!=count or topology(source_count,source_faces)!=digest:
        raise ValueError('source/evaluated topology mismatch')
    edges=[]
    for name,pair,*_ in TARGETS:
        points=_points(vertices,pair);length=_length_mm(points)
        if length<=1e-7:raise ValueError('degenerate neutral edge')
        edges.append({'name':name,'vertex_ids':list(pair),'neutral_endpoints_world_m':points,'neutral_length_mm':length})
    return {'vertex_count':count,'topology_sha256':digest,
            'source_topology_matches_evaluated':True,'edges':edges}


def snapshot(vertices,faces,ref,sample):
    if type(sample) is not int or not 0<=sample<=8:raise ValueError('invalid sample')
    digest=topology(len(vertices),faces)
    if len(vertices)!=ref['vertex_count'] or digest!=ref['topology_sha256']:
        raise ValueError('posed topology drift')
    rows=[]
    for baseline in ref['edges']:
        pair=baseline['vertex_ids'];points=_points(vertices,pair);length=_length_mm(points)
        rows.append({'name':baseline['name'],'vertex_ids':list(pair),'posed_endpoints_world_m':points,
                     'posed_length_mm':length,'length_ratio_to_neutral':length/baseline['neutral_length_mm']})
    return {'sample':sample,'topology_sha256':digest,'edges':rows}


def _scope():
    return {'status':'READ_ONLY_FOUR_PINNED_ROW_EDGES_NOT_ANATOMY',
            'source_sha256':W8_SHA256,'pinned_r57_source_commit':R57_SHA,
            'source_unchanged':True,'saved_blend':False,'plain_keys_zero':True,
            'reference_kind':'EVALUATED_PLAIN_NEUTRAL_BEFORE_ROW',
            'complete_elbow_region':False,'anatomy_approved':False,'limitations':list(LIMITATIONS)}


def report(ref,samples):
    data={**_scope(),'reference':ref,'samples':samples}
    errors=validate_report(data)
    if errors:raise ValueError('; '.join(errors))
    return data


def _valid_edge(row,expected,reference_edge=None):
    name,pair,*_=expected
    if (not isinstance(row,dict) or row.get('name')!=name
        or not isinstance(row.get('vertex_ids'),list)
        or any(type(i) is not int for i in row['vertex_ids']) or row['vertex_ids']!=list(pair)):
        return False
    key='neutral' if reference_edge is None else 'posed'
    try:
        points=row.get(key+'_endpoints_world_m')
        if not isinstance(points,list) or len(points)!=2:return False
        points=[_vector(p,3) for p in points]
        measured=_length_mm(points);stored=row.get(key+'_length_mm')
        if not _number(stored) or stored<0 or not math.isclose(stored,measured,rel_tol=1e-10,abs_tol=1e-8):return False
        if reference_edge is None:return measured>1e-7
        ratio=row.get('length_ratio_to_neutral')
        expected_ratio=measured/reference_edge['neutral_length_mm']
        return _number(ratio) and ratio>=0 and math.isclose(ratio,expected_ratio,rel_tol=1e-10,abs_tol=1e-10)
    except (ValueError,TypeError,KeyError,OverflowError):return False


def validate_report(data):
    if not isinstance(data,dict):return ['invalid scope']
    errors=[]
    for key,value in _scope().items():
        if key=='limitations':
            if not isinstance(data.get(key),list) or any(x not in data[key] for x in value):errors.append('missing limitations')
        elif type(data.get(key)) is not type(value) or data[key]!=value:errors.append('invalid scope')
    ref=data.get('reference')
    if not isinstance(ref,dict):return errors+['invalid reference']
    digest=ref.get('topology_sha256')
    if (type(ref.get('vertex_count')) is not int or ref['vertex_count']<=max(max(t[1]) for t in TARGETS)
        or not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest)
        or ref.get('source_topology_matches_evaluated') is not True):errors.append('invalid reference topology')
    baseline=ref.get('edges')
    if (not isinstance(baseline,list) or len(baseline)!=4
        or any(not _valid_edge(row,target) for row,target in zip(baseline,TARGETS))):
        return errors+['invalid reference edges']
    samples=data.get('samples')
    if not isinstance(samples,list) or len(samples)!=9:return errors+['nine samples required']
    for i,sample in enumerate(samples):
        if not isinstance(sample,dict):errors.append('invalid sample');continue
        if type(sample.get('sample')) is not int or sample['sample']!=i:errors.append('invalid sample identity')
        if sample.get('topology_sha256')!=digest:errors.append('sample topology mismatch')
        rows=sample.get('edges')
        if (not isinstance(rows,list) or len(rows)!=4
            or any(not _valid_edge(row,target,base) for row,target,base in zip(rows,TARGETS,baseline))):
            errors.append('invalid measured edges')
    return errors


def markdown(data):
    errors=validate_report(data)
    if errors:raise ValueError('; '.join(errors))
    lines=['# W8 four pinned mesh edges during the plain row','',
           'Reference: evaluated plain neutral before the row. Ratios are not tissue strain.','',
           '| Sample | 15645–53019 ratio | 17185–44317 ratio | 29237–71026 ratio | 32352–71428 ratio |',
           '|---:|---:|---:|---:|---:|']
    for sample in data['samples']:
        ratios=' | '.join(f"{e['length_ratio_to_neutral']:.6f}" for e in sample['edges'])
        lines.append(f"| {sample['sample']} | {ratios} |")
    lines+=['','## Neutral edge lengths','']
    lines += [f"- {e['vertex_ids']}: {e['neutral_length_mm']:.8f} mm." for e in data['reference']['edges']]
    lines+=['']+[f'- {x}.' for x in data['limitations']]
    return '\n'.join(lines)+'\n'
