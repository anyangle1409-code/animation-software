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

### R59b status (implemented, NOT launched)

`generate_r59_min_accel.py --variant b --envelope-mm 2` implements the plan above:
- all controls ≤ 110° are zero;
- each frame and coordinate is kept inside [min(R52, 0) − 2 mm, max(R52, 0) + 2 mm], solved by an active-set loop.

**The synthetic test shows the envelope defeats the purpose.** Rest-space acceleration only drops from 212 to 205 (×16), against 7 for R59, and the marked pose drifts by 0.17 mm. An envelope that follows R52's rough profile near its peak forces the smooth curve to copy that roughness. **Do not launch it as is.**

## Exact next steps when usage resets (in order)

1. **Localise R59's 39 contacts before any further timing change.**
   - Add a step to `shoulder-r59-min-accel-study.yml` that prints the contact pairs, samples and press elevations from `/tmp/r57/native_final.json`. The artifact can't be downloaded from the Claude container, so print it to the log.
   - Compare them with R57's 7 pairs (10855 vs 22184–22187).
   - **If the new contacts are posterior skin against the arm**, R59 pushes those vertices past R52 in the direction of the contact. The fix is then a **one-sided** limit:
     - cap only the component along the contact normal, not the whole envelope;
     - or cap the increment magnitude at R52's own magnitude, not its per-frame values.
2. **Early outward.** R59a's 1.55 mm came from controls 96–109°. Variant b's "zero ≤ 110°" part is correct and cheap. Run R59a plus that one change alone (a `--variant c`), with no envelope, to separate the two effects.
3. **The owner scope decision (unchanged):** the smoothest S7-only timing still leaves ~1.3–1.9 mm motion excess against the 0.5 mm guard.
   - Either the owner accepts an outline-specific motion tolerance after seeing R59-type renders;
   - or authorises a non-S7 mechanism (weights or helper; R53 evidence);
   - or relaxes the R47 marked offset.

   Do not change thresholds without that decision.
4. **R59's renders** (`visuals/R57_local_study/*` in artifact `original-v1-r59-min-accel-study-20261020`, run 39421297091; the folder name comes from the reused R57 render step) should go to the owner next to R52's, at t = 0.625 and t = 0.8. **Download them from the GitHub web UI**; this container cannot download them.

**Everything is on `claude/home-gym-pt-animation-txux66`.** Read-only diagnostics and unsaved studies only; nothing merged; no model saved; Work's branches untouched.

## Owner review of R59, and R60 (run 39424412374)

**Owner, on the R59 video:** "Something looks wrong … from 148 to 166 degrees you can see the weird deformation at the armpits. It then goes from being correct to having a bit of a dip in between instead of flowing arm into body." They also asked whether the press must end at 166°.

**Diagnosis:**
- **R59's crumple** at 145–156°: R59 replaced each vertex's R52 profile with one smooth shape scaled to the marked pose. After 136° it stopped following R52, and vertices with no marked-pose increment lost their correction entirely.
- **The 148–166° dip in every version (R52/R57/R59/R60):** the 166° S7 control is a protected zero, held at the pre-R47 lockout shape. So the ~35 mm R47 arm-into-body fill must drain away between ~148° and 166°, and the armpit dips as it does.
- **This is a scope limit, not a timing problem.**

**R60 = smoothing R52 instead of replacing it** (`generate_r59_min_accel.py --variant c --fidelity f`):
- per vertex: minimum frame acceleration plus a per-frame fidelity term to R52;
- the marked pose held exactly;
- controls ≤ 110° zero.

| Gate | R52 | R60 f = 0.03 | R60 f = 0.3 | Limit |
|---|---|---|---|---|
| Marked outline | 0.95 mm | 0.95 mm | 0.95 mm | 1 mm |
| Dense 161 motion | 40.6 mm | **9.25 mm** | 17.4 mm | 0.5 mm |
| Early outward | 0.62 mm | **0.0002 mm (passes)** | 0.0002 mm (passes) | 0.05 mm |
| Contacts (83 poses) | 7 | 7 | 7 | 0 |
| Reversed normals in the marked pose | 6 | 6 | 6 | 0 |
| Crease | 142° | 137° | 141° | 2° |
| Original 41-pose motion | — | 3.60 mm | 3.10 mm | 0.5 mm |
| Benchmark regressions | 6 | 6 | 6 | 0 |

