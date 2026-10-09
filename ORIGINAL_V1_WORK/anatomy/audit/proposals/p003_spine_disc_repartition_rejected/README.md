# P003 — disc spaces by re-partitioning c004's spinal curve: REJECTED (diagnostic only)

**Status:** this is not a candidate and not c005. It was rejected by the project's own acceptance rule before any Blender movement run.

**What it tried.** It kept c004's L5–C2 curve and both of its ends, then laid out sourced vertebral bodies and explicit discs along that curve.
- **Heights used:** male MRI edge heights for the lumbar spine, CT source B for the thoracic bodies, and Yukawa for the cervical spine.
- **Scale:** one uniform factor, 1.009, which is the ratio of c004's arc to the sourced sum. Every disc gap becomes positive.
- **Unchanged:** every non-spine bone is byte-identical to c004 (test-enforced).

**Why it was rejected.** The rule (`canonical_spine_geometry_audit_v1.json`) is: *"Thoracic rib attachments remain level-correct after vertebral retargeting."*
- c004's lumbar curve is 43 mm longer than the sourced lumbar bodies plus discs.
- Re-partitioning therefore slides T10–T12 down the curve by 26–38 mm.
- The rib heads stay where they are, so ribs 10–12 end up 30–40 mm above the vertebrae they articulate with (c004: at most 8.3 mm).

**What it shows.** The zero-disc defect (U5) is coupled to the height of the ribcage and sternum. The trunk closure audit (`../../claude_anatomical_development_20261009/trunk_vertical_closure_c004_v1.json`) finds the lower trunk too high on three independent checks: T12/L1 by +38.5 mm, the jugular notch by +24.7 mm and rib 10 by +28.0 mm. The disc rebuild therefore has to move the thoracic cage with the spine, which is a coupled trunk candidate and not a local fix.

Rebuild: `python3 scripts/anatomy_fit/build_proposal_p003_spine_discs.py --out-dir <new dir>` (deterministic; `scripts/test_spine_trunk_audits.py`).
