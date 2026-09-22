# Home Gym PT — high-detail mesh candidate handoff for GPT Work (Blender)

**Repository:** `anyangle1409-code/animation-software`
**Branch:** `chatgpt/absolute-retarget-imports`
**Current HEAD:** `8aaa2ed13139f4173b8d2e0720a058b664482421`
**Shoulder-fix commit:** `eca99bb455ff42b17a8aa4476bb1d67b2eb167b0`
**Known test state:** **290 passed / 8 failed / 1 skipped**

Build a **completely separate high-detail mesh candidate**. Nothing in this package may be
overwritten, and no production file may be changed.

---

## 1. The job, in one paragraph

The shoulder *skeleton* is finished and is the reference. What remains is a **mesh/skin geometry
problem**: the deltoid does not have enough mass above the humeral head, and what mass it does have
sits in front of the bone instead of over it. So the upper arm visually begins at the top of its own
mass and reads as hanging off the **anterior face** of the shoulder rather than descending from
underneath the cap. Fix that with new anatomy and skin geometry in Blender.

---

## 2. Do not move the joint — this is settled by measurement

**Do not move the shoulder joint, the clavicle, or the upper-arm root to fix this.** The current
joint and girdle alignment is the **reference**, not a variable.

This is not a style preference. It was tested:

| Measured at Bottom | Joint at y 1412.1 | Joint moved to y 1390.5 | Change |
|---|---:|---:|---:|
| **Deltoid mass above the joint** | **7.8 mm** | **7.8 mm** | **0.0 mm** |
| Joint z | −21.9 | −22.6 | −0.7 mm |
| Humerus tilt | 3.22° | 3.24° | +0.02° |

Moving the joint **21.6 mm** changed the deltoid's relationship to it by **exactly nothing**. The
deltoid is arm-owned, so it translates rigidly with the arm root — every joint move carries its own
cap along with it. Mesh movement was measured separately and confirms it: 3,650 vertices moved, and
the 255 arm-owned vertices moved a mean of **20.73 mm** for a 21.6 mm joint move, one-for-one.

A joint-seating candidate (clavicle tail y 1.440 → 1.420) was built, measured and **rejected**: it
does not change the junction and renders worse, dropping the arm away from the trapezius. See
`renders/shoulder-junction/` and `docs/SHOULDER_JUNCTION_DIAGNOSIS.md`.

Also ruled out: the rest humerus is vertical by construction (head and tail share the same z), so
its orientation cannot add mass above the joint; and canonical `upperarm_l.head` does not reach the
posed joint at all — moving it down 25 mm left the joint unchanged to the tenth of a millimetre.

---

## 3. The mesh target — measurable

| Measure | Current | Target |
|---|---:|---|
| **Deltoid mass above the joint centre** | **7.8 mm** | **25–35 mm** |
| **Deltoid apex sagittal position (z)** | **+4.8 mm** | **≈ −21.9 mm or posterior** |
| Joint centre sagittal position (z) | **−21.9 mm** | unchanged — this is the reference |

In words:

- The deltoid must **wrap over the humeral head** and reach up toward the acromion, rising 25–35 mm
  above the joint centre instead of the current 7.8 mm.
- The visible deltoid apex must come back from **+4.8 mm** to **approximately the joint's −21.9 mm,
  or behind it**. Today the top of the arm sits 26.7 mm *in front of* the bone, which is what makes
  the junction read as anterior.
- The upper arm must visually **descend from underneath the shoulder cap**, with the deltoid
  wrapping naturally over the humeral head.

Conventions: `+z` is the model's front, the character's **left arm is at +x**, all figures are mm in
world space, measured **posed at Bottom** of the dumbbell curl on `CORNER_FINAL_SHORTS`.

---

## 4. The GLB alone is not enough

**The accepted shoulder correction is not inside any GLB.** There is no "v9" and no corrected
export. The character binaries are still the existing `CORNER_FINAL` bare and dressed assets,
byte-identical to the versions accepted before the shoulder work.

