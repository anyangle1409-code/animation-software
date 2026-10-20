# Shoulder work: Claude's R53–R57 review and R58 localisation (20 Oct 2026)

**Status:**
- No model was changed, saved or approved.
- Work's branches (R53–R57, PRs #119–#122) were read but not edited.
- The R58 diagnostic is read-only. Its files are added as new files on `claude/home-gym-pt-animation-txux66`:
  - `scripts/shoulder_r58/`;
  - `.github/workflows/shoulder-r58-temporal-localisation.yml`.

  Its workflow checks out the R57 sources at their pinned commit; it does not merge them.

## R53–R57 in one paragraph each

**R53 (root cause).**
- With S7 muted, R52 equals R41 exactly. The R52 moving defect is in the S7 increments.
- A sharp skin-weight gradient (edge 18081–21057, lat-helper share 0.32 → 0.40 across ~1 mm) is a real local mechanism.
- S5 and S7 push in opposing directions over ~5,000 vertices.
- Rejected:
  - moving the lat-helper origin: outline error 0.95 → 25.7 mm;
  - the 26-vertex weight averaging: seed edge 14.57 → 15.22 mm at lockout.

**R54.** All 25 global S5/S7 amplitude pairs (0.90–1.10 each) fail. The best pair is the unchanged 1.0/1.0, which keeps the outline (0.95 mm) but still has 40.64 mm motion excess. Global scaling is ruled out.

**R55.**
- 1,711 of 1,796 posterior vertices individually exceed 0.5 mm; 1,685 of them lie outside the 26-vertex patch.
- Worst vertex 19057 (40.64 mm) is 35.5 mm along the mesh from that patch.
- The early-outward vertex is 20913 (10.36 mm).
- The weight patch cannot be the fix.

**R56.** Per-control permissions:
- Source 110° and 166°, and dense controls 95, 110 and 166, are zero and protected.
- Source 120–156°: 1,776 editable posterior vertices.
- All 40 worst hotspots are editable at dense 118°/119°.
- An S7-only local study inside the existing permissions is allowed.

**R57 (cloud run 39411211783; rejected, all failures kept).**
- Change: temporal smoothing of the dense S7 increments over 114–122° (5-tap [1,4,6,4,1], strength ≤ 0.65), within a 55 mm mesh-distance taper around 19057/20913 and their mirrors.
- Results:

  | Check | R57 | Limit |
  |---|---|---|
  | R47 marked outline | 0.95 mm (passes) | 1 mm |
  | Dense 161 motion | 39.38 mm (R52 40.64) | 0.5 mm |
  | Early outward | 0.62 mm, unchanged | 0.05 mm |
  | Reversed normals in the marked pose | 6 | 0 |
  | New contacts in the 83 safety checks | 7 (vertex 10855 vs 22184–22187, samples 25/26/65/66) | 0 |
  | Original 41-pose motion | 1.09 mm | 0.5 mm |
  | Posterior crease | 142° | 2° |
  | Benchmarks regressed | 6 | 0 |
  | Adjacent step | fails | 3 mm |

## What R57 tells us

Smoothing at 114–122° removed only 1.3 of 40.6 mm, so **the dominant extra acceleration is not at 118°**. Two facts from the code (`original_review_r52_native.install`, `original_review_r43_sampling`) point to where it more likely is:

1. **The S7 increment is pinned to zero at the 110° control and the 166° control.** The free controls 111° and 165° next to them can hold up to the 45 mm cap. A large increment that starts or stops within 1° of a pinned zero is a kink in the increment profile. When the press sweeps through that degree it becomes a frame-level acceleration spike.
   - Near lockout the press moves slowly (smoothstep ease-out), so a kink there spans more frames.
   - Mid-press the press moves fastest, so a kink there gives the sharpest per-frame jump.
2. **Early outward (0.62 mm before 110°)** can come only from the free controls 96–109° (95 and 110 are zero). Smoothing at 114–122° cannot touch it.

