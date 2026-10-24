"""Temporary, restored shape-key muting at fixed native poses; never save a model.

All-keys-muted still includes rig helpers, weights, constraints and modifiers.
It is not an isolated physiological tissue or skeletal-skinning ground truth.
"""
import math

EDGES = ((15645, 53019), (17185, 44317), (29237, 71026), (32352, 71428))
FAMILY_PREFIXES = {'S7_muted': 'HGPT_S7_DELT_', 'K1_muted': 'HGPT_K1_ELBOW_',
                   'S1_muted': 'HGPT_S1_SHOULDER_', 'S3_muted': 'HGPT_S3_SHAPE_',
                   'S5_muted': 'HGPT_S5_BAKE_'}
VARIANTS = (*FAMILY_PREFIXES, 'all_nonbasis_keys_muted')
INDIVIDUAL_PREFIXES = ('HGPT_S5_BAKE_', 'HGPT_S7_DELT_')
SEED_SUFFIXES = {EDGES[0]: 'l', EDGES[1]: 'r', EDGES[2]: 'l', EDGES[3]: 'r'}


def adjacent_controls(faces, seeds=EDGES):
    """Other edges of triangles containing an entire seed; no anatomy inferred."""
    canonical = []
    for edge in seeds:
        if (len(edge) != 2 or any(type(i) is not int or i < 0 for i in edge)
                or edge[0] == edge[1]):
            raise ValueError('invalid seed edge')
        key = tuple(sorted(edge))
        if key in canonical:
            raise ValueError('duplicate seed edge')
        canonical.append(key)
    found = {edge: [] for edge in canonical}
    triangles = set()
    for face in faces:
        if (len(face) != 3 or len(set(face)) != 3
                or any(type(i) is not int or i < 0 for i in face)):
            raise ValueError('invalid triangle')
        key = tuple(sorted(face))
        if key in triangles:
            raise ValueError('duplicate triangle')
        triangles.add(key)
        for edge in canonical:
            if set(edge).issubset(face):
                found[edge].append(tuple(face))
    result = []
    for edge, incident in found.items():
        if not incident:
            raise ValueError('missing seed from frozen triangle topology')
        controls = {tuple(sorted((f[i], f[j]))) for f in incident
                    for i, j in ((0, 1), (1, 2), (2, 0))} - set(canonical)
        result.append({'seed_vertex_ids': list(edge), 'incident_triangle_count': len(incident),
                       'control_edges': [list(e) for e in sorted(controls)]})
    return result


def _points(vertices, ids):
    result = {}
    for i in ids:
        if i < 0 or i >= len(vertices):
            raise ValueError('pinned endpoint absent')
        co = tuple(float(v) for v in vertices[i])
        if len(co) != 3 or not all(math.isfinite(v) for v in co):
            raise ValueError('nonfinite or invalid endpoint coordinate')
        result[i] = co
    return result