The corrected shoulder relationship lives in **the canonical rig and the exercise definition** — in
code — and is applied at retarget time, every time the character is posed.

> **Loading the GLB on its own reproduces the OLD, uncorrected forward shoulder.**
> **GPT must read the rig/code references in `rig-and-code/` as well as the GLB.**

This is a property of the engine, not a packaging convenience. An attempt to push the correction
into the asset was measured to be ineffective: a Jacobian over 50 mm rest-space probes came back
rank ≈ 1 — every rest direction produced posed motion along one lateral world axis, because the
posed arm root is placed from the canonical clavicle's frame at the imported clavicle→shoulder
distance. A 40 mm asset edit moved the posed shoulder **1.0 mm**. The reproduction script is
included as `harnesses/armroot.mjs` so this can be re-checked rather than taken on trust.

---

## 5. Hard constraints

1. **The source GLBs are read-only and must never be overwritten.** `HomeGymPT_Male_CORNER_FINAL.glb`
   and `HomeGymPT_Male_CORNER_FINAL_SHORTS.glb` in `characters/` are frozen references.
2. **Create only a separate candidate**, e.g. `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v1.glb`. Give it
   a new filename. Never overwrite, replace or "update in place" either `CORNER_FINAL` file.
3. **Do not change `src/character/bundled.ts` or any production asset reference.** That file decides
   which character the app registers as default; repointing it is promotion, and promotion is not
   authorised. A candidate is reviewed by importing it through the app's own GLB import.
4. **Production v8 files must remain untouched** —
   `public/characters/HomeGymPT_Male_BASELINE_v8.glb` and `..._v8_SHORTS.glb`.
5. **The remaining shoulder defect must be solved by new mesh anatomy and skin geometry, not by
   changing the joint position.** See §2.
6. **Do not silently retune the 8 known failures** (§7), and do not "fix" them as a side effect.
7. **Preserve grip and contact behaviour**, including `scene.extras.homeGymPT` solved-grip metadata
   (`gripSolutionId`, `handleGripOffsets`, `gripFrameOffsets`) and the hand topology it was measured
   against.
8. **Do not merge or promote anything.**

---

## 6. The frozen references

`characters/` — the frozen mesh and skin. This is what a new candidate is measured against.

| File | Bytes | SHA-256 |
|---|---:|---|
| `HomeGymPT_Male_CORNER_FINAL.glb` (bare) | 2,303,476 | `b08844339fb66e54a290eb9687fdc48296d087e4cbbb83981041a03d8501cc7a` |
| `HomeGymPT_Male_CORNER_FINAL_SHORTS.glb` (dressed) | 2,417,316 | `fe30c1dadb1dca442b79155cf3bb662e7b22b4f6f48ee806258fde798e34a71b` |
| `HomeGymPT_Male_CORNER_FINAL_SHORTS.glb.correspondence.json` | 30,513 | `531568e176f592230dc7ef3686df82a50c9a794bcd5762dd234bc485351a9e92` |

`CORNER_FINAL` is the accepted upper-body geometry baseline: Phase A normals repair, the
skin/material pass, and rounds 2–5 of the upper-body geometry work. The dressed variant is the app's
default character; the correspondence file is the garment fit for it.

---

## 7. Corrected rig state — what supplies the shoulder position

### Clavicle rest angle

`rig-and-code/src/rig/humanoid.ts`, `clavicle_l` (the right side is generated by mirroring):

```ts
head: vec3(-0.02, 1.42, 0.012),
tail: vec3(-0.17, 1.44, -0.035),   // corrected — was vec3(-0.17, 1.44, 0)
```

4.5° of posterior angle → **≈ 17.5°**. A real clavicle angles back 15–20°; running almost straight
out put the shoulder girdle, and the whole arm with it, in front of the ribcage.

