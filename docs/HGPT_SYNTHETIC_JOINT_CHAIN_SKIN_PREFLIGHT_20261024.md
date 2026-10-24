# Synthetic whole-body joint-chain and skin-continuity preflight — 24 October 2026

**Status: software QA only. No anatomical ISB calibration, native movement pass, physiological tissue strain or model repair.**

## Why this is the next safe dependency

The owner's goal is a coherent human rig for many exercises, not independent animation shortcuts. The preserved W8/V14/R120 reports each describe 77 resting bones, but their bone-local axes are **not** verified anatomical axes. The original shoulder press, squat and grip failures remain. Before a native joint-chain acceptance test, we need trustworthy mathematical invariants and fail-closed evidence gates.

Source conventions:
- Wu et al. 2005, [ISB Part II: shoulder, elbow, wrist and hand](https://pubmed.ncbi.nlm.nih.gov/15844264/), DOI 10.1016/j.jbiomech.2004.05.042.
- Wu et al. 2002, [ISB Part I: ankle, hip and spine](https://pubmed.ncbi.nlm.nih.gov/11934426/), DOI 10.1016/S0021-9290(01)00222-6.
- [ISB standards index](https://www.isbweb.org/activities/standards) for foot segment conventions.
- [CDC joint ROM reference](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html): population means and confidence intervals are descriptive, not model limits.
- [2025 scapular kinematics review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/): no fixed universal scapulohumeral rhythm is imposed.

The **code's frames are invented proper right-handed Cartesian frames**, not a transcription or certification of any ISB segment-frame recipe. The pair called `shoulder_glenohumeral_proxy` is simply a scapula-to-humerus relative rotation; it is not a clinical GH angle. Likewise `elbow_forearm_proxy` cannot distinguish humeroulnar flexion from radius–ulna pronation.

## New read-only files

- `scripts/cloud_body_analysis/joint_chain_skin_preflight.py`: generates an invented three-sample reference → moved → returned trajectory, measures unsigned relative SO(3) orientation change for eight segment pairs, and compares fixed mesh-edge IDs and edge lengths across samples. Uses `frame_math_contract.py` for existing proper-frame and rotation QA. No Blender import, model open/save, muscle ID modification, production asset or clinical limit.
- `scripts/cloud_body_analysis/tests/test_joint_chain_skin_preflight.py`: 13 synthetic regression tests, including global rigid rotation and translation invariance, return-to-start, valid/invalid handedness, missing foot segment, changed topology, duplicate edges, degenerate edges, nonfinite coordinates and rejected false approvals.
- `.github/workflows/phone-blender-workbench.yml`: the existing comparison job now runs these tests and publishes `synthetic_joint_chain_skin_preflight.json` and `.md` in the phone-rest-cross-model artifact. The independent native localization job also discovers these tests.

The reference chain covers thorax–clavicle, thorax–scapula, scapula–humerus, humerus–forearm, pelvis–femur, femur–tibia, tibia–hindfoot and hindfoot–forefoot. The skin-edge example deliberately changes one invented edge length by 20% and returns it to its original length; this is a test of *measurement*, **not** a safe human tissue stretch limit. Rigid global motion must not alter the relative joint or edge metrics.

## Evidence and status

- **13/13 new tests PASS in local isolated execution**; the synthetic command produced 8 relative-frame pairs and 2 mesh-edge records. Local tests used an equivalent small numerical helper for the existing frame functions. Cloud verification using the actual repository helper is **PENDING**.
- GitHub source commits: `96cfb7c197ca5abc3fa4b8b2aa453f6419d96294` (module), `459e6c7ab02029e551236981cf90387ebde361b2` (tests), `5071ca0af4c9e1421fa20836ae7aaf8373bb38c0` (workflow). Branch ref was compared to the last commit and was identical at that check.
- The historical [five-job run 40029398965](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965) was rechecked in this invocation: **four successful jobs, one failed read-only test**. Its four ZIP archives were freshly downloaded and independently SHA256-matched to GitHub. W8, V14 and R120 embedded `rig_rest_axes_metadata.json` contain 77 bone records each, hashes matching the execution ledger, and `model_motion_axes_calibrated_to_ISB=false`.
- **Not yet verified:** a new workflow run, eight-pair artifact from GitHub, native segment frames, anatomical left/right, radius/ulna separate axes, hip/knee/ankle/foot contact, muscle attachments, skin safety or any new movement.

## Blocking gates

All **46 landmark requirements remain unbound**; **0/19 generic human motion scenarios executed or approved**. Do not use this synthetic test to promote anatomical acceptance. A future *native* diagnostic requires independently reviewed segment landmark positions and coordinate conventions, correct side identity, full time-series transforms, actual skin topology, ground/hand contacts and independent movement review. V14's two-vertex archival mismatch and W8's archive discrepancy remain open.

No original `.blend`, source mesh/weights, validated skeleton, Claude-owned branch, PT-App, production asset, `PT_MODEL_VERSION 1.0`, permanent muscle IDs or owner-deferred muscle highlighting changed. No merge or deployment.
