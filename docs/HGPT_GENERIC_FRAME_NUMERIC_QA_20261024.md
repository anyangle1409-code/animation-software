# Home Gym PT — numerical frame-quality preflight (synthetic, read-only)
**24 October 2026. Not an ISB calibration, an anatomical approval, or a human movement test.**

## Why this is a separate gate

The preceding [joint-frame dependency crosswalk](HGPT_ISB_JOINT_FRAME_DEPENDENCY_CROSSWALK_20261024.md) identifies **46 unbound** candidate anatomical landmarks, **0/19** executed generic motion scenarios and unresolved scapula/clavicle/humerus, radius/ulna and hip/knee/ankle/foot frames. The W8/V14/R120 rest-rig axis comparison establishes consistent authored bone-local metadata, **not** anatomical axes. Before a future reviewer can convert independently verified landmarks into joint-coordinate trajectories, we need reproducible mathematical guards against ill-conditioned triads, reflected coordinate frames and misread rotations.

## New scope

`scripts/cloud_body_analysis/frame_math_contract.py` supplies a **generic mathematical preflight only**, without `bpy`, native models, body mesh, pose edits, or ROM values:

1. A frame is built from three **invented** points: an origin, a primary-axis point and an independent plane point. The generic z-axis follows the primary vector, generic x is the plane vector orthogonalized against z, and y is z × x. This right-handed construction is **not a claimed ISB segment definition**. ISB requires precise segment-specific landmark selection, axis order, joint sequence and independently established anatomical side.
2. Reject nonfinite/bool/non-3D inputs, coincident points, near-collinear axes (illustrative conditioning criterion sine < 0.05), nonunit/nonorthogonal bases and improper reflections (determinant −1). The 0.05 threshold is a **numerical guard**, not an anatomical tolerance or clinical threshold.
3. Compute unsigned SO(3) geodesic angular separation between two proper frames and a sequence's per-step/return-to-initial angular separations. **This is not** elbow flexion, GH elevation, forearm pronation, hip flexion, safe ROM, or an ISB Euler/Cardan angle. It does not establish temporal continuity between samples or skin quality.
4. Four intentionally synthetic examples represent shoulder girdle, elbow/forearm, pelvis/knee and ankle/multisegment foot **as coverage labels only**. Translation invariance, 90°/180° rotations, mirrored-point proper-frame reconstruction, reflection rejection and neutral return are tested; no native landmarks are supplied or inferred.
5. The output `synthetic_frame_math_guards.json/.md` explicitly records zero model landmarks, zero executed generic human movement tests, and FALSE for ISB calibration, side approval, skin, muscle attachment, ROM clamping and highlighting.

**Research foundation and limits:** Wu et al. (2005), [ISB Part II shoulder/elbow/wrist/hand](https://pubmed.ncbi.nlm.nih.gov/15844264/); Wu et al. (2002), [ISB Part I hip/ankle/spine](https://pubmed.ncbi.nlm.nih.gov/11934426/); Senk & Chèze (2006), [joint-angle sequence considerations](https://pubmed.ncbi.nlm.nih.gov/16274906/); [ISB foot standards portal](https://www.isbweb.org/activities/standards). The [2025 scapular kinematics systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/) reinforces that a universal fixed scapulohumeral rhythm must not be assumed. The [CDC clinical ROM population statistics](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html) remain descriptive group means and confidence intervals, **not** model hard stops.

## Reproduce

```bash
python -m unittest discover -s scripts/cloud_body_analysis/tests -p test_frame_math_contract.py -v
python scripts/cloud_body_analysis/frame_math_contract.py --out /tmp/hgpt-frame-preflight
```

The existing cloud `localize-native-movement-failures` job discovers all tests. The `compare-rest-audits` job is extended to run these **synthetic** tests and place the phone-readable JSON/Markdown in the cross-model artifact. A passing test is evidence of **software arithmetic and fail-closed safeguards only**, not an improved Blender model. Verify the triggered Actions run and artifact hashes before marking cloud results verified.

## Next independent anatomical calibration gates (not performed here)

- Review real 3D IJ/PX/C7/T8, scapular TS/AI/AA, clavicular SC/AC and humeral epicondyles plus GH-centre method; derive independently reviewed anatomical side, neutral and segment coordinate definitions before comparing scapula, clavicle and humerus. No universal scapular ratio.
- Review medial/lateral epicondyles and **distinct proximal/distal radius and ulna** segment landmarks before attempting elbow flexion and forearm pronation/supination. A biceps surface PCA taper is not an anatomical tendon or joint frame.
- Review pelvis ASIS/PSIS and femoral centre method, knee epicondyles, tibia/fibula and malleoli, then separate hindfoot/midfoot/forefoot/toes. Preserve foot-ground contact and pelvis/trunk coordination across the full squat.
- Once source- and side-verified landmarks exist, establish exact ISB frame equations, handedness, axis sequence and singularity handling; test actual native Blender trajectories against reference in multiple camera views and quantify skin/contacts. **Do not automatically promote this generic triad utility to ISB coordinates.**

**Preservation:** no original `.blend`, rig, skin weights, shape keys, model-source hashes, production assets, Claude branch, PT-App, PT_MODEL_VERSION 1.0, muscle attachments, UI or exercise contracts are changed. Permanent muscle IDs remain intact; muscle highlighting stays deferred. Existing press/squat/grip failures, archive-equivalence discrepancies and 19 generic motion-test blockers remain.
