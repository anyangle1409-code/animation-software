# Evaluated dressed pose/contact and matched review evidence

Stage 7 GPT preparation, not Phase 7 execution/completion. This extends the raw
body/garment receipts from `GARMENT_RAW_EVIDENCE_PROTOCOL.md` into evaluated
static stress-pose evidence and matched bare-vs-dressed review images. It reuses
the authoritative frozen pose script; it does not redefine stress poses, repair
geometry, classify legitimate contact, waive hidden body defects or approve a
candidate. The current deformation action remains `RUN_ORIGINAL_V1_R30.bat`.

## Entry and exact command

Use only after a same-candidate Stage 6 `raw_pair_evidence.json` exists. Check the
LIVE model branch first, preserve newer work and run the normal evidence preflight.
Use a clean reconciled checkout with the exact local candidate Blend/JSON bytes
and a verified `BLENDER_EXE`. Then run, substituting the real repository-relative
raw pair path and a fresh trial name:

```bat
RUN_ORIGINAL_V1_DRESSED_EVIDENCE.bat rN "ORIGINAL_V1_WORK\candidates\garment_evidence\rN_trial1\raw_pair_evidence.json" trial1
```

The runner refuses dirty/stale branch state, conflicting Blender processes,
missing candidate bytes, missing raw-pair evidence and existing output folders.
It writes under `ORIGINAL_V1_WORK/candidates/dressed_evidence/rN_trialN/`; reruns
must use a fresh trial. Partial failed evidence is preserved and never overwritten.
The Blend is opened with factory startup and is never saved by this workflow.

## What the Blender capture measures

`scripts/capture_original_v1_dressed_evidence_blender.py` invokes
`pose_test_original_v1_o4_candidate_blender.py` in metrics-only mode through
`runpy`. The returned `POSES` functions are then reused directly. No second pose
implementation is introduced and the frozen pose definitions are unchanged.
Every one of the 15 stress poses records exact source identities, the original
body pose metrics, evaluated body/garment counts, raw cross-surface intersecting
face-pair count, bidirectional minimum surface distance, garment lowest-Z and
garment vertices below the fixed floor.

For clearance evaluation the body visibility mask is disabled while the garment
is evaluated, so hidden skin cannot disappear from the measurement. These are raw
geometric observations. An intersection pair is not automatically a defect, and
a small distance is not automatically an acceptable contact. Legitimate contact
still requires a later explicit classification. No new acceptance threshold is
created by this stage.

## Matched review capture

The same run creates real PNG pairs with one unchanged camera/capture key for the
bare and dressed member of every pair. Coverage includes neutral
front/rear/side/3/4, neutral waist/hem/seat close-ups, press, squat, lunge,
push-up, row, curl-handle and pull-up-bar extrema, plus waist close-ups for squat
and lunge. Bare mode shows the full underlying body; dressed mode uses the
candidate's actual mask/garment state.

`original_v1_dressed_evidence.py` verifies exact pose/view coverage, matching
capture keys, image/source hashes and candidate/rig/source identities. The
resulting `verified_dressed_evidence.json` is always `EVIDENCE_ONLY`,
`phase_complete=false`, `production_approved=false`, with owner review pending
and NON-BLOCKING.

## What remains open

This static package does **not** establish continuous dressed motion, production
clearance, acceptable-contact classification, full modifier/shape-key/custom-normal
inventory, garment authoring provenance, material/presentation quality, runtime
behaviour or owner visual acceptance. The raw Stage 6 change/surface audits remain
required, and a final Phase 7 candidate must also prove frozen-body preservation
and bare/dressed equivalence from its own operation history.

Actual laptop/Blender execution is still required. Test fixtures are never model
evidence. Do not relabel early O7 shorts or historical GLBs as Phase 7 output.
Next repo-side preparation is continuous dressed range/contact sampling with
explicit per-frame contact classification, while Phase 3 deformation remains the
actual model execution priority.
