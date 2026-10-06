"""r98 localized axillary support topology + rest-shape (slit opening / apex rounding) on the r95 working parent.

usage: build98.py -- <parent.blend> <params.json> <out.blend> <receipt.json>
Topology: closed quad rings selected by (seed vertex id, approximate direction) on r95 ids, mirrored by the r95 mirror map;
each ring edge split once at its midpoint (all-quad, original ids/positions unchanged, new vertex weights / shape-key points /
attributes interpolated by bmesh). Rest shape: left slit-wall vertices displaced along -normal with a smooth falloff, the
displacement diffused over the surface, mirrored to the right, applied identically to Basis and every shape key (corrective
deltas unchanged)."""
import sys, json, hashlib
import bpy, bmesh, numpy as np
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
src, prm_path, out, receipt = argv[:4]
P = json.load(open(prm_path))
bpy.ops.wm.open_mainfile(filepath=src)
body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
me = body.data
n0 = len(me.vertices)
mirror0 = np.load(P['mirror_idx_r95'])
assert len(mirror0) == n0

bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()

def ring(e0):
    f0 = list(e0.link_faces)
    seq_all = [e0]
    for sf in f0[:2]:
        e, f, seq = e0, sf, []
        while len(f.verts) == 4:
            l = [l for l in f.loops if l.edge == e][0]
            opp = l.link_loop_next.link_loop_next.edge
            if opp == e0:
                return seq_all + seq, True
            seq.append(opp)
            nf = [x for x in opp.link_faces if x != f]
            if not nf or len(seq) > 400: break
            e, f = opp, nf[0]
        seq_all = seq_all + seq
    return seq_all, False

def seed_edge(vi, d):
    v = bm.verts[vi]; d = np.array(d) / np.linalg.norm(d)
    best = max(v.link_edges, key=lambda e: np.dot((np.array(e.other_vert(v).co) - np.array(v.co)) / e.calc_length(), d))
    return best

split = {}
rings_info = []
for spec in P.get('rings', []):
    for side in ('l', 'r') if spec.get('mirror', True) else ('l',):
        vi = spec['seed'] if side == 'l' else int(mirror0[spec['seed']])
        d = np.array(spec['dir'], float) * (np.array([-1, 1, 1]) if side == 'r' else 1)
        r, closed = ring(seed_edge(vi, d))
        assert closed, f'ring from {vi} not closed'
        key = frozenset(e.index for e in r)
        if any(key == frozenset(x['edges']) for x in rings_info):
            continue                                   # torso-wide ring already selected from the other side
        rings_info.append({'name': spec['name'], 'side': side, 'seed': vi, 'edges': sorted(key), 'length': len(r)})
        for e in r: split[e.index] = e
