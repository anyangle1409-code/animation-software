"""Localized re-skin: W = W_solve inside the edited band, W_r97 elsewhere, smooth graph-distance transition.
usage: blend_local.py rest_new.npz rest_r97.npz W_solve.npz W_r97.npz mirror_new.npy params.json out.npz
band seed = vertices whose rest position moved (> seed_mm) or that are new; core = seed dilated `core_rings`; blend over `blend_rings`."""
import sys, json, numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
rn, r7, ws, w7, mir, prm, out = sys.argv[1:8]
P = json.load(open(prm))
a = np.load(rn); b = np.load(r7); S = np.load(ws); Q = np.load(w7); mirror = np.load(mir)
n = len(a['co']); n0 = len(b['co'])
names = [str(x) for x in S['names']]; qn = [str(x) for x in Q['names']]
Wq = np.zeros((n, len(names)))
Wq[:n0] = Q['W'][:, [qn.index(x) for x in names]] if set(names) <= set(qn) else 0
moved = np.zeros(n, bool); moved[n0:] = True
moved[:n0] = np.linalg.norm(a['co'][:n0] - b['co'], axis=1) > P['seed_mm'] / 1000
moved &= a['co'][:, 2] < P.get('z_max', 9)
if n > n0:   # new vertices: r97 weights by interpolation are not defined here; they always take the solve
    pass
T = a['tris']; E = np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]
A = sp.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(n, n)).tocsr(); A = ((A + A.T) > 0).astype(float)
dist = dijkstra(A, indices=np.nonzero(moved)[0], min_only=True, unweighted=True)
c, bl = P['core_rings'], P['blend_rings']
t = np.clip((dist - c) / max(bl, 1), 0, 1); f = 1 - t * t * (3 - 2 * t)        # 1 inside core, 0 beyond core+blend
f[n0:] = 1.0
DECL = {"spine_02", "spine_03", "clavicle_l", "clavicle_r", "scapula_l", "scapula_r", "upperarm_l", "upperarm_r", "glenohumeral_half_l", "glenohumeral_half_r"}
dm = np.array([nm in DECL for nm in names])
W = f[:, None] * S['W'] + (1 - f[:, None]) * Wq
W[:, ~dm] = S['W'][:, ~dm]                      # non-declared bones: exactly the r95 values (identical in both inputs)
q = W[:, ~dm].sum(1)
# protected pruning: drop the smallest DECLARED influences until <= 4, then refill the declared share to 1 - q
for i in np.nonzero((W > 0).sum(1) > 4)[0]:
    extra = int((W[i] > 0).sum()) - 4
    cand = np.nonzero(dm & (W[i] > 0))[0]
    W[i, cand[np.argsort(W[i, cand])[:extra]]] = 0
ds = W[:, dm].sum(1)
W[:, dm] *= np.where(ds > 0, (1 - q) / np.maximum(ds, 1e-12), 0)[:, None]
asym = np.abs(f - f[mirror]).max()
changed = np.unique(np.r_[S['changed'], Q['changed']]).astype(int)
np.savez(out, W=W.astype(np.float32), names=np.array(names), changed=changed)
print('BLEND', json.dumps({'seed': int(moved.sum()), 'core': int((f >= 0.999).sum()), 'blended': int(((f > 0.001) & (f < 0.999)).sum()), 'mask_asym': float(asym), 'max_infl': int((W > 0).sum(1).max())}))
