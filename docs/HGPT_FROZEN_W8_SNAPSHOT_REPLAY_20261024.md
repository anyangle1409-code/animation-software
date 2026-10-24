# Frozen W8 snapshot render replay — 24 October 2026

**Status: native replay40078981970 PASS1/1 with13 cloud checks; main diagnostics40078883271 PASS7/7 with243 tests. No model repair or anatomical approval.**

The source native run40078234201 passed7/7 jobs and retained8 evaluated NPZ snapshots in artifact12553804248. Its pose artifact12554635454 contains the paired exact native render manifest. Both ZIPs and all other7 source-run ZIPs were independently SHA256-matched; per-member hashes are in `recovery_20261023/cloud_verification_20261024_run40078234201.json`.

Pin: `recovery_20261023/w8_control_snapshot_replay_source_v1.json` specifies exact run, both artifact IDs, both ZIP hashes, source commit/model SHA and native manifest SHA `f474ae8cc8b6a4c89b491f29f981005402de97b8e371a9d5a0e92e9ad841dfb9`.

New workflow `.github/workflows/phone-control-snapshot-replay.yml` retrieves only those snapshot/report artifacts. Before rendering, `scripts/control_snapshot_replay/verify.py` requires the pinned manifest hash, exact W8 unapproved provenance, samples0/6, four conditions and every snapshot's native NPZ hash. Native geometry validation remains the renderer's separate task. No .blend is opened or saved, no rig loaded, no pose recipe or benchmark rerun by this workflow. Byte identity never grants anatomical acceptance.

The renderer now accepts finite `--exposure` and positive finite `--light-energy`. Defaults preserve the previous native display; replay selects exposure0.25/light90 to improve diagnostic readability. Camera plans, evaluated vertices, topology, conditions and32-sample AgX rendering remain otherwise fixed. First native Standard images were overexposed; revised AgX low-light images restored highlight detail but lower-position views remained dark. This replay tests balanced display lighting without changing underlying geometry. Visual QA still required after cloud execution.

Seven synthetic verifier tests cover correct8-file identity, modified/missing/extra snapshots, wrong manifest/model/approval, wrong samples and duplicate conditions. Two CLI guards were observed failing before adding render options; all243 standard diagnostics and7 replay guards now pass. Real archived snapshot verification also passes8/8 in the cloud workspace. Independent code review found no remaining workflow/verifier issues; native replay is not inferred from that review.

Workflow push filters are isolated to its own YAML, verifier folder and pin JSON. A renderer-code edit remains covered by the existing main workflow, while changing this replay's lighting arguments or source pin can rerender without repeating all model inspection jobs. Both workflows may run for this initial renderer-option implementation; future replay-only changes use the independent lane.

No body/muscle geometry, skin weights, skeleton, sources, production, Claude branches, PT-App, PT_MODEL_VERSION1.0, permanent muscle IDs, muscle attachments or highlighting changed.46 landmarks remain unbound;0/19 generic motions approved. Comparison images are diagnostic conditions, not new production candidates or accepted fixes.

## Cloud replay verified

Initial replay40078883281 failed before rendering because exact-ID artifact downloads were extracted into named subdirectories. Fix commit `8bfe51dae658e0e8cafed083edc47af059a653e9` explicitly flattens both downloads. That failed run remains failed; it was not model corruption or an anatomical test.

Replay40078981970 succeeded1/1, ran7 byte-verifier +6 camera/CLI checks, verified all8 NPZs, and rendered24 images/6 sheets. Paired snapshot/vertex-buffer hashes and camera plans match the frozen native source exactly. Artifact12554691427 SHA256 `a21e3ccaeeb282b89f0a13bae8311a4177c8633650062609d3feb8f48fbbdb24` independently matched; all member hashes and final visual QA in `recovery_20261023/cloud_verification_20261024_replay40078981970.json`. All six sheets visually inspected; two saved for phone review. No source .blend was opened, no pose recomputed, no anatomical/repair approval granted.
