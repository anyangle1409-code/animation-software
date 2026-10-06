# r101 rotation-driven axillary fold-volume helpers: screening (IN PROGRESS, no candidate)

Declaration: `repair_preparation/r101_axillary_fold_volume_helpers_declared` (commit e914b956, before any edit). Every prototype was built from a fresh copy of r98 with `scripts/r101/vol101.py`.

## Mechanism (as built)

- **Helper bones:** `axvol_ant_<s>` and `axvol_post_<s>` are children of `glenohumeral_half_<s>` and start from its rest frame.
- **Drive:** the helper's local location is `a_max * smoothstep(d0, d1, d) * n_local`. Here `n` is the band's outward normal, and `d` is the distance between probe points 0.2 m along the humerus axis, one under the upperarm and one under `glenohumeral_ref`. That makes `d` a function of glenohumeral swing only.
- **Driver type:** simple scripted expressions with a LOC_DIFF variable. There are no Python drivers and no dependency cycle.
- **Weights:** band vertices hand a fraction (up to 0.8) of their half-helper weight to the fold helper. Base motion is therefore unchanged, all other weights are exactly r98's, the result is mirror-exact, and every vertex keeps at most 4 influences.

## Measured

**Driver response** (`driver_response_Bm_*.json`, first mapping d0 = 0.07, d1 = 0.19):
- Exactly 0 at rest in abduction and flexion.
- Smooth and monotonic.
- Identical for internal, neutral and external rotation, so twist doesn't drive it.
- **It saturated at about 60° of elevation**, because the probe chord is 0.4·sin(θ/2). The mapping was changed to d0 = 0.14 and d1 = 0.33: zero below about 40° of glenohumeral swing (≈60° of arm elevation), full offset at 170°. All six screens below use the corrected mapping.

**15-pose subset** (`screening_subset_results.json`):

| Variant | Collisions | Max edge ratio |
|---|---:|---:|
| r98 | 346 | 4.33 |
| r99-P (rejected) | 196 | 5.19 |
| r100 anterior 6 mm (rejected) | 414 | 4.33 |
| anterior 15 mm | 346 | 4.33 |
| anterior 30 mm | 348 | 4.33 |
| posterior 15 mm | 362 | 4.33 |
| posterior 30 mm | 378 | 4.33 |
| both 15 mm | 362 | 4.33 |
| both 30 mm | 380 | 4.33 |

The posterior helper adds horizontal-adduction contacts: 2 → 18 at 15 mm and 2 → 38 at 30 mm.

**Visual check** (`images/r98_r99P_r100Am_r101Am_r101Bm_*.jpg`, r98 / r99-P / r100-Am / r101-Am / r101-Bm per pose): at 30 mm, the overhead membrane, rear dent and back creases are **visually indistinguishable from r98**. Band vertices carry only part of their weight on the half helper, so a 30 mm helper offset moves the fold by at most about 16 mm.

## Status / continuation note

There is no candidate and no READY record; r98, r99 and r100 are unchanged. The repository 15-pose test and the 56-pose matrix were not run, because no variant was visibly promising.

The next exact step within this declaration's bounds:
- raise the fold share (`band_max` up to 0.8 applies to the half-helper share; consider basing the band on vertices whose half weight is at least 0.3);
- and/or raise the offset toward the 0.04 m hard cap;
- then re-render flexion 170 / abduction 150 / press_top / pullup_hang close-ups against r98.

If the fold still does not read as a rounded band at the cap, record r101 as blocked. The likely remaining causes are either the band normal (fixed in the half helper's frame) not matching the overhead fold orientation, or the membrane being dominated by vertices weighted to the trunk and humerus rather than the half helper. Either would need an amendment to also take share from those bones, with the base-motion change measured.
