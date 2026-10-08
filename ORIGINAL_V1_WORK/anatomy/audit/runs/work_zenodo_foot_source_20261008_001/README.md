# Zenodo foot source acquisition and Blender inspection

This run verifies access and import of source specimens, not a corrected canonical skeleton. No .blend, production geometry, a003 edit or selected target was created.

Source: Grant et al., PeerJ 8:e8397 (2020), DOI 10.7717/peerj.8397; dataset DOI 10.5281/zenodo.3464747 (CC BY 4.0). The download manifest records eight matched files and reproducible URLs. Raw source files are not redistributed here.

Reproduce: download the eight manifest files into a separate directory; run `inspect_blender_source_segments.py SOURCE_DIRECTORY NEW_OUTPUT_JSON` using Blender/bpy 5.2.1 LTS. The script refuses to overwrite the output. It compares an independent STL parse against native Blender import, including every float32 vertex position and triangle geometry. The initial bbox-only run is retained because that check alone could falsely pass altered geometry.

The four STLs import successfully: calcaneus, talus, M1 and grouped midfoot. The last group nominally covers nine bones; the inspected sample has 28 connected pieces, only eight above 100 vertices. That diagnostic threshold does not identify bones or justify discarding fragments. Four segments nominally cover twelve bones, not the complete 26-bone foot, and source segments were transformed separately. Common contact frame, units and donor-specific stature/sex remain unverified. Vertex means are not volume centroids or joint centres. No nearest-point/PCA result becomes anatomical contact evidence.

`carpal_rib_access_recheck.json` retains separate access limits: Brown actual archive requires sign-in; RibSeg binary pages require sign-in and the public quality sheet records missing/incomplete ribs. These checks do not select cases or supply contact geometry.

See `verification.json`, the machine-readable source review and the current laptop handoff. freeze_ready remains false.
