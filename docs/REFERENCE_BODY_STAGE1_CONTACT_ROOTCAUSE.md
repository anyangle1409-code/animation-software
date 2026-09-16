# Stage 1 — curl Bottom/Return contact: root cause

Diagnostic only, per `docs/REFERENCE_BODY_STAGE1_CONTACT_DIAGNOSTIC.md`. **No
asset, pose, rule or source file changed. Stage 1 is not frozen and Stage 2 has
not started.** Candidate remains
`HomeGymPT_Male_STAGE1_CANDIDATE.glb` (`c0d4b690…1eefb`).

## The measurement

Curl Bottom, both sides, real dumbbell geometry, across the abduction sweep.
Positions in millimetres, world space.

| pose | side | shoulder x/z | elbow x/z | grip x/z | inboard plate x/z | region | closest body pt x/y/z | grip→body | clearance | Δx sh/el/grip/plate | axis Δ° |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3° | l | 190/15 | 180/12 | 174/90 | 103/67 | upper thigh | 111/729/56 | 31.0 | **−13.59** | —/—/—/— | — |
| 3° | r | −190/15 | −180/12 | −174/90 | −103/67 | upper thigh | −110/729/56 | 30.3 | **−13.73** | —/—/—/— | — |
| 5° | l | 190/15 | 190/12 | 197/90 | 126/67 | upper thigh | 125/771/72 | 43.6 | −16.16 | 0.0/10.4/22.9/23.0 | 1.9 |
| 6° | l | 190/15 | 196/12 | 209/90 | 138/67 | upper thigh | 138/733/66 | 49.3 | −16.61 | 0.0/15.6/34.4/34.5 | 2.9 |
| 7° | l | 190/15 | 201/12 | 220/90 | 149/67 | upper thigh | 138/733/66 | 52.9 | −5.36 | 0.0/20.7/45.9/46.0 | 3.8 |
| 8° | l | 190/15 | 206/12 | 232/90 | 161/67 | upper thigh | 162/778/70 | 58.6 | −13.17 | 0.0/25.9/57.3/57.6 | 4.8 |
| 9° | l | 190/15 | 211/12 | 243/90 | 172/67 | upper thigh | 171/738/62 | 65.8 | −13.00 | 0.0/31.1/68.8/69.1 | 5.7 |
| 11° | l | 190/15 | 221/12 | 266/90 | 195/67 | upper thigh | 199/744/44 | 83.3 | −12.96 | 0.0/41.4/91.6/92.3 | 7.6 |

Right side mirrors within 0.6 mm at every angle. **Return is identical to Bottom
to the last digit**, as expected — the same pose.

## Root cause

Not category D. **The abduction is not being cancelled.** It transmits exactly
as a rotation about the shoulder should: shoulder Δx = 0.0 mm at every angle,
elbow +10.4 → +41.4 mm, grip centre +22.9 → +91.6 mm, all monotonic, and the
grip centre's distance to the nearest body surface rises monotonically from
31.0 mm to 83.3 mm. My earlier "the abduction is absorbed" reading was wrong: it
came from comparing closest *hand-mesh* to closest *leg-mesh* vertices, a pair
that can sit anywhere on either surface, rather than tracking the grip centre.

Not category C. The owning region is the **upper thigh** — the closest vertex is
dominated by `DEF-thigh.*` (not `.001`, not `DEF-pelvis`) at every tested angle,
at y 729–778 mm and z 44–72 mm. Not hip, pelvis or groin.

Not category A as posed. The grip centre is already 31 mm clear of the body at
3° and 83 mm at 11°, and the plate still penetrates 13 mm.

**The cause is that the control axis and the collision normal are orthogonal.**
The inboard plate is a 48 mm-radius disc whose plane is roughly sagittal, hanging
*in front of and across* the thigh. The contact is on the thigh's **front**
surface, whose outward normal is approximately +z. Shoulder abduction translates
the weight along **+x**, which is tangent to that surface. The plate therefore
slides along the thigh rather than lifting off it.

The signature is in the table: the closest body point tracks the plate laterally
almost one for one — plate centre x 103 → 195 mm, closest point x 111 → 199 mm.
That is sliding contact, not approach and retreat.

The dumbbell's own orientation is close to innocent: the handle axis rotates by
only 1.9–7.6° across the whole sweep, so this is not category B either.

### Why the sweep was non-monotonic

Because the depth is sampling the thigh's local surface relief as the plate
slides across it. At 6° and 7° the closest point is **the same vertex**
(x 138, y 733, z 66) — a local high spot — while the plate moves 11 mm further
out, so the measured depth falls to −5.4 mm. At 8° the contact jumps to a new
vertex at x 162 and the depth returns to −13 mm. The −5.4 mm at 7° is where one
bump happened to fall relative to the disc, not a trend, which is exactly why it
should not have been retained.

`scratchpad/reference-fit/10_curl_bottom_contact.png` shows it in the plane the
disc presents itself in: body surface points lie *inside* the plate circle, and
the free space is to the front.

## Minimum geometric clearance required

Penetration at the retained 3° pose is **13.59 mm (left) / 13.73 mm (right)**,
and the contact normal is approximately +z. So the requirement is about **14 mm
of forward translation at the grip centre, call it 20 mm with a safety margin** —
in +z, not in +x. No lateral movement clears it, because the thigh's frontal
surface spans the entire lateral range the arm can reach.

## The single smallest next change I would test

**`startPose.upperarm_l/r.x` from 0° to about 2° — shoulder flexion, not
abduction.** One scalar, one channel, at the Bottom pose only:

- the grip hangs roughly 0.55 m below the shoulder, so 2° of flexion moves it
  about 19 mm forward — the required range;
- the authored technique rule `shoulder_quiet_l/r` already permits
  `upperarm.x ∈ [−5°, +10°]`, so 2° is inside the accepted envelope;
- abduction stays at the accepted 3°.

I have **not** applied it. The Part C authorisation in the previous decision was
for abduction / lateral clearance, and this diagnostic shows lateral is the wrong
axis; forward flexion is a different change and needs its own approval. It should
also be checked against the elbow-position rules (`elbow_not_inward_*`,
`elbow_under_shoulder_*`) and re-measured at all five curl frames before being
retained.

## Guardrails

Forearm still 14.86%, shoulder chain untouched, grip closure 85%, elbow
corrective 0%, elbow-flexion and supination profiles untouched, clavicle
untouched, dumbbell geometry untouched, nothing nudged by eye, no threshold
weakened, push-up untouched. Instrumentation lives in
`scratchpad/repair/contactdiag.test.mts` and
`scratchpad/reference-fit/contact_image.mjs`, both outside the tracked tree.
