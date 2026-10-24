# Home Gym PT — ISB joint-frame dependency crosswalk (read-only)

**24 October 2026. Status: source-backed planning and fail-closed diagnostics; NOT an anatomical calibration.**

## Purpose and provenance

The 77-bone W8/V14/R120 **rest-axis metadata** are structurally identical in the existing hash-pinned cloud audit. This does not establish anatomical segment frames, joint centres, true left/right sides, skin response, or movement approval. The source reconstructions remain W8 `2434afd0...`, V14 `5969aa98...`, R120 `fb3b0acf...` (full SHA256 values are enforced by the script). The previous [five-job run 40029398965](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965) had three successful Blender model jobs and successful cross-model comparison, but **overall failed** because a text-only test searched a docstring for the string `bpy.ops`. The corrected [run 40030373550](https://github.com/anyangle1409-code/animation-software/actions/runs/40030373550) passed all five jobs. This was a test defect, not evidence of an anatomical fix. Native model ZIPs from the earlier run have independently verified digests recorded in `HGPT_ISB_NATIVE_RIG_LANDMARK_GAP_20261023.md`.

The new `scripts/cloud_body_analysis/joint_frame_readiness.py` joins three *existing* immutable research/checklist inputs without modifying them:

- `docs/anatomy/HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json`: 19 generic test scenarios and named joint families.
- `docs/anatomy/HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json`: 46 permanent but **unbound** anatomical landmark IDs and nine incomplete segment checklists.
- `docs/anatomy/HGPT_HUMAN_MOTION_TEST_EXECUTION_LEDGER_V1.json`: 0/19 generic tests executed, with earlier shoulder press/squat/grip **failures** kept separate.
- Live cloud `rig_rest_axes_metadata.json` for each of W8/V14/R120, validated through `compare_rig_axes.compare` with exact model-source hashes, rest-rig identity and explicit anatomy non-approval.

The output `joint_frame_readiness.json` / `.md` lists, **for each of 19 scenarios**, required existing segment checklists, unbound landmark IDs for both sides, missing distinct segment-frame categories, and related pre-existing benchmark status. The categories are **conservative triage prerequisites**, not copied ISB frame equations or approved axis definitions. Unknown future joint families, altered source identities, forged landmark bindings, changed ROM safety claims and prematurely marked generic tests fail closed.

## Interpretation and priority

**Shoulder:** distinguish clavicle–thorax, scapula–thorax, humerus–scapula and humerus–thorax, not one scalar shoulder angle. Resolve IJ/PX/C7/T8, scapular TS/AI/AA, clavicle SC/AC and GH centre plus humeral epicondyles with reviewed 3D side orientation. Establish actual neutral pose, rotation order and robust singularity handling before assigning ISB angles. A fixed scapulohumeral rhythm is not a substitute for measured movement.

**Elbow/forearm:** verify humeral epicondyles and radius/ulna separate longitudinal frames and proximal landmarks. The existing checklist contains distal radial/ulnar styloids but does not provide independently certified radius and ulna segment frames. The existing W8 upper-arm PCA spread ratio is a **surface-shape proxy**, not a joint-centre, biceps tendon, elbow circumference, or proof of pronation/supination. Test flexion in supinated, neutral and pronated forearm states only after actual axes are calibrated.

**Hip/knee/ankle/foot:** review ASIS/PSIS, estimated femoral head centre, knee epicondyles and malleoli, with explicit tibial and patellar frames. Distinguish hindfoot, midfoot, forefoot and toe motion; verify planted-foot contact and whole-body squat transitions. Lower-limb/foot landmarks in the checklist are marked **proposed candidates**, not certified verbatim ISB definitions. A hip/knee/ankle numerical angle from Blender bone roll is not automatically a human joint angle.

**Whole-body reference:** preserve all 19 generic scenarios and existing source evidence; do not overfocus on the shoulder. No model changes, new pose trajectories, ROM hard stops, exercise contract promotion, muscle binding, highlighting visualization, production or app changes occur in this work.

## Sources

- Wu et al. (2005), ISB Part II: shoulder/elbow/wrist/hand segment and joint coordinates: https://pubmed.ncbi.nlm.nih.gov/15844264/
- Wu et al. (2002), ISB Part I: ankle/hip/spine: https://pubmed.ncbi.nlm.nih.gov/11934426/
- ISB standards portal for multi-segment foot: https://www.isbweb.org/activities/standards
- Senk & Chèze (2006), sequence/singularity considerations: https://pubmed.ncbi.nlm.nih.gov/16274906/
- 2025 systematic review on scapular motion variability: https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/
- CDC joint ROM clinical population means and confidence intervals (descriptive only): https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html

## Reproduce from phone/cloud

```bash
python -m unittest discover -s scripts/cloud_body_analysis/tests -p test_joint_frame_readiness.py -v
python scripts/cloud_body_analysis/joint_frame_readiness.py \
  --rig-root /path/to/three-extracted-phone-blender-report-folders \
  --out /tmp/phone-readiness
```

The workflow's `compare-rest-audits` job downloads the three **same-run** Blender reports and invokes this script. The cross-model phone artifact will contain both `joint_frame_readiness.json` and `joint_frame_readiness.md` **only if CI successfully runs**. At creation of this document, new CI has **not yet been certified**; check run conclusion, tests, emitted report and ZIP digest before claiming a verified result.

**Blocking gates:** independently reviewed landmark positions and sides; measured segment transforms/ISB joint coordinates; actual isolated movement samples; full shoulder/axilla, elbow/forearm and hip/knee/ankle skin/contact evidence; return-to-neutral; failed press/squat/grip acceptance; W8/V14/R120 reconstruction equivalence. No muscle origins/insertions or side axes may be inferred from the report. Muscle IDs remain stable; highlighting is owner-deferred.

## Verified CI outcome — 24 October 2026

The earlier pending statement is superseded: [run 40043125200](https://github.com/anyangle1409-code/animation-software/actions/runs/40043125200) finished **SUCCESS in all seven jobs**. The report-only test discovery ran **135/135 PASS**, and the cross-model job separately ran **12/12 new dependency tests PASS**. [Artifact 12539879095](https://github.com/anyangle1409-code/animation-software/actions/runs/40043125200/artifacts/12539879095) was independently downloaded and inspected; ZIP SHA256 matched GitHub: `463941d354ced308822a28ac786a2c31932feb6a3cfaa02d56a009a25e60bf66`. The embedded `joint_frame_readiness.json` SHA256 is `643f35d583107bd6f65a83e29194fab1c519a8c8917de1d93ecaf79649ee7902`.

The report lists **46/46 unbound landmarks**, **0/19 generic tests executed or approved**, and all native ISB frame/skin/muscle gates FALSE. This verifies the fail-closed crosswalk and exact source evidence, **not** anatomical or exercise correctness. Existing deformation failures and reconstruction blockers remain open.
