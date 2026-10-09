# P005 — rigid shoulder-chain closure diagnostic (2026-10-09)

**STATUS: experimental mechanical replay only — NOT a skeletal or anatomical correction.**

## Why P005 follows P004

Claude found a +43.2 mm lumbar length excess and three high-trunk residuals in c004. P003 supplied independent segment/disc heights but was rejected because vertebrae moved without their ribs (up to 39.95 mm rib-head/level displacement). The independent P004 replay reattached the 24 ribs by their level's 3D displacement; it translated the sternum by an **unsourced median heuristic** and was correctly rejected by the additional sternoclavicular relative-offset guard.

This P005 work checks one more dependency: **does the entire existing shoulder/arm control hierarchy follow a sternum motion without breaking its own SC, AC or GH reference vectors?**

## Explicit operation

`scripts/anatomy_fit/replay_p005_shoulder_chain.py` takes unchanged c004 and independently generated P004 in memory, builds a fresh record, and translates:

- both clavicle bones;
- every true descendant listed by `parent` in the 206-bone inventory — scapulae, humeri, forearms, wrists, hands, fingers;
- all joint markers with a `frame_bone` in that subtree.

The translation is exactly P004's sternum-head difference from c004: **no new target, scaling, deformation, rotation or location is invented**. The prior P004 spine, all 24 ribs, sternum, sacrum and spine-disc marker positions remain unchanged.

The independent `coupled_shoulder_contact_audit.py` compares marker-to-bone reference vectors, bilaterally, at:

- sternoclavicular marker versus sternum head;
- acromioclavicular marker versus clavicle tail and scapula head;
- glenohumeral marker versus scapula head and humerus head.

It also measures change in a **scapulothoracic proxy**: distance from the existing scapulothoracic marker to the nearest rib 1–8 straight control chord on that side. This is *not* a thoracic surface/contact measurement and cannot certify gliding or anatomy. The audit always reports `canonical_promotion_allowed: false`.

The independent `coupled_trunk_preflight.py` still rejects P004's unmatched SC marker: `STERNUM_SC_RELATIVE_OFFSET_CHANGED_GT_5MM`. The 5 mm is a regression change detector, not an allowable clinical SC displacement. A successful P005 relative-reference test does NOT prove that the starting c004 marker is the correct anatomical SC centre.

## Tests and reproducibility

```bash
python3 -m unittest discover -s scripts -p 'test_coupled_trunk_preflight.py' -v
python3 -m unittest discover -s scripts -p 'test_replay_p004_coupled_thorax.py' -v
python3 -m unittest discover -s scripts -p 'test_replay_p005_shoulder_chain.py' -v

python3 scripts/anatomy_fit/replay_p004_coupled_thorax.py --out /tmp/hgpt_p004.json
python3 scripts/anatomy_fit/replay_p005_shoulder_chain.py \
  --p004 /tmp/hgpt_p004.json --out /tmp/hgpt_p005.json
python3 scripts/anatomy_fit/coupled_shoulder_contact_audit.py \
  --baseline ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json \
  --proposal /tmp/hgpt_p005.json
```

All generated records remain in temporary files and are create-only. The CI workflow performs these steps independently and does not modify Claude's saved branch. This draft has no production modifications.


## Additional neutral-pose arm/thigh diagnostic

The same rigid shoulder-chain displacement can change **distal forearm/hand proximity to the femur controls** even when SC/AC/GH reference vectors are unchanged.

`neutral_arm_thigh_clearance.py` independently computes minimum 3D separation between each forearm/selected metacarpal/finger control segment and **each** thigh/femur control segment, before and after P005. It reports the nearest pair, the largest reduction and a 10-mm **engineering review trigger**. It cannot determine anatomical tissue penetration or dynamic exercise clearance. Even if P005 passes the neutral pose report, previous whole-body dynamic sweeps show hand–femur near-contacts and will still need re-testing in source-appropriate movement start poses.

`test_neutral_arm_thigh_clearance.py` includes synthetic segment intersections, skew and parallel lines, point/segment degeneracies, mutation tests and real c004/P005 comparisons. Its numerical report and mandatory no-canonical-acceptance flags are preserved in GitHub CI output.

## Major gaps still blocking actual anatomical work

1. P005 is founded on P003's still-rejected curve and P004's unsourced sternum shift. Source-compatible pelvis/S1 sagittal geometry, standing thorax tilt, SC/AC/GH height and per-level thoracic wedging remain unproven.
2. Rigid translation cannot demonstrate clavicular elevation/retraction, scapular upward rotation or rib-contact curvature during overhead exercise; the shoulder rhythm conflicts above 98° need resolution.
3. Rib control chords are not realistic curved rib surfaces. The apparent scapulothoracic gap is not a validated physical gap.
4. Human soft tissue, muscles, ligament constraints, true cartilage and surface anatomy have not been rebuilt.
5. Whole-body dynamical motion, collision and the 78 unsourced amplitudes remain independent checks.

**No model production integration, c005 or canonical change is authorised.** Readiness is unchanged at **0 READY, 9 PARTIAL, 3 BLOCKED**.
