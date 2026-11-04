# MakeHuman base for the production body: owner decision and provenance (4 Nov 2026)

## Decision

On 4 Nov 2026 the owner chose **option 1**: use the MakeHuman base mesh as the starting point for the production body. This changes the 3 Nov first-party rule, which allowed MPFB only as a reference.

The chain of events:

- The independently authored body built from muscle shapes in code (`scripts/body_v3`) was judged "terrible".
- I explained that the MakeHuman base mesh and its shape targets are released as CC0 (public domain).
- The owner replied "1".

## Licences

| Item | Licence | Ships in the app? |
|---|---|---|
| MakeHuman base mesh, shape targets, weights (bundled with MPFB 2.0.18, git `6ff1eb35`) | CC0 1.0 | Yes: the body is derived from it |
| MPFB add-on code | GPL-3.0 | No: used only as a tool inside Blender |
| Our scripts (fit, definition, dressing, rendering) | Repository licence | Tools only |

## Chain

1. **Build:** `build_mpfb_candidate.py` with the parameters JSON; the MakeHuman macros and targets give the Option 5 build.
2. **Definition:** `define_mpfb_candidate.py`; our own procedural relief.
3. **Outline fit:** `silhouette_fit_blender.py` fits the body to the owner's reference outlines (front width, side profile, legs) height by height.
4. **Review dressing:** `dress_review_blender.py` adds hair, eyebrows and trunks for the comparison renders only. This dressing is not part of the body.

## Still to do before production

- Owner visual approval.
- Re-rigging to the canonical skeleton, or approval of a skeleton revision (the shoulder width).
- Movement keys and the female model.
