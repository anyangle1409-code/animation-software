# Body v3, male, first pass f1 (3 Nov 2026)

**What:** a new, independently authored body (owner's option B).

- It is built in code from anatomical muscle forms on the canonical skeleton. Its signed-distance primitives (pecs, three deltoid heads, lats, traps, quads, hamstrings, calves and so on) are smooth-unioned, with grooves carved along the skin (linea alba, abdominal intersections, semilunaris, inguinal, serratus, spine and lat border). A 3.5 mm "skin" blur goes over them, then marching cubes at 3 mm.
- **No MPFB or MakeHuman geometry was used.** MPFB was used only as the source of the proportion numbers.
- **Builder:** `scripts/body_v3/build_body_v3_blender.py`. The skeleton comes from `export_skeleton_blender.py`.
- **Measurements (cm):** see `body_v3_report.json`. Option 5 male guide numbers are in brackets.

| Measure | f1 (Option 5) |
|---|---|
| Chest | 113.4 (114) |
| Waist | 80.9 (82.6) |
| Hip | 95.2 (104) |
| Upper arm | 46.5 (44) |
| Thigh | 64.6 (65) |
| Calf | 40.0 (42) |

**Status:** a static standing sculpt for review only. It has no rig yet. **Not approved.**
