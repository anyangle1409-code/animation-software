# Home Gym PT body: anatomical defect list (3 Nov 2026)

**Assets reviewed:**

- **W11:** the current candidate.
- **W5:** the published candidate.
- **R41:** the older slim ORIGINAL_v1 model. R47 and R52 were built on it, and R47's own blend is not available here.

**The owner's reference:** a character reference sheet of an athletic adult male, front / three-quarter / side / back
views plus close-ups. It is not stored in git.

**Evidence:**

- `review-assets/body_v2/visual_evidence/comparison_r41_w5_w11_20261103/`: standing, plus the press at rack,
  intermediate, near lockout and lockout, from four angles, with identical skeleton motion and cameras.
- `review-assets/body_v2/visual_evidence/shoulder_w11_20261103/`: videos.

**Severity:** **A** is visible at a glance and wrong; **B** is visible in close-up; **C** is minor or
measurement-only. "Owner" means the fix needs the owner's decision: the skeleton is frozen, and production is
untouched.

## 1. Whole-body shape against the reference

Measured as front-view silhouette widths, each a fraction of standing height. The table is in the comparison folder's
README.

| # | Defect | Severity | Evidence | Cause | Fix |
|---|---|---|---|---|---|
| 1.1 | **Shoulders high and square ("shoulder pads")** | A | The shoulder line starts widening at 0.857 of height (reference 0.834, about 4 cm lower). The width at 0.80 is 0.31–0.32 (reference 0.24–0.26). The skin stands 81 mm above and 82 mm lateral of the GH centre; an adult male is about 40–50 and 55–65 mm | Mesh: too much tissue over the acromion, upper trapezius and deltoid cap. R41 has the same top, so it is inherited | Candidate **S1** (`rest_reshape_shoulders_blender.py`): rest-shape lowering of the trapezius line and slimming of the deltoid cap, keys preserved. **Under test** |
| 1.2 | Shoulder joints set wide | C, owner | The GH centres are 0.236 of stature apart; adult males are about 0.21–0.22 | Skeleton (frozen) | Needs owner approval. After S1 the outer width is still about 5 % over the reference unless the joints move about 2 cm each side |
| 1.3 | Lower thigh thin | B | At 0.37 of height the thigh is 0.081 wide (reference 0.091) | The rebuilt leg rings (R119) were sized to an earlier reference | Rest-shape widening of the lower vastus, as S1 does for the shoulders. Not started |
| 1.4 | Seam line around the top of the thighs | B | A horizontal tone line on the thigh front, outside and back at about 0.44–0.45 of height, with a darker band on the hip side | The R119 leg cut at 0.45 of stature: a stitch strip of long, thin triangles joins the new leg rings to the old fine mesh | Re-triangulate or relax the stitch strip (tangential, shape kept). Not started |
| 1.5 | Upper back flat | B | Back view: no trapezius / rhomboid / latissimus / teres / rear-deltoid forms; the reference shows them | The sculpt's torso relief (R119 v14b) is light on the back | A back relief pass, like the torso definition step. Not started |
| 1.6 | Face: raised ridge on the left forehead and temple | B | Front close-up | A head sculpt artifact | Local rest-shape fairing. Not started |
| 1.7 | Head is a mannequin | C, owner | No face, ears or hair | Out of this lane's scope so far | Separate work package (owner) |
| 1.8 | Fine crinkles on the deltoids at rest | C | Three-quarter standing view | Sculpt relief on the deltoid | Rest relief smoothing on the cap. Could be folded into S1 |
| 1.9 | Matching the reference | none | The waist (0.162 vs 0.163), upper arm, knee, calf and ankle match within a few per cent | | |

## 2. Shoulder press (W11)

| # | Phase | Defect | Severity | Cause | Status |
|---|---|---|---|---|---|
| 2.1 | Rack (90°) | A notch at the front of the shoulder where the pec meets the deltoid | B | The skinning at the pec-deltoid junction | Not started |
| 2.2 | Intermediate (125°) and near lockout (149°) | Wood-grain ripples across the pecs; a pinched notch at the front armpit; creases over the clavicle and anterior deltoid | A | W5 and W7 fixed these only in the lockout key (153). The 120 and 150 keys have nothing | Candidate **W12b**: the same W5 mush and W7 fairing in `R121_ARM_<s>_120` / `_150`. **Under test** |
| 2.3 | Near lockout | The deltoid looks multi-lobed, with a deep groove before the upper arm | B | The upperarm / shoulder_cap weight handover (see W6c) | Partly W6d. Open |
| 2.4 | Lockout | Fine radial lines in the armpit hollow; mottled skin on the inner arm by the armpit | B | That skin is weighted mostly to the torso; nothing patches it | Candidate **W12a** (armpit-hollow fairing). **Under test** |
| 2.5 | Lockout | One transverse band left on the triceps | C | The weight handover | W6d softened it |
| 2.6 | Whole press | Scapular upward rotation and clavicle elevation follow the corrected girdle path (C1). R41's own keys do not fit that path | none | | The girdle path is the reference and is kept |

## 3. Other movements

| # | Movement | Defect | Severity | Status |
|---|---|---|---|---|
| 3.1 | Overhead triceps extension (top) | Wood-grain ripples across both pecs, in W5 and W11 alike | B | Open. The lockout key is on but the arms are turned, so its smoothing does not fit |
| 3.2 | Grip | 56 deep skin crossings at the fist (down from 155) | B | Open: a second contact pass makes it worse; it needs a knuckle-indexed corrective |
| 3.3 | Bent-over row | Left posterior-shoulder fold, 57 crossings vs 2 on the right (a 3.6 mm asymmetry in the rest mesh) | C | Open: a row-pose contact key |
| 3.4 | Push-up | Forearm crease and thumb base | C | Open |
| 3.5 | Squat, lunge, walk, curl, forearm rotation | No visible fault in the before/after frames (hips 555 → 0, knees 129 → 13, walk 0) | none | |

## 4. Foundation (reusable deformation)

- **How correctives work now:** they are shape keys indexed by joint angles (elevation, elbow, hip, knee, wrist,
  finger curl, upper-arm twist band), driven by `r121_drives`. Every exercise built from these joints reuses them.
  The 9 app clips are baked from the same rules.
- **Limit (seen on 3 Nov):** a correction authored on one path (the straight-elbow press) can misfit another path
  through the same angles (the overhead extension, where the upper arm twists). Today's answer is a gate, as
  `R121_ARMBAND` fades out with elbow flexion. The longer-term answer is to index the shoulder keys by twist as well,
  or to move to a muscle and tissue layer.
- **Muscle layer:** the experimental proxies (MG1–MG12) are envelopes for analysis and highlighting. They are not
  validated anatomical muscles and do not drive the skin yet.
