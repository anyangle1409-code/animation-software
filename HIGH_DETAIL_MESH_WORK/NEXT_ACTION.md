# Next action after V8 knee anatomy review candidate

The user accepted V7 as the knee topology solution and requested one local anatomy refinement before the hand phase. V8 is a separate, validated knee anatomy review candidate. Read `WORK_MASTER_HANDOFF.md` and `REVIEW_V8_KNEE_ANATOMY.md`, then inspect `renders_v8_knee_anatomy/V8_V7_DEEPEST_SQUAT_KNEE_COMPARISON.jpg`.

Stop for the user's V8 visual review before beginning Phase B hand anatomy. V8 is subtly cleaner but a small medial notch remains. If the user accepts the anatomy, use V8 as the mesh geometry source for Phase B; otherwise make another separate knee candidate. Preserve V6, V7, and V8.

The canonical hierarchy is frozen at 63 bones, commit `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`; candidate runtime validation uses `614033b256d869230ea273522620467401b0bc71`. Do not change production assets, accepted exercise mechanics, grip/contact guards, `bundled.ts`, or the frozen rig. Do not promote automatically.