**R58 measures this directly instead of guessing.** It reports:
- per frame and arm angle, the worst excess;
- for each worst vertex, its peak frame and angle, and its increment profile over the 72 controls with the top three kinks;
- the early-outward vertex and its angle, and the largest increment at 96–109°.

## R58 results (cloud runs 39412967341, 39413796014, 39419730103; all read-only, all succeeded)

Inputs were hash-verified. The unchanged R52 measurement script, re-run natively, reproduced R52's motion excess exactly (40.6446 mm).

**1. When the excess happens.** It is spread over the whole raise, not concentrated at 118°.

| Elevation band | R52 (mm, ×16) | R57 (mm, ×16) |
|---|---|---|
| 70–95° | 1.31 | 1.31 |
| 95–110° | 34.0 | 34.0 |
| 110–114° | 31.0 | 31.0 |
| 114–123° | **40.6** | **24.0** (R57's only change) |
| 123–136° | 39.4 | 39.4 |
| 136–156° | 36.4 | 36.4 |
| 156–166° | 1.39 | 1.39 |

R57 only moved the maximum from 118° to 125°.

**2. Why.**
- **The profile shape:** the worst posterior vertices (19057, 19370, 18046, 21326, …) carry an S7 increment that rises from 0 at the protected 110° control to about 33–39 mm at 136–138°, close to the 45 mm cap, then falls to 0 at 166°.
- **Roughness:** the profile is rough at 1° resolution, with node-to-node second differences of about 3–4 mm at many controls (110, 111, 118, 124, 125, 129, 142, 145°).
- **Early outward:** 0.62 mm at 105.5° on vertex 20913; 1,306 vertices are over 0.05 mm. It comes from the free controls 96–109°, which reach 2.9 mm.

**3. Feasibility (an LP per vertex over the 72 controls; indicative).**
- **The question:** the smallest possible extra frame acceleration, ×16, for any S7-only increment that keeps:
  - each vertex's R52 value at the R47 marked pose (t = 0.625, 135.6°);
  - zero at the protected controls;
  - the early-outward limit and the 45 mm cap.
- **Approximation:** rest-space increment; bone rotation and R41's own acceleration ignored.

| Scope | Worst of the 40 worst vertices (guard 0.5 mm) |
|---|---|
| Current protected 95/110/166° | **1.26 mm** (all 40 fail) |
| 110° released | 0.88 mm |
| 166° released | 1.03 mm |
| 110° and 166° released | 0.57 mm |
| R52's actual profiles | 27–33 mm |

**Conclusion:** keeping the owner-approved R47 marked-pose offset (~35–37 mm posterior) and the 0.5 mm full-press motion guard is **not achievable with S7-only edits under the current scope**, even with the smoothest possible timing. The approximation can shift this by some tenths of a millimetre, but not by the factor of 2.5 needed. Every further S7-only study (R57-style) will fail the motion gate. Yet the smoothest profile would cut R52's excess by about 25–30×.

## Exact next steps (resume here)

1. **Owner decision needed (scope).** The two approved requirements conflict for S7-only edits. Options, best first:
   - **(a) Build R59** (step 2) and judge it visually. Its expected motion excess is ~1.3 mm against the 0.5 mm guard. If the owner finds the motion smooth, they may accept an outline-specific motion tolerance. **Never relax a threshold without the owner's explicit decision.**
   - **(b) Release the protected 110°/166° zeros:** bound ≥ 0.57 mm, still above the guard.
   - **(c) A smaller marked-pose offset:** changes the approved R47 silhouette.
   - **(d) A non-S7 mechanism:** weights or a helper deformer. Needs a new scope approval; R53's evidence on the weight gradient applies.
2. **R59 = the minimum-acceleration S7 profile.** It is within the existing S7 permission. **It has now been built and launched:**
   - generator: `scripts/shoulder_r58/generate_r59_min_accel.py`;
   - workflow: `.github/workflows/shoulder-r59-min-accel-study.yml`, which runs the pinned R57 sources' gates unchanged;
   - run: 39421297091;
   - artifact: `original-v1-r59-min-accel-study-20261020`.

   The results are recorded below once read. The original plan: For every vertex:
   - **Objective:** minimise the sum of squared frame second differences of the increment along the 161-frame press. Use quadratic least squares, not the L∞ of the LP: it is linear in the target, so spatially smooth targets give spatially smooth profiles.
   - **Hold:** the R52 value at t = 0.625 exactly (outline unchanged); 0 at controls 95/110/166 and at every control the R52/R47 `allowed_dense` mask forbids for that vertex.
   - **Limits:** outward ≤ 0.05 mm before 110° (clamp, then re-solve); the 45 mm cap.
   - **Output and gates:** write `candidate.npz` with `dense_delta` and run the unchanged R57 workflow gates (generator swapped): dense 161 motion, 83 native contact/area/orientation/affine, 13 benchmarks, the R52 actual-native tests, matched renders.
   - **Expect:** outline 0.95 mm (unchanged), early outward ≤ 0.05 mm, motion about 1.3 mm (fails 0.5; recorded). Contacts, normals and crease are unknown and must be measured.
   - Keep every failure.
3. **The 7 contacts** (vertex 10855 against 22184–22187 at samples 25/26/65/66) and the **6 reversed normals in the marked pose** are present in both R52 and R57. They need their own localisation; check whether R59 changes them.
4. The R58 reports are artifacts `original-v1-r58-temporal-localisation` of runs 39412967341 and 39419730103, kept for 30 days. The numbers above are copied from them.

**Rules unchanged:**
- Skeleton, canonical bones, Basis, weights and topology stay frozen.
- HGPT_SHOULDER_* stays with Work.
- No merge or deploy, and no claim of approval.
- The R47 marked silhouette is the owner-approved reference; keep it within 1 mm.
- The newer arm and elbow detail is kept.
- Reference photos stay out of Git.

## R59 result (run 39421297091; artifact `original-v1-r59-min-accel-study-20261020`; unchanged R57 gates; REJECTED, all failures kept)

| Gate | R52 | R57 | **R59** | Limit |
|---|---|---|---|---|
| R47 marked outline | 0.9499 mm | 0.9499 mm | **0.9499 mm** (held exactly) | 1 mm |
| Dense 161-pose motion | 40.64 mm | 39.38 mm | **1.92 mm** | 0.5 mm |
| Early outward | 0.62 mm | 0.62 mm | **1.55 mm** (worse) | 0.05 mm |
| Original 41-pose native motion | — | 1.09 mm | 1.62 mm | 0.5 mm |
| New contacts in the 83 safety checks | — | 7 | **39** (worse) | 0 |
| Posterior crease | — | 142° | 176° | 2° |
| Marked-pose reversed normals | — | 6 | 6 | 0 |
| Benchmark regressions | — | 6 | 8 | 0 |

**What it shows:**
- **The motion spike is a timing problem, and it is fixed by timing alone:** 40.6 → 1.9 mm, with the outline unchanged. This matches the R58 bound (~1.3 mm in rest space, plus bone rotation).
- **The remaining 1.9 mm cannot reach 0.5 mm with S7 alone.** This is the owner scope decision in step 1.
- **Early outward got worse:** the smooth profile starts rising on the free controls 96–109° for vertices that R52 had not moved outward early. My clamp was in rest space and only applied to vertices R52 already moved outward.
- **Contacts and crease got worse:** the smooth profile carries larger mid-press values than R52 at some poses (it no longer dips).

**Next (R59b, small and in scope):**
- Zero all controls below 110° for every coordinate (as in the LP's protected case).
- Add a per-frame cap: |R59 increment| ≤ |R52 increment| + 2 mm at each of the 83 safety samples, enforced as box constraints in the QP (an active-set loop or `scipy.optimize.lsq_linear` per permission pattern). Smoothness is then not bought with new skin intrusion.
- Then localise the 39 contacts: the pairs are listed in `native_final.json` in the artifact.
