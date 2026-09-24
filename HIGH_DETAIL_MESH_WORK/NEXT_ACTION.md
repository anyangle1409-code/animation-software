# Next action: visual review of V13e

V8 remains the accepted body/knee geometry baseline. V11 and V12c are preserved, unaccepted hand candidates. **V13e fingertip retopology is the current unaccepted hand review candidate.** It adds 1,646 distal-finger vertices to V12c and modestly rounds the four fingertips on each side. The protected floor contacts, seam boundaries, rig, weights, UV behavior and exercises are unchanged. See `REVIEW_V13E_FINGERTIP_RETOPOLOGY.md` and the three matched V12c/V13e boards in `renders_v13e_fingertip_retopology/`.

Visual improvement is small. The broad inherited finger sections and facets near protected floor-contact vertices remain. Do not call Phase B finished or start grip refit without visual acceptance. If more hand improvement is required, plan a local finger-body topology replacement with an explicit proof that the push-up contact solution remains identical; repeated small displacement fields have not removed the inherited silhouette. Keep the V12c and V13e assets intact and run `scripts/audit_hand_seams.py` on every new candidate.

## Validation pin

Runtime `614033b` is the pinned validation source. The source branches have since moved to `87b881d`, which has 14 exercises and adds self-collision, feet and equipment-clearance gates. Measured on the current runtime (`REAL_CHARACTER_GLB` pointed at each candidate):

- **Upper arm against chest.** V10 and V11 fall below the production character's recorded baselines on 10 exercises. The closest distances are 0.5 to 4 mm, so they are not penetrations. This comes from the high-detail body's arm and chest shape, not from the hands, and V11 gives the same figures as V10.
- **Incline curl.** The dumbbell grazes the high-detail body's thigh by 0.76 mm (one vertex) at the end of the repetition. On the production character it clears.

Bring the pin forward to the current source before the body is bound for production. These are body-shape and exercise items to settle then; they do not block the hand review.

Do not change the frozen 63-bone `hgpt_canonical_v3` hierarchy, exercise mechanics, equipment, production references, palm motion or scapular rhythm.
