# Next action after V8 knee acceptance

The user accepted V8 as the knee geometry baseline. V8 retains V7's connected topology. Read `WORK_MASTER_HANDOFF.md`, `REVIEW_V8_KNEE_ANATOMY.md`, and the baseline manifest. Start Phase B from V8, in a separate hand-anatomy candidate.

Improve finger, thumb web/base, palm and wrist surface shape while keeping original hand contact vertices, the frozen rig, corrected hand frame, exercise mechanics, and all non-hand geometry unchanged. Validate the hand candidate against runtime `614033b` and the protected floor-contact guard. Generate close-up curl, push-up and pull-up hand images. Stop for visual review before grip refit. Preserve V6, V7 and V8; do not promote production.

The canonical hierarchy is frozen at 63 bones, commit `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`; candidate runtime validation uses `614033b256d869230ea273522620467401b0bc71`. Do not change production assets, accepted exercise mechanics, grip/contact guards, `bundled.ts`, or the frozen rig. Do not promote automatically.
