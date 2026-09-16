# Home Gym PT — Reference Body Match Handoff

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting production head:** `3500b4bb1751fdddfece911d2c262754f8e6d668`  
**Do not merge.**  
**Reference:** the muscular male front-view image supplied by the user with the task. This image is the visual target for body shape/proportions.

## Current production assets

- Bare body: `HomeGymPT_Male_BASELINE_v7.glb`
  - SHA-256: `54222af34402281351b60d8bc2fb66f7e3fdf77d2c03eb869b5581d03adb16c4`
- Shipped default: `HomeGymPT_Male_BASELINE_v7_SHORTS.glb`
  - SHA-256: `a5bec8fac0ce014d2ce96bcdb7b4cb846cfc65ee92ef5364f08ca0f7a2976f66`
- Retained fallbacks remain untouched:
  - v6 bare `46180b57…410ed`
  - v6 dressed `0761fb04…b0d6`
  - proven v5 `dfb0fea6…5702f`

F3 shorts are approved source-of-truth geometry. The current shorts builder no longer reproduces F3 exactly, so do not silently substitute a regenerated variant.

## Hard constraints

Do **not** change during this body-fit task:

- skeleton/joint locations or bone lengths;
- skin weights;
- inverse bind matrices;
- retargeting;
- accepted curl motion;
- exercise definitions;
- elbow corrective — stays **0%**;
- global grip closure — stays **85%**;
- v5/v6/v7 fallback assets.

Do not overwrite v7. Produce a separate reference-match candidate first.

Body-shape work should be bind-pose geometry only (`POSITION` plus regenerated `NORMAL`) unless objective evidence proves that impossible. Do not hide a skeletal mismatch with extreme mesh deformation.

## Goal

Make the production character as close as practical to the supplied muscular male reference in **front-view silhouette and proportions**, using a repeatable calibrated overlay and measurements rather than subjective eyeballing.

The reference is a shape target, not proof of absolute real-world height. Normalize it to the actual v7 sole-to-crown height, then measure all width/landmark differences from that registration.

## 1. Calibrate the reference correctly

Measure the actual v7 character from floor/sole to crown in its neutral reference pose. Normalize the supplied reference image to that height.

Register using:

- floor/soles;
- crown;
- vertical body centre line;
- pelvis/torso centre.

Do **not** scale the image to shoulder/chest width because those are target dimensions to compare.

Create a review-only neutral pose using the existing rig:

- upright;
- head neutral;
- shoulders relaxed;
- arms naturally down/slightly clear of torso;
- elbows nearly straight;
- palms approximately inward;
- stance/feet matched as closely as practical.

This pose must not become an exercise-definition change.

Use an orthographic front camera or a sufficiently long-lens front camera to minimise perspective distortion. Lock camera, crop, pose and image registration for all comparisons.

## 2. Create objective comparison evidence

Create under `scratchpad/reference-fit/`:

1. original supplied reference;
2. v7 baseline render;
3. final candidate render;
4. 50/50 reference-vs-candidate overlay;
5. silhouette/edge comparison;
6. candidate with existing skeleton/joint centres overlaid;
7. reference + candidate silhouette + skeleton overlay;
8. final exercise-validation sheet.

Reference and candidate must have identical displayed sole-to-crown height and floor position. Never resize individual body regions in the comparison image.

## 3. Measure instead of guessing

Record normalized measurements as percentages of total character height.

At minimum measure:

- total height;
- head width;
- neck width;
- shoulder-tip width;
- shoulder slope angle from neck/trapezius into deltoid;
- upper-trapezius contour;
- chest width;
- ribcage width;
- narrowest waist width;
- waist width around navel;
- hip/pelvis silhouette width;
- deltoid width;
- upper-arm/biceps width;
- elbow width;
- forearm maximum width;
- wrist width;
- upper-thigh width;
- mid-thigh width;
- knee width;
- calf maximum width;
- ankle width;
- leg spacing;
- vertical positions of shoulder, chest, waist, hip, knee and ankle relative to total height.

Also compare the silhouette at regular horizontal height bands so local contour mismatches are not hidden by a handful of landmark measurements.

## 4. Match this physique specifically

The supplied image is the target. Reproduce these front-view characteristics as closely as practical:

- athletic muscular male; not exaggerated bodybuilding proportions;
- clear V-taper;
- broad but natural shoulders;
- continuously descending neck-to-shoulder line;
- no square shoulder shelf;
- rounded deltoid caps;
- natural trapezius-to-deltoid transition;
- muscular upper traps without a shrugged appearance;
- full upper chest and natural lower-pectoral contour;
- chest wider than waist without an artificial hourglass;
- subtle lat width contributing to the V shape;
- narrow athletic waist;
- restrained oblique thickness;
- proportionate pelvis/hips rather than an unnaturally narrow base;
- muscular upper arms with readable biceps/triceps shape;
- forearms fuller proximally and tapering naturally into the wrist;
- strong thighs with quad shape rather than cylindrical legs;
- visible narrowing at the knees;
- athletic calves with a clear muscle belly and ankle taper;
- lower body substantial enough to balance the torso;
- natural bilateral symmetry.

