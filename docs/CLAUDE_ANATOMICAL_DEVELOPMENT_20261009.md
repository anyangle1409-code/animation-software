# Claude anatomical development — 9 October 2026 (continuation)

- **Branch:** `claude/skeleton-anatomical-development-20261009`
- **Base:** `f83e6ab3` (my independent-verification branch, which already contains Work `42943652`)
- **Live branch heads read at start:**

| Branch | Head |
|---|---|
| `codex/whole-body-biomechanics-audit-20261007` | `2d4b352c` |
| `codex/skeleton-first-regional-verification-20261009` | `42943652` |
| `codex/anatomical-bone-surfaces-foundation-20261009` (PR #12) | `d0f6bfd3` |

All three are ancestors of this branch except PR #12, which is 9 commits ahead and only reviewed here, not merged. a003, c001–c004, P001 and every production asset are untouched. No c005 or other candidate was created.

**Network:** literature hosts (PubMed, Europe PMC, Crossref, publishers) are still unreachable from the cloud session. GitHub and PyPI are reachable. Everything below uses committed evidence, the committed ANSUR II male table, and the BodyParts3D single specimen that the project already used (grade D).

## Stage 1 — spine and vertebrae

### 1.1 Which thoracic source fits a 1.82 m man (`spine_column_length_discriminator_v1.json`)

**Method:**
- Build sagittal chains from the provisional P1 S1 endplate centre, using the committed level stack and the P1 lumbar endplate orientations.
- For the unknown per-level thoracic tilt, report an envelope over every monotone distribution that meets the committed qualitative constraints. These are: T1–T12 kyphosis 43.7°, T7 near horizontal, no uniform distribution.
- Add the C7 spinous-tip offset from the BodyParts3D specimen, in the endplate-normal frame.
- Compare with the ANSUR II cervicale height at 1.82 m: 1,575.2 mm (n = 4,082, residual SD 11.2 mm).

| Stack | C7 tip vs ANSUR (central) | Source cohort stature needed to close |
|---|---|---|
| Thoracic source A (anatomical 2011) + CT lumbar | −115.7 mm | 1.43 m |
| Thoracic source A + MRI edge lumbar | −96.9 mm | 1.49 m |
| Thoracic source B (CT 2016) + CT lumbar | −43.5 mm | 1.67 m |
| **Thoracic source B + male MRI edge lumbar** | **−24.7 mm** | **1.74 m** |
| c004 as built | −17.8 mm | n/a |

**Reading:** thoracic source A is incompatible with a 1.82 m man by a wide margin; the cohort would need to be shorter than typical adult women. Source B is compatible.
- **Endplate semantics:** the male MRI edge heights are the endplate-centre path, because the endplate concavity (Wang 2012: 1.5 + 0.7 mm) that the CT middle body height loses reappears in the central disc height.
- **Scale-free check:** the specimen's thoracic/lumbar ratio (1.85) sits between the variants, so it is reported but not decisive.
- **Effect on readiness:** this resolves the "mixed-method thoracic body/disc reconciliation" length question in favour of the B scale. It does not supply per-level wedging.

### 1.2 Bottom-up rebuild from S1 is not closable (`spine_rebuild_feasibility_p002_v1.json`)

The P002 diagnostic built the B + MRI-edge column upward from P1 S1 with three thoracic tilt templates (two envelope extremes and the specimen shape) and two cervical families (Reinhold segmental and Hasegawa near-neutral).
- **Thoracic position:** every variant puts the thoracic column 40–66 mm anterior of c004.
- **Depth behind the sternal notch:** the T2–T3 bodies end up only 40–56 mm behind the skin jugular notch, against 91 mm in c004 and roughly 90–100 mm in the specimen.
- **Conclusion:** the sagittal position of the column cannot be set from the pelvis upward with population-mean angles. It needs a closed solve against the thorax (sternum–spine depth), S1 depth and SVA, and those sources are not committed.

### 1.3 Curve-preserving disc re-partition P003: rejected

`audit/proposals/p003_spine_disc_repartition_rejected/` keeps c004's curve and both ends and lays sourced bodies and discs along it (scale 1.009). All disc gaps become positive.
- **Why rejected:** ribs 10–12 end up 30–40 mm above the vertebrae they articulate with (c004: at most 8.3 mm). That breaks the acceptance rule "thoracic rib attachments remain level-correct".
- **Movement:** no Blender movement run was made for a rejected proposal.

### 1.4 Trunk vertical closure (`trunk_vertical_closure_c004_v1.json`)

| Check (c004) | Residual | Evidence |
|---|---|---|
| Lumbar L5–L1 arc vs male bodies + discs | **+43.2 mm** (+61.0 vs CT) | Hegazy 2014 MRI; LUMBAR_CT/DISC |
| T12/L1 height vs P1 S1 + sourced lumbar rise | **+38.5 mm** | Hasegawa PTh/PT/SS, P1 orientations |
| Rib 10 anterior end vs ANSUR tenth-rib height | **+28.0 mm** (z +1.38; landmark definitions differ, directional only) | ANSUR II |
| IJ (skin) vs ANSUR suprasternale | **+24.7 mm** (z +2.11) | ANSUR II |
| Thoracic T12–T1 arc vs source B + discs | −5.6 mm | THORACIC_CT_2016 + 2011 discs |
| Cervical C7–C3 arc vs Yukawa | −15.5 mm | Yukawa 2012 male |
| C7 spinous tip vs ANSUR cervicale | −17.8 mm (lean ±10°: −26.9 to −7.9) | grade-D tip offset |

**Finding:** three independent checks say the lower and middle trunk sit 25–39 mm too high. These are the pelvis-anchored T12/L1, the ANSUR tenth rib and the ANSUR suprasternale. The c004 lumbar spine is correspondingly 43–61 mm too long, while the thoracic arc fits source B.
- **Disc defect is coupled:** the zero-disc defect (U5) cannot be fixed locally. The disc rebuild has to lower the thoracic cage (vertebrae, ribs, sternum) together with the spine. It also bears on the open shoulder-height closure, because the SC joints hang from the IJ.
- **Classification:** recorded as **GEOMETRY_DEFECT (lumbar length / trunk height), coupled, BLOCKED**. It awaits a coupled trunk candidate and the owner's go-ahead. Nothing was moved.

Diagram (coordinates, not a render): `ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/spine_sagittal_diagnostic.jpg`.

**Still needed** (literature, unreachable from this session):
- per-level thoracic wedge/tilt tables (PMC3171774, PMID 41047402 Table 6, Bernhardt & Bridwell 1989);
- a sternum-to-vertebral-body depth source for men;
- S1 endplate AP depth (for SVA).

**Tests:** `scripts/test_spine_trunk_audits.py`, 9 tests, all pass.

## Stage 2 — hands and wrists

**P001 stays experimental.**
- **Why it's kept:** its metacarpal evidence (Aydinlioglu 1998 plus the 2025 CT series, agreeing within 2.1 mm) is unchanged.
- **Why it isn't promoted:** the carpal centroid layout is still BLOCKED. That blocker needs the eight carpal centroids in one wrist frame, and no committed or reachable source supplies them. Only the grade-D BodyParts3D specimen does, and it may not set a target.
- **Fingertip endpoints (H2):** the ten fingertip endpoints remain an evidence gap. Work's tip-context replay (`audit/work_hand_tip_context_20261009/`) was reviewed and not repeated.

**Grip mechanics (`grip_capacity_c004_v1.json`, `grip_capacity_p001_v1.json`).** For digits 2–5, I computed the smallest cylinder around which the bony phalanx chain can close without any joint exceeding its committed active-flexion mean (FINGER_ACTIVE, 390 hands).

| Digit (left) | P1 / P2 / P3 mm (P3 tip unsourced, H2) | Minimum axis radius mm | Binding joint | Wrap ° | Handle Ø at t = 10 mm | Tip to metacarpal axis at full flexion mm |
|---|---|---|---|---|---|---|
| D2 | 45.0 / 27.0 / 18.9 | 24.94 | PIP | 238.9 | 29.9 | 24.56 |
| D3 | 49.0 / 30.0 / 21.0 | 27.47 | PIP | 237.3 | 34.9 | 26.47 |
| D4 | 46.0 / 28.0 / 20.16 | 25.79 | PIP | 238.0 | 31.6 | 25.69 |
| D5 | 36.0 / 22.0 / 16.72 | 20.81 | PIP | 231.0 | 21.6 | 20.56 |

**Reading:** the fingers can close around handles of roughly 30–35 mm (barbell and dumbbell grips) within active-mean ranges, with the PIP joint the binding constraint. No defect was found.
- **Soft-tissue offset:** t is not sourced, so the table shows it as a parameter.
- **Effect of P001:** none on finger wrap, since its phalanges are unchanged.
- **Thumb:** opposition and cupping are not modelled, so grip *closure* with the thumb remains the open item H9.

## Stage 4 — knee, hip and foot

**Patellar tracking (L3, `patellar_tracking_c004_v1.json`).** The follower template is the published Rajagopal 2016 patellofemoral path (opensim-models `d9b05d47`), scaled by femur length (×1.012).

| | Patellar-ligament length change, 0–120° |
|---|---|
| c004 now (patella static on the femur) | **+62.15 mm (113.7 %)** |
| c004 with the Rajagopal follower | 5.11 mm (9.4 %) |
| Rajagopal model itself | 8.2 % |

**Reading:** a static patella more than doubles the length of a nearly inextensible ligament, so L3 is a real movement-model defect. The sourced follower brings the error down to the model's own level.
- **Not installed:** that would change the shared movement machinery owned by GPT/Work. It is recorded as the recommended next movement change.
- **Rest position:** Rajagopal's patella point sits 58 mm anterior and 8 mm inferior of its knee origin. c004's inferior pole sits 42 mm anterior and 16 mm inferior. The knee-origin definitions differ, so this is context only.

**Hip adduction test design (L4, `hip_adduction_start_posture_c004_v1.json`).**
- **The problem:** at 20° adduction from neutral standing, the two tibial axes come within 0.85 mm; they effectively cross.
- **The fix:** with the contralateral hip abducted, the closest axis distance becomes 23.15 mm at 10°, 68.05 mm at 15° and 135.95 mm at 20°.
- **Recommendation:** start the adduction sweep with the opposite hip abducted by at least 10–14°, plus an envelope margin. Amplitudes are unchanged. This is a test-design fix, not a bone defect.

**Tarsals (L5)** remain BLOCKED: there is no committed or reachable tarsal contact geometry.

**Register update:** `defect_register_update_v1.json` adds three entries, U10, U11 and H10, and updates U5, L3 and L4. U10 is new and the most important: the lumbar spine is too long and the trunk sits too high.

**Tests:** `scripts/test_spine_trunk_audits.py` now has 13 tests, all passing.
