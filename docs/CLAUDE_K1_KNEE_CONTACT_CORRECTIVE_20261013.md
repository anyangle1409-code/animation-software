# K1: experimental hinge contact correctives — knee and elbow (Claude, 13–14 Oct 2026)

- **Branch:** `claude/movement-benchmarks-20261013` (draft PR #113).
- **Script:** `scripts/build_original_knee_contact_corrective_blender.py`.
- **Tests:** `scripts/blender_tests/test_original_knee_contact_corrective.py` (7 native tests pass, knee and elbow; run in the benchmark CI workflow). Run with `-- --hinge knee|elbow`.
- **Evidence:** `ORIGINAL_V1_WORK/anatomy/audit/claude_k1/` (report + phone sheet).

**Scope:** a review-only engineering candidate on the unchanged original male (a003 `670a37bf…cbbe56`, 67-joint rig, existing weights).
- The keys exist **in memory only**: nothing is written to the blend (a test checks its hash), and production weights and keys are untouched.
- The contact model is an assumption, not tissue mechanics. There is no anatomy, deformation, GLB or clinical approval.

## Why the knee, and why it can work where the shoulder could not

M1/M2 showed calf/thigh interpenetration at deep knee flexion: squat 72, lunge 42 and single-leg stance 42 pairs per side.

- **The knee is well conditioned.** It is a single-plane hinge, so its blended skinning matrices are well conditioned: the smallest singular value equals cos(θ/2), i.e. **0.71 / 0.57 / 0.42 at 90 / 110 / 130°**.
- **The shoulder is not.** Shoulder-top skin reaches 0.0024 (W2/#112), so a bounded rest-space corrective cannot reach the posed target there.
- **So at the knee** a rest-space corrective reaches its posed target, amplified at most 2.4×.

## Method (per key 90, 110 and 130°, per side, pure knee flexion)

1. **Contact plane:** the plane through the knee-joint centre that bisects the flexion angle.
2. **Flatten:** posterior skin within 0.30 m of the knee is split into thigh and calf sides by its rest thigh-vs-shin weight. Each side is moved along the plane normal to ±2 mm of the plane.
3. **Taper:** the displacement is extended harmonically over 4 rings, falling to zero at the outer ring, so there is no seam.
4. **Restore volume:** the removed volume is restored by a normal offset of the taper band; the contact skin stays on the plane.
5. **Map to rest:** through each vertex's blended LBS matrix, with no damping, and capped at 40 mm. The 130° key needs 37.6 mm; a 30 mm cap clipped 40 vertices and left 128 instead of 36 pairs at 130°.
6. **Drive:** keys `HGPT_K1_KNEE_<side>_<deg>` follow the measured knee flexion per side, using piecewise-linear hats: 0 at or below 60°, a partition of unity from 90°, and clamped above 130°.

| Key | Contact vertices per side | Max posed push | Volume removed → after restoration | Band offset | σmin | Max rest delta |
|---|---|---|---|---|---|---|
| 90° | 72 | 5.5 mm | 0.06% → 0.000% | 0.7 mm | 0.707 | 6.7 mm |
| 110° | 131 | 16.9 mm | 0.45% → 0.014% | 3.9 mm | 0.574 | 18.0 mm |
| 130° | 199 | 36.8 mm | 1.40% → 0.10% | 10.0 mm | 0.423 | 37.6 mm |

## Results (before → with K1)

**Pure knee sweep, both legs:**

| Knee flexion | Self-intersecting pairs | Collapsed faces | Stretch > 2 | Body volume Δ % |
|---|---|---|---|---|
| 0–70° | 0 → 0 (keys inactive or zero) | 0 → 0 | 0 → 0 | unchanged |
| 80° | 34 → **0** | 0 → 0 | 0 → 0 | −0.17 → −0.17 |
| 90° | 84 → **0** | 0 → 0 | 0 → 0 | −0.26 → −0.26 |
| 100° | 120 → **0** | 0 → 0 | 0 → 0 | −0.35 → −0.34 |
| 110° | 144 → **0** | 0 → **2** | 0 → 0 | −0.44 → −0.43 |
| 120° | 176 → **0** | 2 → 2 | 0 → 0 | −0.54 → −0.49 |
| 130° | 208 → **36** | 2 → **4** | 0 → 0 | −0.63 → −0.53 |

**Benchmarks, keys driven every frame:**

| Benchmark | Worst pairs | End-frame pairs | Worst collapse | Note |
|---|---|---|---|---|
| Squat | 371 → 227 | 371 → 227 | 26 → 28 | All 144 calf/thigh pairs are gone. The rest are hip-flexion folds (thigh/thigh 61 per side, pelvis/thigh 51–54), outside K1's scope. |
| Lunge | 84 → 60 | 84 → **0** | 0 → 0 | The worst frame is now the early thumb/thigh contact (rest-pose hand proximity). |
| Single-leg stance | 60 → 60 | 42 → **0** | 0 → 0 | Same: the worst frame is the early thumb/thigh contact. |

**Visible:** at 110°, the compressed calf shows a flat contact band with a sharp edge where it meets the taper, and a crease behind the knee (see the phone sheet). The skin no longer passes through itself, but the band edge is harder than real soft tissue. A smoother contact profile, such as a curved contact surface or a longer taper, is the next refinement.

## Elbow (the same method, 14 Oct)

**Generalisation:** the script now takes hinge configurations. The knee results are reproduced exactly after the refactor.
- **Elbow configuration:** upper-arm vs forearm (+ the two forearm twist groups); keys at 90, 120 and 140°; zone 0.22 m; flexion = forearm −X.
- **Conditioning:** σmin = cos(θ/2), i.e. 0.71 / 0.50 / 0.34.
- **Evidence:** `claude_k1/elbow_contact_corrective_report.json` and `elbow_contact_corrective_phone_sheet.jpg`.

| Elbow flexion | Crease pairs (both arms) | Collapsed faces | Stretch > 2 | Body volume Δ % |
|---|---|---|---|---|
| 80° | 80 → **0** | 0 → 0 | 0 → 0 | −0.31 → −0.30 |
| 90° | 124 → **0** | 0 → 0 | 0 → 0 | −0.35 → −0.35 |
| 100° | 140 → **0** | 0 → 0 | 0 → 0 | −0.40 → −0.38 |
| 110° | 168 → **0** | 4 → **0** | 0 → 0 | −0.43 → −0.41 |
| 120° | 186 → **0** | 0 → **8** | 0 → 0 | −0.47 → −0.43 |
| 130° | 208 → **0** | 12 → 8 | 0 → **8** | −0.50 → **−0.59** |
| 140° | 238 → 2 | 20 → 14 | 0 → **84** | −0.52 → **−0.73** |

- **Benchmarks (worst pairs):**
  - Bent-over row: 156 → **16**.
  - Grip: 150 → **26**.
  - All elbow-crease classes are gone. What remains is finger/hand self-contact in the grip, and shoulder/neck pairs in the row.
- **The 140° key is over-constrained.** Flattening removes 1.1% of body volume, the 10 mm band offset and the 40 mm rest cap both bind (14 vertices clipped), and new stretch appears. 140° is near the CDC passive mean (144.6°), where real tissue compression is not planar.
- **Visible at 120° — a failure despite the metric:** the pair count is 0, but the renders show a **pinched elbow tip and a ridge on the upper arm**. That looks worse than the uncorrected crease. At 90° the change is mild and acceptable.
  - **Usable range on the evidence: up to about 110°**, which covers the row (100°) and the grip (90°).
  - Above that, a curved contact surface (or a compression profile from a source) is needed, not a plane.

## Rejected: the same method at the hip (squat fold), measured 14 Oct

**Configuration (scratch, not committed as a feature):**
- proximal side: `pelvis` + `spine_01`;
- distal side: `thigh_<s>`;
- flexion = thigh −X;
- keys at 90, 110 and 130°; zone 0.30 m.

**Result — pure hip flexion, both legs, before → after:**

| Hip flexion | Pairs | Collapse | Stretch > 2 | Volume Δ % |
|---|---|---|---|---|
| 90° | 0 → 49 | 2 → 16 | 46 → 78 | −2.55 → −2.55 |
| 110° | 228 → 379 | 28 → 46 | 62 → 146 | −3.80 → −4.65 |
| 130° | 266 → 776 | 24 → 28 | 76 → 263 | −5.02 → −6.14 |

**Worse at every angle.** 12, 173 and 440 rest deltas hit the cap at 90, 110 and 130°, and the result is left/right asymmetric.

**Why:**
- The abdomen/groin fold is not a two-segment contact about one hinge.
- Pelvis skin near the midline belongs to both sides' zones.
- Much of the contact is thigh-on-thigh skin, which the proximal/distal weight split cannot separate.

**What the hip fold needs instead:** a three-body contact model (trunk, left thigh, right thigh) or a different skinning approach. It is not pursued here.

## Limits and next

- **The bisector plane is assumed.** Real calf/hamstring compression is not symmetric, and there is no sourced contact surface or pressure data.
- **130° keeps 36 pairs and 4 collapsed faces.** The benchmarks stop at 110°.
- **It changes the runtime contract.** This is a pose-space corrective: shipping it would add 6 shape keys and a driver per knee. The Lane G GLB carries six zero-weight morphs, and the runtime has no knee-driven morphs, so it needs the same owner + Lane G decision as W3.
- **Next:**
  - a hip-flexion fold corrective (squat thigh/thigh and pelvis/thigh) using the same method;
  - a curved contact surface for elbow flexion above about 110° and for the knee band edge.