- **Visual:** R60 f = 0.03 is no worse than R52 at 145/156°. R59's crumple is gone.
- **Media:** `review-assets/shoulder_r60/r60_fid0.03/` and `r60_fid0.3/`.
- **Still failing:** R60 keeps R52's 7 contacts and 6 reversed normals, and it still has the 148–166° dip.

**Pending owner decision (asked on 20 Oct):**
- **Option 1 (recommended):** release the protected 166° control, letting the R47 arm-into-body flow continue to lockout. Re-solve R60 with control 71 free, holding the marked pose. Per R58, releasing 166° also lowers the motion bound.
- **Option 2:** end the press earlier (~150–155°) instead.

**Do not release the 166° control without the owner's explicit yes.**

## R61 (press first): generator ready, NOT run

**Owner (20 Oct), on R60 at 156°:** the arm-into-body flow turns into a dip from ~148° to the top. The press normally does go past 145° (lockout ~150–170°; elbows only straighten near the top). The owner wants the high range fixed ("finish the press first"; the pull-up comes after).

**`generate_r59_min_accel.py --variant d --hold-from 145 --fidelity 0.03`:**
- releases the 166° S7 control for every vertex already allowed at 165°;
- holds each vertex's R52 fill from 145° to lockout instead of draining it (synthetic check: fill at 166° is 28.6 mm instead of 0);
- otherwise uses the R60 smoothing; the marked pose is held exactly and controls ≤ 110° are zero.

**Blocker:** Work's installer `original_review_r52_native.install` (used by every gate script) raises an error if control 166 is non-zero. Making it run means either:
- **(a) Work adds an explicit, owner-approved option** to that installer for the 166° release;
- **(b) Claude forks the installer and the gate scripts** into its own lane under new names.

Patching the guard inside the CI checkout was refused by the session's safety check. Do not do it that way.

## R61 result (run 39428294376; media in `review-assets/shoulder_r61/`; REJECTED)

**Setup:**
- The owner approved releasing the 166° control (20 Oct; "finish the press first").
- Claude's own installer and gate copies are in `scripts/shoulder_r61/`. They are identical to Work's apart from allowing the 166° control and locating Work's sources; all thresholds are unchanged.
- Patching Work's guard in CI was refused by the session's safety check, so it was not done.

**Results** (generator `--variant d --hold-from 145 --fidelity 0.03`, which holds each vertex's rest-space fill from 145° to 166°):

| Gate | R60 | **R61** |
|---|---|---|
| Outline | 0.95 mm | 0.95 mm |
| Dense motion | 9.25 mm | 9.25 mm |
| Early outward | 0 | 0 |
| **Contacts** | 7 | **165** |
| Crease | 137° | 164° |
| Benchmark regressions | 6 | 10 |

The renders show the armpit crumple again at 156°.

**Why:** a rest-space offset held while the humerus keeps rotating points into the arm at high elevation. Holding the fill needs a posed-space lockout target, not a held increment.

**Next for 148–166° (the press, then the pull-up):**
- Build posed-space targets at ~150/156/166° that keep the arm-into-body line.
- Use the R24–R33 skin-slide approach: `build_original_skin_slide_targets_blender.py`, with surface-walking slide and auto clean-up of crossing pairs and folds.
- Bake them into the released 156/166 controls with the R17 LBS-inverse bake, then run the same gates.

## R62 (launched on top of R60, not R61)

- **Change:** upper-trapezius bunching, `--variant c --fidelity 0.03 --trap-mm 10`. It is an outward swell over the model's `muscle_trap_l/r` helper region (634 vertices, region file `scripts/shoulder_r61/r62_upper_trap_region.npz`), faded in from 136° (the marked pose is untouched) to full at 160°.
- **Sources** (owner asked to verify): the upper trapezius is part of the upward-rotation force couple and is highly active in the military press; the scapula rotates upward ~48–61° at 150° of elevation. The model's own press reaches 41°/49° at 132°/145°, consistent.
- **Workflow:** `.github/workflows/shoulder-r62-trap.yml`.
