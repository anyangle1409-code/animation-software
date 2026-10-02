# ORIGINAL v1 — generic shoulder/axilla corrective deformation (design, written before implementation)

Status: DESIGN · 2026-10-02 · authorised by the owner brief of the same date · skeleton rev2c stays LOCKED (this layer sits on top of it)

## Why a corrective, with evidence

Linear blend skinning (LBS) with any weight field on the locked skeleton cannot satisfy both the gates and the visual form at the axilla. The frontier was measured, not assumed:
r45 (gate-only weights) lateral-torso **tent flaps** (326 torso vertices > 10 cm from their trunk-driven position), r46 (hard trunk anchoring) **axilla web tears** (shoulder stretch 7.9×),
r47/r48 (moderate anchoring) reduced flaps, jagged edges, 3 development failures (torso edge stretch 5.12 / 6.34 / 5.84, gate 5.0). Continuous-arc audit of r48
(`ORIGINAL_V1_WORK/candidates/repair_checks/shoulder_corrective_20261002/r48_arc_before.json`): the lateral-torso drift from the trunk-driven position grows ≈ linearly with humerothoracic elevation
(0.026 m at 21°, 0.052 m at 41°, 0.101 m at 83°, 0.188 m at 166° in press_top; 0.232 m for the high-scapular-share variant); more than 5 cm of drift appears from ≈ 40° (first vertices) and flaps larger than 10 cm from ≈ 80°; torso edge stretch crosses 3 at ≈ 83° and the 5.0 gate at ≈ 160° (press_top) / ≈ 140° (rhythm).

Real skin does not behave like that: scapular-region skin stretch at maximum elevation is about 48–61 % (peak around the axillary fold), spread over a wide area with a roughly constant gradient
(PMC8434297; PMC11835493 for trunk skin stretch of 22–29 % spread over large areas; PubMed 30107567 sternal skin strain 12–15 % at 90–180° flexion; shoulder kinematics PMC3377910, PMC9246406, PMC6620199). Skin slides and unfolds over the thorax; it neither rides up as a flap nor tears.
A corrective that makes the posed surface look like that is anatomically motivated, not decorative.

## 1. Driver variables

* **Humerothoracic elevation** `θ_side` (deg): angle between the humerus direction (upperarm bone, armature space) and the **downward trunk axis** (−direction of `spine_03`), per side, computed in the armature frame, so it already contains clavicle + scapula + glenohumeral contributions, is independent of world orientation (a push-up or a hanging body behaves the same as an upright one) and needs no exercise name.
  Exact definition in `scripts/audit_original_v1_shoulder_arc_blender.py::elevation()`; closed form, no solver.
* Second driver only if one key proves insufficient: scapular upward rotation `φ_side` (the rhythm variants at the same θ carry different scapular share). Start with one key per side; add the second only on evidence.

## 2. Activation function

`a(θ) = S((θ − θ0) / (θ1 − θ0))`, `S(t) = 0` for t ≤ 0, `3t² − 2t³` for 0 < t < 1, `1` for t ≥ 1 (C¹-continuous, monotone, no pop).
`θ0`, `θ1` are DERIVED from the arc audit, not guessed: θ0 ≈ **40°** (first elevation at which any torso vertex is dragged more than 5 cm from its trunk-driven position in any pose), θ1 ≈ **150°** (elevation by which the drift/stretch curves reach their working maximum for the overhead poses). Both are stored in the corrective spec and can be re-derived by re-running the audit; they are validated by the continuous sampling below, not assumed.

## 3. Affected anatomical region

Lateral torso below the armpit (serratus / latissimus / teres region), the axillary web between the arm and the chest wall, the pectoral insertion and the posterior scapular surface, and the underside/deltoid transition of the upper arm — i.e. the vertices that the skinning solver already treats as the shoulder zone (torso + shoulder + arm vertices within ≈ 0.30 m of the glenohumeral joint, plus any vertex carrying scapula weight). Neck, hands, legs, face untouched.

## 4. Vertex / edit mask

Declared before any solve, committed (`repair_preparation/<rN>_shoulder_corrective_declared/`): explicit vertex ids of the LEFT-owned set (x ≤ 0 incl. the midline) with the rule that produced them; the right side is derived by mirror. Allowed change: **rest-space displacement vectors of those vertices only** — no weights, topology, geometry at rest, bones or other vertices change.

## 5. Symmetry rule

The left key stores a displacement `D_L` for left-owned vertices; the right key is `D_R(v) = S ⊙ D_L(m(v))` with `S = (−1, 1, 1)` and `m` the exact rest-space mirror map. Both keys are active independently, each driven by its own side's `θ`. Midline vertices receive both keys and therefore a symmetric net displacement (x component cancels). Symmetry is by construction and audited (max asymmetry ≤ 1e-6 m).

## 6. Interpolation behaviour

The posed rest-space position is `rest + a(θ_L)·D_L + a(θ_R)·D_R`, then ordinary skinning. Because skinning is linear in the rest position, the effect is a pose-space displacement that varies smoothly with `θ` through `a`. Intermediate positions are therefore interpolations by construction (no pop); the continuous-arc audit samples 0, 12.5, 25 … 100 % of each overhead movement and a finer sampling across the θ0/θ1 blend zones.

## 7. Runtime representation

Deterministic project-owned data, no engine feature required:

```
hgpt_shoulder_corrective_v1 {
  driver: { type: "humerothoracic_elevation", humerus_bone: "upperarm_<s>", trunk_bone: "spine_03", frame: "armature" },
  activation: { type: "smoothstep", theta0_deg, theta1_deg },
  mirror: { rule: "x -> -x", map: mirror vertex index list },
  left: { vertices: [ids], delta_m: [[dx,dy,dz], ...] }      // rest-space metres, float32
}
```
Blender implements it as one shape key per side on the body mesh, set each evaluation by the pose script from the closed-form `θ` (same mechanism as the twist helpers; no Blender drivers/constraints). The standalone engine reproduces it as `vertex += a(θ)·delta` before skinning (morph-target add). The spec file is exported with the candidate (`ORIGINAL_V1_WORK/shoulder_corrective_<rN>.json`).

## 8. Why this is generic, not an exercise workaround

The only inputs are two bone directions of the locked skeleton; the exercise name never enters. The same correction fires for any human movement that raises the arm relative to the trunk by the same amount (press, pull-up, row recovery, reach, hang, handstand-like loading), on either side, in any body orientation. It is anatomical skin sliding/unfolding at the axilla expressed as a pose-space displacement, calibrated on six overhead stress poses and their continuous arcs (not only end poses) and validated on poses it was not solved on.

## Authoring (first-party solve)

`scripts/optimize_original_v1_shoulder_corrective.py` (numpy only): minimises over `D_L` — edge stretch/compression hinges (targets inside the gates with margin; real skin strain data support targets well below the 5.0 gate), a trunk-anchoring form prior for lateral-torso skin (so it neither tents nor tears), graph smoothness of `D`, a small magnitude regulariser — over the 15 stress poses plus continuous-arc samples of the six shoulder poses, using the exact LBS model reconstructed from the candidate (reproduces Blender to ~1e-7). Mirror-symmetric parameterisation. Candidate = r48 + shape keys (new numbered candidate); the full evidence run, change audit (only declared vertices' shape-key data), arc audit and images follow.
