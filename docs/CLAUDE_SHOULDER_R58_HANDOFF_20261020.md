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

**Option (a) tested (R68g): rejected.** A per-vertex linear/dual-quaternion blend in the shoulder only (second Armature modifier with Preserve Volume, multi-modifier, weight 0.6 around the pinch centre), with the correctives on:
- rear pinch falls only modestly: 425 → 343 at 135.6°, 375 → 310 at 156°;
- new folds (up to 26) and self-intersections (up to 36 at 166°);
- **the approved outline moves 11–15 mm.**

So the skinning-method change is not viable without re-approving the outline. The S7 key rebuild (R68e) remains the best root-cause fix found.

### R68 in the press candidate: gates (run 39496277724)

The R68 fix now goes in through the dense increments (generator `--r68 <npz>`). This is exactly equivalent to changing the R41 S7 keys, but keeps Work's affine pose model exact. The first attempt changed the keys inside the installer, which broke the native affine gate (execution = 1).

| Gate | R67b (base) | **R68e** | R68d | Limit |
|---|---|---|---|---|
| Outline at marked pose | 0.95 | **0.95 (pass)** | 0.95 | 1 mm |
| Early outward | 0 | **0 (pass)** | 0 | 0.05 mm |
| Adjacent step | pass | **pass** | pass | 3 mm |
| Contacts | 7 | **7 (unchanged; 4 are R52 originals)** | 7 | 0 |
| Reversed normals | 6 | **6 (inherited)** | 6 | 0 |
| Benchmark regressions | 7 | **6** | 6 | 0 |
| Dense motion | 18.91 | **18.91** | 27.23 | 0.5 mm |
| 41-pose motion | 7.62 | 7.62 | 7.62 | 0.5 mm |
| Crease | 132.8° | 132.8° | 132.8° | 2° |

- **R68e adds no gate regressions** and removes one benchmark regression.
- **The correction is NOT complete:** the inherited failures (contacts, normals, motion, crease, benchmarks) remain, and visually the restored rear deltoid still reads as a lump with posterior-axilla crinkles.
- Before/after sheets: `review-assets/shoulder_r68/before_after/` (R67e against R68e at 135.6°, 156° and 166°; six views each).

## R69 (20 Oct): "the shoulder looks good but the arm still has that bit at the armpit"

**Owner on R68e:** the shoulder is good; the arm still has the bit at the armpit.

**First attempts on bare R41, which failed in the press pipeline:**
- R69a/b: thin-plate rebuild of the inner-arm crease inside the S7 keys. R69b's gates: outline 5.9 mm, 71 contacts, 12 benchmark regressions. The inner-arm patch lies on the front-lateral outline, whose support vertices differ in the R52 candidate from bare R41.
- R69c: posterior-groove pass only. Contacts 7 → 1, but outline 2.5 mm and 13 reversed normals.
- R69d: R69c plus candidate-geometry pinning in the generator (`--r68-pin`). Gates OK, but almost no visual change.

**Finding the real source.** The close-up workflow now exports the candidate's dense increments (`candidate_dense_f32.npz`) and R52's. `diagnose_shoulder_skinning_blender.py` can install them locally (`R69_DENSE`); its local renders match CI exactly.

Arm-underside folds (> 45°) at 156° in the press candidate:

| Variant | Arm-underside folds at 156° |
|---|---|
| R52 | 0 |
| candidate | 18 |
| without the outline fill (`--hull`) | 9 |
| without the fold relax | 14 |
| without the shoulder relax | 18 |

So the bit is made by my lockout outline fill plus the S7 rear restore.

**Fix (R69f):**
- The R68/R69 S7 change is added to the start candidate, so every posed-space stage sees it.
- New `--armpit-tp 0.05`: in each lockout pose, a thin-plate (bi-Laplacian) rebuild of the arm-underside patch at the armpit (rest centre (±0.209, 0.005, 1.367), r 5 cm), with that pose's approved-outline support (Work's `support_vertices`) and a 2-ring pinned. It is solved into the controls like the other lockout targets.
- Arm-underside folds > 45°: 156° 18 → **2**, 166° 13 → **0** (R52: 0 and 8).
- Pinched triangles remain about 100, against R52's 40–69.

**R69f gates (run 39513829888)** — no regressions against R68e:

| Gate | R69f |
|---|---|
| Outline | 0.95 mm (pass) |
| Early outward | 0 (pass) |
| Adjacent step | pass |
| Contacts | 7 (4 are R52 originals) |
| Reversed normals | 6 |
| Benchmark regressions | 6 |
| Dense motion | 18.91 mm |
| 41-pose motion | 7.62 mm |
| Crease | 132.8° |

- Media: `review-assets/shoulder_r64/R69f/`, `review-assets/shoulder_r64_closeups/R69f_closeups/`, `review-assets/shoulder_r68/before_after/R67e_vs_R69f_press_slow.mp4` and `R67e_R69d_R69f_R69g_*deg.jpg`.

**Still open:**
- A faint dark groove in the rear three-quarter view where the rear deltoid meets the back.
- Arm-underside pinch above R52.
- The front-axilla diagonal fold (present in R52 too).
- The inherited gate failures.

## R70 (21 Oct): new top of the press (owner option C, chose "150 with 30")

**Owner reference:** a real dumbbell-press photo from behind. The elbows stay slightly bent and flare out at the top. The owner chose the 150° elevation / 30° elbow option from a local render sheet (`review-assets/shoulder_r70/`).

