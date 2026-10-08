# Shoulder proposal c001 (audit candidate, not canonical)

**Identity:** `r95_a003_shoulder_proposal_c001`
**Status:** `AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED`. `freeze_ready=false`, `character_accepted=false`.

This candidate is the a003 audit record with only the shoulder girdle replaced by the reconciled CP1a solution. It exists for review. It is not a production asset, not a frozen target and not an accepted skeleton. a003 and every production asset are unchanged.

## Inputs (sha256, first 16 hex characters)

| Input | Path | sha256 |
|---|---|---|
| Base record | `ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json` | `11712ba3e105aa88` |
| Base blend (read, never saved) | `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend` | `670a37bfd206d702` |
| Shoulder solution | `ORIGINAL_V1_WORK/anatomy/canonical_shoulder_girdle_solution_182_v1.json` | `52a7e6d1308e6cde` |

Solution choices:
- variant `source_scale` (reconciled);
- world `bony_specimen_deg__IJ_at_a003` (thorax pitch 7.04°, IJ at the a003 bony IJ);
- GH head radius 24.0 mm.

## Outputs

| File | What it is |
|---|---|
| `candidate_record.json` (`08e9f2e1187dbeda`) | Fit-record schema with a `candidate` block: moved lists, the 29 scapula landmarks per side, open questions and limitations |
| `HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_proposal_c001.blend` (`63ef703ef3a3b160`) | Rebuilt anatomical master plus 58 `SCAPLM_*` landmark empties |
| `build_stdout.json` | Build log, including the a003 hash before and after the build |
| `roundtrip_report.json` | CP3 round trip: PASS (bones 5.9e-8 m, markers 1.9e-7 m) |
| `review/` | 80 captioned JPEGs with `manifest.json` (sha256 of every image and source) |

## What changed: a003 → c001 (left side; the right is an exact mirror)

| Measure | a003 | c001 | Source / reference |
|---|---|---|---|
| Clavicle SC–AC joint-centre chord | 222.9 mm | 151.3 mm | Qiu 152.9 ± 9.3 mm |
| Clavicle elevation / retraction (thorax frame) | — | 9.8° / 18.4° | Matsumura male standing 8 ± 4° / 23 ± 6° |
| Bilateral AC distance | 481.4 mm | 333.9 mm | Maximum acromion breadth 418.4 mm vs ANSUR biacromial (skin) 425.2 ± 16.2 mm |
| Bilateral SC distance | 50.0 mm | 50.9 mm | Seth |
| AC–GH | 41.8 mm | 41.3 mm | Seth 42.0 mm |
| Bilateral GH distance | 437.8 mm | 386.4 mm | — |
| Scapula reference stick (glenoid → inferior angle) | 211.7 mm | 152.4 mm | Lee 2024 landmarks at 182 cm |
| GH translation | — | medial 25.7, anterior 38.9, up 57.7 mm | — |

The change touches 64 bones: both clavicles and scapulae, plus each humerus subtree translated rigidly. It also touches 88 markers. CP2 verdicts are identical to a003's (test-enforced).

## Known defects (recorded, not passed)

1. **Shoulder too high relative to standing anthropometry.**
   - The lateral acromion (LM27) sits at 1560.7 mm, which is 63.0 mm above the ANSUR acromial height at 1.82 m (1497.7 ± 16.2 mm; z 3.89).
   - Placing the IJ at the ANSUR suprasternale still leaves +38.3 mm.
   - This is inherited from the OPEN vertical relation. See `../../shoulder_vertical_relation_audit_v1.json`.
2. **Mesh not refitted.** By design (skeleton-first policy), GH and AC sit at or above the a003 skin of the shoulder top in the close-ups.
3. **Arm lengths are a003's.** The short forearm (owner policy) is not applied at this stage.
4. **Marker frames.** SC/AC/GH marker frames keep the a003 orientations; only their centres changed.
5. **Poses are illustrative only.** They are a rigid humerus rotation about GH; scapula and clavicle are static, with no scapulohumeral rhythm. They are not movement tests.

## Open questions

- **Absolute shoulder height relative to the trunk.** The C7 and acromion living-vs-bony relations need opposite suprasternale offsets. Even with the IJ eliminated, the solved AC is at least 35.7 mm higher relative to C7 than ANSUR. The v1 single-offset hypothesis is withdrawn.
- **Standing chest/thorax pitch** (bony 7.04° vs living-implied −11.3°): unchanged and unresolved.
- **Skin-to-bone offsets** for acromiale and cervicale need a source that pairs the skin landmarks with bone.

## Reproduce

```
python3 scripts/anatomy_fit/build_shoulder_candidate_record.py --out <new path>
python3.13 scripts/anatomy_fit/build_shoulder_candidate_blender.py --source-blend ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend --record <record> --out-blend <new path>
python3.13 scripts/anatomy_fit/render_shoulder_candidate_review.py views|poses --blend <blend> --record <record> --out <new dir>
python3 scripts/anatomy_fit/compose_shoulder_review.py --a003-views .. --c001-views .. --a003-poses .. --c001-poses .. --out <new dir>
python3 scripts/anatomy_fit/shoulder_vertical_relation_audit.py --out <json>
python3 scripts/test_shoulder_proposal_c001.py   # 15 tests
```

`python3.13` is Blender 5.2.1 run as the bpy module. Rendering is Workbench; it needs Mesa EGL (`libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri`).

## Where to look first

- `review/sheets/sheet_before_after_shoulder_left.jpg` and `review/sheets/sheet_before_after_shoulder_right.jpg`
- `review/sheets/sheet_full_body_c001.jpg`
- `review/sheets/sheet_before_after_poses.jpg`
- per-view pairs in `review/before_after/`
