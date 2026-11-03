# Shoulders, armpits and upper arms: W5 vs W11 (3 Nov 2026)

**Status:** review candidate.

- W5, the published candidate, is unchanged and still available.
- Production, `PT_MODEL_VERSION 1.0` and the approved skeleton are unchanged.
- Nothing is merged or deployed.

**What W11 changes, each judged against how a real body deforms** (`docs/REAL_BODY_DEFORMATION_REFERENCE_20261101.md`):

| Area | Real body | W11 |
|---|---|---|
| Front armpit fold, arms overhead | One rounded ridge | The two or three thin lines at each front armpit are faired into one smoother fold (W7) |
| Pecs, arms overhead | The lower mass thins and its border fades | Flatter lower pec and a softer lower border (W8f). The fine wrinkle texture of the first attempt is removed |
| Upper arms at the press lockout | Stretched skin is smooth | The 2–3 cm bands across the triceps are softer (W6d). Cause: the uneven upperarm / shoulder_cap weight handover |
| Closed fist | Folded skin meets, it does not pass through | Skin crossings at the fist 155 → 56 (W9 contact keys) |

**Cameras.** Every pair uses identical cameras. They are close-ups of the shoulders (front, side, back), fixed per
movement from the skeleton, and every frame is a real Blender render.

**Files:**

- `press_w5_vs_w11.mp4`: the shoulder press, 49 frames, out and back twice. The stills
  `STILLS_press_front.jpg`, `_side.jpg` and `_back.jpg` show neutral, rack, lockout and return.
- `pulldown_w5_vs_w11.mp4` and `overhead_extension_w5_vs_w11.mp4`: the same close-ups for the other two overhead
  movements. Their stills are `STILLS_<movement>_<view>.jpg`.
- `grip_w5_vs_w11.mp4`: closing the fist. The stills are `STILLS_grip_hands_front.jpg` and `STILLS_grip_hand_side.jpg`.
  The hand in C1 and W5 is the same, so the left column is labelled "C1 / W5".

**Metrics against W5** (17-frame harness):

- **Press:** self-intersections and folds unchanged; edges over 35° 318 → 309.
- **Overhead extension:** folds 67 → 59, self-intersections 381 → 365.
- **Grip:** self-intersections 155 → 56.
- **Other movements:** the lateral raise, curl, squat, push-up, forearm rotation, row, lunge and walk are identical.
- **Worse:** collapsed edges, about +300, in the faired armpit fold, where the skin shortens as it rounds.

The full table is in `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md`, section W11.

**Still visible:**

- the overhead extension's top: wood-grain ripples across the pecs, in W5 and W11 alike. The lockout key is on there,
  but the arms are turned;

- the mottled skin on the inner arm by the armpit;
- fine radial lines in the armpit hollow (side view);
- 56 deep skin crossings at the fist;
- the bent-over row's left posterior-shoulder fold.
