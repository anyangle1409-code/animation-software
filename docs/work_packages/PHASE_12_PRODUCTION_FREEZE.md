# PHASE 12 — PRODUCTION FREEZE / PROMOTION

PREPARED ONLY; NOT STARTED.

Phase 12 is the final controlled release boundary for
`HomeGymPT_Male_ORIGINAL_v1`. No optimiser, model-selection script, comparison
score, CI job, automated QA detector or agent may promote an asset.

The current model remains experimental and the real Blender priority remains
`RUN_ORIGINAL_V1_R30.bat`.

## Two-key release model

Phase 12 deliberately separates:

1. **technical promotion eligibility** — the existing
   `verify_original_v1_production_promotion.py` proves every named technical,
   provenance, deformation, anatomy, topology, clothing, contact, runtime, QA and
   standalone-release gate is explicitly satisfied for the same exact candidate,
   final bare/dressed exports and runtime commit; and
2. **production-freeze authorization** — an explicit owner decision bound to those
   exact bytes/commits and the exact successful promotion packet/receipt.

Neither key alone authorizes production.

The new final-freeze verifier is
`scripts/verify_original_v1_final_freeze.py`. It is non-mutating. Even a
successful result says only:

`ALL_FREEZE_PREREQUISITES_SATISFIED`

and still writes `production_approved=false`.

The actual change to a production allowlist/runtime asset pointer must happen in a
separate controlled owner-authorised release operation on the standalone runtime
track, followed by exact-SHA release re-verification and an immutable freeze record.

## Promotion receipt provenance tightened

The Phase 12 preparation also strengthens
`verify_original_v1_production_promotion.py`.

Future eligibility receipts now record:

- exact promotion-packet repository path;
- exact promotion-packet SHA-256;
- final candidate SHA-256;
- exact target runtime commit.

The final-freeze verifier refuses an eligibility receipt that does not bind the
exact promotion packet bytes it claims to have verified.

Historical receipts created before this contract are not silently upgraded. Re-run
the promotion verifier on the final packet.

## Final-freeze packet

Prepare an incomplete shape later with:

```bat
RUN_ORIGINAL_V1_FINAL_FREEZE_CHECK.bat --template ORIGINAL_V1_WORK\phase12\final_freeze_template.json
```

The real final packet must set `status=FINAL_FREEZE_PACKET` and bind:

- final candidate SHA-256;
- exact final model source commit;
- exact standalone runtime commit;
- exactly two distinct final assets: bare and dressed;
- exact promotion packet path/hash;
- exact successful promotion receipt path/hash;
- exact Phase 4, 5, 6, 7, 8, 9, 10 and 11 exit-report paths/hashes;
- exact explicit owner production-freeze authorization path/hash.

All referenced files are repository-local and content-addressed. Any changed byte
invalidates the packet until re-verified.

## Phase-exit binding

The final-freeze verifier does not trust `phase_complete=true` labels.

It re-runs the Phase 4–11 exit-contract verifier against every referenced report.

Additional final bindings:

- **Phase 9** `source_git_commit` must equal the packet's exact final model source
  commit;
- **Phase 10** target runtime commit must equal the final runtime commit;
- **Phase 11** target runtime commit must equal the final runtime commit.

This prevents a final release from mixing old model validation with a newer mesh,
or old runtime/QA evidence with a different standalone build.

The current production-control state must also independently report Phases 0–11
complete, no development failures, no strict R2 regressions, no newer incomplete
candidate and zero recomputed production deformation failures.

## Final owner records

The technical promotion packet already requires final visual:

```
OWNER ACCEPTED
```

for the exact final candidate and both final exports.

Phase 12 additionally requires a separate final record:

```
OWNER AUTHORISED PRODUCTION FREEZE
```

That record must contain:

- `actor: owner`;
- exact candidate SHA;
- exact target runtime commit;
- exact bare/dressed asset inventory;
- exact promotion-packet reference;
- exact promotion-receipt reference;
- truthful decision source;
- timezone-aware decision timestamp;
- `production_approved: false`.

The authorization record itself is permission evidence for the controlled release
operation. It is not allowed to edit or pre-claim production state.

An agent must never synthesize either owner decision from previous reviews,
silence, a successful CI run or a quality score.

## Verify without mutation

Once all real evidence exists:

```bat
RUN_ORIGINAL_V1_FINAL_FREEZE_CHECK.bat <final-freeze-packet.json> <fresh-freeze-eligibility-receipt.json>
```

The verifier re-checks:

- final asset bytes and candidate lineage;
- technical promotion packet and all gate reports;
- exact successful promotion receipt and packet hash binding;
- all Phase 4–11 exit reports;
- Phase 9 model commit;
- Phase 10/11 runtime commit;
- explicit owner freeze authorization;
- current generated production-control state;
- current development/regression state;
- recomputed `production_target` deformation gate.

It never:

- changes `production_approved`;
- changes a runtime asset allowlist;
- changes a production loader;
- merges branches;
- edits the R2 baseline;
- edits the model;
- creates an owner decision.

## Controlled release operation after eligibility

Only after a clean final-freeze eligibility receipt exists may the owner-authorised
release operation proceed.

That operation belongs on the separately verified standalone runtime branch and
must be asset-only/config-only as appropriate. Never merge this model branch's
older runtime/framework history.

After the release commit:

1. re-run standalone verification on the exact release SHA;
2. re-run browser viewport smoke on that same SHA;
3. re-run release/first-party/output/network/resource audits;
4. verify the installed/loaded final asset SHA values are the authorised bare and
   dressed bytes;
5. preserve the promotion packet, eligibility receipt, freeze packet, freeze
   eligibility receipt, owner acceptance and owner freeze authorization;
6. record the actual release commit and immutable production freeze record.

If the release commit changes afterward, its release evidence must be re-run.
If either final asset byte changes, Phase 12 eligibility is invalid and the
affected upstream evidence must be regenerated.

## Current state

Stage 12 tooling is prepared, but roadmap Phase 12 is **NOT STARTED**.

Current r29 cannot pass:

- Phase 3 is still active;
- development failures and R2 regressions remain;
- production failures remain;
- Phases 4–11 have not exited;
- the discovered live runtime checkpoint is not exact-SHA green;
- the visual-reference inventory is intentionally empty pending real captures;
- there is no final OWNER ACCEPTED record;
- there is no OWNER AUTHORISED PRODUCTION FREEZE record;
- there are no final production bare/dressed exports.

This is expected. The Phase 12 package exists now so the eventual release boundary
is deterministic and cannot be improvised during the final session.
