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


## Male v7 (target height 1.82 m)

| Guide | Target (cm) | Model (cm) | |
|---|---|---|---|
| Height | 180-184 | 182.7 | in range |
| Shoulder width (biacromial, approx.) | 45-49 | 46.0 | in range |
| Chest circumference | 100-108 | 109.5 | high |
| Waist circumference | 78-84 | 81.5 | in range |
| Hip circumference | 96-102 | 102.1 | high |
| Upper arm circumference | 33-37 | 36.4 | in range |
| Thigh circumference | 56-61 | 61.0 | in range |
| Calf circumference | 37-40 | 40.1 | high |
| Inseam (crotch to floor) | 82-86 | 86.2 | high |
| Shoulder : hip (biacromial / hip breadth) | 1.20-1.30 | 1.156 | low |

## Female v7 (target height 1.68 m)

| Guide | Target (cm) | Model (cm) | |
|---|---|---|---|
| Height | 165-170 | 168.2 | in range |
| Shoulder width (biacromial, approx.) | 36-39 | 37.4 | in range |
| Bust circumference | 86-92 | 91.0 | in range |
| Underbust circumference | 72-78 | 71.2 | low |
| Waist circumference | 64-70 | 68.2 | in range |
| Hip circumference | 90-96 | 93.9 | in range |
| Upper arm circumference | 26-29 | 27.4 | in range |
| Thigh circumference | 52-56 | 55.2 | in range |
| Calf circumference | 34-36 | 34.6 | in range |
| Inseam (crotch to floor) | 77-79 | 78.7 | in range |
| Shoulder : hip (biacromial / hip breadth) | 0.95-1.00 | 1.03 | high |

## Notes

- **v7 against v3:**
  - male shoulder width 44 → 46 cm (in range); inseam 89 → 86.2 cm (shorter legs);
  - female bust 95 → 91 cm (breast-size control 0.3); upper arm 30 → 27 cm; shoulder width 35.8 → 37.4 cm (in range);
  - female muscle raised and definition 1.6 → 2.1.
- **Still slightly out:**
  - male chest about 1.5 cm high and hip about 0.1 cm high;
  - female underbust 0.8 cm low (it did not respond to MPFB's underbust control).
- **Shoulder-to-hip ratios (biacromial ÷ hip breadth):** male 1.16 (target 1.20–1.30), female 1.03 (target 0.95–1.00). Both depend on the biacromial approximation (rig clavicle ends) and the hip-breadth slice, so they are low-confidence.
- **Male inseam:** MPFB's leg lengths are shortened here. A production model takes its limb lengths from the canonical skeleton.
- **Female definition:** the generic pass with the pectoral features off. Female-specific detail is still to come.
- **Approval:** both await owner review.

## v8: match the photos (owner, 3 Nov: "both need more fixing"; when the photos and guide numbers disagree, the photos win; all areas)

- **Male:**
  - deltoids, arms and forearms bigger;
  - quads, calves and glutes fuller;
  - chest and lats more;
  - definition 2.8.
- **Female:**
  - the thin-upper-arm narrowing removed, replaced by deltoid and arm muscle;
  - stronger quads, calves and glutes;
  - definition 2.6.
- **Male measurements (cm):**
  - chest 114.1, waist 82.6, hips 104.2;
  - upper arm 44.1, thigh 64.9, calf 42.0;
  - inseam 86.1, shoulder width ≈46.0.
- **Female measurements (cm):**
  - bust 93.5, underbust 71.3, waist 68.2, hips 96.9;
  - upper arm 29.1, thigh 58.8, calf 38.5;
  - inseam 78.7, shoulder width ≈37.4.
- Several girths are now above the guide ranges, as the owner chose.
- Bald heads: MPFB's bundled assets include no hair.
- `params.json` / `measurements.json` hold v8. **Not approved.**
