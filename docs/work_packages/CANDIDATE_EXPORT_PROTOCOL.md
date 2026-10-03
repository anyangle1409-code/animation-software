# Revision-isolated candidate GLB export protocol

PREPARED ONLY. These tools produce EXPERIMENTAL export evidence, never approval.
The next actual deformation task remains `RUN_ORIGINAL_V1_R30.bat`; export capture
is an optional eligible evidence task, not a replacement for that experiment.

## Laptop capture

From the repository root, with the latest complete non-rejected candidate and its
exact local Blend/JSON manifest available:

```bat
RUN_ORIGINAL_V1_CANDIDATE_EXPORT.bat rN "ORIGINAL_V1_WORK/candidates/exports/rN_trial1"
```

Replace rN with the current numbered candidate. Use a fresh repository-local
folder. The runner checks live/local branch agreement, a clean tree, frozen
controls, source hashes, Blender, disk/process/power information using
`original_v1_session_preflight.py --evidence-only`. This mode does not require
optimiser dependencies or disposable r30 dump inputs. Unknown power information
is reported honestly; it is not an assurance of sufficient battery.

The existing exporter now requires explicit revision, source manifest and fresh
output arguments. Its previous no-argument invocation refuses to run. Historical
shared GLBs/manifests remain untouched. Only the owned locked rev2c rig (67 total / 66 deform bones; historical 63-bone structure plus four forearm-twist helpers), body and
existing first-party shorts are selected. Missing shorts stop the paired capture.
Unrelated objects are excluded. The armature is temporarily REST; authored
non-armature modifiers follow the recorded export_apply setting. The body mask is
applied for dressed capture and disabled for bare capture. Scene selection,
visibility, armature pose position, mask and temporary identity properties are
restored even after export failure. No Blend save, geometry, weight, rest-bone,
pose definition, baseline or gate edit is performed.

Outputs:

- `HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_rN_BARE.glb`
- `HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_rN_DRESSED.glb`
- `CANDIDATE_GLB_EXPORT.json`: schema 2, source candidate/manifest and exporter
  hashes, export hashes/bytes/settings, actual Blender version, source git commit,
  timestamp, REST scope and approval false.
- `candidate_export_verification.json`: source identity and existing structural
  GLB audit, with production approval false and no visual-review claim.

Owned mesh-node extras bind revision and source SHA inside each GLB. Export
identity and structural packaging are separate checks; neither validates clothing
motion, anatomy, grip metadata, animation continuity or production eligibility.
The script checks live/local HEAD again after capture. Changed lineage stops
verification and preserves the output for reconciliation.

## Verify existing actual exports without Blender

```bash
python scripts/original_v1_export_evidence.py rN --out-dir ORIGINAL_V1_WORK/candidates/exports/rN_trial1 --json-out ORIGINAL_V1_WORK/candidates/exports/rN_trial1/reverification_1.json
```

The verification receipt must be fresh and cannot alias a GLB or capture manifest.
Source manifest and exporter bytes must match their recorded hashes; an unavailable
local Blend is explicitly UNAVAILABLE, not verified. A present Blend must match.
If exporter code changes later, verify using a preserved checkout of the recorded
source commit with the original evidence; do not rewrite recorded hashes.
Exit 0 means identity plus structural audit passed; 1 means structural failure;
2 means invalid inputs/capture failure. No exit code constitutes phase completion.

## Failures, source bytes and review

Keep partial outputs after interruption/failure. Do not resume into, delete or
reuse that folder automatically. Reconcile the evidence and use a new folder.
A partial pair without a complete valid capture manifest is not a valid export.
Do not relabel historical GLBs as a later candidate.

Git attributes now preserve exact ORIGINAL-v1 Python source bytes across Windows
and cloud checkouts. Existing autocrlf-converted laptop files may differ from the
committed bytes. Preserve uncommitted/newer work and local candidates. Use a fresh
isolated checkout of the reconciled live commit if necessary, then verify copied
candidate bytes. Never blindly restore files or run broad renormalisation.

Tests cover pure receipt validation and mocked Blender selection/REST/restoration.
Actual Blender execution remains required on the laptop, including checking that
the installed bundled exporter retains the identity extras and correct skin/rest
transforms and dressed mask. Repeat-export determinism is unproven until measured.
No candidate export or review image was generated during this preparation stage.
Commit/push actual evidence where appropriate; review images must come from actual
candidate renders or runtime capture. Mark OWNER REVIEW pending and continue safe
work: REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Follow the master's explicit
pause exceptions. Production promotion stays exclusively in Phase 12.


New candidate export manifests bind the exact rev2c skeleton-motion lock, rig-structure SHA and rig payload. Structural GLB audit derives the expected joint count/hierarchy from that manifest-declared payload; historical manifests without a rig_payload field continue to use their historical audit payload. A new rev2c export must never be forced through the old 63-bone default.
