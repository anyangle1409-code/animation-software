# MPFB benchmarks for the Option 5 reference pack (3 Nov 2026): male and female

**Status:** experimental MPFB references. **Not production** and **not approved**. Per the owner's first-party rule, no MPFB geometry goes into production.

- **Pack:** the owner's Option 5 pack (male "Athletic – Stronger", female "Athletic – Stronger"; the female sheet used for the views is Option 4). The pack images are not in git.
- **Male and female:** built **independently**. The female is MakeHuman's own female body type (gender 0) with her own settings, **not a scaled male**.
- **Views:** `male/` and `female/` hold the front, 3/4 front, side, 3/4 back and back views, upper-body close-ups, and arms-out front and back (30°). All renders are barefoot.
- **Settings:** `params.json` per model. Rebuild with `scripts/mpfb_experimental/build_mpfb_candidate.py`; the definition pass is `define_mpfb_candidate.py`:
  - male: `V2_DEF=2.3 V2_PEC_RISE=0.03 V2_PEC_MASS=0 V2_PEC_UPPER=3.5 V2_PEC_FLATTEN=2.8 V2_NIPPLE_FLAT=2.5`;
  - female: `V2_SEX=female V2_DEF=1.6`;
  - add `V2_ARMS_OUT=30` for the arms-out views.
- **Measurements:** `scripts/mpfb_experimental/measure_guide.py`, stand pose. Circumferences are convex-hull slices, which approximate a tape measure, so they read slightly high over concave areas. Limb circumferences are measured perpendicular to the bone (left side). Biacromial is approximated from the rig's clavicle ends.

## Male (target height 1.82 m)

| Guide | Target (cm) | Model (cm) | |
|---|---|---|---|
| Height | 180-184 | 182.6 | in range |
| Shoulder width (biacromial, approx.) | 45-49 | 44.3 | low |
| Chest circumference | 100-108 | 109.1 | high |
| Waist circumference | 78-84 | 84.0 | in range |
| Hip circumference | 96-102 | 98.9 | in range |
| Upper arm circumference | 33-37 | 36.3 | in range |
| Thigh circumference | 56-61 | 59.3 | in range |
| Calf circumference | 37-40 | 39.6 | in range |
| Inseam (crotch to floor) | 82-86 | 89.0 | high |
| Shoulder : hip (biacromial / hip breadth) | 1.20-1.30 | 1.145 | low |

## Female (target height 1.68 m)

| Guide | Target (cm) | Model (cm) | |
|---|---|---|---|
| Height | 165-170 | 168.2 | in range |
| Shoulder width (biacromial, approx.) | 36-39 | 35.8 | low |
| Bust circumference | 86-92 | 94.8 | high |
| Underbust circumference | 72-78 | 72.1 | in range |
| Waist circumference | 64-70 | 69.7 | in range |
| Hip circumference | 90-96 | 94.4 | in range |
| Upper arm circumference | 26-29 | 29.5 | high |
| Thigh circumference | 52-56 | 54.4 | in range |
| Calf circumference | 34-36 | 36.4 | high |
| Inseam (crotch to floor) | 77-79 | 78.7 | in range |
| Shoulder : hip (biacromial / hip breadth) | 0.95-1.00 | 0.989 | in range |

## Notes

- **Male inseam:** high because MPFB's own leg proportions are long. A production model fitted to the canonical skeleton takes its limb lengths from that skeleton.
- **Biacromial:** an approximation from MPFB's clavicle bones, so it is low-confidence.
- **Female definition:** the relief pass is the male one with the pectoral features off, at a lower strength. Female-specific definition is still to come.
- **Approval:** both await owner review.

