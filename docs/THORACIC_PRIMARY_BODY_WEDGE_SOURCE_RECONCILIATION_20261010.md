# HOME GYM PT — First-party thoracic body wedge source recovery (10 October 2026)

**Status:** independent, noncanonical primary-source evidence. **No Blender, no skin fit, no c005 approval, no new angular geometry.**

## Why this is significant

The existing frozen evidence stack \`ORIGINAL_V1_WORK/anatomy/canonical_spine_level_stack_v1.json\` uses the *average* of anterior/posterior radiographic heights for each T1–T12 vertebra. The earlier qualitative constraints record explicitly said the individual level-wise anterior/posterior body values were unavailable. They are in fact openly readable in Kunkel et al.'s **original Table 2**. They can now be kept separately, without averaging away the wedge signal.

**Verified primary publication:** Kunkel ME, Herkommer A, Reinehr M, Böckers TM, Wilke HJ. “Morphometric analysis of the relationships between intervertebral disc and vertebral body heights: an anatomical and radiographic study of the human thoracic spine.” *J Anat.* 2011;219(3):375–387. DOI 10.1111/j.1469-7580.2011.01397.x, PMCID PMC3171774, PMID 21615399.

- Official full article and Table 2: https://pmc.ncbi.nlm.nih.gov/articles/PMC3171774/
- Sample/methods: **72 spine segments from 30 deceased donors**, 15 men and 15 women; six segments per disc level; donor mean age 57.43 ± 11.27 years. No per-sex per-level table is provided. Specimens were separated into units and positioned neutrally for calibrated radiography. **Vertebral-body** corner heights (VBHA and VBHP) are *radiographic* measurements, unlike the reported directly measured anatomical disc heights; do not silently mix these methods.
- Table 2 includes **C7** as a transitional *cross-source comparison only*. HGPT's separately selected C7 height is NOT replaced by this sample.

## Primary data and verified relationship

The new exact published Table 2 values live in:
\`ORIGINAL_V1_WORK/anatomy/audit/thoracic_primary_body_wedge_kunkel2011_v1.json\`.

The standard-library-only verifier is:
\`scripts/anatomy_fit/thoracic_primary_body_wedge_evidence.py\`.

For each T1–T12, it verifies that the arithmetic mean of VBHA and VBHP agrees (to publication rounding) with the published Table 2 average **and** with HGPT's previously recorded mean in \`canonical_spine_level_stack_v1.json\`.

Selected explicit numerical contrasts (radiographic measurements; mm):

| Level | Anterior mean | Posterior mean | Posterior minus anterior |
|---|---:|---:|---:|
| T1 | 14.49 | 15.28 | +0.79 |
| T4 | 15.42 | 18.15 | +2.73 |
| T8 | 16.99 | 20.05 | +3.06 |
| T11 | 19.60 | 22.67 | +3.07 |

The published average heights were already present; **the recovered evidence is the anterior/posterior difference for each of all 12 vertebral bodies**, not a newly accepted total spine length. Posterior taller than anterior on all twelve levels is consistent with thoracic body kyphotic wedging, and reinforces the existing qualitative source constraint. This is *not* a numeric per-level angle solution.

## Stop conditions — why no final 3D wedge or rib position can be set

1. The **sagittal anterior-posterior body depth at each matched level** is absent from this Table 2. A difference in anterior/posterior height alone cannot be converted into a defensible angle. A uniform body depth assumed from a separate study would mix donors/methods and require an explicit uncertainty model and endpoint matching.
2. This is a mixed-sex, older **cadaveric isolated radiographic** sample, not a 1.82-m standing male with coherent S1, T1, thorax and head frames. Published SDs do not become patient-specific acceptance limits.
3. Actual **superior/inferior endplate geometry, disc wedge, kyphotic sign conventions, 3D rib attachment contact, and facet closure** remain unobserved. Radiographic corner-height wedges and total T1–T12 Cobb kyphosis describe different quantities.
4. The global male standing thoracic mean (~43.7° in another source) must **not** be spread equally across T1–T12. The published levels cannot be added naively to reproduce global standing alignment.
5. This new evidence does not resolve the C7 orientation conflict, spine-to-sternum depth, rib curvature/contact or the need for independently identified bone surfaces.

**Next primary-source decision:** acquire endpoint-matched per-level AP depths and a compatible endplate/segmental angle table or an original 3D bone surface dataset. Compare per-level measurement definitions and cohort/posture before proposing numerical wedges. A true 3D Blender fit must measure opposing endplate surfaces, not just the zero/positive centre gaps.

## Reproduce safely without laptop or Blender

    python scripts/anatomy_fit/thoracic_primary_body_wedge_evidence.py
    python -m unittest -v scripts.test_thoracic_primary_body_wedge_evidence

The verifier produces a JSON-only diagnostic with exactly 13 rows (C7 plus 12 thoracic levels), original anterior/posterior values, posterior-minus-anterior in **mm** and a unitless posterior/anterior ratio. Every \`angle_deg\` is null, no bone changes are made, and anatomical approval stays false. The 11 regression tests reject swapped/missing levels, numeric discrepancies, source ambiguity, forged approvals and altered upstream mean heights.

**Existing original a003 and accepted proposal records c001–c004 remain untouched.** The global 0 READY / 9 PARTIAL / 3 BLOCKED readiness is unchanged. This recovers one previously absent *source measurement dimension*, not a geometry or movement certification.
