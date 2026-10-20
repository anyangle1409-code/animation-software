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

### R62 result (run 39430368223; media in `review-assets/shoulder_r62/`)

**Gates:** identical to R60 on every check. The trapezius swell adds no new contact, crease, motion or benchmark problems:

| Gate | R62 | Limit |
|---|---|---|
| Outline | 0.95 mm | 1 mm |
| Dense motion | 9.25 mm | 0.5 mm |
| Early outward | 0 | 0.05 mm |
| Contacts | 7 | 0 |
| Reversed normals | 6 | 0 |
| Crease | 137° | 2° |
| Benchmark regressions | 6 | 0 |

At the marked pose the swell adds 0.0 mm, as designed.

**Visual:** a subtle, fuller neck-to-shoulder mound at 145–156° (`R52_vs_R62_neck_closeup_145_156.jpg`). If the owner wants it stronger, raise `--trap-mm` (10 → 15–20 mm) and re-check contacts near the neck.

**Still open:** the 148–166° arm-into-body dip, which needs posed-space lockout targets (see R61).

## R62b (15 mm trapezius) and R63 (posed-space lockout sculpt), 20 Oct

**R62b** (`--trap-mm 15`, run 39433070757):

| Gate | R62b | Limit |
|---|---|---|
| Outline | 0.95 mm | 1 mm |
| Dense motion | 9.25 mm | 0.5 mm |
| Early outward | 0 | 0.05 mm |
| **Contacts** | **98** (10 mm: 7) | 0 |
| Crease | 137° | 2° |
| Benchmark regressions | **8** | 0 |

The owner chose to keep 15 mm and fix what it hits.

**R63** (`scripts/shoulder_r61/generate_r63_lockout.py`, run 39437923899; first version kept in `review-assets/shoulder_r63_first/`):
- **Method:** posed-space design using Work's exact affine pose model.
  - Seen from behind, the side of the back below the armpit is pushed out to the arm's outer-edge line (gain 0.6, depth 25 cm), ramped in over 146–152°.
  - The push is smoothed, and controls 146–166 are solved back by batched least squares with temporal smoothing.
  - Posed fit ≤ 2 mm; 4,437 vertices affected; the outline is untouched.
- **Visual:** the owner's circled dip is largely filled at 156°/166° (`R52_vs_R63_armpit_156_166.jpg`). But there are stringy wrinkles on the back of the shoulder, and the 15 mm trapezius looks lumpy.

| Gate | R63 | Limit |
|---|---|---|
| Outline | 0.95 mm | 1 mm |
| Dense motion | **22.2 mm** | 0.5 mm |
| Early outward | 0 | 0.05 mm |
| **Contacts** | **215** | 0 |
| Crease | 171° | 2° |
| 41-pose motion | 6.9 mm | 0.5 mm |
| Benchmark regressions | 9 | 0 |

- **Note:** the contact-location report crashed in CI after the total (it works locally). Its stderr is now captured.

**R63b (next run):** cap each pushed vertex at its posed distance to the nearest upper-arm skin minus 8 mm, before and after smoothing (`--arm-margin`).

**Still to do:**
- localise the trapezius contacts from the new report, and cap the 15 mm swell where it meets the neck/head;
- bring the R63 motion back toward R60's 9 mm (raise `--lam`, or ramp in over more degrees).

### R63b (run 39440663200) and R63c (launched)

**R63b** (8 mm arm-distance cap on the fill):

