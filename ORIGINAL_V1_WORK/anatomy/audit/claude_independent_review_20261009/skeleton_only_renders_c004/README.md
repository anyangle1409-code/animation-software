# Skeleton-only Blender renders of c004 (first pass, 9 October 2026)

These are real Blender 5.2.1 Workbench renders made by `scripts/anatomy_fit/render_skeleton_only_review.py`. Inputs:
- Work's skeleton-only rehearsal blend (`audit/runs/work_fresh_c004_rehearsal_20261009/rehearsal.blend.gz`, raw sha256 `9b587950…`, unchanged after rendering);
- the c004 record;
- for poses, Work's animated movement blend and its samples.

**What you are looking at:** each bone is a **straight stick from its rig head to its rig tail** (display radius only), and black dots are joint-marker centres. Sticks are *not* bone geometry: ribs appear as straight chords, the os coxae as one SI-to-pubis stick, and skull bones as short segments. Bone shapes are not represented at all.

Views: whole body (front, back, left, right, two three-quarter views); shoulders (front, top); spine (left, back); pelvis (front, top); left hand (palmar, dorsal, radial); right hand (palmar); left foot (medial, top, plantar); head/neck (left); 8 movement extremes (`pose_*`).

Superseded by the annotated second pass where one exists (see the audit report).
