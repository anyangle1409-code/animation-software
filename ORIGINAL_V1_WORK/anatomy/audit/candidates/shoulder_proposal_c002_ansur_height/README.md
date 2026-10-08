# Shoulder proposal c002: ANSUR living-height anchor (audit candidate, not canonical)

**Identity:** `r95_a003_shoulder_proposal_c002_ansur_height`
**Status:** `AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED`. `freeze_ready=false`, `character_accepted=false`.
**Closure against the retained trunk: FAIL** (see below).

> **Naming:** "c001" and "c002" here are short for the audit IDs `r95_a003_shoulder_proposal_c001` and `…_c002_ansur_height`. They are unrelated to the reserved canonical name `HGPT_CANONICAL_SKELETON_FIRST_c001`, which has not been created and must not be until target selection is freeze-ready.

## Owner policy

`SHOULDER_HEIGHT_ANCHOR_ANSUR_LIVING` (8 October 2026; recorded in `canonical_target_selection_v1.json` `owner_decisions`):
- absolute shoulder height follows the living standing ANSUR survey;
- internal clavicle length and orientation, scapular geometry and AC–GH relations stay those of the reconciled bony solution;
- the standing thorax pitch stays an open sensitivity variable.

This is a modelling policy for a living exercise character. It does not settle the skin-to-bone landmark relationship.

## Construction

| Item | Value |
|---|---|
| Source | `../shoulder_proposal_c001/candidate_record.json`, sha256 `08e9f2e1187dbeda…`, pinned. c001 itself is unchanged. |
| Target | ANSUR II acromial height at 1.82 m: **1497.7 mm**, residual SD 16.2 mm. Recomputed in a test from the committed 4,082-man CSV (OLS on stature). |
| Matched bony landmark | Lee 2024 **LM27, lateral distal acromion**, both sides |
| Bracket landmark | LM25, exterior acromial angle: 14.2 mm lower than LM27 |
| Skin-to-bone offset | **Not applied.** It is unquantified; the bony point lies below the skin point, so applying it would lower the bones further. |
| Translation | **x 0, y 0, z −63.0 mm.** Applied rigidly to all 64 c001-moved bones, 88 markers, the 29 scapula landmarks per side and the shoulder `skeleton_input` points. |
| Unchanged | Trunk, sternum, ribs and spine (a003's); every internal girdle and arm distance (test-enforced) |

**Landmark-definition caveat:** I could not reach the primary ANSUR II landmark text from this environment (Hotzman et al. 2011, NATICK/TR-11/017; Gordon et al. 2014; DTIC and archive.org are blocked). The mapping therefore rests on secondary descriptions: the landmark is on the lateral edge of the acromion at the shoulder tip. Verify it on the laptop.

## Before and after (left side; the right is an exact mirror)

| Point | c001 z (mm) | c002 z (mm) |
|---|---|---|
| LM27 lateral acromion | 1560.7 | 1497.7 (= target) |
| AC centre | 1545.7 | 1482.7 |
| GH centre | 1520.1 | 1457.1 |
| SC centre | 1526.0 | 1463.0 |

a003 for comparison: AC 1497.5, GH 1462.4 mm.

## Closure check: FAIL (recorded, not forced)

- The retained a003 jugular notch (sternum head) is at 1519.2 mm. The c002 SC joints sit **56.2 mm below it**. The source relation (Seth) puts SC 6.0 mm *above* IJ.
- That is beyond the whole range of published male mean manubrium lengths (46–55.2 mm), so the clavicles no longer reach the clavicular notches of the retained sternum.
- **No recorded variant closes:**

| Thorax pitch | IJ height | LM27 dz | SC − own IJ | LM25 dz | SC − own IJ |
|---|---|---|---|---|---|
| bony 7.04° | a003 (1519.2) | −63.0 | −56.2 | −48.8 | −41.9 |
| bony 7.04° | ANSUR (1494.5) | −38.3 | −31.5 | −24.1 | −17.3 |
| living −11.3° | a003 | −66.1 | −61.6 | −66.6 | −62.1 |
| living −11.3° | ANSUR | −41.4 | −37.0 | −42.0 | −37.5 |

**Reading:** with the bony clavicle orientation retained (elevation 9.8°), the living acromial anchor and the bony SC-on-manubrium relation cannot both hold. One more owner decision, or new evidence, is needed:
- **(a) Lower the thorax/sternum with the girdle.** This changes the trunk; it would also conflict with the ANSUR suprasternale and cervicale anchors.
- **(b) Accept a lower clavicle elevation.** Closing from IJ at ANSUR would need roughly −4.8° instead of 9.8°. That is a first-order estimate: the chord is rotated about SC, ignoring pitch and the scapula's response. It is about 3.2 SD below the Matsumura male mean of 8 ± 4°, so this would need evidence.
- **(c) Obtain a source that pairs skin acromiale with bone,** which might remove part of the gap.

## Other checks

- **CP3 round trip:** PASS (bones 5.9e-8 m, markers 2.9e-7 m).
- **CP2 verdicts:** identical to a003 and c001; the same inherited disc-gap FAIL and disc-clearance UNVERIFIED. CP2 has no SC–sternum check, which is why this closure check exists.
- **Scapulothoracic contact** with the retained ribs: not evaluated (rib geometry BLOCKED).

## Evidence (`review/`, 80 JPEGs, `manifest.json` with sha256)

Every c002 image is captioned "AUDIT PROPOSAL, NOT CANONICAL – SC CLOSURE FAIL".

| Folder | Contents |
|---|---|
| `views_c002/`, `poses_c002/` | 20 views and 4 illustrative GH poses (bones only) |
| `before_after_c001_vs_c002/`, `before_after_a003_vs_c002/` | Per-view and per-pose pairs |
| `sheets/` | Contact sheets: `sheet_{c001,a003}_vs_c002_{body,shoulder_left,shoulder_right,poses}.jpg` |

Look first at `sheets/sheet_c001_vs_c002_shoulder_left.jpg` and the side views, where the SC sits below the top of the sternum.

## Reproduce

```
python3 scripts/anatomy_fit/build_shoulder_candidate_c002.py --out <new path>
python3.13 scripts/anatomy_fit/build_shoulder_candidate_blender.py --source-blend ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend --record <record> --out-blend <new path>
python3.13 scripts/anatomy_fit/cp3_rehearsal_blender.py capture --blend <blend> --out <capture>
python3 scripts/anatomy_fit/cp3_roundtrip_compare.py --record <record> --capture <capture> --out <report>
python3.13 scripts/anatomy_fit/render_shoulder_candidate_review.py views|poses --blend <blend> --record <record> --out <dir>
python3 scripts/anatomy_fit/compose_shoulder_review_c002.py --a003-views .. --c001-views .. --c002-views .. --a003-poses .. --c001-poses .. --c002-poses .. --out <dir>
python3 scripts/test_shoulder_proposal_c002.py   # 16 tests
```

| File | sha256 (first 16) |
|---|---|
| `candidate_record.json` | `aa344a6819dde763` |
| `HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c002_ansur_height.blend` | `48091eedb7bc8010` |
