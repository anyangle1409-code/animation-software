# Current W8 screenshot review — 22 October 2026

**VISUAL TRIAGE ONLY — BLENDER NOT EXECUTED — CAUSES UNVERIFIED.**

This review converts four supplied screenshots into reproducible QA observations. It does not validate a `.blend`, anatomy, deformation, animation, topology, weights, modifiers, or measurements. The crops and cameras are not matched, so image-space proportions must not be used as scene dimensions. The exact source branch, commit, `.blend` path/hash, and Blender version were not supplied and remain mandatory before native work.

The machine-readable source is `current_w8_visual_qa.json`; `python -m experiments.anatomical_muscles.visual_qa` checks its evidence hashes, permanent muscle IDs, exercise phases, and non-native status. The four files themselves are review evidence and are not committed.

## Evidence manifest

| Image | Pixels | SHA256 | Useful view |
|---|---:|---|---|
| `full_w8.jpeg` | 2059×1040 | `b9f92d67a2948a5776ccb6375af94058c142017ffb73a548fb243e7613a12438` | Whole-body front/side comparison |
| `arm_front.jpeg` | 675×724 | `93bac98ed25e79391f37aee2d57fcc9f05070fc7230a1b10eedebdc4f8d33a8d` | Shoulder, axilla, arm |
| `legs_front.jpeg` | 959×724 | `e7405219a10e066529880e63b5bc0d5f84e6545c84a970260b54269d27516d9f` | Groin, thighs, knees, calves |
| `feet_side.jpeg` | 2241×444 | `6894aeb202655d6d9865cd8e25a4da95b6424ace5f5c6863b6ee0137910acd99` | Foot/ankle side comparison |

## Prioritized observations

| Finding | Priority | Visible symptom | Contract checkpoint |
|---|---|---|---|
| `W8-VIS-AXILLA-001` | P0 | Deep narrow axillary slit; weak anterior/posterior fold transitions | Shoulder press rack and overhead hold |
| `W8-VIS-SHOULDER-002` | P0 | Oversized spherical shoulder cap; weak deltoid-head and adjacent-plane separation | Shoulder press rack, press, lower |
| `W8-VIS-GROIN-004` | P0 | High, deep, pinched central cleft; unclear adductor plane | Squat stand and bottom hold |
| `W8-VIS-HIP-005` | P0 | Broad smooth hip/thigh transition and shelf-like posterior pelvis | Squat descent, bottom, ascent |
| `W8-VIS-ARM-003` | P1 | Smooth tapered arm; weak elbow and flexor/extensor landmarks | All curl phases |
| `W8-VIS-KNEE-006` | P1 | Horizontal knee band; weak patella/condyles; smooth calf and thick ankle | Squat stand and bottom hold |
| `W8-VIS-FOOT-007` | P2 | Blocky heel/midfoot; weak arch/Achilles; simplified forefoot/toes | Squat support poses |
| `W8-VIS-TORSO-008` | P2 | Thick cylindrical neck; smooth chest/abdomen planes and strong side projection | Shoulder press rack and overhead hold |

The screenshots support these symptoms, not their causes. Candidate causes in the JSON are a diagnostic queue only. Do not broadly resculpt to the reference image or let the experimental muscle layer conceal base-body defects.

## Required diagnostic order