### The arm chain follows it

```ts
upperarm_l  head/tail  z = -0.035
forearm_l   head/tail  z = -0.035
hand_l      head/tail  z = -0.035
```

### The finger knuckles move too

The five `FINGER_SPECS` knuckles are **absolute world rest positions**, so they carry the same
−0.035. Leaving them behind tilts the hand's measured axis by `atan(0.035 / 0.09) = 21.3°`, because
the palm axis comes from the mean knuckle position rather than the hand bone's tail.

### The re-solved curl

`rig-and-code/src/exercises/definitions/bicepCurl.ts`:

| Setting | Before | After |
|---|---:|---:|
| Bottom elbow (`jointTargets` `forearm_{l,r}` axis `x` `start`) | 6° | **16°** |
| Bottom upper-arm flexion (`startPose` `upperarm_{l,r}.x`) | 4.55° | **3°** |
| Peak upper-arm flexion (`peakPose` `upperarm_{l,r}.x`) | 8.55° | **7°** |
| Peak elbow | 126° | 126° (unchanged) |
| Upper-arm abduction | `z: -3` / `+3` | unchanged |

Clearance comes from the elbow, not from tilting the humerus forward — tilting it forward would
reinstate exactly what the correction removes.

### Reference state to preserve

| Measure | Value |
|---|---:|
| Shoulder forward of ribcage mid-depth | +19.6 mm |
| Humerus sagittal tilt at Bottom | 3.22° |
| Dumbbell ↔ shorts clearance at Bottom | +1.99 / +2.15 mm, 0 inside |
| Grip contacts (fingers / palm / thumb) | −10.75 / −2.54 / −10.35 |
| Finger wrap | 343° |
| Renderer vs exporter grip frame | 0.0000 mm |
| Bare ↔ dressed posed equivalence | 0.0000 mm over 10,839 vertices |

---

## 8. Known test state — 290 passed / 8 failed / 1 skipped

The 8 failures are **known, accepted, non-curl regressions** from correcting a rig every character
shares. They must not be silently retuned as part of the mesh work.

| Test | Failure | Cause |
|---|---|---|
| `exercises > Push-Up` ×3 | 2 technique rules; 22 IK targets; `hand_l` contact 0.0056 > 0.005 | hands plant on the floor and the arm root moved 35 mm |
| `body/ecorche` ×2 | biceps patch 94 < 100; 108 inverted triangles > 80 | écorché sculpt built around the old arm position |
| `body/shoulder` | 6.77 > 5.5 | procedural-body metric, authored against the old chain |
| `muscles` | `deltoid_anterior_l` 0.0022 > 0.001 outside the skin | muscle belly fitted to the old arm |
| `editor/review` | two-hand grip-socket gate false | barbell sockets authored against the old hand positions |

If the mesh work changes this count in either direction, **say so explicitly**. A drop from 8 is as
important to report as a rise.

---

## 9. The measurable shoulder check — `sagittal.test.mts`

`harnesses/sagittal.test.mts` is **the** check for this work. It reports, posed at Bottom:

- the joint centre, clavicle origin, elbow and humerus sagittal tilt;
- **deltoid apex (arm-owned) — its y, its z, and its height above the joint** ← the two target numbers;
- the acromion/trapezius apex and the outer trunk apex, for context;
- a height-banded sagittal profile of the arm's front surface, back surface and midline against the
  humerus axis.

Run it from the **repository root** (not from inside this folder):

```
ASSETS=HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb \
  npx vitest run --config scratchpad/repair/vitest.config.mts scratchpad/repair/sagittal.test.mts
```

Point `ASSETS` at the new candidate to check it. Expect to see
`deltoid apex … -> 25-35 mm ABOVE the joint` and an apex `z` at or below −21.9.

### A measurement caveat worth inheriting

