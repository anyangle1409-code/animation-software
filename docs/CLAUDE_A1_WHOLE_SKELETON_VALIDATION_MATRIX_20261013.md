# A1: whole-skeleton validation matrix for ORIGINAL_v1 (Claude, 13 Oct 2026)

- **Branch:** `claude/master-execution-20261013`.
- **Matrix:** `ORIGINAL_V1_WORK/anatomy/audit/claude_a1/whole_skeleton_validation_matrix_v1.json`, built by `scripts/anatomy_fit/build_whole_skeleton_validation_matrix.py`. Pure test: `scripts/test_whole_skeleton_validation_matrix.py`, which includes a check that the committed matrix is current.
- **New measurement:** `scripts/audit_original_skeleton_containment_blender.py`, with report `claude_a1/skeleton_containment_report.json`, phone sheet `claude_a1/skeleton_containment_phone_sheet.jpg`, and 5 native tests in `scripts/blender_tests/test_original_skeleton_containment.py`.
- **CI:** `.github/workflows/original-skeleton-containment.yml` runs the native tests, re-runs the audit, diffs its summary against the committed report, and runs the pure matrix test.
- **Source:** the unchanged a003 audit blend (`670a37bf…cbbe56`), at rest, with legacy shape keys at 0.

**Scope:** consolidation plus one geometric measurement. Region readiness is **copied** from `canonical_freeze_readiness_v1.json` and never upgraded here: overall `NOT_READY_FOR_NEW_CANONICAL_BLENDER_REVISION` — 0 READY, 9 PARTIAL, 3 BLOCKED. Nothing is edited and nothing is approved.

## Skeleton-in-skin containment (rule 2: the mesh conforms to the skeleton)

**Method:**
- Signed depth below the skin is measured at 5 points along each of the 206 bone axes, at the 427 joint centres and at the 51 landmarks.
- Inside/outside is decided by ray parity on the closed, manifold body, voting over three axes. 2 votes were not unanimous (points lying on the skin).
- The depth magnitude is the nearest-surface distance.

| Measure | Result |
|---|---|
| Bones whose axis leaves the skin | **2 / 206**: fibula L/R |
| Bones with an axis point < 3 mm deep | 2: first metacarpal L/R |
| Joint centres outside the skin | 0 / 427 |
| Bony landmarks outside the skin | 0 / 24 |
| Skin landmarks, largest offset from the skin | 0.0 mm (they were placed on it) |
| Bilateral mirror error (bone heads) | max 0.29 mm over 86 pairs |
| Body height / skeleton z-span | 1.82 m / 1.7966 m |

**Findings (measurements, not judgements):**

1. **Fibula, both sides:**
   - The axis leaves the lateral distal shank skin by up to 1.9 mm, between z = 0.19 and 0.11 m (about 70–90% down the bone). Elsewhere it is 9–20 mm deep.
   - The fibula is a `proportional`, low-confidence placement, 35–43 mm lateral of the tibia axis.
   - Either the distal lateral calf skin is too thin (mesh conforms to skeleton → mesh fix) or the fibula sits too far lateral (skeleton evidence → skeleton review). The repo has no sourced fibula-to-skin cover or distal tibiofibular offset to decide between them, so nothing is changed.
2. **First metacarpal, both sides:** the axis passes 0.06 mm under the thumb-web skin at mid-shaft. It is a `surface_station`, low-confidence placement, tied to the open hand blockers (H1–H3/c005).
3. **Thin cover is not measured:** a bone axis is not its surface. Without sourced bone radii, "inside" does not mean "covered", so this audit cannot show that a bone's surface stays inside the skin. Distal phalanges at 3.0–3.4 mm and the frontal bone at 3.2 mm are the next-shallowest. This is consistent with the thin lesser-toe and finger girth found in F4.

## Matrix (one row per freeze-readiness region)

Session packages (13 Oct) per region, with their status at the time of writing (the live status is in the task ledger); M1, M2 and E1 cover all regions and are omitted from the column. Min axis depth uses the audit's 5 samples per bone (a finer profile gives 0.06 mm for the first metacarpal and −1.9 mm for the fibula). Anchors / blockers are counts from the readiness file.

| Region | Readiness | Anchors / blockers | 9 Oct blocker items | Session packages | Bones | Min axis depth (mm) | Containment |
|---|---|---|---|---|---|---|---|
| shoulder_girdle | **PARTIAL** | 6 / 10 | U9, G3, U3 | W1 TESTED, W2 TESTED, W3 BLOCKED, W4 COMPLETE | 4 | 11.02 | all inside |
| spine | **PARTIAL** | 13 / 8 | G3, U5/U10 | — | 26 | 46.18 | all inside |
| ribs | **BLOCKED** | 6 / 5 | U9, G3, Rib slope | W1 TESTED | 25 | 10.2 | all inside |
| forearm | **PARTIAL** | 3 / 4 | G3, U7/U8 | — | 4 | 5.06 | all inside |
| carpus | **BLOCKED** | 5 / 3 | H8, G3, H1-H3/c005 | — | 16 | 10.6 | all inside |
| hand | **PARTIAL** | 2 / 3 | G3, H6/L4/L7, H1-H3/c005 | — | 38 | 0.29 | shallow: metacarpal_1_left, metacarpal_1_right |
| pelvis | **PARTIAL** | 4 / 4 | G3 | — | 2 | 7.35 | all inside |
| lower_limb_long_bones | **PARTIAL** | 2 / 3 | G3, L3, H6/L4/L7 | — | 8 | -1.51 | outside: fibula_left, fibula_right |
| tarsus | **BLOCKED** | 3 / 3 | G3, L5 | F1 COMPLETE, F3 BLOCKED, F6 TESTED | 14 | 7.57 | all inside |
| forefoot_toes | **PARTIAL** | 3 / 3 | G3 | F1 COMPLETE, F2 TESTED, F3 BLOCKED, F4 TESTED, F5 BLOCKED, F6 TESTED | 38 | 3.74 | all inside |
| head_neck_fixed | **PARTIAL** | 4 / 3 | G3 | — | 29 | 3.14 | all inside |
| humerus | **PARTIAL** | 3 / 5 | G3, U7/U8 | — | 2 | 38.7 | all inside |

## What this changes

- **Nothing in readiness.** It is still 0 READY, because every region's blockers need primary sources, surfaces, a contact model or an owner decision (9 Oct blocker matrix). This session's work did not add primary anatomical evidence.
- **Two new geometric defects are registered:** fibula containment (lower limb) and first-metacarpal cover (hand). Both are measured, reproducible in CI, and attached to existing low-confidence placements.
- **Owner decisions still pending:** C3 foot skeleton (F3) and the shoulder runtime contract (W3).

## Next

- A sourced soft-tissue cover target for the distal lateral leg (or a tibiofibular offset) would decide the fibula finding; a mesh-only lateral shank candidate can then be built and measured in the same audit.
- Bone-radius-aware containment, once bone radii or surfaces are available.
