# Source-only foot geometry for laptop inspection

Open `SOURCE_ONLY_Grant_M02_segments.blend` in Blender 5.2.1 LTS. Use the scene selector to choose calcaneus, talus, M1 or grouped midfoot. Each scene contains one unchanged source mesh, a camera and visible source-only labels. Select the mesh and use Frame Selected if the viewport needs centring. Read the embedded `READ_ME_SOURCE_ONLY` text.

These are separately aligned source segments, not an assembled foot, canonical skeleton, movement rig or production candidate. Physical units and common contact pose remain unverified. The grouped midfoot must not become one bone or be assigned named bones from component size alone. No canonical master, a003, production mesh, weights or drivers were changed.

Attribution: Grant TM et al. (2020), A statistical shape analysis of the human foot, PeerJ 8:e8397, https://doi.org/10.7717/peerj.8397. Dataset: https://doi.org/10.5281/zenodo.3464747, CC BY 4.0. Source mesh geometry is unchanged; inspection scenes, cameras, annotations and renders added. Original sample filenames and SHA256 values are stored in the objects and verification file. No sex/stature is inferred from M02.

Verification: source file checksums match the preceding acquisition audit; save/reload preserves every mesh vertex coordinate and polygon index (mesh SHA256 comparison); all four scenes have exactly one mesh and no armature. All four 900px renders were opened and visually inspected for readable labels and complete segment framing. EGL warnings were emitted, but rendering completed successfully; stdout retained. No anatomical acceptance is implied.

Reproduce with bpy: `build_source_inspection.py SOURCE_DIRECTORY NEW_OUTPUT_DIRECTORY`. Output must be a new directory to preserve immutable results. Source download URLs are in the preceding acquisition manifest.
