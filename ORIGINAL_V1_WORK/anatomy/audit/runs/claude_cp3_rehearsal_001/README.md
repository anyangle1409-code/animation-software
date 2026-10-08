# CP3 build rehearsal 001 (not an audit revision)

**Purpose:** prove the skeleton-first build path before CP3. The target data is built into Blender with no character mesh, saved, reloaded in a fresh process, captured, compared with the input and run through the CP2 preflight.

- **Input:** `ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json`. This is a003's data, used only because it is the only complete 206/427 record; a003's .blend files are untouched.
- **Build:** `scripts/anatomy_fit/cp3_rehearsal_blender.py build`, using GPT's `build_armature` and `build_markers` unchanged. Blender 5.2.1 LTS (bpy module, python3.13), empty factory scene.
- **Scratch .blend:** not kept and not committed, because it is not a revision. Its sha256 was `3111a99e9e591f20ad437f79aeea94fc0e5b5ffb680e23c77ad1951f9757075b`.
- **Capture:** `cp3_rehearsal_blender.py capture`, run in a fresh process. The output is `capture.json.gz`.
- **Comparison:** `scripts/anatomy_fit/cp3_roundtrip_compare.py` produced `roundtrip_report.json`.

## Result

- **Round trip: PASS.**
  - All 206 bone and 427 marker identities are equal, and there are no parent or parent-relation mismatches.
  - Bone endpoints match to 5.9e-8 m, marker centres to 2.9e-7 m, and frame components to 4.0e-6 (single-precision storage).
- **CP2 preflight on the capture** gives the same result as on the input: 8 PASS, 1 FAIL (the known a003 zero disc gap), 1 UNVERIFIED (no endplate surfaces) and 1 INFO.
- **Roll (reported, not gated):** for bones with a defined roll target, bone Z matches within 0.022°. **74 bones have no defined roll:** `joint_markers.bone_frame` puts X along the bone for horizontal bones, and the builder passes that X to `align_roll`. They are the ribs 1–7 and 12, both clavicles, talus, navicular, cuboid, all metatarsals and toe phalanges, five skull bones (occipital, parietals, sphenoid, ethmoid), the palatines, inferior nasal conchae, stapes and the hyoid. Their bone Z is therefore whatever Blender picks. The left and right hallux proximal phalanges differ by about 4.5° from mirror symmetry.
- **Impact today:** none on the isolated movement tests. `run_isolated_tests_blender.py` applies world-space deltas conjugated by each bone's rest matrix, so the roll cancels.
- **Impact later:** a defined roll matters for any bone-local convention, such as a runtime-rig transfer (CP9) or keyed local rotations. Suggested CP3 builder fix: give `align_roll` a target perpendicular to the bone for horizontal bones (for example bone_frame Y, the superior direction) and record the convention.
- **Checker fix found by this rehearsal:** `cp2_preflight.FLOAT_EPS` was 1e-9, which rejected Blender's single-precision frames (orthonormality error about 7e-7). It is now 1e-5, which is numerical rather than anatomical.