**Path** (`scripts/shoulder_r61/r70_press_path.py`, env `R70_TOP=150:30:10`, patched in by Claude's installer):
- Identical to Work's path v4 up to the approved marked pose (t = 0.625, 135.6°, elbow 44.3°).
- After that it eases to 150° elevation, 30° elbow bend and a 10° elevation plane.
- Elevation and elbow are both monotonic, with the original slope at the join.

**Pose model** (`build_r70_source_blender.py`, run in CI before everything else):
- Rebuilds Work's affine model for main samples 26–40: native base with dense = 0, an exact per-vertex skinning matrix by probe key, and Work's `coefficients()` weights from the stored basis.
- Self-check: samples 0–25 reproduce Work's model (base 0.0003 mm, mat 5e-5, weight 2e-6).
- Native gates then run against it; the affine 0.01 mm check passes.

**Generator:** sample elevations are now read from the pose model, and the lockout ramp reaches full at 148°.

**R70a** (R69f configuration on the new path; gates run 39557102983):

| Gate | Result |
|---|---|
| Outline | 0.95 mm (pass) |
| Early outward | 0 (pass) |
| Adjacent step | pass |
| Contacts | 6 (3 are R52 originals at sample 25) |
| Reversed normals | 6 |
| Benchmark regressions | 6 |
| Dense motion | 24.1 mm (R69f 18.9) |
| 41-pose motion | 8.9 mm (R69f 7.6) |
| Crease | 150.7° (R69f 132.8°) |

- Media: `review-assets/shoulder_r64/R70a/`, `review-assets/shoulder_r64_closeups/R70a_closeups/`, `review-assets/shoulder_r68/before_after/R67e_vs_R70a_press_slow.mp4` and `top_R69f_166_vs_R70a_150.jpg`.

**Still open:**
- The motion and crease figures are worse: the lockout layers were tuned for the old straight-arm top and still sit at 137–150°.
- The build differs from the photo (option A kept: no extra muscle).
- The front-axilla fold.
- The inherited gate failures.

## R71 (21 Oct): small crease inside the arm at the shoulder top

**Owner on R70a:** "It looks good to me." The one doubt is a small fold on the inside of the arm, marked on the 150° rear close-up.

**Location:** the owner's mark was matched through the rear close-up camera to a crease of about 33° between adjacent faces, at rest (0.258, −0.011, 1.456). Tool: the `creases` mode of `diagnose_shoulder_skinning_blender.py`, on the exported R70a dense with `R70_TOP`.

**Fix:** a second thin-plate patch in the same generator stage (`--armpit-tp-centre` now takes several centres separated by "/"). R71b uses r 6 cm with centres (0.209, 0.005, 1.367) and (0.258, −0.011, 1.456). The zoom comparison `R70a_R71a_R71b_inner_crease_zoom_150deg.jpg` shows the corner rounded off.

**R71b gates (run 39560785701)** — same as R70a, except benchmark regressions 6 → **7**:

| Gate | R71b |
|---|---|
| Outline | 0.95 mm (pass) |
| Contacts | 6 |
| Reversed normals | 6 |
| Dense motion | 24.1 mm |
| Crease | 150.7° |
| Adjacent step | pass |

- Media: `review-assets/shoulder_r64/R71b/`, `review-assets/shoulder_r64_closeups/R71b_closeups/`, `review-assets/shoulder_r68/before_after/R70a_vs_R71b_press_slow.mp4`.

**Next:**
1. Find which benchmark regressed (R70a → R71b) and pin it.
2. Re-tune the lockout layers for the new 150° top (motion 24 mm, crease 151°).
3. The front-axilla fold.
4. The pull-up dead hang.

## R72 (21 Oct): lump and crease where the arm meets the shoulder, from behind

**Owner on R71b:** circled the arm–shoulder junction on the 150° `arm_shoulder_rear` close-up: "It's this bit I'm not so sure about."

**Location:** the `markmap` mode of `diagnose_shoulder_skinning_blender.py` maps the circle to 465 visible vertices. Their rest centroid is (0.244, 0.005, 1.432), and the p90 radius is 9.8 cm. The circle covers a rounded mound on the back of the arm root, with a crease above it and a dark groove below.

**R72a/b (thin-plate patch over that area, r 6 / 8 cm):** barely changed the mound. A thin-plate patch smooths creases but cannot remove a broad, smooth bulge.

**Cause, found by elimination at 150° on the R70 path:**

| Mesh | Mound? |
|---|---|
| R41 rig, all dense increments zero | No |
| Work's R52 | No |
| Every Claude candidate since R69d (with or without hull, fold or shoulder relax) | Yes |
| R52 + the r69c S7 rear restore alone | Yes, the same mound and crease; very visible from the side |
| R52 + half of r69c | Still visible |

The r69c S7 rear restore adds up to 25 mm to the posterior-deltoid keys (110–166). It was built against the old straight 166° lockout, where LBS pinched the rear shoulder. On the new 150° / elbow 30° / plane 10 top, R52 is not pinched there, so the restore overshoots into a lump.

- Images: `review-assets/shoulder_r72_traps_closeups/cause/`.

**R72c/d (close-ups workflow):** R71b settings without `--r68`.
- R72c keeps the two crease patches.
- R72d has no patches.

**Result:** in the close-ups (rear, side, above-rear and traps, at 135.6° and 150°), the mound is gone in both R72c and R72d, and the arm root runs smoothly into the back. The two look almost the same. R72c is the candidate because it keeps the two R71 crease patches.
- Images: `review-assets/shoulder_r72_traps_closeups/fix/`.

**R72c gates (lockout workflow):** the same as R71b on every check, so removing the rear restore cost nothing in the numbers.

| Gate | R72c |
|---|---|
| Outline | 0.95 mm (pass) |
| Reversed normals | 6 |
| Contacts | 6 |
| Native motion | 8.93 mm |
| Crease | 150.7° |
| Dense motion | 24.05 mm |
| Early outward | pass |
| Adjacent step | pass |
| Benchmark regressions | 7 |

The status is still `R57_REJECTED_OR_INCOMPLETE_NATIVE_GATES`. Not approved, and not saved, merged or deployed.
- Media: `review-assets/shoulder_r64/R72c/`, `review-assets/shoulder_r68/before_after/R71b_vs_R72c_press_slow.mp4`.

**Open:**
- The pinch that r69c was made for (old 166° top) should be re-checked on the 150° path over the full range.
- The motion, crease and benchmark failures that R70/R71 inherited.
- The front-axilla fold.
- The pull-up dead hang.

**Owner decision (21 Oct), after seeing the R72c front views** (`review-assets/shoulder_r73_front/`): "Great let's lock that in now."

R72c is now the visual baseline for the shoulder, armpit and arm-root shape on the 150° / elbow 30° / plane 10 press top:
- generator settings: the R72c row in `shoulder-r63-lockout.yml`;
- dense increments: `review-assets/shoulder_r64_closeups/R72c_closeups/candidate_dense_f32.npz`.

Later work must keep this look; compare any change against R72c close-ups (rear, side, above-rear, front).

This records the owner's visual sign-off on the shape only. The numerical gates still fail (see the R72c gate table above), and nothing is approved, saved, merged or deployed.

**Front-axilla fold check (21 Oct).** The owner said it "looks fine to me", but asked for a check against other references before locking it in.

*References used* (photos stay out of git):
- the owner's arms-overhead front photo;
- the owner's front-right 3/4 dumbbell-press series;
- anatomy texts: the anterior axillary fold is the lower border of pectoralis major; the pectoralis major tendon untwists in full flexion; serratus digitations can show on the lateral chest in lean people.

*What the references show:* with the arms overhead, the front of the armpit is one smooth, rounded diagonal ridge running from the chest up into the arm, with a soft hollow behind it.

*What R72c shows:* the line circled on the 150° front close-up is in the right place, with the right direction and the right length. It is the pectoralis major edge, not a skinning fault.

*Sharpest creases* (adjacent-face angle, front of the right armpit, posed y < 0, `creases` mode):

| | 150° | 135.6° |
|---|---|---|
| R72c | ≤ 34° | the same as R52 |
| Work's R52 | ≤ 40° | — |

So R72c is no worse than Work's base, and slightly smoother at 150°.

*Only difference from the photos:* the lower third of the line is a little narrower and darker than real skin (a groove rather than a soft hollow). It is minor, it is inherited from R52, and it is not counted as wrong.

**Decision:** R72c's front of the armpit is kept as-is and locked in with the rest of R72c.

## R73 (21 Oct): full-range check and the 120° side-chest crease

### Full-range check of R72c against R52

Measured at 0, 45, 90, 120, 135.6, 145 and 150°, on both sides, and again with the arm turned −30 / 0 / +30° at 90, 120, 135.6 and 150° (`R68_ANGLES` and `R68_ROT_ANGLES` in `diagnose_shoulder_skinning_blender.py`).
- The rear-shoulder pinch counts match R52 at every angle, so the old pinch has not come back.
- 0–90° and 135.6° are identical to R52.
- At 145 and 150° R72c has no sharp folds, where R52 has some.
- Asymmetry is the same as R52's.
- Files: `review-assets/shoulder_r73_range/`.

### New finding: a jagged crease on the side of the chest at 120°

The crease sits at rest (0.161, 0.095, 1.381). Its sharpest angle is 134° in R72c against 63° in R52, and it was already present in R69d.

Close-up ablation:

| Version | 120° crease |
|---|---|
| R73a (R72c repeated, exact) | 134° |
| R73b (no pulse smoothing) | 64° |
| Start candidate | 64° |

The cause is the hard edge of the R66 pulse-smoothing set at `--pulse-zmax 1.38`; the crease lies exactly on it.

### Fix

New option `--pulse-taper` fades the pulse correction out over the edge of the set.
- R73c uses 4 cm. The crease drops to 57°.
- The locked-in 150° look is unchanged (`locked150_R72c_vs_R73c.jpg`).
- On the main part of the back the pulse smoothing still works as before: native-trajectory second difference at 1.25–1.32 m is p95 3.49 mm, as in R72c, against 3.75 mm with no smoothing (traj mode).
- R73d (8 cm) gives the same result.

### R73c gates

Identical to R72c on every check:

| Gate | R73c |
|---|---|
| Outline | 0.95 mm (pass) |
| Reversed normals | 6 |
| Contacts | 6 |
| Native motion | 8.93 mm |
| Crease | 150.7° |
| Dense motion | 24.05 mm |
| Benchmark regressions | 7 |

The status is still `R57_REJECTED_OR_INCOMPLETE_NATIVE_GATES`. Not approved, and not saved, merged or deployed.
- Video: `review-assets/shoulder_r68/before_after/R72c_vs_R73c_press_slow.mp4`.

**R73c replaces R72c as the candidate.** It is the same locked look, plus the 120° fix.

### Also found

The back width just under the armpits (z 1.35) narrows and widens 3 times between t 0.35 and 1, against once in R52. It is the same in every candidate with or without pulse smoothing, so it comes from the top-of-press (≥137°) layers. It belongs with the motion and crease gate work.

### Next

The inherited gate failures, re-tuned for the 150° top without changing the locked look:
- dense motion 24 mm;
- crease 151°;
- 7 benchmark regressions (find the R70a → R71b one);
- 6 contacts and 6 reversed normals;
- the z 1.35 width wobble.

Then the pull-up dead hang.

**Owner decision (21 Oct), after the R73c front views** (`review-assets/shoulder_r74_front_R73c/`): "No I think it's fine. I want the model to be accurate but I'm not sure delving into such fine detail is necessary."
- R73c is confirmed as the visual candidate.
- The small dark notch at the left armpit at 135.6° is left as-is. It is inherited from R52's approved marked pose.

Owner guidance for later work: aim for accuracy, without chasing very fine surface detail.

This is the owner's visual sign-off only. The numerical gates still fail, and nothing is approved, merged or deployed.

## R74 (21 Oct): targeted cleanup, first part (owner chose "Targeted cleanup")

**Owner direction:** fix what is real or visible, keep the locked look, report the remaining tiny-limit failures honestly, then move to the pull-up dead hang.

### Benchmark regressions

All 7 are in Work's `shoulder_press` benchmark (`bench.pose_press`: 90→160°, elbow straightening to 0). The other 12 movements are clean.
- Tools: `scripts/shoulder_r68/bench_local.py` (the local gate copy) and `bench_locate.py`.
- At t=0.75 (about 149°, elbow 14°) the top-of-press layers stretch the deep armpit to 14× its rest area (rest (±0.168, 0.086, 1.395)). 411 triangles are over 2×, against 10 for R52.
- **Cause:** the S7 dense correctives are keyed by elevation only, so the bent-elbow press path and the straight-arm benchmark share the controls at 137–150°.

### Fix attempts

- **R74a/b** (new `--guard-stretch`, pinning over-stretched skin back to the start candidate in the benchmark guard poses): rejected. The t=0.75 stretch fell to 181 / 280, but there were 25 new self-intersections and blotchy side-chest bumps in the straight-arm pose (`review-assets/shoulder_r74_straight_arm/`).
- **R74c** (the guard only in guard poses ≥ 151°, `--guard-stretch-from 151`, weight 4; controls the press path never uses):
  - The locked 150° look is unchanged (mean pixel difference < 0.4).
  - The local benchmark has 6 regressions. The t=0.875 self-intersection is gone; stretch at 0.875 / 1.0 is 65 / 52 (R73c 81 / 63, R52 23 / 30).
  - t=0.75 is unchanged at about 392. This is a known limit of elevation-only correctives and is left as reported.

### R74c gates

| Gate | R73c | R74c |
|---|---|---|
| Outline | 0.95 mm (pass) | 0.95 mm (pass) |
| Reversed normals | 6 | 6 |
| Contacts | 6 | **4** |
| Native motion | 8.93 mm | 8.90 mm |
| Dense motion | 24.05 mm | 23.97 mm |
| Benchmark regressions | 7 | **6** |
| Posterior crease | 150.7° | **162.4°** |

- The 4 contacts: 3 are at the marked pose t=0.625, in the left armpit (R52's notch, which the owner chose to leave). 1 is at benchmark sample 65.
- **Crease, located locally** (`crease_local.py`, the gate's measure against R52 natively): the worst edge is in both versions, deep in the armpit hollow at rest (0.16, 0.10, 1.39), in Work's straight-arm benchmark at t=0.85.
  - R73c 151° against R52, R74c 144°.
  - R74c is higher at benchmark t 0.78–0.83 (about 81° against 50°).
  - On the bent-elbow press path the same hollow folds 30–70° above R52 from sample 31 up.
- **Not visible** in any owner view. Treated as fine detail, per the owner's direction.

The status is still `R57_REJECTED_OR_INCOMPLETE_NATIVE_GATES`. Not approved, and not saved, merged or deployed.

**R74c is the candidate:** fewer contacts and benchmark regressions, and the same look.

**Next in the cleanup:** the back-width wobble at z 1.35 near the top of the press. Then the pull-up dead hang, where the straight-arm overhead armpit (controls above 150°) gets shaped for real.

## R75 (21 Oct): pull-up dead hang, first pass

**Owner decision:** "Match the photo." The hang is 170° elevation, a slightly wide grip (elevation plane 10°), straight elbows, and the shoulders shrugged up (12°).
- Pose: Work's `px.apply_pose` (0–180° coupled shoulder plus shrug) with the plane overridden.
- `diagnose_shoulder_skinning_blender.py`, `R68_MODE=hang`, `R75_HANG=ht:plane:shrug`. It renders the back, trapezius, rear and side armpit and front views, and lists the sharpest creases.

### First look (R74c and R52 alike)

| Problem | Where | Sharpest crease |
|---|---|---|
| Crumpled skin on top of the shoulder, where the deltoid meets the trapezius under the shrug | rest (0.28, 0.04, 1.45) | 115° |
| A folded flap at the front of the armpit | rest (0.19, −0.02, 1.36) | 121° |
| The chest pulled into thin straps to the arms | front view | — |

### Method

Our press stops at 150°, so the dense S7 controls above it are used only by straight-arm poses: Work's benchmark press up to 160°, and the hang, which reads the 166° control.

`scripts/shoulder_r68/hang_fix_blender.py`:
1. Poses the hang with the candidate installed.
2. Measures the exact per-vertex map M from a rest-space offset to the posed skin (probe key).
3. Builds the posed fix: Taubin relaxation over weighted regions (the armpit, the shoulder top and the front armpit), plus an optional outward fill along the normals of a heavily smoothed copy.
4. Maps the fix back: d = M⁻¹ δ.
5. Adds d to the controls with a smoothstep ramp. The native check against the target gives 0.000 mm.

Tried:
- **H1:** the armpit only. No visible change.
- **H2:** adds the shoulder top. The crumples are gone.
- **H3/H4:** a stronger front relax. Worse; the flap folded tighter.
- **H5 / H7:** H2 plus a 12 mm fill at the front armpit. The flap is gone from the crease list.

Ramp: a ramp from 151° made Work's straight-arm benchmark worse at 157–160° (stretch 158 / 330), because that pose has a different plane and no shrug. **H7** ramps from 160° instead, which changes only controls 161–166 (up to 31.6 mm at 166).

### Result (H7, saved as `scripts/shoulder_r68/data/r75_hang_dense_f32.npz`)

At the 170° hang:
- the shoulder-top crumples are gone (traps and armpit-rear views);
- the front-armpit flap is gone;
- the chest straps are slightly softer but still visible from the front.

Unchanged:
- the press path (controls ≤ 160 identical to R74c), so the locked look is untouched;
- the local benchmark: 6 regressions, the same as R74c.

At 165° the fix is only partial (shoulder-top creases up to 98°). That matters only during the pull-up transition.

Images: `review-assets/shoulder_r75_hang/hang170_R74c_vs_R75.jpg`.

H7 is a local dense candidate, not yet through the CI gates. It needs a closeups/lockout workflow that installs it: generator output plus this increment on controls 161–166. Not approved, and not saved, merged or deployed.

### R75b: the owner's real dead-hang photo (front and back); pose re-targeted

**Owner's photo** (shown in chat only; it stays out of git): the upper arms are nearly vertical beside the head, the shoulders are lifted so the head sits between the arms, and the shoulder blades are rotated up so the lats show as a wide V.

The model at 170 / 10 / 12 had a wider V from low, broad shoulders. That is mainly the skeleton pose, not the skin.

**Pose trials** (`hang_pose_trials_{front,back}.jpg`):

| Pose (elevation / plane / shrug) | Result |
|---|---|
| 175 / 5 / 20 | — |
| 178 / 0 / 25 | Matches the photo's arm line and head-between-arms; used from now on |
| 180 / 0 / 30 | — |

At 178 the skin folds over at the shoulder top (edges near 170°) and the front armpit.

**Hang fix re-run at 178 / 0 / 25** (`r75_hang178_dense_f32.npz`, H9):
- centres: the armpit, the shoulder top, the front armpit and the pec;
- fills of 16 mm at the front armpit and 10 mm at the shoulder top;
- 300 Taubin iterations;
- ramp from 160°, so only controls 161–166 change.

Result:
- the fold-overs are gone;
- the local benchmark has 6 regressions, unchanged;
- the press path is untouched.

**Still visible:** a groove where the arm meets the top of the trapezius (rear armpit view), and small lumps near the trapezius–arm junction. The lats and back are smoother and less V-shaped than in the photo.

## Body v2 (21 Oct): muscle definition on the R41 body

**Owner direction:**
- "The muscles need better definition." The owner supplied a 7-view lean-athletic reference set: front, back, side, both three-quarters, arms raised front and back, and close-ups. It appears AI-generated, so it is used as a style target only; it stays out of git.
- "Start now please."

**Tool:** `scripts/body_v2/build_body_v2_sculpt_blender.py`. Same mesh, skeleton and skin weights; only the rest surface changes.
- Skeleton-anchored muscle swellings: along the bones for the limbs, ellipsoids for the torso.
- Combined as a soft union, so a groove forms where bellies meet.
- The right side is mirrored to the left; symmetry error ≤ 0.012 mm.

**Draft history:**

| Draft | What changed |
|---|---|
| D | First full pass |
| G | Owner: "spine very harsh, no lower-back muscle, nothing should stick out." The measured lumbar hollow was 65 mm below the glute-to-upper-back line (already in V1). An erector fill of 34 mm brings it to 39 mm; glutes and calves toned down. |
| H–I | Owner: "torso very slim, photos a bit wider." Measured as fractions of height (front view): waist 0.156 against the reference's 0.187, chest 0.179 against 0.20, shoulders 0.332 against 0.300. The ribcage and waist sides were widened (waist 24 mm, chest 16 mm, kept clear of the arm) and the lateral deltoid trimmed. |

**Rest-surface self-intersections:** none in V1, but 436 (D/G) and 494 (I), because the inner upper arm pushed into the lats and armpit and the hands into the thighs.
- D–G were shown to the owner before this was measured.
- **K** fixes it: clearance shrink, then an exact triangle-overlap loop. The overlap count goes 410 → 0 in 11 iterations.

**K (current):**
- waist 0.179 of height;
- shoulders 0.332;
- chest width is limited by the arms, which hang against the torso in the bind pose;
- 0 overlaps.

**Next:**
- Region-by-region definition against the close-ups, plus bony landmarks.
- Owner decisions pending: the head, and the standing posture (the skeleton is untouched).
- Then re-fit the shoulder correctives on the v2 surface.

**Body v2 draft N:**
- **Owner:** "G looks better yes. I think it's the same thing with the hamstrings too", and asked to look at the head and the posture now.
- **Hamstrings:** side profile of the back of the thigh. In K it dropped about 55 mm within 14 cm below the glute peak; the reference is about 34 mm to mid-thigh. A 20 mm fill (peak at rest z 0.76) brings the drop to 36 mm.
- **Posture:** the spine bones are straight, so the forward-chest look is the surface. The chest stood 22 mm ahead of the abdomen in V1 and 40 mm in L; the reference is about 10 mm. Pecs 13 → 7 and an abdominal-wall fill of 15 mm bring it to 21 mm. No skeleton change.
- Still 0 rest overlaps.

**Head:**
- The face has 318 vertices at about 10 mm spacing, which is too coarse for eyes, lips or nose detail.
- Realistic features would need a denser head: a separate head mesh on the head bone, or a remesh, which would change Work's topology.
- Owner decision needed.

**Head v2** (owner chose "Detailed separate head"): `scripts/body_v2/build_head_v2_blender.py`.
- The body's head above rest z 1.585 (3644 faces) is copied into a separate mesh.
- It is subdivided twice, linearly: 29,289 vertices at about 2.5 mm spacing. The interior is Taubin-relaxed with the boundary fixed, so the seam follows the body's own edges.
- Facial features are smooth normal-direction fields placed on the measured surface, from head-proportion canons: eye line at half head height, nose base, mouth, chin.
- The body mesh is unchanged. Review renders hide the replaced faces with a mask.
- The "boundary_max_gap" figure in the report is the distance from each boundary vertex to the nearest body vertex. Subdivision midpoints lie on body edges, so this is not a seam gap.

Draft 2 (`review-assets/body_v2/head_v2_draft2/`) is still crude: the eyes read as holes and the features as separate bumps. A convincing realistic face needs many more rounds, or a different approach.

**Body v2 photo fit (R77).** Owner: "This model needs to be close to the photos as you can get." The owner asked for:
- a realistic head;
- a look at the standing posture;
- grids on all photos, with the build based on them, proportional;
- the photo's muscles replicated.

Owner decision on the arms: a standing pose with the arms slightly out; the bind pose is unchanged.

**Tools** (`scripts/body_v2/fit/`), all with the reference stature normalised:
- `overlay.py`: each reference view with the model's outline at the same stature and a 5% grid;
- `profiles.py`: silhouette segments at every 2% of height;
- `armw.py`: arm widths.
- The person is segmented from the reference automatically (skin saturation or dark shorts/hair against the grey background).

**Findings:**

| Item | Model | Reference / target |
|---|---|---|
| Head height (fraction of stature) | 0.11 | ~0.14 in the reference; a real adult man is ~0.13 |
| Shoulder line | 6–8 cm higher (V1) | — |
| Forearm width | — | ~1.6× the model's (model forearm ~5 cm, wrist 37 mm) |
| Elbows (front view) | — | ~5 cm further out (arm abduction) |

**Draft T:**
- **Standing pose:** arms abducted 9°, elbows flexed 6°. The elbows and hands now line up with the photo.
- **Shoulder line:** lowered 2–4 cm, sloping from the neck to the acromion. It stops at realistic anatomy; the AI reference's long neck is not matched fully.
- **Forearms:** the forearm muscles now run elbow → wrist (bug: the forearm bone ends mid-forearm). Forearm/wrist volume added: arm width ratio to the reference is now 1.09–1.18 against 1.50–1.64 before.
- **Overlap test:** now runs in the standing pose. In the build pose the forearms lie against the hips; build-pose overlaps there are expected and not shown.
- 0 standing-pose overlaps.

**Next:**
1. Head v2 at realistic size (0.13 H) with a realistic face.
2. Region-by-region muscle definition from the close-ups.
3. Side-view chest and posture.

**Draft X** (owner on T: "The shoulders look messed up now and sharp instead of sloped"):
- T had moved only the upward-facing skin down, which folded a jagged ridge at the side of the deltoid. The whole shoulder cap now moves as one smooth field of rest x and z.
- The forearm bulk was moved off the elbow (T showed knobs there).
- Roughness on the deltoid was still there with the overlap step off and in the bind pose. Measured extra surface roughness in the deltoid region (`fit/rough.py`) shows where it came from: the overlap shrink (largest share), then the shoulder drop, then the bellies.
- Fixes:
  - skin-weight masks relaxed on the surface;
  - a smooth, wider overlap shrink with offset relax;
  - a shoulder-region offset relax.
- Result: vertices with more than 0.5 mm extra roughness went 165 (K) → 62 (W) → 0 (X). 0 standing-pose overlaps.

**Draft Z.** The owner pointed at the ORIGINAL shoulder: "the natural curve of the shoulder ... how it slopes down without the ridge."
- Y still had a crest where the lowered shoulder top met the deltoid side.
- The separate deltoid bellies and the shoulder lowering were both removed. Instead, the original shoulder is expanded smoothly about the humeral head: a 3D field, 11 % at the joint fading to 0 at 13 cm, applied to the outward side only.
- The original's neck-to-arm curve is kept, just rounder.
- Roughness: 0 vertices over 0.5 mm. 0 standing-pose overlaps.
- The photo's lower shoulder line is not matched; the owner prefers the original curve.
- Z2 (6 %) was rendered for comparison.

**Owner decision:** "Z2". The shoulder expansion is 6 %, now the default. The current body v2 candidate is `review-assets/body_v2/draft_z2/body_v2_offsets.npz`.

**Draft v3a: head size.** The head was 0.11 of stature (0.20 m, chin to top); a real adult man is about 0.13 (~23 cm) and the reference about 0.14.
- The head is scaled 1.15× about a pivot at ear level (z 1.70), blended into the neck over 3.5 cm.
- Top of head 1.820 → 1.838; the chin drops about 1.2 cm.
- Body below z 1.55 is identical to Z2 (0.000 mm).
- The head outline now matches the photo grid.
- The detailed face (head v2 builder) is built next, on top of this body.

**v3c.** Owner: "There's not much of a neck now ... a very noticeable line departing [torso and legs]."

**Neck:**
- The head pivot is now at chin level (z 1.628), so the chin no longer drops into the neck.
- The blend from neck to head runs over 8.5 cm; a 3 cm blend left a ring round the neck.
- The neck is lengthened by 8 mm. The top of the head is now at about 1.86 m.

**Hips:** a ridge ran round the hips where the torso meets the thighs (faint in V1, made stronger by the waist and abdomen fills ending above it). The positions in that band (z 0.905 ± 0.10) are Taubin-relaxed (40 iterations) and kept as offsets. The line is gone.

0 standing-pose overlaps.

### Draft v3e: lower belly, groin and top of the thighs (21 Oct)

The owner circled the lower belly, groin and upper thighs on v3c ("This point here needs fixing"). What was wrong, compared with the reference:
- The front of the groin read as a flat, boxy panel, with V1's faceted V-crease lines along it.
- A shelf/crease sat below the navel.
- The tops of the thighs flared outward.

Changes in `build_body_v2_sculpt_blender.py`:
- **Abs fill:** now fades in from z 0.86 instead of 0.95.
- **Waist side push:** now fades in from z 0.84 instead of 0.92.
- **New groin relax:** `V2_GROIN_RELAX` (default 80) runs Taubin passes over the front of the lower belly, groin and upper thighs. Region: z 0.95 ± 0.13, |x| < 0.17, front-facing, arms excluded.
- **Vastus lateralis:** starts lower (0.38–0.66 of the thigh) and is weaker (amp 4, was 8).
- **Base thigh layer:** starts at 0.35 of the thigh instead of 0.20.

Results:
- 0 standing-pose overlaps.
- Renders and before/after zoom are in `review-assets/body_v2/draft_v3e/`. The reference-photo comparison stays local.
- **Still open:** a faint horizontal line remains at the top of the thighs, where the crotch starts. It is softer than before.

### Draft v3h: leg / torso proportion (21 Oct)

The owner asked: "The torso seem very long and the legs short. Is this correct?" They chose "Longer legs, same height".

**Measured against ANSUR II male data** (n = 4,082; values predicted from stature by linear regression, at the v3e stature of 1.857 m):

| Landmark | Model | ANSUR prediction |
|---|---|---|
| Knee joint | 0.515 m | lateral femoral epicondyle 0.525 m |
| Hip / trochanter | ~0.968 m | trochanterion 0.962 m |
| Crotch | 0.837 m | 0.905 m (model is −2.8 SD) |

The project's own proportion audit (F-PROP-001) already had the V1 crotch at z −1.85.

**Conclusion:** the leg bones are the right length. The soft-tissue crotch hung about 6–7 cm too low, so the legs looked short and the torso long. The fix keeps the skeleton and the stature unchanged.

**R79 (`V2_CROTCH_MM`, default 58):** a vertical lift of the crotch and the top of the inner thighs.
- Strongest at the midline, fading to zero at the thigh axis.
- Rises from z 0.60 up to the old crotch, then fades out by z 1.12.
- Only applied to surfaces that face sideways or down (between the legs). Lifting the front and back faces too pushed the lower belly into a fold (v3f/v3g, rejected).
- Applied before the hip-band and groin relax.

**Result:**
- Crotch at 0.882 m = 0.475 H (ANSUR mean 0.487, SD 0.013).
- Stature unchanged at 1.857 m.
- 0 standing-pose overlaps.
- `review-assets/body_v2/draft_v3h/` holds the offsets, the proportion grid and the groin before/after.

**Other findings from the same audit, not yet acted on:**
- The arms are short (acromion to fingertip z −2.18 on V1).
- The armpit and sternal notch sit high (z ≈ 2).
- The head enlargement raised the stature from 1.82 to 1.857 m, so the shoulders are now about 2 cm low for that height.

### Draft v3k: arms, shoulders, waist and groin (21 Oct)

The owner asked for the open proportion findings to be fixed ("Fix them now"), plus: "the groin looks to be very high too. Can we sort out the waist also?"

**New measuring tool: `scripts/body_v2/fit/proportions.py`.**
- It takes exact horizontal mesh sections of the bind surface (R41 rest + offsets) and compares them with ANSUR II male data, predicted from stature by linear regression at the model's own stature.
- On V1 it reproduces the project's proportion audit (F-PROP-001) to within about 1 mm.
- Chest and buttock girths are not compared: in the bind pose the arms touch the trunk.

| ANSUR, 1.857 m | v3h | v3k |
|---|---|---|
| acromion height | −1.28 SD | −0.35 SD |
| acromion → fingertip | **−2.96 SD** (0.780 vs 0.843 m) | 0.00 SD |
| wrist height | +0.88 | −0.75 |
| axilla height | −0.32 | +0.50 |
| suprasternale | −0.43 | −0.43 |
| crotch height | −0.94 | −0.77 |
| waist breadth (omphalion) | −0.66 | −1.22 (lean; ANSUR is an average soldier population) |
| hip breadth | −0.50 | −0.28 |

**R81, skeleton change (review candidate):**
- Upper arm lengthened 27 mm, forearm 23 mm.
- Hand scaled ×1.074 about the wrist (+14 mm).
- Shoulder girdle raised 15 mm. The lift fades out towards the neck so the neck is not shortened.
- The skin follows its own bones through the skin weights, so the elbow and wrist stay continuous.
- This is kept as a separate field (`proportion` in the npz), so the overlap shrink cannot undo it. The saved `offsets` = sculpt + proportion.
- The scene rig is edited to match. The before/after head and tail of each bone are in `skeleton_edits.json`.
- **Not yet done:** the anatomical master skeleton (humerus, radius/ulna, hand bones, clavicle, scapula) and the press/hang correctives still need to follow this change.

**R80, waist:** the old side push gave the natural waist (z 1.10–1.22) as much as the chest, so the torso read as a box.
- New `V2_SIDE_PROFILE`: hips kept, waist pulled in (24 → 13 mm), ribs/lats 20 mm.
- Front-view waist is now narrower than the hips, and tapers up into the lats.

**R80b plus hip-band changes, groin:** the lower belly met the thighs along a horizontal line about 4–5 cm above the crotch, so the legs seemed to start there.
- Inguinal grooves 12 mm deep, running from the ASIS landmark down to the pubis (the V).
- Hip-band relax re-centred on the lifted surface: z 0.95 ± 0.10, 120 Taubin iterations.
- The line is much softer. It is still faintly visible in the shading.

**Status:** 0 standing-pose overlaps. Assets are in `review-assets/body_v2/draft_v3k/`.

### Draft v4b: pelvis, groin and legs from the owner's reference figures (21 Oct)

The owner sent two reference figures, front, side and back, saying: "This is how the pelvis and groin and legs should look."

**Front-silhouette widths, as fractions of stature.** Measured on both figures and on the first photo; script `scripts/body_v2/fit/front_profile.py`.

| Height | References | v3k | v4b |
|---|---|---|---|
| hips 0.50 | 0.207–0.211 | 0.187 | 0.207 |
| waist 0.60 | 0.171–0.178 | 0.161 | 0.170 |
| ribs 0.66 | 0.162–0.169 | 0.178 | 0.167 |
| ribs 0.70 | 0.186–0.187 | 0.200 | 0.189 |
| upper thigh 0.44 | 0.102–0.109 | 0.094 | 0.099 |
| thigh 0.34 | 0.069–0.076 | 0.091 | 0.078 |
| inner-thigh half-gap 0.34 | 0.016–0.032 | 0.009 | 0.017 |

**What changed (R82, R82b, R82c):**
- **R82:** a silhouette field with two parts.
  - `V2_SIL_LAT`: a per-side push on the outward-facing skin, by height.
  - `V2_SIL_MED`: a push on the medial leg skin, which also opens the gap between the thighs.
  - Together they widen the hips and the top of the thighs, pull the lower thighs in to taper to the knee, and trim the R80 rib push.
- **R82b:** a belly-button dimple at 0.612 of stature.
- **R82c:** a fill on the thigh side of the inguinal V.

**Results:**
- 0 standing-pose overlaps.
- The ANSUR landmarks are unchanged from v3k.

**Limit found: mesh resolution.** Median edge lengths on R41:

| Region | Median edge |
|---|---|
| belly | 12.8 mm |
| groin | 15.1 mm |
| face | 10.2 mm |
| thigh | 3.6 mm |
| hand | 3.9 mm |

The belly button (5 vertices within 15 mm), the sharp V crease, the pubic wedge, the gluteal fold and fine muscle separations cannot form at 13–15 mm spacing. So R82b and R82c barely show. This needs an owner decision on adding resolution.

### Draft v5n: refined mesh plus fine detail (21 Oct)

Owner chose "Refine the torso mesh". R41 has 13–15 mm edges on the belly and groin, and long thin triangles, 30–40 mm long, on the legs, chest, back and neck ring. At that spacing the belly button, the V, the pubic shape and the gluteal fold cannot form.

**Pipeline (R83):**

1. **Sculpt on R41.** The whole sculpt runs on R41 as before. Its relax and smoothing steps are counted in neighbour hops and were tuned at that mesh scale.
2. **Refine at the end.** `scripts/body_v2/refine_torso_blender.py` does this.
   - Any triangle with an edge over `V2_REFINE_MM` (8) is split at all three edge midpoints, then re-triangulated, repeated until none is left. It covers the whole body; the hands and arms are already finer.
   - Skin weights and all 79 shape keys are carried over by linear interpolation, so the new vertices deform like the old surface.
   - New vertices are placed by Phong tessellation (α 0.75) on their old triangle. Old vertices are unchanged, and the same rest move is added to every shape key.
   - Result: 21,600 → 219,974 vertices, median edge 4.1 mm.
   - `refine_map.npz` holds the exact linear map (old triangle and weights per new vertex). Use it to carry any 21,600-vertex array (dense correctives, hang/press fixes, earlier offsets) over to the refined mesh.
3. **Carry the sculpt over smoothly.**
   - Sculpt offsets: Gaussian over the nearby old body vertices, only from skin facing the same way. Sigma is 0.5 × the longest incident old edge.
   - The arm chain, including the fingers, keeps the exact linear map. In the bind pose the hands hang against the thighs.
   - The proportion field keeps the exact linear map. Its shoulder-lift weight is smoothed, so the arm weights no longer jump point to point around the trapezius.
4. **Fine normal smoothing.** Cotangent-weighted, along the normal only: 12 Taubin steps everywhere except the hands, 40 at the neck base.
5. **Details, in mm, on the fine mesh.**
   - Belly button at 0.612 of stature: 6 mm deep, with a rim.
   - Inguinal creases from the hip bone to beside the crotch: 4 mm.
   - Gluteal folds: 5 mm.
6. **Fine overlap loop.** Smoothed shrink; stops when it no longer improves.

**What went wrong on the way (v5a–v5m, all rejected):**

| Draft | Problem | Cause / fix |
|---|---|---|
| v5a | noisy skin, crumpled thighs | refining first, so every hop-counted step was 3–4× shorter |
| v5c/v5d | ripples, neck pleats | Taubin relax on the slivers |
| v5d/v5e | diamond cross-hatch | the linear carry-over kinks along every old edge |
| v5f–v5l | finger prints on the hips | the hand vertices filled the hip skin's neighbour list |
| v5k | degenerate triangles | splitting only the long edges |
| v5f–v5m | neck pleats | sigma from the mean edge length; now the longest edge |

**Other changes:**
- The standing pose is now 12° of arm abduction (was 9°). With the longer arms, the thumbs pressed into the wider upper thigh.

**Results:**
- 0 standing-pose overlaps.
- The front silhouette and the ANSUR landmarks are unchanged from v4b (all within 1 SD).

**Still open:**
- A faint horizontal line where the belly meets the thighs.
- The pubic area is flatter and squarer than the references.
- The glutes are less round and less projecting than the references.
- A few dark specks on the upper back and chest (to check: degenerate triangles).
- 220k vertices will need a lighter version for the app.
- The press/hang dense correctives (21,600-based) must be carried over via `refine_map.npz` before the exercises.

### Draft v6d: front torso muscles (21 Oct)

The owner asked: "please notice the detail in the muscles like the abs etc and how they should look."

**Measured on both reference figures (fractions of stature):**
- Abs: top of the abs at 0.70–0.71, under the pecs. Tendinous intersections at about 0.685, 0.663 and 0.640.
- Navel: 0.61.
- Rectus columns: about 6–8 cm wide each, with soft rounded segments.
- Linea alba: thin, from the sternum to the navel, gone below it. The lower belly is smooth.
- Pecs: a full rounded mass with a curved lower border rising towards the armpit, and a sternal groove.
- Serratus: fingers on the side of the ribs.
- The model's abs were R41's own boxy grid: too narrow, with a deep groove running below the navel.

**R84, `V2_MUSCLE_FRONT`, on the refined mesh:**
- **Erase:** 150 plain normal-only cotangent smoothing steps over the front of the belly (0.545–0.735 of stature, |x| < 0.125). Taubin steps kept grooves this broad (v6a).
- **Relief:** a height field along the smoothed normal, sizes in mm:
  - rectus pad 2.5 mm between the linea semilunaris curves;
  - segments as smooth pillows (`V2_ABS_SEG_MM` 3.6) whose valleys form the intersections;
  - linea alba 1.8 mm, from the sternum to the navel;
  - linea semilunaris 1.0 mm;
  - pec mass `V2_PEC_MM` 7, sharper along the lower border; sternal groove 1.2 mm;
  - serratus, four fingers, 1.6 mm.

**Results:**
- 0 standing-pose overlaps.
- Assets in `review-assets/body_v2/draft_v6d/`: model-only before/after. The reference comparison stays local.
- The offsets are for the refined mesh. Use `draft_v5n/refine_map.npz`; the topology is identical.

**Still open:**
- The ab segments are still a little narrow and ridge-like compared with the references.
- Some wrinkles on the side of the chest under the armpit.
- The belly/thigh line.
- Arms, back, shoulders and legs are next.

### Draft v7b: groin rebuilt to the reference (21 Oct)

The owner sent the reference figure's groin close-ups: "Can we have the groin area match this … I still see the weird line at the top of the legs where it meets the torso … There is no line there and it's smooth transition."

**Before:**
- A horizontal fold ran across both thigh tops at about 0.49 of stature, just above the crotch.
- The pubic area was a flat, wide shelf.

**Reference:**
- The inguinal creases are long soft curves from the side of the hip (about 0.56 of stature) to beside the crotch (about 0.48).
- Between them is a rounded pubic wedge with a U-shaped bottom.
- There is no horizontal line.

**R85, `V2_GROIN_REBUILD`, on the refined mesh:**
- **Flatten:** 200 plain normal-only cotangent steps over the groin band, from the crotch −0.025 to +0.115 of stature, |x| < 0.20. Back-facing skin and inner-thigh skin facing the other leg are excluded.
- **Creases:** follow the reference curve. 3 mm deep, sigma 10 mm, fading out before the crotch so the bottom reads as a U, not a point.
- **Pubic mound:** 5 mm, a rounded Gaussian across x.
- **Thigh side:** comes forward 2 mm along the crease.
- The old R80b/R82 inguinal grooves are off while the rebuild is on.

**Results:**
- 0 standing-pose overlaps.
- The horizontal line is gone from the front, side and three-quarter views.

**Still open:**
- The gluteal folds are slightly wavy.
- Some small vertical streaks on the thigh tops.

### Draft v8c: abs and pecs reworked to the reference figure (21 Oct)

The owner wants the look of the reference figure for our model. The face, skin colour and so on come later.

> "The abs are still not right … they aren't just blocks. They are more rounded and wider … The top of abs is curved and also the visibility of them is defined but not so prominent. The pecs still need better defined also like the picture I sent."

**Measured on the reference torso:**
- Rectus columns reach |x| about 0.07 m.
- The top row sits under an arch that follows the rib margin.
- Segments are soft and rounded, with shallow valleys between them.
- The pecs are full masses reaching almost to the armpit. Their lower border is nearly level across the middle, rises towards the armpit, and has a crisp shadow under it.

**R86 changes:**
- **Chest erase:** the erase now covers the chest too (0.70–0.80 of stature, |x| < 0.165), removing R41's own crease across it.
- **Abs:**
  - columns wider (`xo` up to 0.08);
  - rib-arch top: 0.708 at the sternum, falling 0.45 per metre outwards;
  - segments are cos^1.5 × cos^1.2 domes (`V2_ABS_SEG_MM` 3.0) on a 2 mm pad;
  - the intersections curve slightly;
  - linea alba sigma 5.5 mm (narrower than the mesh could resolve before) and sternal groove sigma 7 mm.
- **Pecs:**
  - `V2_PEC_MM` 11, centred at |x| 0.095;
  - lower border at 0.732, rising 0.30 per metre beyond |x| 0.10, sharp below (sigma 0.0065);
  - stops short of the arm (|x| 0.175). The first try reached the arm: 895 standing overlaps before the shrink loop.

**Results:**
- 0 standing-pose overlaps after the fine loop (332 at its start).

**Still open:**
- The abs still read a little more blocky than the reference.
- Small lumps along the sternum, from R41's sternal ring.
- Wrinkles on the side of the chest at the armpit, seen from the side.

### Draft v9e: abs at the reference's size (21 Oct)

The owner said: "No the abs need to be bigger … how wide they are in relation to the body and also height."

**The cause was a units bug in v8c.** The rectus edge was set in metres, but it had been measured as a fraction of stature: 0.08 m against a measured 0.072 of stature, about 0.134 m.

**Measured on the reference with an x/y grid in fractions of stature (`scripts/body_v2/fit/abs_grid.py`):**
- Rectus edge at |x| 0.064 (navel), 0.072 (at 0.66 of stature) and 0.076 (at 0.70). That fills about 80 % of the front of the waist.
- The top is at 0.716 under the pecs, arching down to about 0.70 at the edge.
- Intersections at 0.640, 0.665 and 0.690.

**R87 changes:**
- `xo` is now a fraction of stature × Hs.
- Each block is a rounded-rectangle dome (super-ellipse, power 3), 6 mm (`V2_ABS_SEG_MM`).
- Linea alba 4.5 mm (sigma 6 mm).
- Linea semilunaris 2.6 mm (sigma 10 mm).
- The erase now covers |x| < 0.165 m.

**Not working, for the record:** plateau or cos-shaped blocks across the 13 cm columns read as horizontal stripes under the studio light (v9a–v9d). They only read as blocks once the vertical lines framed them and each block got its own dome.

**Results:**
- 0 standing-pose overlaps.

**Still open:**
- Small lumps along the sternum, from R41's sternal ring.
- Wrinkles at the side of the chest by the armpit.

### Draft v9f: three rows of abs (21 Oct)

The owner said: "There looks to be too many [abs] … There is less in my photo."

**Cause:** the reference shows three rows (a six-pack): 0.640–0.665, 0.665–0.690 and 0.690 up to the top. The skin from 0.640 down to the navel is smooth. v9e also domed the navel row, which made four.

**Change (R88):**
- The lowest intersection (0.640) is now the bottom edge of the pack.
- The pad, linea alba and semilunaris below it are unchanged.

**Results:**
- 0 standing-pose overlaps.

### Draft v9g: ab rows re-counted (21 Oct)

The owner said: "Still too many abs … count how many you have."

**Counting method:** a contrast-stretched zoom of the reference (fractions of stature).

**Reference:** three pairs.

| Row | Height (fraction of stature) |
|---|---|
| top | 0.705–0.735, directly under the pecs |
| middle (largest) | 0.665–0.705 |
| bottom (faint) | 0.642–0.665 |

- The pec lower border is at about 0.742 at the centre.
- The skin is smooth from the bottom row down to the navel.

**What v9f got wrong:** its pec border sat at about 0.725 and the abs top at 0.716, so the strip between them read as a fourth row.

**R89 changes:**
- Abs top (rib arch) at 0.735 at the sternum.
- Intersections at 0.642, 0.665 and 0.705.
- Pec lower border at 0.744.
- The linea alba now runs up to 0.74.
- The erase now reaches 0.75.

**Results:**
- Counted on the same contrast view: three pairs.
- 0 standing-pose overlaps.

### Draft v9i: contoured ab blocks (21 Oct)

The owner said: "The abs have more of a contour than what you have. Use the reference as a guide."

**R90 changes:** each pair now has its own outline, measured on the contrast-stretched reference (fractions of stature).

| Pair | Height | Width |x| | Shape | Amp |
|---|---|---|---|---|
| top | 0.705–0.735 | 0.060 at the top, 0.071 at the bottom | follows the rib arch; lower edge sloping down to the side | 7 mm |
| middle | 0.665–0.705 | up to 0.075 | largest, rounded corners | 9 mm |
| bottom | 0.642–0.665 | up to 0.063 | lower edge a soft U | 5.5 mm |

- Each block is a super-ellipse dome (power 2.3), centred slightly above the middle of the block.
- The dome falloff is cos². A steep (cos^0.9) edge read as a hard horizontal line (v9h). With cos² the pillows meet in gentle valleys.

**Results:**
- 0 standing-pose overlaps.
- Contrast comparison tool: `scripts/body_v2/fit/abs_contrast.py`.

### Draft v9j: abs top at the owner's line (21 Oct)

The owner drew a line on the reference at about 0.706 of stature: "It's the line of the top of the abs in the reference drawing. This is where it should be. Also look at the shape of the abs."

**What R89/R90 got wrong:** the band from 0.706 to 0.74, under the pecs, is smooth lower ribs. R89/R90 had counted it as the top pair of abs.

**R91 changes:**
- Abs top at 0.706, with a slight drop towards the edge.
- Three pairs below the line, inside a rounded shield outline:

| Pair | Height (fraction of stature) |
|---|---|
| top | 0.684–0.706 |
| middle | 0.660–0.684 |
| bottom | 0.636–0.660 |

- Rectus edge: about 0.071 at the middle pair, about 0.060 at the top, about 0.056 towards the navel.
- Pec border unchanged (0.744). The linea alba still runs up through the rib band to the sternum.

**Results:**
- 0 standing-pose overlaps.

### Draft v9l: two pairs below the owner's line (21 Oct)

The owner said: "you have the abs sitting too high and almost at the bottom of the pecs."

**Measured on a contrast zoom of the reference, with the owner's top line at about 0.709 of stature:** only two pairs lie below the line, then the skin is smooth to the navel.

| Pair | Height (fraction of stature) |
|---|---|
| tall | 0.665–0.707 |
| lower | 0.635–0.665 |

**What v9j got wrong:** it squeezed three short rows into 0.636–0.706, so the visible blocks sat high, against the pecs.

**R92 changes:**
- Two pairs, at 9 mm and 7.5 mm.
- `V2_ABS_SEG_SCALE` 1.45, so they read at full-body scale. At 1.0 they were barely visible there (v9k).

**Results:**
- 0 standing-pose overlaps.

### Draft v9m: softer abs (21 Oct)

The owner, marking the outer ends of the blocks on v9l, said: "The abs look too raised … it's a slight contour and definition."

**R93 changes:**
- `V2_ABS_SEG_SCALE` lowered from 1.45 to 0.6.
- Each block fades towards its outer end: × (1 − 0.55·u^1.5).
- The linea semilunaris is shallower and wider: 1.0 mm, sigma 14 mm (was 2.6 mm, sigma 10 mm). This removes the step at the outer ends.
- Linea alba 2.5 mm (was 4.5 mm).

**Results:**
- 0 standing-pose overlaps.

### Draft v10c: pecs to the reference (21 Oct)

The owner said: "the pecs need to be better defined like the reference drawing."

**Measured on the reference (fractions of stature):**
- The lower border is a rounded curve: 0.736 at the sternum, lowest at about 0.728 mid-pec (|x| 0.05), sweeping up to about 0.775 at the armpit (|x| 0.105).
- Fullest in the lower half (0.74–0.77), fading up under the clavicle (about 0.825).
- A valley between the two pecs at the sternum.
- A soft deltopectoral line from the clavicle down to the armpit.
- Nipples at about 0.751, |x| about 0.077.

**R94 changes:**
- The pec is a dome bounded below by the quadratic border curve `zb`.
  - Height profile `ss(v/0.16)·(1−v)^1.1`, where v runs from the border up to 0.825.
  - Across the pec: `sin(π·x/0.104)^0.55`, fading out from 0.10 so it does not run into the arm.
  - `V2_PEC_MM` 13.
- Deltopectoral line: 1.4 mm.
- Subtle nipples.
- The chest erase now reaches 0.815 of stature and |x| 0.17 m.

**Rejected on the way:**
- v10a: a flat plate with a sharp lower step and a crumpled outer edge (1,467 overlaps).
- v10b: a separate shadow groove that doubled the edge, and a kink in the piecewise border.

**Results:**
- 0 standing-pose overlaps (199 at the start of the fine loop).

**Still open:**
- The nipples hardly show under the workbench light.

### Draft v10h: pecs reworked after "still looks wrong" (21 Oct)

The owner said: "Still looks wrong. They need to be like the reference model."

**Side silhouettes** (`scripts/body_v2/fit/side_prof.py`): front edge ahead of the front at 0.70, as a fraction of stature.

| Height | Reference | v10c | v10h |
|---|---|---|---|
| 0.72 | −0.003 | +0.004 | — |
| 0.74 | +0.002 | +0.016 | about +0.008 |
| 0.75 | +0.001 | +0.014 | — |

- On the reference, the lower ribs and upper abs are about as far forward as the pecs: one full chest curve, with the pec reading by its outline and a slight overhang.
- v10c's pec stood about 3 cm proud of a recessed rib area, a shelf.

**R95 changes:**
- Pec projection reduced.
- Lower ribs filled forward up to the border (`V2_LOWER_RIB_MM` 5).
- A broad belly fill over the front of the abdomen (`V2_BELLY_FILL_MM` 8, 0.585–0.735 of stature).
- A soft shadow under the border.
- The outer lower pec corner fades earlier.

**R96 changes** (front view, compared with the reference):
- The pec profile in height is `ss(v/0.14)·sin(π(0.18+0.82v))^0.6`: fuller up under the clavicle.
- Across the pec: `sin(π·x/0.110)^0.8`, so it is rounded towards the sternum and the two pecs make a soft valley. The separate thin sternal line is gone.
- `V2_PEC_MM` 12.
- Larger nipples (still faint under this light).

**Tried and left in, but it did not move the silhouette (v10g):** an erase of the outer lower pec corner into the front of the armpit. The ledge comes from R41's chest form, not that corner.

**Results:**
- 0 standing-pose overlaps.

**Still open:**
- In the side view the chest is still a little proud below the nipple line compared with the reference.
- Some wrinkles at the front of the armpit (R41).
