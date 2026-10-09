# Annotated skeleton-only renders of c004 (real Blender 5.2.1)

Made by `scripts/anatomy_fit/render_skeleton_annotated.py` from Work's skeleton-only rehearsal blend (sha256 `9b587950…`, unchanged) and the c004 record.

**Legend:**
- **Coloured sticks:** each rig bone drawn head-to-tail (display radius only; *not* bone shape).
- **Black spheres:** joint-marker centres. Labelled ones carry their joint id.
- **White / grey dots:** bone heads / tails (regional views).
- **Axes:** red = X (character left), green = Y (posterior), blue = Z (up).
- **Black bar:** 100 mm.
- **Red sphere:** camera-check probe.

**Camera/scale verification** (`scripts/anatomy_fit/render_camera_check.py`): the probe is found as the compact red blob (shape criterion, not position) and compared with the analytic projection of its known world point.
- **Verified (20 of 22):** within 0.64–1.45 px, i.e. 0.16–0.75 mm on regional views and 1.2–1.6 mm on 2 m whole-body views.
- **Not verified (2):** `pelvis_hips_left` and `skull_neck_left`, where the midline probe is hidden behind nearer bones. They share target and scale with verified front views.

**Views:**
- whole body: front, back, left, right, ¾;
- shoulders: front, back, top;
- spine/ribcage: left, front;
- pelvis/hips: front, left;
- left hand: dorsal, radial;
- left knee: front, lateral;
- left ankle: back, lateral;
- left foot: lateral, top;
- skull/neck: left, front.

See `docs/CLAUDE_SKELETON_INDEPENDENT_VERIFICATION_20261009.md` for which visible oddities are genuine defects and which are drawing artefacts.
