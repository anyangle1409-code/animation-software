# Phase 7 garment scene / authoring protocol

Prepared only; Phase 7 remains NOT STARTED.

This package closes the remaining deterministic scene/provenance gap around the
future first-party garment. Dressed deformation/contact tools already exist; this
adds exact scene-state capture and an explicit clean-room garment operation ledger.

## Authoring record

Start from:

`ORIGINAL_V1_PHASE7_GARMENT_AUTHORING_TEMPLATE.json`

A real record must change status to `AUTHORING_EVIDENCE_COMPLETE` and bind the
exact candidate SHA.

It must explicitly state:

- independent_authorship=true;
- legacy_geometry_imported=false;
- third_party_geometry_imported=false;
- transferred_weights_or_bind_data=false;
- external_texture_or_material_content=false;
- a truthful non-empty starting_source.

Every garment operation must have a unique ID, description, tool/method, scope,
input candidate SHA, output candidate SHA, topology/weight-change flags and hashed
source evidence. Operation output must chain to the next input; the final operation
must end at the exact candidate SHA.

This is an audit trail, not permission to fabricate provenance.

## Detailed Blender scene capture

`capture_original_v1_garment_scene_blender.py` captures the actual body/garment
scene without saving it.

For both body and shorts it records:

- object/data linked-library state;
- mesh counts;
- vertex groups;
- mesh attributes;
- UV layers;
- custom-normal state when available;
- every modifier and serializable RNA property;
- explicit list of any modifier properties that could not be serialized;
- shape keys;
- shape-key drivers/targets;
- material slots;
- referenced image datablocks;
- armature binding.

It also records scene linked libraries and canonical 63-bone rig identity.

An unsupported modifier property is not silently ignored; it remains a blocking
coverage gap until reconciled.

## One-command future capture

After Phase 6 is genuinely complete and same-candidate raw body/garment evidence
exists:

```bat
RUN_ORIGINAL_V1_PHASE7_GARMENT_SCENE.bat <rN> <authoring-record.json> <raw-pair.json> <fresh-output-dir>
```

The orchestrator checks branch/live HEAD, clean tree, Phase 6 completion, candidate
bytes, latest-candidate identity, Blender/process/disk preflight, and same-candidate
authoring/raw-pair evidence.

It then writes:

- `garment_scene_capture.json`;
- `garment_scene_verification.json`.

## Evidence interpretation

The verifier refuses:

- linked scene/object/data/material/image libraries;
- wrong body/garment/rig identity;
- non-63-bone canonical rig;
- incomplete modifier property coverage;
- unavailable custom-normal state;
- incomplete shape-key/driver inventory;
- missing group/attribute inventory;
- broken garment operation lineage;
- false clean-room provenance claims;
- candidate identity drift.

An `EVIDENCE_COMPLETE` garment-scene result still has
`phase_complete=false` and `production_approved=false`.

It does not replace:

- raw garment/body pair evidence;
- static dressed clearance/intersection evidence;
- continuous dressed range evidence;
- legitimate-contact classification;
- bare/dressed equivalence;
- real review images;
- Phase 7 exit verification.

## Current boundary

Do not execute this as Phase 7 evidence on r29. Current work remains Phase 3/r30.
The tooling is prepared now solely to reduce future Claude Blender/session setup.


## Bare/dressed underlying-body equivalence

After the real Phase 7 garment exists on the exact candidate, run
`RUN_ORIGINAL_V1_PHASE7_EQUIVALENCE.bat <rN> <fresh-output-dir>`.

The Blender capture reuses the frozen 15 stress poses. For each pose it compares
the evaluated **full underlying body** with the garment hidden versus garment
visible while the body dressed-mask is disabled/absent in both states. It records
rounded vertex-coordinate hashes, rig pose-state hashes, body-metric hashes,
topology counts and exact vertex deltas.

This is an identity contract, not a new deformation tolerance. Any changed body
hash/pose/metric/nonzero vertex delta blocks equivalence and must be investigated.
The check does not assess garment clearance, contact legitimacy or appearance.
Even `IDENTICAL_UNDER_GARMENT_PRESENCE` remains Phase-7 evidence only.
