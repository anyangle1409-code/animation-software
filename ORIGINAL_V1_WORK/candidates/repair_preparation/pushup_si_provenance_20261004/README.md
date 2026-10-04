# Push-up self-intersections 158 (P3B1) vs 164 (r45, r48 and every later candidate): provenance

Measured with scripts/diagnose_original_v1_self_intersections_blender.py on pushup_bottom (`pu_si_<rN>.json`). Candidate history from the evidence folders: r20-r24 156, r25/r26 142, r27-r38 144-154, r41 158, **r42 158 (P3B1)**, **r45 164**, **r47 158**, **r48 164**, r55-r90 164.

Breakdown by region pair (identical in r42/r47 versus r45/r48/r90 except one entry): hand|thumb 12, arm 98, hand 16, arm|hand **32 -> 38**. The six extra pairs (three per side) are cross-region arm|hand pairs at the forearm-hand junction on the floor (posed bounding box x +-0.35..0.42 m, y -1.37..-1.24 m, z 0.03..0.29 m: the planted hand), dominant bones forearm_tw0/forearm_tw1/hand. They are not shoulder pairs; no shoulder-owned vertex appears among the changed top vertices.

Introduced with the wrist-band weights (o26) that arrived at r45 and are part of every later lineage: the project record says they cleared the push-up hand minimum, which was one of P3B1's 14 development failures. r47 (no wrist band) has 158 and r48 (wrist band) 164, so the +6 is the price of that 3D fix. The shoulder corrective keys (abduction, flexion) are inactive in the push-up (theta 35.5 deg, flexion key 0) and r83/r87/r90 give exactly the r48 value.

Conclusion: the item is a Phase 3D wrist-band side effect, unrelated to Phase 3A. No baseline, tolerance or weight was changed. Options are an owner decision or a declared local wrist-weight experiment (3D), not part of the shoulder work.
