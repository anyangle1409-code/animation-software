"""r100 geometry-only fold-ridge rest volume on a fresh copy of r98 (weights unchanged).
usage: ridge100.py -- <r98.blend> <params.json> <mirror_idx.npy> <out.blend> <receipt.json>
params: {"ridges": {"ant": {origin, insertion, radius, amp, facing:[nx,ny,nz], facing_min, s_pow}, ...}, "smooth_iters", "cap_m"}"""
import sys, json, hashlib, bpy, numpy as np, scipy.sparse as sp
argv = sys.argv[sys.argv.index('--') + 1:]
src, prm, mir, out, rec = argv[:5]
P = json.load(open(prm)); mirror = np.load(mir)
bpy.ops.wm.open_mainfile(filepath=src)
body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']; me = body.data
n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nrm = np.array([v.normal[:] for v in me.vertices])
left = co[:, 0] < -1e-6
E = np.array([e.vertices[:] for e in me.edges])
A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr(); deg = np.asarray(A.sum(1)).ravel()
amp = np.zeros(n); info = {}
for key, F in P['ridges'].items():
    O = np.array(F['origin']); I = np.array(F['insertion']); seg = I - O
    t = np.clip((co - O) @ seg / (seg @ seg), 0, 1); dseg = np.linalg.norm(co - (O + t[:, None] * seg), axis=1)
    fac = np.clip((nrm @ np.array(F['facing'], float) - F['facing_min']) / 0.3, 0, 1)   # only outward-facing fold surface
    # ridge curve ON the skin: at stations along the fold line, the outward-facing vertex nearest to the line
    cand = left & (fac > 0.5) & (co[:, 2] > 1.15)
    pts = []
    for ts in np.linspace(0.08, 0.92, 9):
        m = cand & (np.abs(t - ts) < 0.06)
        if m.any(): pts.append(co[np.nonzero(m)[0][np.argmin(dseg[m])]])
    pts = np.array(pts)
    d = np.full(n, 9.0); tt = np.zeros(n)
    for k in range(len(pts) - 1):
        a_, b_ = pts[k], pts[k + 1]; sg = b_ - a_
        u = np.clip((co - a_) @ sg / max(sg @ sg, 1e-12), 0, 1); dd = np.linalg.norm(co - (a_ + u[:, None] * sg), axis=1)
        better = dd < d; d[better] = dd[better]; tt[better] = (k + u[better]) / (len(pts) - 1)
    r = np.clip(d / F['radius'], 0, 1); radial = 0.5 * (1 + np.cos(np.pi * r))          # rounded (cosine) cross-section
    bump = np.sin(np.pi * np.clip(tt, 0, 1)) ** F.get('s_pow', 1.0)
    info.setdefault('ridge_curves', {})[key] = pts.round(4).tolist()
    a = F['amp'] * radial * bump * fac * left * (co[:, 2] > 1.15) * (co[:, 2] < 1.50) * (np.abs(co[:, 0]) >= 0.08)
    a_peak = F['amp']
    info[key] = {'vertices': int((a > 1e-5).sum()), 'peak_m': float(a.max())}
    amp = np.maximum(amp, a)
pk = amp.max()
for _ in range(P.get('smooth_iters', 3)):                        # smooth the scalar height (no facet noise), stays local
    amp = np.where(left, 0.5 * amp + 0.5 * (A @ amp) / deg, 0)
amp *= pk / max(amp.max(), 1e-12)                                # keep the declared peak amplitude after smoothing
disp = nrm * amp[:, None]
cap = P.get('cap_m', 0.008); nd = np.linalg.norm(disp, axis=1)
disp *= np.where(nd > cap, cap / np.maximum(nd, 1e-12), 1)[:, None]
li = np.nonzero(left)[0]; disp[mirror[li]] = disp[li] * np.array([-1, 1, 1])
for kb in me.shape_keys.key_blocks:
    k = np.empty(n * 3); kb.data.foreach_get('co', k); kb.data.foreach_set('co', (k.reshape(-1, 3) + disp).ravel())
me.vertices.foreach_set('co', (co + disp).ravel()); me.update()
sc = bpy.context.scene
sc['hgpt_candidate_revision'] = 'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r100'
sc['hgpt_r100_ridge_receipt'] = json.dumps({'params': P, 'info': info})
sc['hgpt_r100_parent'] = json.dumps({'revision': 'r98', 'sha256': '89e98cc74cc7dfd17f6d5a0991a9f0f6954e8de4d99ea3d3b30be2ec617b2ce0'})
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
nd = np.linalg.norm(disp, axis=1)
R = {'parent': src, 'params': P, 'ridges': info, 'moved_vertices': int((nd > 1e-6).sum()), 'max_disp_m': float(nd.max()),
     'out_sha256': hashlib.sha256(open(out, 'rb').read()).hexdigest()}
json.dump(R, open(rec, 'w'), indent=1); print('RIDGE', json.dumps({k: R[k] for k in ('ridges', 'moved_vertices', 'max_disp_m')}))
