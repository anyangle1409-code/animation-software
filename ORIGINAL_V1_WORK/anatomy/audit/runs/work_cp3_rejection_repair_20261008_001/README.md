# CP3 rejection and frame-metadata repair

New Blender files are a003-data metadata rehearsals, not new canonical anatomical candidates. No a003 or production file is modified. See manifest.json for compressed and raw hashes and marker parent/centre comparison. Source frame, attachment carrier and actual Blender parent are distinct concepts; 202 old capture frame IDs were mislabeled.

before_fix.txt retains failing regressions; extreme_before_fix.txt retains an overflow false-pass. legacy_frame_mismatch_*.json retains the stricter check's discovery on old immutable files. Both fresh metadata-corrected builds pass the new storage comparator, while CP2 anatomy remains FAIL on the inherited zero disc gaps. Geometry and attachments are unchanged.

26 affected tests pass; 805 full-suite tests retain the same nine named baseline failures/errors. Full traces and per-name comparison are retained. Prior 135 isolated movement results are historical implementation evidence, not a fresh rerun for this metadata repair or anatomy acceptance. Gates 6/8/9 and canonical target closure remain open.

Laptop review: docs/LAPTOP_SKELETON_HANDOFF_20261008_2030.md. Reproduce using new scratch output paths; compare identities and hashes as well as numeric tolerances. Do not promote a valid round-trip to a canonical anatomy pass.