def measure(body, evaluate, update, pose_signature, rest_vertices, observed_vertices,
            observed_faces, edges=EDGES, snapshot_sink=None):
    """evaluate() returns common-space vertices/faces; update() refreshes depsgraph.

    Caller supplies native observed/rest arrays and a full skeletal pose signature.
    Muting only removes key contributions: group comparisons are conditional,
    nonlinear modifier-stack effects, not additive causal percentages.
    """
    keys = list(body.data.shape_keys.key_blocks)
    if len(keys) < 2 or keys[0].name != 'Basis':
        raise ValueError('relative Basis and corrective keys required')
    names = [key.name for key in keys]
    if len(set(names)) != len(names):
        raise ValueError('duplicate shape-key name')
    if any(not math.isfinite(float(key.value)) for key in keys):
        raise ValueError('nonfinite shape-key value')
    if len(rest_vertices) != len(observed_vertices):
        raise ValueError('reference vertex count mismatch')
    ids = sorted({i for edge in edges for i in edge})
    rest = _points(rest_vertices, ids)
    observed = _points(observed_vertices, ids)
    reference = {edge: math.dist(rest[edge[0]], rest[edge[1]]) for edge in edges}
    if any(v <= 1e-10 or not math.isfinite(v) for v in reference.values()):
        raise ValueError('degenerate reference edge')
    faces = tuple(tuple(int(i) for i in f) for f in observed_faces)
    state = [(key, bool(key.mute), float(key.value)) for key in keys]
    individual = sorted(((key, value) for key, muted, value in state[1:]
                         if not muted and value > 1e-8
                         and key.name.startswith(INDIVIDUAL_PREFIXES)),
                        key=lambda item: item[0].name)
    individual_conditions = [
        {'condition': 'individual_key_muted::' + key.name,
         'key_name': key.name, 'actual_value': value}
        for key, value in individual]
    pose = pose_signature()
    measured = {'observed': observed}
    if snapshot_sink is not None:
        snapshot_sink('observed', observed_vertices, observed_faces)
    counts = {}
    try:
        for variant in VARIANTS:
            muted = []
            for key, original_mute, _ in state[1:]:
                selected = (variant == 'all_nonbasis_keys_muted'
                            or key.name.startswith(FAMILY_PREFIXES[variant]))
                key.mute = original_mute or selected
                if selected:
                    muted.append(key.name)
            counts[variant] = muted
            update()
            vertices, current_faces = evaluate()
            if (len(vertices) != len(observed_vertices)
                    or tuple(tuple(int(i) for i in f) for f in current_faces) != faces):
                raise ValueError('evaluated topology changed')
            measured[variant] = _points(vertices, ids)
            if snapshot_sink is not None:
                snapshot_sink(variant, vertices, current_faces)
            if pose_signature() != pose:
                raise ValueError('skeletal pose changed during key isolation')
        for item, (selected_key, _) in zip(individual_conditions, individual):
            for key, original_mute, _ in state[1:]:
                key.mute = original_mute or key is selected_key
            update()
            vertices, current_faces = evaluate()
            if (len(vertices) != len(observed_vertices)
                    or tuple(tuple(int(i) for i in f) for f in current_faces) != faces):
                raise ValueError('evaluated topology changed')
            condition = item['condition']
            measured[condition] = _points(vertices, ids)
            if snapshot_sink is not None:
                snapshot_sink(condition, vertices, current_faces)
            if pose_signature() != pose:
                raise ValueError('skeletal pose changed during key isolation')
    finally:
        for key, original_mute, _ in state:
            key.mute = original_mute
        update()
    if pose_signature() != pose:
        raise ValueError('skeletal pose not preserved')
    if any(bool(key.mute) != mute or float(key.value) != value for key, mute, value in state):
        raise ValueError('shape-key activation/mute state not preserved')
    restored_vertices, restored_faces = evaluate()
    if (len(restored_vertices) != len(observed_vertices)
            or tuple(tuple(int(i) for i in f) for f in restored_faces) != faces):
        raise ValueError('restored topology mismatch')
    restored = _points(restored_vertices, ids)
    restoration_error = max(math.dist(restored[i], observed[i]) for i in ids)
    if restoration_error > 1e-8:
        raise ValueError('restored coordinates differ from observed baseline')
    rows = []
    for edge in edges:
        lengths = {variant: math.dist(coords[edge[0]], coords[edge[1]])
                   for variant, coords in measured.items()}
        rows.append({'vertex_ids': list(edge),
                     'benchmark_rest_length_mm': round(reference[edge] * 1000, 7),
                     'length_ratios_to_benchmark_rest_NOT_strain': {
                         variant: round(value / reference[edge], 7)
                         for variant, value in lengths.items()},
                     'length_mm': {variant: round(value * 1000, 7)
                                   for variant, value in lengths.items()}})
    return {'status': 'NATIVE_FIXED_POSE_KEY_MUTING_DIAGNOSTIC_NOT_REPAIR',
            'anatomical_approval': False, 'skinning_alone_certified': False,
            'pose_and_key_state_restored': True,
            'restored_endpoint_max_error_m': restoration_error,
            'temporarily_muted_key_names': counts, 'edges': rows,
            'individual_active_key_conditions': individual_conditions,
            'limitations': [
                'All keys muted retains authored rig helpers, constraints, weights and modifiers.',
                'Relative effects at a fixed W8 press pose are not additive causality or a repair.',
                'Edge ratios are geometric descriptors, not tissue strain or acceptance limits.',
                'No anatomical side, joint axis, muscle attachment or movement approved.',
            ]}


