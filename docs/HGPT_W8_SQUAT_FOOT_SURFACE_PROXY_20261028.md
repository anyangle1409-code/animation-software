# W8 squat foot-surface lower-envelope proxy — 28 October 2026

**Status: actual pinned W8 geometry, read-only. No verified ground plane, anatomical side, foot contact or squat approval.**

## Method

Input is run 39937882229 artifact 12495910312, independently downloaded, CRC-checked and SHA256-matched at `3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e`. The source model SHA256 remains `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`.

For saved squat samples 0, 7 and 8, the diagnostic requires exact equality of rest vertices, triangle topology and dominant-group assignments. It selects vertices whose dominant weight label is `foot_<suffix>` or `toe_<suffix>`, separately for authored suffixes `l/r`. These labels and suffixes are not anatomical landmarks or independently verified human sides.

Source-authored Z is used only as a model vertical proxy. Sample 0 is the standing lower-envelope reference, not a measured floor. The report records minimum Z, mean Z of the lowest one percent of selected vertices, exact lowest-one-percent vertex-ID overlap, centroid drift and selected-vertex displacement. It imposes no pass threshold.

## Actual W8 result

Each suffix has 6,865 selected vertices: 5,310 foot-labelled and 1,555 toe-labelled. The lowest-one-percent set contains 69 exact vertex IDs.

| Authored suffix / sample | Minimum Z delta vs standing | Centroid delta XYZ (m) | Lowest 1% ID overlap | Maximum selected displacement |
|---|---:|---|---:|---:|
| `l` / 7 | +0.000813794 m | +0.016733, +0.001504, +0.000990 | 37/69 | 0.022591257 m |
| `l` / 8 | +0.000813764 m | +0.016299, +0.001561, +0.001049 | 37/69 | 0.022794653 m |
| `r` / 7 | +0.000813816 m | −0.016733, +0.001504, +0.000990 | 37/69 | 0.022591349 m |
| `r` / 8 | +0.000813790 m | −0.016299, +0.001561, +0.001049 | 37/69 | 0.022794729 m |

The bilateral centroid motion toward source X=0 is approximately 16–17 mm per authored suffix, while only 37/69 standing-lowest IDs remain in the lowest one percent at the later samples. This is a geometric change in the selected surface, not proof of foot sliding, loss of balance, pressure redistribution or failed contact. A verified floor transform, plantar landmarks, anatomical side calibration and load/contact model are still required.

## Scope boundary

This report does not establish a floor, friction, pressure, centre of pressure, balance, physiological foot contact or safe squat technique. It does not modify or save any `.blend`, mesh, rig, weight, corrective key, muscle, app or production asset. Population ROM values are not used as limits. Muscle highlighting remains deferred.
