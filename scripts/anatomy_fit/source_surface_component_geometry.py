#!/usr/bin/env python3
"""Read-only, exact-vertex source shell geometry in UNKNOWN source units.

Area/volume centres are mathematical diagnostics, never joint centres.
Closed topology does not rule out self-intersection or validate anatomy.
No download, repair, island deletion, scaling or registration is performed.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys

MAX_BYTES = 16_000_000


def sub(a, b):
    return tuple(a[j]-b[j] for j in range(3))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def analyze(raw: bytes) -> dict:
    if not 134 <= len(raw) <= MAX_BYTES:
        raise ValueError('Truncated or oversized binary STL')
    n = struct.unpack_from('<I', raw, 80)[0]
    if n == 0 or len(raw) != 84+50*n:
        raise ValueError('STL triangle count/length mismatch')
    vertices, lookup, roots, faces = [], {}, [], []
    degenerate = 0

    def vertex(p):
        if p not in lookup:
            lookup[p] = len(vertices)
            roots.append(len(vertices))
            vertices.append(p)
        return lookup[p]

    def find(i):
        while roots[i] != i:
            roots[i] = roots[roots[i]]
            i = roots[i]
        return i

    for i in range(n):
        values = struct.unpack_from('<9f', raw, 96+50*i)
        if not all(math.isfinite(x) for x in values):
            raise ValueError('Nonfinite source vertex')
        a, b, c = [tuple(values[j:j+3]) for j in (0, 3, 6)]
        normal = cross(sub(b, a), sub(c, a))
        if all(x == 0 for x in normal):
            degenerate += 1
            continue
        ids = tuple(vertex(p) for p in (a, b, c))
        root = find(ids[0])
        for other in ids[1:]:
            roots[find(other)] = root
        faces.append(ids)
    if not faces:
        raise ValueError('No nondegenerate source faces')
    groups = defaultdict(list)
    for f in faces:
        groups[find(f[0])].append(f)
    results = []
    for component_faces in groups.values():
        ids = sorted({i for f in component_faces for i in f})
        lo = [min(vertices[i][j] for i in ids) for j in range(3)]
        hi = [max(vertices[i][j] for i in ids) for j in range(3)]
        origin = vertices[ids[0]]
        edges = defaultdict(list)
        areas, area_moments, volumes, volume_moments = [], [[], [], []], [], [[], [], []]
        for f in component_faces:
            a, b, c = [vertices[i] for i in f]
            normal = cross(sub(b, a), sub(c, a))
            area = math.sqrt(math.fsum(x*x for x in normal))/2
            areas.append(area)
            # Moments are expressed relative to a component-local origin.
            ar, br, cr = [sub(p, origin) for p in (a, b, c)]
            for j in range(3):
                area_moments[j].append(area*math.fsum((ar[j], br[j], cr[j]))/3)
            vol = math.fsum(x*y for x, y in zip(ar, cross(br, cr)))/6
            volumes.append(vol)
            for j in range(3):
                volume_moments[j].append(vol*math.fsum((ar[j], br[j], cr[j]))/4)
            for a_id, b_id in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
                edges[min(a_id, b_id), max(a_id, b_id)].append(1 if a_id < b_id else -1)
        boundary = sum(len(e) == 1 for e in edges.values())
        overused = [edge for edge, incident in edges.items() if len(incident) > 2]
        winding = sum(len(e) == 2 and sum(e) != 0 for e in edges.values())
        area, vol = math.fsum(areas), math.fsum(volumes)
        volume_eligible = boundary == 0 and not overused and winding == 0 and vol != 0
        results.append({
            'nondegenerate_faces': len(component_faces),
            'bbox_min_source_units': lo, 'bbox_max_source_units': hi,
            'bbox_extent_source_units': [hi[j]-lo[j] for j in range(3)],
            'surface_area_source_units_squared': area,
            'surface_area_centroid_source_units': [origin[j]+math.fsum(area_moments[j])/area for j in range(3)],
            'boundary_edges': boundary, 'nonmanifold_edges': len(overused),
            'same_direction_paired_edges': winding,
            'nonmanifold_edge_locations_source_units': sorted(
                [list(vertices[a]), list(vertices[b])] for a, b in overused),
            'signed_algebraic_volume_source_units_cubed': vol if volume_eligible else None,
            'algebraic_volume_centroid_source_units':
                [origin[j]+math.fsum(volume_moments[j])/vol for j in range(3)] if volume_eligible else None,
            'self_intersection_checked': False,
            'anatomical_identity_or_contact_accepted': False,
        })
    results.sort(key=lambda c: (-c['nondegenerate_faces'], c['bbox_min_source_units']))
    declarations=set(re.findall(rb'\bSPACE=([A-Za-z]+)',raw[:80]))
    declared=(next(iter(declarations)).decode('ascii')
              if len(declarations)==1 and declarations <= {b'LPS',b'RAS'}
              else 'AMBIGUOUS_OR_UNSUPPORTED' if declarations else 'UNSPECIFIED')
    return {
        'schema_version': 1, 'kind': 'SOURCE_EXACT_VERTEX_COMPONENT_GEOMETRY_DIAGNOSTIC',
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'source_header_coordinate_declaration': declared,
        'source_frame_registration_verified': False,
        'raw_faces': n, 'degenerate_faces': degenerate,
        'component_definition': 'Nondegenerate triangles connected by exact float32 vertex positions; point-connected shells remain one group',
        'components': results,
        'centroid_definitions': {
            'surface': 'Triangle-area-weighted triangle centres',
            'volume': 'Signed tetrahedral first moment divided by signed volume, only when edge closure/winding checks pass and algebraic volume is nonzero; self-intersection is NOT excluded',
        },
        'source_units_or_frame_verified': False,
        'anatomical_centroids_accepted': False,
        'canonical_promotion_allowed': False,
        'source_geometry_modified': False,
    }


def require_private(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == Path(resolved.anchor):
        raise ValueError('Filesystem root forbidden')
    for ancestor in (resolved, *resolved.parents):
        if (ancestor/'.git').exists():
            raise ValueError('Source/output must remain outside every Git checkout')
    return resolved


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True, type=Path)
    ap.add_argument('--sha256', required=True)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    try:
        src, out = require_private(args.input), require_private(args.output)
        if args.input.is_symlink() or args.output.is_symlink() or out.exists():
            raise ValueError('Symlink source/output or existing output refused')
        if not re.fullmatch('[0-9a-f]{64}', args.sha256):
            raise ValueError('Invalid source SHA256')
        if src.stat().st_size > MAX_BYTES:
            raise ValueError('Oversized source STL')
        raw = src.read_bytes()
        if hashlib.sha256(raw).hexdigest() != args.sha256:
            raise ValueError('Source SHA256 mismatch')
        report = analyze(raw)
        encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+'\n'
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('x', encoding='utf-8') as fp:
            fp.write(encoded)
        print(json.dumps({'raw_faces': report['raw_faces'], 'components': len(report['components']), 'canonical_promotion_allowed': False}))
        return 0
    except (ValueError, OSError) as exc:
        print('Source component QA refused: '+str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
