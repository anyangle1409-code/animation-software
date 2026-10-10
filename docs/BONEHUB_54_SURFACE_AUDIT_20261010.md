# Whole-region real STL geometry source QA — 10 October 2026 (NONCANONICAL)

## Goal and scope

Continue draft PR #33's **54/54 source-file discovery** (16 wrist carpals, 14 ankle/foot tarsals, 24 ribs, two sides), building on PR #32's four actually checksum-verified raw STL examples. This isolated branch adds **real raw-byte SHA256 verification** and mesh-quality checks for the entire 54-file subset. All medical/mesh bytes stay out of the source repository and reports store numerical evidence only.

Dataset: [BoneHub / Visible Human Full-Skeleton 3D Bone Models](https://huggingface.co/datasets/BoneHub/visible-human-3d-models), DOI 10.57967/hf/10464 (Alavi and Asseln, 2026), derived from Andreassen et al. (2023), DOI 10.1038/s41597-022-01905-2. CC BY 4.0; attribution to both sources required. The dataset male is 180 cm and 39 years; the HGPT target is about 182 cm. **Both data releases use the same Visible Human male donor, not independent population subjects.**

Frozen upstream source revision for this audit:

\`ac8de2b38f5ae1a0996053ca0639dd6ae43358f1\`

## Verifiable first-party implementation

\`scripts/anatomy_fit/bonehub_54_surface_audit.py\` (Python standard library only):

- Query the upstream official read-only metadata API; reject any movement away from the frozen full Git commit SHA.
- Require exactly 16 carpal, 14 tarsal and 24 rib candidates, split 8+8, 7+7, 12+12 across labelled sides.
- Require an upstream raw-file SHA256 pin (LFS OID or the original four independently verified hashes) for each file; refuse unknown/missing pins, broken identity and altered historical examples.
- Fetch through the exact immutable \`resolve/<40hex-sha>/...\` URL; SHA256-verify the actual source bytes **before** storing an STL to external/private cache. Verify cached files again; do not overwrite stale or corrupt files.
- Cap individual and total source file size, refuse duplicate files, forbidden output directories and source/report overwrites.
- Parse binary STL triangles, reject truncation/nonfinite coordinates and compute bounding extents *in native unknown STL units*.
- Weld source vertices by **exact float32 position** for a diagnostic. Report degenerate triangles, boundary edges (one incident face), nonmanifold edges (three or more incident faces), same-direction paired edges, and vertex-connected component count.
- Mark a single closed consistently oriented connected exact-weld topology candidate as such, **not** as an anatomically sound / cartilage-bearing surface.

Adversarial offline tests check the frozen revision, side counts, missing/corrupted/repeated files, provenance checks, unapproved source claims, STL closure/boundary/degeneracy/orientation, safe caching and private output.

A dedicated GitHub Actions workflow acquires all 54 raw source STLs to temporary private runner storage, validates each, and uploads **only JSON numerical diagnostics and fingerprints**. Neither GitHub nor Work/Claude receives source mesh objects through this PR.

### Running independently

From the correct checked-out source branch with external/private output destinations:

    python -m unittest discover -s scripts -p 'test_bonehub*.py' -v
    python scripts/anatomy_fit/bonehub_54_surface_audit.py \
      --download \
      --private-dir /tmp/hgpt-bonehub-raw-reference-cache \
      --output /tmp/hgpt-bonehub-all54-qa-report.json

The \`--download\` flag is explicit; removing it makes the process strictly private-cache-only. Windows paths can be substituted for \`/tmp\`. Do not put cache or numeric report under the Git checkout; do not commit them. Existing source files are never overwritten after a mismatch.

## Scientific limitations that remain open

The source-mesh topology is a necessary engineering check but **not** sufficient for correct anatomical shape. Even fully manifold STLs do not identify the radiocarpal, intercarpal, subtalar, midfoot or rib articular contact patches. A connected nonintersecting shell is not cartilage, a bone-head/capsule/ligament origin, or a joint-centre trajectory.

The source original coordinate axes, linear unit, anatomical left/right semantics and scanner-to-HGPT transform have not been independently registered here. The STLs do **not** establish the canonical 182 cm proportions. All jaw/vertebral/head movement, costal cartilage, articular orientation, soft tissue and functional ROM remain independent studies.

The previous measured first-rib and talus STL triangles contained some exactly degenerate faces; this expanded QA is deliberately diagnostic rather than a procedure that silently repairs the original meshes. A future explicit geometry-cleaning experiment must retain the untouched raw hash and source scientific uncertainty.

**Canonical CP1/Gate6 remains open; regional counts remain 0 READY / 9 PARTIAL / 3 BLOCKED.** Neither source file availability nor metric mesh quality can promote a bone target. Preserve a003/c001–c004, r95, Work/Claude and runtime unchanged.

## Next independent steps (only after real 54-file QA has passed)

1. Independently validate the image/stl physical coordinate frame and left/right mapping against source DICOM/NIfTI orientation and existing 72-slice CT sampling.
2. Examine mesh defect incidence across all 54, not just the initial examples.
3. Identify bone-specific candidate articular surface neighborhoods and landmarks from source geometry, with human/Blender review where required.
4. Cross-check dimensions and contact corridors against genuinely independent anatomical cohorts, not a second segmentation of the same subject.
5. Submit any candidate HGPT coordinate and neutral-pose proposals separately, preserving source/target measurement definitions and blocker flags.

**This branch's purpose is independent source evidence and engineering QA, not a completed skeleton.**
