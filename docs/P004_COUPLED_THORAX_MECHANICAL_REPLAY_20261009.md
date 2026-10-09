# P004 — coupled thorax mechanical replay, 9 October 2026

**Status: DIAGNOSTIC ONLY / NOT A NEW CANONICAL CANDIDATE.**
Owner permitted a reversible isolated investigation of the combined lumbar, thoracic, rib and sternal problem. This branch does not implement or approve a new anatomical profile and does not alter existing candidate or production files.

## Provenance

- Saved Claude checkpoint: `claude/skeleton-anatomical-development-20261009` @ `f3f725f46c33ab1d4d480070f56ddc6b350f3d87`.
- Frozen comparison: `ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json`.
- Explicitly **rejected** source: `ORIGINAL_V1_WORK/anatomy/audit/proposals/p003_spine_disc_repartition_rejected/proposal_record.json`.
- Analysis reason: c004 spine has +43.2 mm lumbar arc excess compared with committed male MRI-edge data, and the T12/L1 height is +38.5 mm; P003 introduces nonzero disc spaces but fails rib level closure by up to 39.95 mm.
- These source comparisons still do not settle sagittal depth, vertebral wedging, SC height or source-compatible 3D contact.

## What new script P004 actually does

`scripts/anatomy_fit/replay_p004_coupled_thorax.py` is an intentionally simple, reproducible *kinematic replay*, designed to answer **whether the ribs can be carried with the changed vertebrae without losing their previous relative rib-head-to-articular-level positions**.

1. Read c004 and P003 without mutating either.
2. Keep P003's already-source-attributed spine segments, disc markers and vertebral coordinates exactly as they are, including its existing sagittal curve and ~1.009 scale-to-arc factor.
3. For each of the 24 ribs, map its attachment level as in the existing P003 audit (rib 1→T1 centre, ribs 2–9→their thoracic intervertebral level, ribs 10–12→own vertebral centre). Translate the rib rigidly by the 3D displacement of *that* level from c004 to P003.
4. Translate markers carried by the rib by the identical delta. Lengths, orientations and pre-existing relative joint-contact offsets remain unchanged.
5. Translate the sternum and sternum-carried markers by the componentwise **median of rib 1–7 level displacements**. This is an **UNSOURCED COMPUTATIONAL PLACEHOLDER**, not an actual sternum placement target or validated cartilage biomechanics.
6. Keep clavicles, scapulae, arms, neck, sacrum, all non-trunk bones and legacy `skeleton_input` unchanged; flag all associated closure evidence as unresolved.

The script makes a new JSON only when the caller specifies a fresh `--out` path. It uses exclusive-create mode and refuses to overwrite an existing record.

### Run

```bash
python3 -m unittest discover -s scripts -p 'test_coupled_trunk_preflight.py' -v
python3 -m unittest discover -s scripts -p 'test_replay_p004_coupled_thorax.py' -v

python3 scripts/anatomy_fit/replay_p004_coupled_thorax.py --out /tmp/hgpt_p004_audit_record.json

python3 scripts/anatomy_fit/coupled_trunk_preflight.py \
  --baseline ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json \
  --proposal /tmp/hgpt_p004_audit_record.json
```

## What to check

- P003 moved the thoracic vertebrae but had left ribs unmoved, producing 30–40 mm vertical errors at lower rib attachments. This script **by construction** restores c004's head-to-vertebral-level offsets in all three coordinates. A preserved original relative offset does NOT establish correct costovertebral surface contact.
- **No skeletal acceptance:** c004 contact offset may itself be anatomically uncertain; sternum shift is heuristic; costal cartilage is unmodelled; rib shapes are two-point chords; the sternal notch/SC/AC/GH sources conflict; the same point on the model can represent different endpoints in different studies; forearm/hand and foot blockers remain.
- The generator records endpoint-to-sternocostal-marker distances as an engineering proxy. These are **not** clinical cartilage lengths.
- Remaining requirements include per-level thoracic wedge tables, adult male sternum-spine sagittal dimensions, S1 depth, independent AC/SC target mapping, and all 3D contact/joint frame checks.

## Why P004 remains unaccepted even if tests pass

A synthetic spine-rib reconstruction can satisfy topological and Z-attachment equations but still have an anatomically implausible whole-body profile. In particular, it can leave clavicles disconnected from the relocated sternum or bring ribs too close to the abdominal cavity. There is **no** canonical c005 and no approval for new muscles/skin from this branch.

## Resume instructions

When Claude resumes, compare this replay's results with anatomical reference data, reject unsupported sternum/SC depths, and replace the kinematic placeholders only with sourced joint-centre and surface definitions. Preserve everything now recorded, rather than repeating the P003 rib-level failure. Use orthographic Blender renders and whole-body motion only after enough source anchors can be defined.

**Readiness remains 0 READY / 9 PARTIAL / 3 BLOCKED.**
