# ORIGINAL_v1 review candidate R3 = R2 + K1 wrist-extension keys (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.** R3 replaces R2 as the single
consolidated review candidate. R1 and R2 stay in place unchanged as its ancestors.

**Lineage:**
- **R1:** C5 feet + W3A shoulder helper + K1 knee 90/110/130 + K1 elbow 90/110.
- **R2:** R1 + S1 overhead-shoulder relax keys.
- **R3:** R2 + K1 wrist-extension keys.

## The defect

The dorsal wrist skin of a003 passes through itself in extension. The pure-extension sweep on R2 (both hands, collapse / stretch > 2 / pairs):

| Extension | R2 | R3 |
|---|---|---|
| 60° | 0 / 4 / 0 | 0 / 6 / 0 |
| 70° | 0 / 8 / 16 | 0 / 10 / 0 |
| 80° | 4 / 10 / 52 | 0 / 12 / 0 |
| 90° | 10 / 12 / 130 | 0 / 14 / 0 |
| 100° | 8 / 20 / 140 | 4 / 22 / 0 |

- **Where it bites:**
  - the push-up's top frames, which need 97° of loaded extension (192 pairs, mostly forearm/hand and forearm/metacarpal);
  - the wrist circuit's extension frame at the 68° active mean.
- **Volume:** identical to R2 within 0.01 % at every angle.
- **Cost:** +2 stretched faces from 60° up (one per hand). This is recorded, and the test allows exactly that.

## Method

K1 is generalised in `scripts/build_original_knee_contact_corrective_blender.py`:
- **Per hinge:** an `axis`, a per-side sign, and an activation start.
- **Optional per hinge:** softplus contact and a count-based fold/collision guard.

Knee and elbow behave exactly as before; K1's 7 native tests pass.

**The `wrist` hinge:**
- **Motion:** hand about local Z. Extension is −Z on `_r` and +Z on `_l`, i.e. minus the measured palmar sign; the build checks this on the rig.
- **Groups:** proximal = forearm and its twist bones; distal = hand and metacarpals.
- **Keys:** 60, 80 and 100° of extension, starting from 30°.
- **Zone:** 10 cm radius.
- **Contact:** soft (softplus 3 mm, gap 2 mm).
- **Rest-space mapping:** blended LBS is well conditioned here (σmin 0.64–0.87), with no clipping (max rest delta 20 mm).

**Guard:** over 30–100° in 5° steps, wherever the keyed mesh has more collapsed faces or more pairs than the key-free mesh, the deltas of the newly bad faces (+ 2 rings) are halved. It acted once (60°: +2 collapsed fixed) and was clean on the second pass.

**Rejected on the way:**

| Variant | Result | Why rejected |
|---|---|---|
| Hard projection (K1's knee mode) | +12–16 collapsed faces from 60° | worse folds |
| Gap 4 mm | +8–14 collapsed faces | worse folds |
| Soft 3 mm + gap 4 mm | +4–10 collapsed faces | worse folds |
| Set-based guard | the benefit is removed (pairs at 90° back to 126) | the crease converts pass-through skin into compressed skin, so some faces newly collapse even where the total falls |

## Results on all 13 benchmarks (`r3_validation.json`)

- 12 benchmarks are identical to R2 at the worst frame.
- **Push-up:**

  | | Collapse | Stretch | Pairs |
  |---|---|---|---|
  | R2 | 14 | 74 | 192 |
  | R3 | 2 | 72 | 50 |
  | a003 | 12 | 64 | 196 |

  - The top frames' wrist pairs fall from 192 to 42.
  - **K1 angle fix (same day):** K1 read the elbow angle from an XYZ Euler, which under-reported a pronated 110° elbow as 97.5°, so the elbow keys under-fired in the push-up's bottom frames (166 pairs). The read is now swing–twist and exact under twist (regression test added; K1 on the movement branch carries the same fix). With it, the bottom elbow crease is handled and the push-up's worst frame is 50 pairs (remaining: thumb base against index metacarpal). R1/R2/R3 validations were re-run with the fix; nothing else changed.
- **Wrist circuit:** worst frame unchanged. The extension frame has 0 pairs instead of 2, with +2 stretched faces.

## Evidence

- `closeups/wrist_ext90_{front,lateral}_compare.jpg`: R2 vs R3 at 90° pure extension. The crease is flatter, with less pass-through; the difference is subtle at phone scale.
- `sequences/push_up*`, `sequences/wrist_circuit*`: a003 vs R3.
- **Everything else:** use R2's (shoulder) and R1's (other benchmarks, full body, close-ups). The validation shows them identical.

## Tests

`scripts/blender_tests/test_original_review_candidate_r3.py`, 5 native tests:
- **Identity:** the SHAs, and the side signs match the measured palmar sign.
- **Contents:** R3 equals R2 plus exactly six wrist keys; 67 joints, same weights.
- **Deltas:** the wrist deltas stay on their own wrist and are capped.
- **Pure sweep:** no worse folds or collisions; stretch at most +2; volume within 0.02 %; the 90° crease goes from > 100 pairs to 0.
- **Benchmarks:** unchanged except the push-up, which improves on every measure.

CI runs it (`original-review-candidate-r1.yml`), together with the K1 tests on the generalised module.

## Still open

- **Thenar stretch** from the push-up thumb extension.
- **Hip fold:** deadlift and squat; needs a three-body contact model.
- **W3A armpit bulge and posterior axillary web.**
- **Shipping:** needs the R1/R2 runtime-contract items plus six wrist morphs on the measured wrist angle (owner + Lane G, PR #26).