def individual_summary(samples, tolerance=1e-7, seed_suffixes=SEED_SUFFIXES):
    """Count geometric direction-of-change; unit distance is not a quality target."""
    def counts(rows, condition):
        result = {'count': len(rows), 'closer_to_unit_ratio': 0,
                  'farther_from_unit_ratio': 0, 'unchanged': 0}
        for row in rows:
            ratios = row['length_ratios_to_benchmark_rest_NOT_strain']
            observed = abs(float(ratios['observed']) - 1.0)
            muted = abs(float(ratios[condition]) - 1.0)
            if muted < observed - tolerance:
                result['closer_to_unit_ratio'] += 1
            elif muted > observed + tolerance:
                result['farther_from_unit_ratio'] += 1
            else:
                result['unchanged'] += 1
        return result

    suffix_by_seed = {tuple(sorted(seed)): suffix for seed, suffix in seed_suffixes.items()}
    if not suffix_by_seed or any(suffix not in ('l', 'r') for suffix in suffix_by_seed.values()):
        raise ValueError('invalid authored suffix mapping')
    output = []
    for sample in samples:
        isolation = sample['corrective_edge_isolation']
        for item in isolation['individual_active_key_conditions']:
            condition = item['condition']
            groups = {}
            for role in ('ranked_seed', 'adjacent_topology_control'):
                rows = [row for row in isolation['edges'] if row.get('edge_role') == role]
                groups[role + '_edges'] = counts(rows, condition)
            parts = item['key_name'].split('_')
            if len(parts) < 3 or parts[-2] not in ('l', 'r'):
                raise ValueError('individual key lacks authored l/r suffix')
            suffix = parts[-2]
            selected_seeds = {seed for seed, value in suffix_by_seed.items() if value == suffix}
            selected_controls = set()
            for selection in isolation['adjacent_control_selection']:
                seed = tuple(sorted(selection['seed_vertex_ids']))
                if seed in selected_seeds:
                    selected_controls.update(tuple(sorted(edge))
                                             for edge in selection['control_edges'])
            seed_rows = [row for row in isolation['edges']
                         if row.get('edge_role') == 'ranked_seed'
                         and tuple(sorted(row['vertex_ids'])) in selected_seeds]
            control_rows = [row for row in isolation['edges']
                            if row.get('edge_role') == 'adjacent_topology_control'
                            and tuple(sorted(row['vertex_ids'])) in selected_controls]
            output.append({
                'sample': sample['sample'], 'condition': condition,
                'key_name': item['key_name'], 'actual_value': item['actual_value'],
                **groups,
                'matching_authored_suffix_NOT_anatomical_side': {
                    'suffix': suffix,
                    'ranked_seed_edges': counts(seed_rows, condition),
                    'adjacent_topology_control_edges': counts(control_rows, condition),
                },
            })
    return {
        'status': 'NATIVE_INDIVIDUAL_KEY_GEOMETRY_SUMMARY_NOT_REPAIR',
        'anatomical_approval': False,
        'unit_ratio_is_not_anatomical_target': True,
        'authored_suffix_scope_is_anatomical_side': False,
        'individual_conditions': output,
    }


def individual_markdown(summary):
    lines = [
        '# W8 individual active S5/S7 key isolation', '',
        '**NATIVE FIXED-POSE GEOMETRY — NOT anatomical improvement, repair or approval.**', '',
        '| Sample | Active key muted | Value | Authored suffix | Local seed closer / farther / same | Local adjacent closer / farther / same |',
        '|---:|---|---:|---:|---:|---:|',
    ]
    for row in summary['individual_conditions']:
        local = row['matching_authored_suffix_NOT_anatomical_side']
        seed = local['ranked_seed_edges']
        adjacent = local['adjacent_topology_control_edges']
        lines.append('| {} | {} | {:.6f} | {} | {} / {} / {} | {} / {} / {} |'.format(
            row['sample'], row['key_name'], row['actual_value'], local['suffix'],
            seed['closer_to_unit_ratio'], seed['farther_from_unit_ratio'], seed['unchanged'],
            adjacent['closer_to_unit_ratio'], adjacent['farther_from_unit_ratio'],
            adjacent['unchanged']))
    lines += ['', 'The l/r scope is an authored key suffix, NOT independently reviewed anatomical laterality.',
              'Closer to a unit edge ratio is only a geometric descriptor; it is not a tissue-safety or anatomy criterion.',
              'Each condition temporarily mutes one active unmuted S5/S7 key and restores the original pose/key state.', '']
    return '\n'.join(lines)


def markdown(samples):
    lines = ['# W8 fixed-pose corrective key isolation', '',
             '**NATIVE GEOMETRY DIAGNOSTIC — NOT ANATOMICAL APPROVAL OR REPAIR.**', '',
             '| Press sample | Edge IDs | Observed / rest | S7 muted / rest | K1 muted / rest | All keys muted / rest |',
             '|---|---|---:|---:|---:|---:|']
    for sample in samples:
        for row in sample['corrective_edge_isolation']['edges']:
            if row.get('edge_role') == 'adjacent_topology_control':
                continue
            values = row['length_ratios_to_benchmark_rest_NOT_strain']
            lines.append('| {} | {} | {:.6f} | {:.6f} | {:.6f} | {:.6f} |'.format(
                sample['sample'], row['vertex_ids'], values['observed'],
                values['S7_muted'], values['K1_muted'], values['all_nonbasis_keys_muted']))
    lines += ['', '## Additional populated shoulder-family controls', '',
              '| Press sample | Edge IDs | S1 muted / rest | S3 muted / rest | S5 muted / rest |',
              '|---|---|---:|---:|---:|']
    for sample in samples:
        for row in sample['corrective_edge_isolation']['edges']:
            if row.get('edge_role') == 'adjacent_topology_control':
                continue
            values = row['length_ratios_to_benchmark_rest_NOT_strain']
            lines.append('| {} | {} | {:.6f} | {:.6f} | {:.6f} |'.format(
                sample['sample'], row['vertex_ids'], values['S1_muted'],
                values['S3_muted'], values['S5_muted']))
    lines += ['', 'All-keys-muted retains rig helpers, weights, constraints and modifiers.',
              'These ratios are geometry, not tissue strain, safe limits or additive causal percentages.',
              'Original key state, endpoint coordinates and skeletal pose are checked after restoration.',
              'No joint frame, anatomical side, muscle attachment, generic motion or repair approved.', '']
    return '\n'.join(lines)
