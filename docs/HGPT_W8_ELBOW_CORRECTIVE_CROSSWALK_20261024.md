# W8 elbow-edge / actual shoulder corrective crosswalk — 24 October 2026

**Read-only diagnostic; not anatomical validation or a deformation fix.** Repository branch: `work/phone-blender-workbench-20261023`. The original W8/V14/R120 reconstructions, skeleton, weights, muscle registry, PT-App and production assets remain untouched.

## Verified inputs

- [Seven-job run 40064463613](https://github.com/anyangle1409-code/animation-software/actions/runs/40064463613): all seven jobs SUCCESS (three Blender inspections, pose probe, rest comparison, driver consistency, native localization).
- W8 Blender artifact **12548203789**, independently downloaded ZIP SHA256 `9b749298038c78045da30e15590059d6526e9597c201c8dd5a0ea83d7a2cce38` MATCH GitHub. Embedded `W8/w8_elbow_edge_endpoint_weights_and_keys.json` SHA256 `f6eae5169797780118db5eabd172f913f9d1933a2c5bfffa0b240da22a0b0865`.
- W8 actual pose artifact **12548499105**, independently downloaded ZIP SHA256 `613f94744f75597aa5acd69831b76798283f2e8f878ad7064cca42f90f84e7a9` MATCH GitHub.
- Driver-consistency artifact **12548479437**, independently downloaded ZIP SHA256 `4d2f95d8dfd05d2613b4130d9ba28375482edb03713cadce1cf37a68e71865fa` MATCH GitHub.
- All inputs declare reconstructed W8 SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`; no source model was saved. These are *read-only report provenance checks*, not acceptance of the archived original.

## Static edge evidence (source pinned)

| W8 authored region suffix (NOT anatomical side) | Mesh vertices | Rest length (mm) | Endpoint skin-weight L1 | Key with large stored geometry effect |
|---|---|---:|---:|---|
| distal l | 15645, 53019 | 6.116202 | 0.1284237 | S5_BAKE_l_85: stored edge/Basis 1.7081 |
| distal r | 17185, 44317 | 6.055721 | 0.1284237 | S5_BAKE_r_85: 1.7259 |
| middle l | 29237, 71026 | 3.554222 | 0.0300108 | S7_DELT_l_145: 2.8142 |
| middle r | 32352, 71428 | 3.528345 | 0.0300107 | S7_DELT_r_130: 2.7894; S7_DELT_r_145: 2.7767 |

The middle edges have similar endpoint weight vectors: ~0.862–0.872 `upperarm_[suffix]`, ~0.070–0.073 `spine_03`, with smaller shoulder-cap, scapular and forearm influences. **Low L1 difference does not rule out pose-dependent skinning or corrective deformation.** A stored shape key's edge-length ratio is *not* the final posed edge ratio and cannot be multiplied by the key value to calculate one.

## Observed key values from the actual nine-frame W8 press probe

- At press **sample 0**, measured pinned-driver humerothoracic angle ~87.68 degrees: `S5_BAKE_[l/r]_85` observed ~0.892817/0.892818. Middle-edge S7 145 key observed **0**.
- At **sample 6**, measured ~145.73 degrees: `S7_DELT_[l/r]_145` observed **0.934006/0.934011** and `S7_DELT_[l/r]_156` observed **0.065994/0.065989**. These are the same sample and region in which the prior ranked-edge report identified maximum middle-arm pose/rest ratios **2.673372/2.648593**.
- At **sample 8**, measured ~156.10 degrees: `S7_DELT_[l/r]_156` observed **0.989697/0.989694** and `S7_DELT_[l/r]_166` observed ~0.0103; `S7_DELT_[l/r]_145` observed **0**.
- The actual pose probe does **not** list the `HGPT_K1_ELBOW_[l/r]_90/110` keys that appear in some top-12 stored static key inventories. **Missing is UNKNOWN, not zero.** The new crosswalk preserves that distinction.

These observations narrow the investigation to the **interaction** of S5/S7 corrective values, bone skinning, cap/helper motion, shape-key relative-key semantics and the original pose. They do **not** isolate the cause or demonstrate elbow flexion/forearm rotation, because the sampled exercise is a shoulder press.

## New reproducible read-only tool

`scripts/cloud_body_analysis/elbow_corrective_crosswalk.py` takes two JSON members (`--endpoint`, `--pose`) and writes `w8_elbow_corrective_crosswalk.json/.md` to `--out`. It rejects mismatched immutable source hashes, missing samples, nonfinite values, duplicate records and false anatomical approvals. It distinguishes measured zero from missing values, and includes input member SHA256.

Eight synthetic tests in `scripts/cloud_body_analysis/tests/test_elbow_corrective_crosswalk.py` **PASS locally**. A real archived-data replay against the three downloaded run-40064463613 artifacts produced four edge records and samples 0/6/8 successfully. The cloud workflow has been extended to run the test and crosswalk in the existing W8 driver-consistency job. **The new workflow's cloud CI result and its new artifact digest remain unverified until a subsequent run completes.**

## Remaining independent gates

The [ISB upper-limb recommendations](https://pubmed.ncbi.nlm.nih.gov/15844264/) and [lower-limb recommendations](https://pubmed.ncbi.nlm.nih.gov/11934426/) define anatomical coordinate conventions, not certified Blender axes. Thorax/clavicle/scapula/humerus landmarks, humeral epicondyles, radius/ulna landmarks and pelvis/hip/knee/ankle/foot coordinate mapping remain unbound. The [2025 scapular review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/) does not justify a universal fixed scapulohumeral ratio. [CDC population ROM means](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html) are descriptive, **never model limits**.

**46 anatomical landmarks unbound; 0/19 generic movement tests approved.** Shoulder press, squat and grip failures remain unresolved; V14 archive two-vertex and W8 archive differences remain unresolved. Do not edit preserved .blend sources, attach muscles, implement highlighting, merge or deploy. Next evidence needed: independently verified new cloud crosswalk artifact, then controlled isolated candidate tests comparing S7 on/off with actual pose and identical skinning, plus independent anatomical frame calibration.
