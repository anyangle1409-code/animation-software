# Next action after V7 knee review candidate

V6 remains the latest **reviewed** geometry baseline. V7 is a separate knee candidate awaiting review on the `codex-high-detail-candidate-v7-knee-review-20260923` branch. Read `WORK_MASTER_HANDOFF.md` and `REVIEW_V7_KNEE_RETOPOLOGY.md`, then inspect `renders_v7_knee_retopology/V7_KNEE_V6_COMPARISON.jpg`.

The V7 squat knee is visibly cleaner, but a small medial notch and simplified patellar dome remain. Do not accept this as production ready without reviewing those views and deformation. If V7 is accepted as the next geometry baseline, continue to Phase B hand anatomy. If the knee contour needs another pass, make a new candidate based on V7, improve that local region, and rerun the supplied guards. Preserve V6 and V7.

The canonical hierarchy is frozen at 63 bones, commit `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`; candidate runtime validation uses `614033b256d869230ea273522620467401b0bc71`. Do not change production assets, accepted exercise mechanics, grip/contact guards, `bundled.ts`, or the frozen rig. Do not promote automatically.
