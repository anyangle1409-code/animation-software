# Coupled trunk rebuild — independent mechanical preflight (2026-10-09)

**STATUS: AUDIT-ONLY / NOT A CANDIDATE.** No bones, coordinate targets, animations, muscle layers, meshes, c004, P001 or existing rejected P003 were changed.

### Why this exists

Claude's independent investigation found c004's lumbar segment has a +43.2 mm excess versus male MRI body-edge/disc evidence, and three closure checks locate the lower/mid trunk high: T12/L1 +38.5 mm, rib 10 +28.0 mm (directional landmark), sternum skin IJ +24.7 mm. The thoracic segment length is approximately source-compatible (−5.6 mm). A spine-only disc repartition (P003) fixed some gaps but left ribs 10–12 30–40 mm off their articulation heights and was rejected.

The owner approved **only an isolated, reversible, experimental coupled trunk rebuild**, not canonical promotion. Claude reached its usage limit, so this branch prepares the regression checks for the next candidate without guessing a new anatomy.

### Delivered

`scripts/anatomy_fit/coupled_trunk_preflight.py` compares two JSON skeletal records (the unchanged c004 baseline and a proposed *separate* record):

- exactly matching bone inventories, finite control-bone coordinates;
- candidate spine movement and intervertebral gap projection along the lower bone control axis (diagnostic 1–20 mm corridor, **not a sourced per-level disc target**);
- rib-head Z-height deviation from designated spinal articular levels for all **24 ribs**, using the same historical level convention as P003 (rib 1→T1 centre; ribs 2–9→appropriate disc midpoint; ribs 10–12→own thoracic level);
- preservation of the existing P003 regression limit: worst rib-head height misalignment may not exceed 2× the c004 baseline maximum (~16.5 mm; **not an anatomical contact tolerance**);
- independently flags a proposal that moves the lower thorax without corresponding rib displacement or the upper thorax without a sternal displacement;
- explicitly flags shoulder/SC/AC/GH height reassessment if the upper thorax moves;
- diagnostic output **always** includes `safe_for_canonical_promotion: false` and a list of unresolved anatomy/pose/evidence requirements.

The tests do not prescribe a trunk shape or compute a valid lumbar disc stack. A physically incorrect synthetic rigid translation can pass this mechanical preflight by design: anatomical source checks are separate and mandatory. In particular, a Z-aligned rib head can still have an invalid 3D costovertebral contact and a properly displaced sternum can still have incorrect AP depth or shape. A joint-gap projection does not model intervertebral cartilage or facet joint contact.

`scripts/test_coupled_trunk_preflight.py`: 13 focused mutation/regression tests, including **actual committed c004 and rejected P003**. It verifies:
- c004 unmodified/no positive disc gaps is **not** an accepted rebuild;
- P003 remains rejected for missed rib coupling;
- a controlled coupled synthetic transform clears only the **mechanical** preflight, never anatomical acceptance;
- moving the spine without the ribs/sternum fails;
- missing ribs, invalid coordinates, excessive/insufficient gaps fail;
- immutable input semantics.

### Reproduce

```bash
python3 -m unittest discover -s scripts -p 'test_coupled_trunk_preflight.py' -v

python3 scripts/anatomy_fit/coupled_trunk_preflight.py \
  --baseline ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json \
  --proposal ORIGINAL_V1_WORK/anatomy/audit/proposals/p003_spine_disc_repartition_rejected/proposal_record.json
```

### Next tasks when compute agent resumes

1. Resolve evidence for sagittal S1/SC depth, sternum-to-spine dimensions, and per-level thoracic wedge inclinations. **Do not invent these.**
2. Create a separate candidate with independently justified lumbar body/disc geometry and proper thorax/vertebra/rib/sternum coupling, not merely a global vertical translation.
3. Run this preflight, followed by joint frames, rib-head/costal-tubercle 3D contact, shoulder closure, height residuals, Blender comparison renders, isolated/whole-body movements, and full regression suite.
4. Keep the candidate experimental and update canonical readiness only if independently evidenced gates actually close.

**No change in canonical readiness from this branch: 0 READY / 9 PARTIAL / 3 BLOCKED.**
