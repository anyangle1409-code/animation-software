# Model round 2 — upper-body appearance

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `e09fc17`
**Candidates only. Production v8 untouched. Not merged.**

Items 1–4 of the round-2 scope recorded in `MODEL_APPEARANCE_PHASE.md`. Body vertex positions
only; topology, skin weights, skeleton, joint matrices, inverse binds, bind/rest pose,
`scene.extras.homeGymPT`, the garment and every exercise definition are untouched.

## The diagnosis that shaped the work

Items 1, 2 and the pec half of item 4 turned out to be **one defect**. The `breast`-owned region
carried a **+22.0 mm bump on the rear rib** (x ±0.211, y 1.352, z −0.083) and a **−17.0 mm hollow
at the front armpit** (x 0.196, y 1.501) — a ~39 mm ripple across a single area. That is the back
protrusion, the abrupt armpit and the unclean pec shape, all from the same source. Relaxing the
ripple addressed all three at once rather than sculpting each by hand.

## What changed

| Stage | Operation | Extent |
|---|---|---|
| 1 | Pec / rear-rib / armpit ripple relaxed — masked Laplacian, feathered vertically over the ribcage and laterally from sternum to arm | 628 points |
| 2 | Deltoid cap silhouette lifted toward a larger target arc, **y only** | 59 points per side, max 8.00 mm |
| 3 | Waist drawn in laterally, above the waistband only, depth left alone | 328 points, max 8.41 mm per side |

Largest single vertex move 31.39 mm (the bump being flattened), over 982 points. Every co-located
duplicate moves together, so no vertex pair was split and no crack introduced.

Normals were recomputed only where the surface moved plus one ring out — 1,243 vertices across
1,204 dirty groups — accumulated across whole co-located groups so both sides of a UV seam agree.
The Phase A seam repair therefore survives: **7 groups / 14 vertices / 71.0°**, unchanged.

### Two things I got wrong first, recorded because the measurements caught them

- **Stage 2, first attempt** relaxed the cap on y and z while holding x, to protect the shoulder
  span. It measured *worse*: the cap kink grew 17.7 → 35.7 mm. Forbidding one axis makes the
  smoothing shear the surface. A y-only relaxation then barely moved a convex apex (radius 109.4 →
  102.5 mm, still slightly worse).
- **My first kink metric was unreliable** — it read 431 mm on a slab spanning torso and arm. I
  replaced it with the radius of curvature of the cap's side-view silhouette, fitted to its upper
  envelope, which is interpretable and stable. Only then did the third approach — lifting the
  flanks toward a larger arc — show a real gain.

## Measured results

| Item | Measure | Before | After |
|---|---|---:|---:|
| 1 | Largest outward relief, pec/rib region | **22.0 mm** | gone from the top of the list |
| 1 | Largest torso relief anywhere | 22.0 mm | **10.9 mm** (pre-existing lower back, under the shorts, untouched) |
| 2 | Deepest pec/armpit hollow | **−17.0 mm** | **−6.7 mm** |
| 3 | Shoulder cap silhouette radius | **109.4 mm** | **128.4 mm** (+17%) |
| 3 | Cap apex height / position | y 1.6003, z −0.055 | y 1.6003, z −0.055 — unchanged |
| 4 | Waist half-width (y 1.28) | 158.3 mm | **150.3 mm** |
| 4 | Abrupt half-width step at y 1.32 | **+36.2 mm** | **+17.5 mm** |

The half-width profile is now monotonic from waist to chest, where before it pinched at y 1.28 and
flared 36 mm at y 1.32.

## Validation — nothing locked moved

| Check | Result |
|---|---|
| Shoulder span (x bounds) | −0.8833..0.8833, **identical** |
| Bare ↔ dressed grip solution and offsets | `homeGymPTMale`, (0.0174, 0.0452, 0.0083) — both |
| Bare ↔ dressed posed hand / body | **0.0000 mm** / **0 of 10,839** vertices |
| Grip contacts, curl t = 2 | −0.46 / −0.36 / −0.22 / −0.11 mm, 0 inside; thumb +1.18; palm −2.54; wrap 252° |
| Renderer vs exporter | 0.0000 mm, all six samples |
| Thigh clearance, body only / with garment | +4.68 / +4.79 mm and +0.48 / +0.64 mm, 0 inside |
| Clothing closest approach | 1.97 mm, non-interpenetrating |
| `clothing` / `waistband` / `clothdebug` | all pass |
| Phase A seams | 7 groups / 14 vertices / 71.0° |

## Candidate assets

| Role | File | SHA-256 |
|---|---|---|
| Bare | `scratchpad/reference-fit/HomeGymPT_Male_TORSO_FINAL.glb` | `da5b3c5ed72dd131d111b50e6c7e12eb531c89cc212992039a1ee49e3dc1e003` |
| Dressed | `scratchpad/reference-fit/HomeGymPT_Male_TORSO_FINAL_SHORTS.glb` | `cf6c09a50152b20c018945d9f6cc416acc35bcf5063aacd923ee56189f804bd7` |

Rollback chain: skin candidates `d71b70bc…c18f2be` / `8d07100f…f08f27ca`, Phase A candidates
`b3dc70e1…89fdf09` / `71c5bdef…9fe42da9`, production v8 `951c2c39…963ee0` / `cc728366…5722e3`.

The skin tone and curvature shading were regenerated from the new geometry, so the surface
shading matches the new shape rather than the old one.

## Captures

Matched pairs, one browser session per asset (a second import into one session reuses the cached
build — see `MODEL_PHASE_B_SKIN_MATERIAL.md`), `light` backdrop, no selection gizmos: front, 3/4,
side, back, upper body, and the curl at Peak. Plus magnified crops of the rear armpit and the side
shoulder, where the changes are clearest.

## What remains

- **Refined abs and lower torso** (part of item 4) — **not attempted.** Deepening abdominal
  separation means adding surface detail that is not in the mesh, which a field operator cannot
  invent convincingly. It needs either a normal/displacement map or real sculpting.
- **Chest fullness.** The V-taper reads cleaner mainly because the step artifact is gone and the
  waist is 8 mm tighter per side, not because the chest widened — the chest measure actually fell
  (y 1.40: 217.4 → 196.8 mm), almost all of which is the rear bump being removed rather than pec
  volume lost. Against the reference board the pecs could still be fuller, and adding that volume
  is an additive change I have not made without a decision from you.
- The apex of the shoulder cap still sits 55 mm behind centre. Centring it means moving the cap in
  z, which changes the shoulder's depth — a trade-off worth showing before doing.

## Blocker

None that stopped this round. The one thing I could not do procedurally is the ab/lower-torso
refinement above; it needs a decision on method (map versus sculpt) rather than more attempts.

## Status

Items 1, 2, 3 and the silhouette half of item 4 done and validated. Stopped for review.
**Not merged, nothing promoted.**