1. **Pin source identity.** Record branch, commit, `.blend` path, SHA256, Blender version, body object, armature, units, anatomical-side mapping, active modifiers, and render camera. Copy to a new suffixed experimental file. Do not save the source.
2. **Make matched evidence.** Render neutral front, side, back, and three-quarter orthographic views from identical cameras for baseline and candidate. Add silhouette overlays and scene-unit measurements at named landmarks.
3. **Isolate the visible defect.** Toggle outer surface, experimental muscle/tendon layers, normals, modifiers, weights, and correctives one category at a time. Record the first state that changes the symptom; do not infer it from a still.
4. **Check guides and clearance.** Overlay the unchanged skeleton, anatomical landmarks, attachment patches, paths, wrap guides, and skin surface. Measure intersections and clearance. Never move the validated skeleton to fit the surface.
5. **Check the layer below skin.** Render muscle-only, skin-only, and overlay views. Inspect broad attachment patches, tendon transitions, tissue overlap, and path continuity before connecting skin response.
6. **Check motion and activation separately.** First run the joint trajectory with activation fixed at zero. Then hold pose fixed and sweep the explicit visual activation channel. Finally combine them. Record path length, envelope volume, intersections, maximum skin delta, and temporal discontinuities.

## Initial native test matrix

| Region | Poses / phases | Muscle IDs to expose first | Acceptance evidence |
|---|---|---|---|
| Shoulder/axilla | Neutral; press rack; 45°, 90°, 120°, 150–160° elevation; overhead hold; lower | Deltoid anterior/middle/posterior, pec major heads, latissimus, teres major, triceps long, cuff, serratus, trapezius — both sides | No slit/puncture or surface crossing; readable folds and head transitions; continuous paths; no temporal pop; neutral silhouette unchanged at zero activation |
| Arm | Curl setup, concentric midpoint, top hold, eccentric midpoint, return | Biceps long/short, brachialis, brachioradialis, triceps long — both sides | Length direction agrees with contract; fixed-pose activation changes belly/skin without moving bones; elbow remains legible; returns to neutral |
| Pelvis/upper thigh | Stand; hip 45°, 90°, 110°; squat descent, bottom, ascent; hip extension and abduction | Gluteals, iliacus/psoas, TFL, sartorius, rectus/vasti, adductors, hamstrings — both sides | Genital-neutral surface; no central pinch or intersection; continuous gluteal/adductor/quad planes; no banding or temporal pop |
| Knee/calf/ankle | Squat stand/bottom plus sampled transition frames | Rectus/vasti, gastrocnemius heads, soleus — both sides | Patellar route remains plausible; knee ring does not appear; calf volume and ankle transition remain continuous |

The foot observation is a separate morphology checkpoint. The lower-leg muscle pass may clarify Achilles continuity, but it must not be accepted as a repair for heel, arch, forefoot, or toe proportions without direct native review.

## Accept/reject rules

Accept a region only when all required views and transition frames exist; source and candidate use matched cameras and poses; the source skeleton, body Basis, topology, production weights, and non-experimental keys compare unchanged; muscle IDs and reviewed bone-local bindings are recorded; activation-at-fixed-pose and pose-at-zero-activation both pass; overlap, clearance, skin displacement, volume, and temporal results are recorded; and the nine prior movement benchmarks plus the R52/R57 native checks are rerun under identical conditions.

Reject or keep blocked when identity/hash is missing, only endpoint stills exist, a screenshot symptom is presented as a diagnosed cause, a deep muscle transfers directly to skin, activation is inferred from joint angle, rest silhouette changes at zero activation without approval, previous failed global corrective/weight experiments are repeated, or the production asset/version is modified.

## Claude action order

1. Pin the exact current W8 source identity and generate matched baseline evidence.
2. Diagnose `W8-VIS-AXILLA-001` and `W8-VIS-SHOULDER-002`; complete one shoulder side in the copied experiment and verify the opposite side independently.
3. Run the shoulder-press contract with joint motion and activation isolated, then combined.
4. Diagnose `W8-VIS-GROIN-004` and `W8-VIS-HIP-005`; complete one pelvis/upper-thigh side and independently verify the opposite side.
5. Run the squat contract and retain failed frames. Then run the curl contract against the arm observations.
6. Record Blender commands, version, source/candidate hashes, metrics, renders, and a PASS/FAIL/BLOCKED matrix. Save only a new suffixed experimental `.blend`.

Production promotion, asset replacement, merge, and deployment remain outside this experiment and require explicit approval.