Three arm-surface selection methods were tried before one held up. An x-slab and a sleeve-radius
selection both reached the lat and ribcage behind the arm, reporting implausible arm depths of
115–148 mm and a midline biased backwards — which would have produced the same "bone ahead of the
mass" conclusion for entirely the wrong reason. The figures in this document use **skin ownership**
(`upper_arm*` weight ≥ 0.7), which is well defined at the arm/torso junction where geometry is not,
plus apex measurements that need no slab at all. The invariance result in §2 is independent of all
of it: it compares the same measure against itself across two rig states.

### If the new mesh is a dressed variant

The dressing pipeline must carry, from the source body: node **rest-pose matrices** (all 160
joints), **inverse bind matrices**, and **`scene.extras.homeGymPT`**. Omitting the node matrices is a
real defect that has occurred here before: every vertex-level check passed while the dressed default
posed like an older body, because glTF nodes in these assets use `matrix` and never TRS — comparing
`node.translation` / `node.rotation` gives a false pass. Verify with
`harnesses/dressed_equivalence.test.mts`, which asserts 0.0000 mm across all 10,839 posed vertices.

---

## 10. What is in this package

Every file is a byte-verified copy; per-file sizes and SHA-256 hashes are in `MANIFEST.txt`.

| Handoff path | Source | What it is |
|---|---|---|
| `characters/` | `scratchpad/reference-fit/` | frozen mesh/skin reference — bare, dressed, correspondence |
| `rig-and-code/src/rig/` | `src/rig/` | canonical rig — `humanoid.ts` holds the clavicle correction |
| `rig-and-code/src/exercises/definitions/bicepCurl.ts` | same | the re-solved curl |
| `rig-and-code/src/retargeting/retarget.ts` | same | the attachment mechanism that makes the GLB alone insufficient |
| `rig-and-code/src/character/` | same | `retargetSource.ts`, `muscleDeformation.ts`, `importedDeformation.ts`, `types.ts` |
| `harnesses/sagittal.test.mts` | `scratchpad/repair/` | **the shoulder check** |
| `harnesses/` (13 more) | same | curl guards, clearance, grip, equivalence, and `armroot.mjs` |
| `renders/shoulder-junction/` | `scratchpad/seatreview/` | the junction close-ups; right column is the **rejected** joint-seating test |
| `renders/shoulder-true-fix/` | `review-assets/renders/` | before/after of the accepted clavicle correction, plus loop strips |
| `renders/shoulder-diagnosis/` | same | earlier pack; right column is a **rejected** −4° pose workaround |
| `renders/muscle-stage1/` | same | the arm-muscle layer, off vs on |
| `docs/SHOULDER_JUNCTION_DIAGNOSIS.md` | `docs/` | **the current diagnosis — read this first** |
| `docs/` (4 more) | same | true-fix record, alignment diagnosis, Stage 1, model-appearance phase rules |

### Reading order

1. `docs/SHOULDER_JUNCTION_DIAGNOSIS.md` — why this is a mesh problem and not a joint problem.
2. This file, §2 and §3 — the constraint and the numeric target.
3. `docs/SHOULDER_ALIGNMENT_TRUE_FIX.md` — how the joint got where it is, and what it cost.
4. `AI_CHANGELOG.md` in the repository — chronological summary of every round.

---

## 11. Note on the Stage 1 muscle layer

`muscleDeformation.ts` is active and adds pose-driven corrective morph targets to the arms at load
time — code-side, nothing baked into the asset. It is exactly 0 at Bottom and Return, so it does not
affect a static comparison there, but it **will** change the arm silhouette at Mid and Peak. Match
the frame when comparing against renders. It can be taken to 0% in the editor's Correctives panel
("Arm muscle contraction") without touching an asset.

---

## 12. Status

Package assembled and verified. No GLB was created, `CORNER_FINAL` was not rebuilt, and no rig,
animation, mesh, exercise, grip, corrective, production asset or code file was modified in preparing
it.
