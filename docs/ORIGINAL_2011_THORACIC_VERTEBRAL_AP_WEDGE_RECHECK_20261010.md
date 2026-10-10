# Actual Kunkel 2011 Table 2 — restored original thoracic vertebral body anterior/posterior heights

**Date:** 10 October 2026 · **Status:** direct primary evidence recovered, **NONCANONICAL**. Do not edit original/a003/c001–c004/a005/frozen production/Blender/Work or other owners.

## Formerly missing primary data is publicly accessible

Original full peer-reviewed primary text: Kunkel ME, Herkommer A, Reinehr M, Böckers TM, Wilke H-J. "Morphometric analysis of the relationships between intervertebral disc and vertebral body heights: an anatomical and radiographic study of the human thoracic spine." *Journal of Anatomy* **219**:375–387 (2011); DOI **10.1111/j.1469-7580.2011.01397.x**, PMID **21615399**, PMCID **PMC3171774**, https://pmc.ncbi.nlm.nih.gov/articles/PMC3171774/.

The full source **Table 2**, not merely abstract or a graph, has original anterior **VBHA mean±SD** and posterior **VBHP mean±SD** separately for all C7, T1–T12. We independently read the whole table at the above primary URL. The older `THORACIC_BODY_DISC_2011` entry in `ORIGINAL_V1_WORK/anatomy/canonical_proportion_sources_v1.json` included only their **combined average height**, not the source's two separate height measurements. **This is the previously identified "missing per-level body anterior/posterior source" block**. The original PDF was not downloaded or SHA-pinned; no source patient imagery, figures, or PDF is in Git.

## Original measurement cohort and precise semantics

- The paper sampled **72 dissected spine segments from 30 donors**, 15 male and 15 female, **six samples for each of 12 disc levels** C7/T1 through T11/T12. Donor mean age **57.43 ±11.27 years**. Segments had mild-to-moderate degenerative features. **Not a 182cm male-only or healthy standing-population reference**.
- Vertebral body **VBHA/VBHP** heights were measured **on calibrated side radiographs of isolated cadaveric segments placed neutral for radiography**, from the outermost anterior/posterior endplate corners. This is NOT direct physical caliper disc-height measurement, NOT whole-spine upright global lordosis/kyphosis, NOT an accepted CT-to-Blender registration.
- The distinct disc **ADH/PDH** values in the same paper were directly measured on sagittal specimens and were already stored with their source-independent method in the canonical file. Recovered body A/P levels should be interpreted alongside those disc sources, **without treating group means as paired 3D centres from the same cadaver**.
- The old canonical source's **13 printed mean-of-A/P height** values match the new primary VBHA/VBHP table. This independent source recovery **does not invalidate or change those means**.

### Original primary Table 2 values and derived differences

All heights and differences in **millimetres** from this study. The "posterior − anterior" column is **arithmetic over two population means**, not a measured Cobb/wedge angle, a joint-rotation parameter, an intervertebral-disc height or a per-subject paired variance.

| Vertebra | Original anterior mean ± SD | Original posterior mean ± SD | Posterior − anterior mean | Previously recorded average |
|---|---:|---:|---:|---:|
| C7 | 13.89 ±1.42 | 14.38 ±2.22 | 0.49 | 14.14 |
| T1 | 14.49 ±1.23 | 15.28 ±1.14 | 0.79 | 14.88 |
| T2 | 15.01 ±1.51 | 16.11 ±1.67 | 1.10 | 15.56 |
| T3 | 15.65 ±1.85 | 17.41 ±1.12 | 1.76 | 16.53 |
| T4 | 15.42 ±1.46 | 18.15 ±1.54 | 2.73 | 16.79 |
| T5 | 15.84 ±1.07 | 17.33 ±2.16 | 1.49 | 16.59 |
| T6 | 16.04 ±1.43 | 18.22 ±1.38 | 2.18 | 17.13 |
| T7 | 15.94 ±1.61 | 18.67 ±1.64 | 2.73 | 17.31 |
| T8 | 16.99 ±1.70 | 20.05 ±1.77 | 3.06 | 18.52 |
| T9 | 18.26 ±2.12 | 20.25 ±2.44 | 1.99 | 19.26 |
| T10 | 18.98 ±1.40 | 20.35 ±1.89 | 1.37 | 19.67 |
| T11 | 19.60 ±1.92 | 22.67 ±1.38 | 3.07 | 21.14 |
| T12 | 20.80 ±1.96 | 23.12 ±1.94 | 2.32 | 21.96 |

All 13 posterior means exceed anterior means, supporting a **kyphotic body-wedging direction trend**, but **without AP chord/depth and endplate tangents you cannot derive one segmental angle**, let alone reproduce 43.7° T1–T12 global kyphosis. The body wedge's "height difference" is **not itself an angle**. The means and SD values come from a cadaveric mixed-sex sample and do not yield standing male 182cm conditional distributions or per-subject covariance.

### Cross-check with independent 2016 Indian CT body heights

The original pre-existing `THORACIC_CT_2016_INDIA` in the frozen ledger also shows posterior greater than anterior vertebral body height at every T1–T12 level, but its sample and measurement method produce **substantially different absolute values**. For example, at T4 the Kunkel 2011 radiographic means are **15.42 anterior / 18.15 posterior mm**, while the Indian CT evidence reports **20.98 / 22.34 mm**. This cross-study **sign agreement** supports a qualitative physical wedge shape, not a numerical fusion, a mean-angle calculation, or a valid 182cm male bone target. Never take a wedge-height difference from one source and front–back depth from another to calculate artificial per-level angles.

### Exactly what was completed and what remains

**Completed and verified in this isolated branch:** a complete, original, level-specific 13-row Table 2 source record with all paired mean/SD and previously reported averages; first-party audit against the actual frozen source averages and independently distinct CT sign; 18 adversarial offline regressions; GitHub Actions recheck; a numerical noncanonical artifact (no PDF or donor imagery).

**Still blocked before the canonical T1–T12 sagittal stack:** a source-bound **AP vertebral chord/depth and endplate plane at each level**, a defensible **upright standing segmental angle** distribution matched to age/stature/male condition, disc-to-body angular coupling with a true 3D contact envelope, and coupled SC/sternum/ribcage/global C2–S1 alignment. The mixed cadaveric mean-height table **cannot replace** the original requested 2025 Finoco standing segmental Table 6 or 1989 Bernhardt & Bridwell normal standing segmental table; retrieve those actual raw angle sources separately if accessible.

**Readiness stays: 0 READY / 9 PARTIAL / 3 BLOCKED; no accepted c005, CP1 Gate6 remains OPEN.** This closes missing access to a primary table, **not** thoracic per-level curvature/accepted 3D pose.
