# Phase 9 rib–sternum coupled inspiration on a003

**What it tests:** pump-handle rotation of ribs 1–7 at the 4.6° TEST AMPLITUDE (Beyer 2014 smallest level mean, FRC–TLC; the same amplitude as the isolated rib tests). Ribs 8–10 follow through the interchondral joints, and the sternum takes the rigid sagittal motion that least deforms the costal cartilages. That sternal motion is solved, not chosen.

**Result:** see `rib_sternum_report.json`.
- **Integrity PASS:**
  - Blender bone ends match the solver within 5e-7 m;
  - costovertebral drift 1.4e-7 m;
  - mirrored displacement symmetric within 2e-6 m.
- **Sternum direction:** at peak it rises and moves anteriorly (the textbook pump handle); the direction emerges from the solve.
- **Cartilage:** coupling cuts the worst costal-cartilage change from 15.8 mm (sternum fixed) to about 4.7–4.8 mm. The remainder reflects one uniform amplitude across levels.

**Not modelled:** bucket-handle and long-axis components, cartilage elasticity, the shoulder's response to breathing (the clavicles are carried by the sternum), and lung volume. This is implementation-integrity evidence only, not anatomical acceptance.

**Files:** the test blend is not committed (its hash is in the report). Clips (a003 vs c003; front and side thorax close-ups at true scale) are in `../rib_sternum_coupling_c003_001/clips/`.
