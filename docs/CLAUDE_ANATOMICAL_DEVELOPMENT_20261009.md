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