edges = list(split.values())
res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=False, smooth=0.0)
bm.verts.ensure_lookup_table()
assert all(len(f.verts) == 4 for f in bm.faces), 'non-quad face after subdivision'
bm.to_mesh(me); bm.free(); me.update()
n1 = len(me.vertices)
# new (interpolated) vertices: at most 4 deform influences, renormalized (runtime limit)
bone_names = {b.name for b in bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL'].data.bones}
gname = {g.index: g.name for g in body.vertex_groups}
pruned = 0
for v in me.vertices[n0:]:
    bw = sorted([(g.weight, g.group) for g in v.groups if gname[g.group] in bone_names and g.weight > 0], reverse=True)
    if len(bw) > 4:
        keep = bw[:4]; s = sum(w for w, _ in keep)
        for w, gidx in bw[4:]: body.vertex_groups[gname[gidx]].remove([v.index])
        for w, gidx in keep: body.vertex_groups[gname[gidx]].add([v.index], w / s, 'REPLACE')
        pruned += 1

# ---- mirror map for the new topology
co = np.array([v.co[:] for v in me.vertices])
kd = KDTree(n1)
for i, c in enumerate(co): kd.insert(c, i)
kd.balance()
mirror = np.array([kd.find((-c[0], c[1], c[2]))[1] for c in co])
merr = max((co[mirror[i]] - co[i] * np.array([-1, 1, 1])).__abs__().max() for i in range(n1))

# ---- rest-shape: open the axillary slit and round its apex (left computed, mirrored)
open_info = {}
if 'open' in P:
    O = P['open']
    gi = {g.name: g.index for g in body.vertex_groups}
    W = np.zeros((n1, len(gi)))
    for v in me.vertices:
        for g in v.groups: W[v.index, g.group] = g.weight
    arm = W[:, gi['upperarm_l']] + W[:, gi.get('forearm_l', gi['upperarm_l'])] * 0
    nrm = np.array([v.normal[:] for v in me.vertices])
    L = (co[:, 0] < -0.09) & (co[:, 2] > O['z_min']) & (co[:, 2] < O['z_max'])
    arm_side = L & (arm > 0.5); trunk_side = L & (arm <= 0.5) & (co[:, 0] > -0.2)
    from scipy.spatial import cKDTree
    ta, tt = cKDTree(co[arm_side]), cKDTree(co[trunk_side])
    disp = np.zeros((n1, 3))
    for mask, other, amt, key in ((trunk_side, ta, O['trunk_m'], 'trunk'), (arm_side, tt, O['arm_m'], 'arm')):
        idx = np.nonzero(mask)[0]
        d, j = other.query(co[idx])
        ocoords = (co[arm_side] if key == 'trunk' else co[trunk_side])[j]
        to_other = ocoords - co[idx]; to_other /= np.maximum(np.linalg.norm(to_other, axis=1)[:, None], 1e-9)
        facing = np.einsum('ij,ij->i', nrm[idx], to_other)
        t = np.clip((O['reach'] - d) / (O['reach'] - O['full']), 0, 1); f = t * t * (3 - 2 * t)
        f *= np.clip((facing - 0.2) / 0.4, 0, 1)            # only surfaces that face the opposite wall of the slit
        # taper toward the region's vertical limits
        zt = np.clip((co[idx, 2] - O['z_min']) / 0.05, 0, 1) * np.clip((O['z_max'] - co[idx, 2]) / 0.03, 0, 1)
        disp[idx] = -nrm[idx] * (amt * f * zt)[:, None]
        open_info[key + '_moved'] = int((f * zt > 0.01).sum())
    # diffuse displacement over the surface graph (keeps the rest surface smooth at the band edge)
    E = np.array([e.vertices[:] for e in me.edges])
    import scipy.sparse as sp
    A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n1, n1)).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    band = L.copy()
    for _ in range(O.get('diffuse_iters', 4)):
        avg = (A @ disp) / deg[:, None]
        disp[band] = 0.5 * disp[band] + 0.5 * avg[band]
    # apex rounding: tangential-free Laplacian relaxation of apex vertices (both walls close together near the top of the slit)
    if O.get('apex_relax_iters', 0):
        cur = co + disp
        apex = np.zeros(n1, bool)
        ia, it = np.nonzero(arm_side)[0], np.nonzero(trunk_side)[0]
        da, _ = tt.query(co[ia]); dt, _ = ta.query(co[it])
        apex[ia[da < O['apex_dist']]] = True; apex[it[dt < O['apex_dist']]] = True
        apex &= co[:, 2] > O['apex_z_min']
        for _ in range(O['apex_relax_iters']):
            avg = (A @ cur) / deg[:, None]
            cur[apex] = cur[apex] + O.get('apex_relax_lambda', 0.4) * (avg[apex] - cur[apex])
        disp = cur - co
        open_info['apex_vertices'] = int(apex.sum())
    # mirror left -> right (exact symmetry)
    left = co[:, 0] < -1e-6
    li = np.nonzero(left)[0]
    disp[mirror[li]] = disp[li] * np.array([-1, 1, 1])
    if 'max_disp_m' in O:                                # declared cap: smooth radial clamp (tanh), keeps direction
        nd = np.linalg.norm(disp, axis=1); cap = O['max_disp_m']
        sc_ = np.where(nd > 1e-12, cap * np.tanh(nd / cap) / np.maximum(nd, 1e-12), 1.0)
        disp *= sc_[:, None]
    open_info['max_disp_m'] = float(np.linalg.norm(disp, axis=1).max())
    open_info['moved_vertices'] = int((np.linalg.norm(disp, axis=1) > 1e-5).sum())
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            k = np.empty(n1 * 3); kb.data.foreach_get('co', k); kb.data.foreach_set('co', (k.reshape(-1, 3) + disp).ravel())
    new = co + disp
    me.vertices.foreach_set('co', new.ravel())
    me.update()

bpy.context.scene['hgpt_r98_topology_rest_receipt'] = json.dumps({'rings': [{k: v for k, v in r.items() if k != 'edges'} for r in rings_info], 'open': open_info})
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
sh = hashlib.sha256(open(out, 'rb').read()).hexdigest()
rec = {'parent': src, 'params': P, 'vertices_before': n0, 'vertices_after': n1, 'new_vertices': n1 - n0,
       'rings': [{k: v for k, v in r.items() if k != 'edges'} for r in rings_info], 'split_edges': len(edges),
       'all_quads': True, 'pruned_new_vertices': pruned, 'mirror_max_err_m': float(merr), 'rest_shape': open_info, 'out_sha256': sh}
json.dump(rec, open(receipt, 'w'), indent=1)
np.save(receipt.replace('.json', '_mirror_idx.npy'), mirror)
print('BUILD', json.dumps({k: rec[k] for k in ('new_vertices', 'split_edges', 'mirror_max_err_m', 'rest_shape')}))