The shoulder line is a primary acceptance criterion. It should read:

`neck → descending upper trap → rounded deltoid cap → upper arm`

and not:

`neck → horizontal shelf → abrupt deltoid drop`.

## 5. Fit systematically

Do not make one giant sculpt pass. Work region-by-region:

1. overall torso silhouette / V-taper;
2. neck and trapezius;
3. shoulder slope and deltoid cap;
4. chest/ribcage;
5. waist/obliques;
6. upper arms;
7. forearms;
8. pelvis/upper-thigh transition;
9. thighs;
10. knees;
11. calves/ankles.

Use smooth spatial/anatomical masks and falloffs. Keep edits symmetric unless a source asymmetry is already proven. Do not move unrelated vertices merely because they are numerically nearby. Rebuild normals after geometry edits. Keep all skin weights byte-identical to v7.

## 6. Iterate internally to convergence

Do not stop after the first plausible candidate and ask the user to choose between a sequence of half-finished versions.

Use the locked overlay and measurements to refine internally. During iteration use cheap targeted renders/measurements; do not run the full suite after each trial. Retain only the strongest final candidate.

Practical front-reference convergence targets:

- shoulder slope within about **2°** of reference;
- major body widths within roughly **2% of total body height**;
- major vertical landmarks within roughly **1.5% of total body height**;
- no obvious silhouette discrepancy at neck/shoulders/chest/waist/arms/thighs/calves in a 50% overlay;
- negligible new left/right mismatch;
- final candidate visibly closer than v7 across essentially every major silhouette region.

These are targets, not permission to create visibly bad anatomy merely to satisfy a metric. If the overlay and a measurement disagree, diagnose the cause.

## 7. Do not invent unsupported 3D depth

This supplied image is a front reference. Use it strongly for:

- widths;
- vertical proportions;
- front silhouette;
- shoulder slope;
- visible muscular mass distribution.

Do not aggressively invent chest depth, scapular/back shape, glute depth or other rear/side anatomy from a front image. Keep front-invisible depth close to v7 except where a small smooth transition is necessary.

Record which remaining regions genuinely require side/rear reference views.

## 8. Check body surface against the proven skeleton

Overlay the existing skeleton/joint centres on the final candidate and inspect:

- shoulder joints inside the deltoid mass;
- elbow centres aligned with visible elbows;
- wrist centres;
- hip centres inside the pelvis/thigh transition;
- knee centres;
- ankle centres.

Do **not** move the skeleton to chase the image. If matching a photographic dimension would leave a proven joint in an implausible anatomical position, preserve rig integrity, quantify the conflict and report it.

## 9. Validate the retained candidate in motion

After front-reference fitting has converged, inspect the candidate at:

- curl bottom;
- curl mid;
- curl peak;
- deepest squat;
- shoulder press bottom;
- shoulder press overhead;
- push-up top;
- push-up bottom;
- pull-up bottom;
- pull-up top.

Inspect shoulders/armpits, elbows, wrists, chest, waist, hips/groin, knees and calves/ankles.

Reject or repair any new:

- pinching;
- abnormal creases;
- shoulder collapse;
- self-intersection;
- obvious weight-transition defect;
- left/right asymmetry;
- equipment-contact regression.

For the final retained candidate run the appropriate real-character diagnostic and deformation/strain checks, then run typecheck/test/build once. Do not weaken existing thresholds to obtain a pass.

## 10. Shorts handling

Fit and approve the **bare body first**.

After body geometry is final, place the approved F3 garment over the candidate without rebuilding or reinterpreting it unnecessarily.

Approved F3 is source-of-truth geometry because the current builder produces a different front-panel result (previously measured up to about 6.6 mm different). Do not replace it with that regenerated variant.

Check that the new body does not intersect or visibly distort the approved garment.

## Deliverable / stop point

Do **not** promote or merge the reference-match body yet.

Produce one finished candidate, not a menu of unfinished options.

Report concisely:

- candidate filename;
- SHA-256;
- number of moved vertices;
- maximum displacement;
- confirmation topology/skeleton/weights/inverse binds remain unchanged;
- before → after measurement table against the supplied reference;
- shoulder-slope comparison;
- largest remaining front-silhouette mismatches;
- validation result;
- aspects that genuinely require side/rear references.

Provide the locked evidence set:

- supplied reference;
- v7 baseline;
- final candidate;
- reference/candidate 50% overlay;
- silhouette difference;
- skeleton overlay;
- exercise-validation sheet.

Do not stop at “looks closer.” The evidence should make it visually obvious and numerically defensible that the retained candidate is substantially closer to the supplied physique than v7.

**Do not merge.**