| Gate | R63b | Limit |
|---|---|---|
| Contacts | **235** (no better than R63's 215) | 0 |
| Dense motion | 22.2 mm | 0.5 mm |
| Crease | 170° | 2° |
| Benchmark regressions | 9 | 0 |
| Outline | 0.95 mm | 1 mm |

- **So the contacts are not torso pushed into the arm.**
- **Correction:** the gate's contact pairs are **triangle** indices, not vertex indices. That also applies to R57's "10855 vs 22184". `print_contacts.py` now labels each triangle by its corners.
- **Likely causes:**
  - **Contacts and wrinkles:** a purely sideways push concentrated near the outline (sigma 5 cm) shears the skin and folds it into itself.
  - **Motion:** a 30 mm push ramped in over only 6° (146–152°).

**R63c parameters:** `--from 137 --full 156 --gain 0.5 --sigma 0.08 --smooth 80`.
- The ramp now starts at 137°: the first solved control is 137, while 135/136 (the marked pose) stay untouched.
- It gives a wider, gentler, smoother push.

### R63c result (run 39442313870; media in `review-assets/shoulder_r63/`)

| Gate | R63c | R60 | Limit |
|---|---|---|---|
| Outline | 0.95 mm | 0.95 mm | 1 mm |
| Dense motion | **9.25 mm** | 9.25 mm | 0.5 mm |
| Early outward | 0 | 0 | 0.05 mm |
| 41-pose motion | 3.60 mm | 3.60 mm | 0.5 mm |
| Benchmark regressions | **6** | 6 | 0 |
| Contacts | 106 | 7 | 0 |
| Crease | 173° | 137° | 2° |

**Contact locations** (`contacts_where.txt`):
- **85 are trapezius self-contacts:** the 15 mm swell folds into itself beside the neck (|x| 7–9 cm, z 1.58–1.60), samples 32–40.
- **21 are posterior-armpit torso contacts** (around (−0.17, 0.07, 1.40)), including R52's original 7 (triangle 10855 vs 22184–22187).

**Visual:** the owner's circled dip is filled with a straight, smooth arm-into-body line at 156/166° (`R52_vs_R63c_armpit_156_166.jpg`), and it is smoother than R63.

**R63d:** taper the trapezius swell to zero within 9 cm of the midline, full from 12 cm (`--trap-neck-taper 0.09,0.12`).

### R63d result (run 39444882093; trapezius neck taper 9–12 cm)

| Gate | R63d | R60 | Limit |
|---|---|---|---|
| Contacts | **21** (R63c 106) | 7 | 0 |
| Benchmark regressions | **5** | 6 | 0 |
| Outline | 0.95 mm | 0.95 mm | 1 mm |
| Dense motion | 9.25 mm | 9.25 mm | 0.5 mm |
| Early outward | 0 | 0 | 0.05 mm |
| Crease | 173° | 137° | 2° |

- **The neck taper worked:** every trapezius self-contact is gone.
- **The 21 contacts left** are all torso skin at the back of the armpit, around (−0.17, 0.07, 1.40), at samples 25/26 and 31–35. They include R52's original triangle 10855 vs 22184–22187.

**Owner (20 Oct), on R63c:** "There is still the incorrect section at the armpit to solve." Claude's rear sweep (132–166°) confirms a smaller corner remains at the arm/torso junction from ~151°.

**R63e (queued after R63d):**
- `--torso-max 0.7`: the shared corner skin may move.
- `--top 0.06`: fill 6 cm higher.
- `--arm-margin 0.003`.

### R63e result (run 39445422665) and R63f

**R63e** (corner fill: `--torso-max 0.7 --top 0.06 --arm-margin 0.003`):

| Gate | R63e | R63d | Limit |
|---|---|---|---|
| Contacts | 39 | 21 | 0 |
| Benchmark regressions | 7 | 5 | 0 |
| Outline | 0.95 mm | 0.95 mm | 1 mm |
| Dense motion | 9.25 mm | 9.25 mm | 0.5 mm |
| Early outward | 0 | 0 | 0.05 mm |
| Crease | 168° | 173° | 2° |

- **Where the extra contacts are:** the 18 new ones are upper arm against torso at the **benchmark-press samples 77–81**. The generator had only been solved against the main press samples 0–40.
- **Visual:** `rear_sweep_R52_R63d_R63e.jpg` shows the corner under the arm is largely gone in R63e from 156° up (R63d still has a small notch).

**R63f:** `--include-bench` also solves against every benchmark-press sample that uses the solved controls, with the same corner fill and 3 mm arm gap built in that pose. Elevation is read from Work's decoded control weights.

### R63f result (run 39449120792; `--include-bench`)

| Gate | R63f | R63e | Limit |
|---|---|---|---|
| Contacts | **72** | 39 | 0 |
| Dense motion | **20.6 mm** | 9.25 mm | 0.5 mm |
| Benchmark regressions | 8 | 7 | 0 |
| Crease | 174° | 168° | 2° |
| Outline | 0.95 mm | 0.95 mm | 1 mm |
| Early outward | 0 | 0 | 0.05 mm |

- **Contacts:** all 72 are torso self-folds. The arm/torso contacts are gone, but the back folds at samples 30–35 and 73–81.
- **Visual:** the corner fill is similar to R63e (`rear_sweep_R52_R63e_R63f.jpg`).
- **Diagnosis:** solving the main and benchmark press paths with equal weight gives conflicting targets for the same controls; the compromise folds the skin and adds motion.

**Best candidate so far:**
- **Visually, for the owner's corner:** R63e.
- **Numerically:** R63d (21 contacts, 5 benchmark regressions).

**Next options:**
- **(a)** Weight the benchmark samples low (e.g. 0.2), or make them gap-only constraints, so they only stop arm contact without driving the fill.
- **(b)** Accept R63e's 18 benchmark-path contacts as a known issue of that path's slightly different pose. That needs the owner's decision.

### R63g (owner chose option 1, 20 Oct): benchmark press as a contact guard only

`--guard-bench`: the R63e corner fill is solved on the main press only. Benchmark-press samples that use the solved controls act as **guards**:
- after each solve, any affected vertex brought within the 3 mm arm margin in a guard pose (and closer than the start) is pinned back to its start-candidate position in that pose (weight 4);
- re-solve, up to 6 iterations.

The guard never adds fill.

### R63g result (run 39452287262): best candidate so far for the press

| Gate | R63g | R63e | R60 | Limit |
|---|---|---|---|---|
| Outline | 0.95 mm | 0.95 mm | 0.95 mm | 1 mm |
| Dense motion | 9.25 mm | 9.25 mm | 9.25 mm | 0.5 mm |
| Early outward | 0 | 0 | 0 | 0.05 mm |
| 41-pose motion | 3.60 mm | — | — | 0.5 mm |
| **Contacts** | **21** | 39 | 7 | 0 |
| Reversed normals | 6 | — | — | 0 |
| Crease | 168° | 168° | 137° | 2° |
| Benchmark regressions | 6 | 7 | 6 | 0 |

- **The guard:** it pinned 39 vertices in round 1 and none in round 2. The 18 benchmark-path arm contacts are gone.
- **Visual:** the corner fill matches R63e (`rear_sweep_R52_R63e_R63g.jpg`).
- **R63g contains:** R60 smoothing; the 15 mm neck-tapered trapezius bunching (fade 136→160°); and the posed-space lockout sculpt (137–166°, corner fill, 3 mm arm gap, benchmark guard).
- **Remaining contacts:** 21 torso self-contacts at the back of the armpit (around (−0.17, 0.07, 1.40)), including R52's original 7.
- **Still failing:** motion 9.25 mm against 0.5 mm (the S7-only bound, an owner-accepted tolerance per "option 1"), crease, and 6 reversed normals; all are inherited.

**Next:**
1. Owner review of R63g.
2. Localise and fix the 21 posterior-armpit self-contacts.
3. Then the pull-up (dead hang), using the same posed-space method.

## R64 (20 Oct): posterior armpit shape from anatomy references

**Owner mark:** R63g, 166° rear close-up. The posterior armpit, where the underside of the upper arm meets the side of the back, is wrong. The outline steps in, and the skin above the step crumples.

**References:**
- [Kenhub teres major](https://www.kenhub.com/en/library/anatomy/teres-major-muscle)
- [Kenhub latissimus dorsi](https://www.kenhub.com/en/library/anatomy/latissimus-dorsi-muscle)
- [Dartmouth BHA ch. 8](https://humananatomy.host.dartmouth.edu/BHA/public_html/part_2/chapter_8.html)
- [Wikipedia latissimus dorsi](https://en.wikipedia.org/wiki/Latissimus_dorsi_muscle)
- [Proko shoulder notes](https://www.proko.com/course-lesson/inventing-the-shoulder-muscles/notes)

**Target shape:** with the arm overhead, latissimus dorsi and teres major form one smooth, convex posterior axillary fold, running from the medial underside of the arm diagonally into the back. There is no notch, the skin is taut and unwrinkled, and the hollow of the armpit lies in front of the fold.

**Code changes** (`scripts/shoulder_r61/generate_r63_lockout.py`):
- `--fold`: outward-only Laplacian relax in a rest-space posterior-armpit region (centre (±0.17, 0.07, 1.40), radius 0.10 m).
  - Fills dents and evens out facets, and never pushes bumps in.
  - Cap: 25 mm.
- `--hull`: the rear-view outline is filled to its **outward convex envelope**. This replaces R63's straight arm-edge line, which used gain 0.5 and so only half-filled the gap.
- **Finding:** R63's arm-distance cap (`--arm-margin`) is about 0 right at the arm/back join. That is what held the notch, so R64c onward run with `--arm-margin 0`. The benchmark guard is kept.

**Variants and close-ups:**
- Close-ups are in `review-assets/shoulder_r64_closeups/` (`R64b_closeups/` … `R64e_closeups/`, plus the `compare_*_166deg_*.jpg` comparisons).
- Workflows: `shoulder-r64-closeups.yml` (matrix) and `shoulder-r63-lockout.yml` (gates and video; currently R64d).

| Variant | Flags | 166° rear outline |
|---|---|---|
| R64 | `--fold` | crumples reduced, step remains |
| R64b | + `--hull --gain 1.0`, arm cap 3 mm | step remains (cap) |
| R64c | + arm cap 0 | step mostly gone; the 80-pass smoothing dilutes the push (40 → 27 mm) |
| **R64d** | + `--smooth 30` | **one smooth convex arm-to-back line (best)** |
| R64e | + `--top 0.10 --maxpush 0.045 --sigma 0.10` | similar outline; spreads towards the neck |

**R64 gates (run 39460581242):**
- Contacts 21 → **7**. These are only R52's original 7, at samples 25/26/65/66, on protected or approved controls.
- Crease 168 → 146°.
- Outline 0.95 mm (pass). Early outward 0 (pass).
- Worse: dense motion 13.1 mm (R63g 9.25), benchmark regressions 9 (R63g 6), and the **adjacent step fails (4.58 mm > 3 mm)**. Fix: raise the temporal penalty `--lam`.

### R64d → R64j: adjacent step (20 Oct)

**R64d gates (run 39463799503):**
- Contacts: 13. These are R52's 7 plus 6 torso self-contacts on the benchmark press at samples 72–74.
- Dense motion: 9.25 mm. Crease: 137°. Benchmark regressions: 7.
- **Adjacent step: 5.27 mm (fail).**

Things that did not fix the step (R64f–i, close-ups only):
- `--lam` 1 / 3: step 4.2 mm.
- `--full 164`: step 4.1 mm.
- lighter fold: step 4.3 mm.

The worst step was a few vertices between controls 162 and 163, at rest (−0.285, 0.038, 1.437).

**R64j:** `--step-limit 0.0029`. After the solve, any vertex whose control curve steps more than 2.9 mm between adjacent controls has that curve relaxed in time ([1,2,1]/4 on the free controls). This took 73 iterations, 5.27 → 2.90 mm. The 166° outline is visually unchanged from R64d.

**R64j gates (run 39466912968) — current best for the press:**

| Gate | R64j | R63g | Limit |
|---|---|---|---|
| Outline | 0.95 mm | 0.95 mm | 1 mm |
| Early outward | 0 | 0 | 0.05 mm |
| **Adjacent step** | **pass (2.9 mm)** | pass | 3 mm |
| **Contacts** | **10** | 21 | 0 |
| **Crease** | **137°** | 168° | 2° |
| Benchmark regressions | 6 | 6 | 0 |
| Dense motion | 12.07 mm | 9.25 mm | 0.5 mm |
| 41-pose motion | 4.59 mm | 3.60 mm | 0.5 mm |
| Reversed normals | 6 | 6 | 0 |

**Contacts:**
- 4 are R52's originals, at samples 25 and 65, on approved or protected controls.
- 6 are benchmark-press torso self-contacts at samples 72–74. The guard only checks arm distance, so it misses torso-torso contacts.

**Command:** see `shoulder-r63-lockout.yml`.
- Generator flags: `--fold --hull --gain 1.0 --arm-margin 0 --smooth 30 --step-limit 0.0029`, on top of the R63g flags.
- Media: `review-assets/shoulder_r64/R52_vs_R64j_press.mp4`, plus `review-assets/shoulder_r64_closeups/R64j_closeups/`.

**Next:**
1. Owner review of the 166° outline (R64d/j).
2. Extend the benchmark guard to torso self-proximity at samples 72–74, for the 6 benchmark contacts.
3. Reduce the dense-motion rise, 9.25 → 12.07 mm. This is an owner-accepted tolerance per "option 1", but it should not grow.
4. Then the pull-up dead hang.

## R65 (20 Oct): owner reference photos — fuller arm root, wider upper back, trapezius 25–30 mm

**Owner's photos** (seen in chat only; reference photos stay out of git): a dumbbell press lockout, a pull-up dead hang and a barbell press lockout, all from behind.

What they show, compared with R64j:
1. The arm stays thick into the body. The rear deltoid, the underside of the arm and the top of the lat form one rounded mass; R64j's arm base looks pinched.
2. The shoulders shrug up. The trapezius rises to about ear level and little neck shows.
3. The upper back is widest just under the arms.

**Owner decisions:** go ahead; **option (a)** for the shoulders, i.e. trapezius bunching raised to about 25–30 mm, skin only, with no skeleton change.

**New generator flags** (`scripts/shoulder_r61/generate_r63_lockout.py`):
- `--root-mm`, `--root-whole-back`: inflate the back half of the upper-arm weight-blend ring along the posed normal.
- `--root-smooth N`: use smoothed normals and a smoothed push.
- `--root-relax`: run the R64 outward-only relax over the arm root too.
- `--lat-bulge`, `--lat-bulge-span`: add a sine bulge to the hull outline under the armpit.

The close-up renderer now also writes `*_back_full.png`, a whole-back view framed like the photos.

**Variants and close-ups** (`review-assets/shoulder_r64_closeups/R65*_closeups/`, plus the `compare_*`):

| Variant | Settings | Result |
|---|---|---|
| R65a / R65b | arm-base fill 10/15 mm, lower ring only, bulge 8/12 mm, trapezius 25/30 mm, taper 0.09–0.12 | barely visible |
| R65c / R65d | arm-base fill 25 mm, whole back of the ring, taper 0.06–0.10 / 0.04–0.08 | outline like the barbell photo, but lumps and a dark crease on the arm |
| R65e | + `--root-smooth 40` | lumps gone |
| **R65f** | + `--root-relax` | **smoothest; arm thicker into the body (visual pick)** |

**R65f gates (run 39471273333):**
- **314 contacts.** 310 are trapezius self-contacts, caused by the narrow neck taper (0.04–0.08); the rest are R52's 4. The 6 benchmark-path torso contacts from R64j are gone.
- Dense motion 21.2 mm. 41-pose motion 8.2 mm.
- Adjacent step: pass. Outline 0.95 mm: pass.
- Benchmark regressions: 9.

Lesson: the trapezius push near the neck needs the wider taper, as in R63d.

**Running now:** R65g (trapezius 30 mm, taper 0.09–0.12) and R65h (25 mm, taper 0.06–0.10), as a matrix in `shoulder-r63-lockout.yml`. Media goes to `review-assets/shoulder_r64/R65g|R65h/`.

**Still open:** the head sits high and the neck shows more than in the photos. Part of this is likely skeletal (the shoulder blades and collarbones don't lift enough). The owner chose the skin-only option, so the skeleton is untouched.

### R65g / R65h gates (run 39473694860): R65f with the wide trapezius neck taper restored

R65g is trapezius 30 mm with taper 0.09–0.12; R65h is 25 mm with taper 0.06–0.10. Both give the same gate maxima:

| Gate | R65g | R64j | R63g | Limit |
|---|---|---|---|---|
| Outline | 0.95 mm | 0.95 | 0.95 | 1 mm |
| Early outward | 0 | 0 | 0 | 0.05 mm |
| Adjacent step | pass (2.9) | pass | pass | 3 mm |
| **Contacts** | **4 (R52 originals only, samples 25/65)** | 10 | 21 | 0 |
| Crease | 137° | 137° | 168° | 2° |
| **Benchmark regressions** | **5** | 6 | 6 | 0 |
| Dense motion | 21.2 mm | 12.1 | 9.25 | 0.5 mm |
| 41-pose motion | 8.2 mm | 4.6 | 3.6 | 0.5 mm |
| Reversed normals | 6 | 6 | 6 | 0 |

**Current best press candidate: R65g.** It is unsaved and not approved.
- Media: `review-assets/shoulder_r64/R65g/` and `review-assets/shoulder_r64_closeups/R65g_closeups/`.
- Comparison image: `compare_R64j_R65g_166deg.jpg`.
- Commands: the matrix entry R65g in `shoulder-r63-lockout.yml`.

**Open items:**
1. Motion rose (dense 21 mm). The arm-root fill moves quickly over 137–156°. Try `--full 160` or a lower `--root-mm` to bring it back down. This is judged by eye under the owner's option 1, but it should not grow.
2. The neck still shows more than in the owner's photos. Skin-only trapezius bunching (option a) has reached what it can do without self-contacts. The rest would need the shoulder blades and collarbones to lift more (option b, skeleton), which needs an owner decision.
3. Small crinkles remain where the top of the arm meets the trapezius.
4. Then the pull-up dead hang.

## R66 (20 Oct): head widening and body pulse

Owner, on R65g: "Why does the body still pulse when the arms move and why now does the head widen also?"

**Measurement:** silhouette widths per frame on the review videos (rear panel, rows through the head and the upper back). The script is in the scratchpad; the method is to take the width of the lit run through the panel centre on each row.

**Head widening:**
- R65g was +10 px against R52 at the lower head over the last frames (about 20%), starting at about 150°.
- History: R62b 0 px; R63 / R64 +5 px; R64d onward +10 px.
- Cause: my rear-outline fill (`lat_fill`). At lockout the armpit is at head height, so the fill band (up to `--top` above the armpit, sides with u > 0.03) included the head and neck.
- Fix: `--protect-head`. All lockout target changes are multiplied by 1 − smoothstep((z − 1.48)/0.05) × smoothstep((0.14 − |x|)/0.03), with rest-space head z ≥ 1.59 and neck z 1.51–1.61, |x| ≤ 0.11 (read from the R41 .blend).
- Result: 0 px difference from R52.

**Body pulse:**
- The upper back under the arms narrows, widens, narrows and widens between about 118° and 166°: at row 285, 134 → 127 → 137 → 129 → 138 px, about 1.5 cm per side.
- **R52 is identical, so this is inherited from the S7 increments.** The first dip sits on the approved marked pose.
- Fix: `--pulse-smooth` (`scripts/shoulder_r61/pulse_smooth.py`).
  1. Take each torso vertex's posed trajectory over the 41 main press samples.
  2. Low-pass it in time with a second-difference penalty (β), holding samples that use only fixed controls exactly.
  3. Batched least squares on the free controls 111–134 and 137–166.
  - Controls 95–110 and 135/136 (the marked pose) are asserted unchanged. The step limit now also covers 111–134 with 135/136 kept.

**Variants:**

| Variant | Smoothed torso set | Contacts | Benchmark regressions | Row-285 width after the marked pose |
|---|---|---|---|---|
| R66a | z < 1.50, arm weight < 0.2, β 30 | 12 (8 new, armpit/shoulder top) | 7 | 128 → 134 → 132 → 138 |
| R66b | same, β 100 | 28 | 10 | similar |
| **R66c** | **z < 1.38, arm weight < 0.1, β 30** | **4 (R52 originals)** | **5** | **128 → 133 → 132 → 138 (1 px bump)** |
| R66d | z < 1.34, arm weight < 0.05 | 4 | 5 | bounce 137 → 133 remains |

**R66c gates (run 39482244424):**
- Outline 0.95 mm (pass), early outward 0 (pass), adjacent step (pass).
- Contacts 4, all R52 originals at samples 25 and 65.
- Benchmark regressions 5.
- Crease 132°.
- Dense motion 23.4 mm and 41-pose motion 9.5 mm. These are worst-case figures not on the visible pulse; they are dominated by the lockout arm-root fill.
- Head: 0 px difference from R52.
- Torso second difference in the smoothed set: 8.3 → 2.6 mm.

**Current best press candidate: R65g + head protection + pulse smoothing = R66c** (unsaved, not approved).
- Media: `review-assets/shoulder_r64/R66c/`.
- Command: the matrix entry R66c in `shoulder-r63-lockout.yml`.

**Still open:**
- The single narrowing into the approved 135.6° pose remains. Its width is locked by the approved outline.
- Dense-motion worst case from the arm-root fill.
- Neck exposure (skeleton option b, not authorised).
- Then the pull-up dead hang.

## R67 (20 Oct): the arm looks detached from the shoulder; the trapezius looks wrong

**Owner, on R66c at 156° rear** (circled the whole shoulder top): "It looks like the arm isn't attached to the shoulder. And also the traps are horrible looking."

**Diagnosis** (156° rear across versions):
- R63g / R64j already show a flat trapezius shelf with a small knob next to the neck, and a crease across the top of the arm root.
- R65's 30 mm trapezius enlarged the knob.
- R65's arm-root ring fill made a hard-edged collar, read as a seam, so the arm looks detached.

**Girdle check** (option 3: skeleton first, report only; measured locally with bpy on the R41 rig, press path v4, lockout 166°):

| t | Elevation | Clavicle above horizontal | Clavicle vs rest | Scapula vs rest | Acromion vs head base |
|---|---|---|---|---|---|
| 0 | 70° | 10.4° | 6.8° | 18.4° | −76 mm |
| 0.625 | 135.6° | 22.2° | 19.4° | 45.4° | −40 mm |
| 0.8 | 156° | 33.9° | 30.6° | 55.8° | −6 mm |
| 1.0 | 166° | 38.0° | 35.0° | 60.3° | +5 mm |

- Literature: SC clavicle elevation is typically under 10° during arm elevation ([PMC2730194](https://pmc.ncbi.nlm.nih.gov/articles/PMC2730194); [Ludewig handout](https://www.orthopt.org/uploads/content_files/2014_Annual_Meeting_Handouts/Sahrmann___with_Ludewig_Scap___humerus.pdf)); scapular upward rotation is about 50–60° at maximum.
- The rig, at 35° and 60°, is already at or above the literature range. **No skeletal change is warranted**; the problem is soft tissue.

**New generator flags:**
- `--shoulder-relax N` with `--shoulder-mu` (−0.51): Taubin smoothing over the shoulder top (rest sphere (±0.21, 0.02, 1.48), r 0.10) plus the R62 trapezius region. Tested on a synthetic knob: 4% → 1.3% with no growth.
- `--shoulder-rise`: the shoulder-line sculpt. Seen from behind, the top skin between the neck edge and the arm's inner edge is lifted in +z to a convex curve that rises `rise` up the arm (5 mm bins, Gaussian `--shoulder-line-sigma` below the top).
- `--protect-head` narrowed: full at |x| < 0.09, none beyond 0.115.

**Close-up variants** (`review-assets/shoulder_r64_closeups/R67*_closeups`):

| Variant | Changes | Result |
|---|---|---|
| R67a | trapezius 15 mm, no root ring | |
| R67b | + relax 300 | seam and creases softer, smaller knob; flat shelf remains |
| R67d | + rise 30 mm | |
| **R67e** | **+ rise 50 mm** | **the trapezius slopes up into the arm and the arm reads as attached (visual pick)** |
| R67c | R65g's 30 mm trapezius + ring + relax | |

Gates for R67d/e are running in `shoulder-r63-lockout.yml`.

## R68 (20 Oct): root cause of the rear shoulder / armpit deformation

**Owner brief:** fix the cause, not the look. The illustration is guidance only. Test the full range, all views, both sides and arm rotations; give before/after renders and numbers; don't mark it complete until the tests pass.

**Method:** local bpy on Work's immutable R41 rig (sha-checked). Script: `scripts/shoulder_r68/diagnose_shoulder_skinning_blender.py`.
- Poses: 0°, 45° (coupled arm raise); 90°, 120°, 135.6°, 156°, 166° (press path v4).
- Metrics per side, on the shoulder region and its rear half:
  - triangle area ratio posed/rest: pinched < 0.5, stretched > 1.8;
  - folds: adjacent faces more than 100° apart;
  - self-intersections (BVH);
  - whole-body volume;
  - left/right mirror asymmetry.
- Results: `review-assets/shoulder_r68/local_r41/`.

**Cause, layer by layer:**

| Layer | Finding |
|---|---|
| Skeleton / joint motion | At or above the literature range (clavicle +35°, scapula 60° at lockout; see R67). Not the cause. Unchanged. |
| Skinning method | One Armature modifier, linear blend (Preserve Volume off). Raw linear skinning loses rear-shoulder area above about 90° (rear pinched 38 → 159 from 90° to 166°). Dual-quaternion skinning keeps the area but over-inflates the whole shoulder (+9.6% body volume at 166°). |
| **Corrective keys** | **The S7 deltoid family (HGPT_S7_DELT_*) compresses the posterior deltoid / posterior axillary fold.** Rear triangles < 50% area: current 425 → **63** with only S7 off at 135.6°; 375 → 109 at 156°. S1/S3/S5/H1/C1 change it little (`r68_family_ablation.json`). The pinched triangles' rest centroid is (0.234, 0.07, 1.49): the back of the shoulder cap. |
| Topology | Not changed. Crinkles in the posterior axilla remain in every configuration, so edge flow there may also matter (not yet tested). |

The approved R48 outline is measured only in the ±x and (±x, −y)/√2 directions, so the rear surface is free to change without touching it.

**Fix at the source:** `scripts/shoulder_r68/rear_restore_s7_blender.py`, applied to each S7 key at its own elevation, both sides:
1. Laplacian editing of the rear-shoulder region: surface detail from the S7-off skin, boundary from the current skin.
2. Every approved-outline support vertex (Work's `silhouette()`) and its one-ring are pinned.
3. A smooth weight centred on the measured pinch (r 0.10 m).
4. The result is mapped back to rest-space key offsets through each vertex's exact skinning matrix (probe key).
5. Output: sparse deltas in `scripts/shoulder_r68/data/r68{d,e}_s7_rear_restore.npz`. Claude's installer applies them with `R68_S7_SPARSE` before the dense increments.

**Variant results (local R41, right side; left matches):**

| Variant | Rear pinched, 120 / 135.6 / 156 / 166° | New folds / self-intersections | Outline change |
|---|---|---|---|
| current | 415 / 425 / 375 / 480 | — | — |
| R68a (hard region) | 40 / 59 / 91 / 113 | folds +6–8, self-intersections up to 13 → **rejected** (crease at the shoulder top) | |
| R68d (blend 1.0, weight) | 196 / 203 / 162 / 237 | 0 | 0.000 mm |
| **R68e (blend 0.7)** | **241 / 248 / 202 / 311** | **0** | **0.000 mm** |
| R68f (ARAP to rest) | 180 / 193 / 146 / 192 | 0, but buckles into a sharp flap visually → **rejected** | |

- Rotation robustness (humeral axial ±30° at 90° / 120° / 156°): R68e lowers rear pinch 35–45% at 120° and 156° in every rotation, with no new self-intersections (1 at 156°/+30°) and symmetric sides.
- 90°: unchanged, since S7 starts at 110°. The remaining 90° pinch comes from linear skinning plus S1/S5 (open item).

**In the press candidate (CI, on R67b):**
- R68d gives a distinct ball-like rear deltoid with a groove: an artificial bulge.
- R68e is softer: a rounded rear deltoid mass, but still lumpy, with crinkles in the posterior axilla.
- Reason: the S7-off reference skin carries linear-skinning bulge shapes of its own.
- Gates for R68d/e are running in `shoulder-r63-lockout.yml`.

**Not complete:**
- **Visual:** the rear deltoid is a lump rather than a smooth taper into the arm.
- **Crinkles:** remain in the posterior axilla.
- **At 90°:** the pinch is untouched.
- **Gates:** contacts, motion, benchmark and crease still need confirming on R68.

**Next options:**
- (a) A per-vertex linear/dual-quaternion skinning blend in the shoulder only (multi-modifier), as the volume source instead of the S7-off skin, with outline re-pinning.
- (b) Re-author the S7 keys with an explicit rest-area constraint plus smoothness (constrained Laplacian), which avoids both the bulge and the ARAP buckling.
- (c) A topology/edge-flow check of the posterior axilla.
