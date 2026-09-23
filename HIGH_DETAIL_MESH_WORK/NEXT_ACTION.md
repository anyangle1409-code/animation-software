# Next action after V9 hand geometry review

V8 remains the accepted knee geometry baseline. V9 is a separate, unaccepted
hand-only review candidate. Do not promote either to production.

Inspect the matched V8/V9 closeups in renders_v9_hand_geometry_review for
curl, push-up and pull-up. The V9 sculpt passes the frozen rig and exercise
guards, including unchanged push-up floor contact and equipment matrices.
Visible improvement is modest, and the inherited polygonal finger tips,
thumb/web and wrist bands remain. See REVIEW_V9_HAND_GEOMETRY_REVIEW.md.

Phase B hand anatomy is not yet accepted. If V9 is insufficient, the next
candidate-side task is hand topology and sculpting in Blender using V8/V9
as references, while preserving the protected floor vertices, frozen
hgpt_canonical_v3 hierarchy, corrected hand frame from 614033b, UV/weight
compatibility, exercise mechanics and all non-hand geometry. Do not start
Phase C curl-grip refit until hand geometry passes visual review.

Preserve V6, V7 and V8. Do not change production assets, bundled.ts, asset
references, accepted mechanics, grip/contact logic or the frozen rig.
