# CP1 sternum endpoint compatibility contract and 3D notch underdetermination

10 October 2026. **NONCANONICAL SAFETY VALIDATOR**, stacked on independent PR #36; NOT a geometry revision, target candidate or accepted human skeleton. No patient CT, primary PDF, article figures, STL, body rig, animation, model weights or runtime file is imported or modified.

## Purpose

The skeleton-first programme's sternum geometry remains unresolved; three sources have different definitions, and a legacy JSON key falsely describes the Turkish 154.1 mm total as inclusive of the xiphoid. The measurement acceptance layer must reject combining values merely because they have the same units or similar numbers.

Machine-readable original source terms are stored in `ORIGINAL_V1_WORK/anatomy/sternum_endpoint_compatibility_contract_20261010.json`, bounded by immutable Git input blob IDs for the two frozen original audit files and two source recheck sidecars. Read-only first-party verifier: `scripts/anatomy_fit/sternum_endpoint_compatibility_gate.py`. Tests: `scripts/test_sternum_endpoint_compatibility_gate_20261010.py`.

## Explicitly incompatible uses

| A | B | Why a direct skeleton target comparison is invalid |
|---|---|---|
| Selthofer 2006 whole sternum 208.6 mm | Turkish 2018 combined CL 154.1 mm | The former ends at **distal xiphoid**, the latter excludes xiphoid |
| Selthofer 2006 whole sternum 208.6 mm | a003 213.226 mm Blender sternum stick | The control ends at the **xiphisternal region**, without the xiphoid; additionally not a measured osseous surface |
| Selthofer 2006 M+B **164.9 mm derived** | Turkish CT CL **154.1 mm direct** | Closest broad anatomical family, but first is an **arithmetic sum of separate group means**, second is the direct reported CL mean in a different cohort and acquisition/geometry method; difference **10.8 mm** is descriptive only |
| Thai 2022 CMM 146.02 mm | Turkish 2018 CL 154.1 mm | Explicit Thai **straight chord** is not established as an identical CT combined segment/path operator |
| Thai 2022 rib 2→3 costal facet centre distance 29.30 mm | a003 level 2→3 **Z-projection** 35.2 mm | Source physical 3D cartilage-facet centres are not proved to coincide with a003 model control points or axial components |

Cohorts: 55 Selthofer adult male sternum cadavers (2006); 97 Turkish CT male observations (2018); 104 Thai training dry male sternums (2022); a003 is a model *candidate*, **not a patient cohort**. The Thai source's training stature range 140–180 cm does not include the user's 182 cm target. The Thai paper's CC BY-NC illustrated content is **not imported into production**. These numerical observations do not constitute a commercial licensing clearance for any source CT meshes or clinical image assets.

## Constructive mathematical counterexample: three 3D distances do not produce 3D geometry

The published Thai male mean local distances between successive costal-facet centre labels are

`d23 = 29.30 mm`, `d34 = 25.20 mm`, `d45 = 19.56 mm`.

Consider *mathematical demonstration only*, not anatomy:

- A straight series of four points `(0,0,0), (d23,0,0), (d23+d34,0,0), (d23+d34+d45,0,0)`.
- A right-angled series `(0,0,0), (d23,0,0), (d23,d34,0), (d23,d34,d45)`.

Every consecutive pair has exactly the same respective distance in the two constructions, but the full 2→5 end-to-end distances differ (straight **74.06 mm** vs bent **approximately 43.52 mm**). By varying bend/torsion, infinitely many 3D arrangements remain possible even if we knew three exact within-individual distances. Real reported group means also do **not** guarantee simultaneous occurrence in any real donor.

Therefore using only these three distances cannot reconstruct rib levels 2,3,4,5 in world axes, much less 1 and 6,7, their left/right counterpart patches, disc clearance, sternoclavicular anchors, adult 182 cm stature or costal-cartilage deformation. **No geometric solver may mark CP1, joint centres or normal function validated from this contract.**

## How to use without the laptop

Run offline from the correct checkout containing PR #36:

```bash
python -m unittest discover -s scripts -p 'test_sternum_endpoint_compatibility_gate_20261010.py' -v
python scripts/anatomy_fit/sternum_endpoint_compatibility_gate.py
python scripts/anatomy_fit/sternum_endpoint_compatibility_gate.py --compare SELTHOFER2006_WHOLE TURKEY2018_CL
```

The CLI writes no files or external requests. The full report returns each forbidden pair with `REJECT_FOR_CANONICAL_TARGET`, keeps canonical approval false and explicitly demonstrates geometry underdetermination. Invalid or substituted source rows and forged population/registration readiness are refused by tests.

## Work/Blender continuation

When Work constructs a future *noncanonical* sternum proposal it must:

1. Use actual selected end point roles: jugular notch, manubriosternal junction, mesoxiphoidal/xiphisternal boundary and xiphoid tip must be distinct where the source distinguishes them.
2. Resolve the actual physical/coordinate correspondence of costal facets 1–7, each side's notch landmark and cartilage; three source scalars alone cannot do this.
3. Preserve the **original historical audit JSON without silent renaming**; propose a reviewed versioned semantic migration of `total_including_xiphoid_turkey_CT` rather than interpreting the label at face value or rewriting frozen evidence.
4. Treat adult stature, acquisition pose, source population and osteological vs CT paths as distinct.
5. Test registered 3D relative distances against scientifically matched measurements before any accepted rib/sternum frame update.
6. Preserve Claude/Work ongoing model, armature, c003/c004/a003 source and full-body motion test records while making the new source selection.

**Result of this stage:** measurement compatibility and underdetermination guards can be verified. **NOT** anatomical source endpoint and contact closure. Readiness remains **0 READY / 9 PARTIAL / 3 BLOCKED**, CP1 / Gate 6 OPEN and c005 has not been approved.
