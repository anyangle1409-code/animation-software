# Live runtime discovery and evidence-harness preparation

Stage 10 GPT preparation. This package prepares the future Phase 10 runtime
integration handoff without editing the standalone runtime, copying model-branch
runtime code, activating candidate assets or claiming any runtime PASS.

The current real model/Blender priority remains `RUN_ORIGINAL_V1_R30.bat`.

## Authority discovered on 2026-10-01

The authoritative standalone branch is:

```
work/standalone-first-party-audit-20260927
```

The separate `handoff/standalone-v4-shadow-safe-20260930` branch points back to
that active branch and is not a development target.

At preparation time the live runtime branch HEAD was:

```
e3a7d915079f018acbfd8198655f623ea7831fbf
```

It was 25 commits ahead of the last fully verified checkpoint named by
`docs/CURRENT_HANDOFF.md`:

```
27ac3697d47bbcf32c9e94e674707f8e4b1eb5c3
```

Current source/contract state at the live HEAD shows canonical v4 active:

- `CANONICAL_V4_RUNTIME_CONTRACT.json: mode=v4_active`;
- `src/rig/skeleton.ts` imports `HGPT_CANONICAL_V4_ORIGINAL_BONES`;
- the `Skeleton` constructor defaults to those v4 bones;
- `canonicalSkeleton = new Skeleton()`.

Some CURRENT_HANDOFF prose still says the accepted v3 humanoid is the live
canonical skeleton. Under PROJECT_AUTHORITY, current source plus executable gates
outrank that stale prose. Do not silently use the older statement.

## Current exact-SHA runtime blocker

The latest `Standalone prep verification` for
`e3a7d915079f018acbfd8198655f623ea7831fbf` is **not green**.

Run ID: `36739619686`.

Typecheck, provenance/v4 payload tests, authority/hygiene, model anti-creep,
promotion guard, dormant ORIGINAL-v1 cutover guard and canonical-v4 coupling gate
all passed before the focused first-party foundation test step failed.

The failing file was:

`src/rig/firstPartySkeleton.parity.test.ts`

Two assertions failed because root and root/tail parity differed by 0.02 m against
the old 2e-11 parity expectation. The downstream full suite/build/audits did not
run. Browser viewport run `36739619753` was cancelled.

This package therefore records that runtime HEAD as **discovered but not an
integration-ready checkpoint**. Do not weaken the parity tests here; the runtime
track must reconcile its own v4 activation evidence and return to exact-SHA green.

## Contact semantic comparison

Stage 9 defined the model-side source semantics in
`ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.json`.

Against the runtime HEAD, six of nine source files were byte-identical. Three
legitimately diverged:

- `src/exercises/families/horizontalPress.ts`;
- `src/equipment/attach.ts`;
- `src/equipment/library.ts`.

The required contact semantics remain compatible:

- push-up Top/Bottom authored values and world-locked floor hand contacts remain;
- dumbbells are still resolved from the real evaluated hand matrix;
- runtime attachment now scales default anatomical grip offsets from active hand
  length, which is a v4 proportion adaptation rather than a separate trajectory;
- pull-up rack sockets remain fixed and body-relative while the rack itself is
  static.

Byte equality is therefore informative, not the acceptance condition. The Stage 9
semantic verifier is rerun against the exact runtime checkout. Any future semantic
drift causes a STOP.

## Read-only discovery command

Use a **separate checkout/worktree** of the standalone runtime. Do not switch the
model checkout onto the runtime branch.

From the model checkout:

```bat
RUN_ORIGINAL_V1_RUNTIME_DISCOVERY.bat "C:\path\to\standalone-runtime-checkout" "ORIGINAL_V1_WORK\runtime_discovery\trial1.json"
```

`scripts/original_v1_runtime_discovery.py` requires:

- model checkout on the isolated model branch and clean;
- runtime checkout on the active standalone branch and clean;
- both local HEADs equal their current remote branch HEADs;
- Stage 9 contact semantics verify against runtime source;
- runtime v4 contract/source agree;
- every compared source file exists and is hashed.

It writes only into a fresh path under the model repository. It never modifies the
runtime checkout.

If the runtime HEAD has changed since the prepared snapshot, CI status becomes
`UNKNOWN_FOR_NEW_HEAD` rather than inheriting an old green/failing result. Re-read
exact-SHA Actions before any later integration.

## Future real-engine evidence packet

`ORIGINAL_V1_RUNTIME_EVIDENCE_TEMPLATE.json` is an **INCOMPLETE TEMPLATE** only.

It already enumerates the required future scenarios:

- dumbbell shoulder press;
- dumbbell bicep curl;
- pull-up;
- push-up;
- air squat;
- lunge;
- bent-over row.

The first required prompt-level acceptance remains:

```
exercise: dumbbell shoulder press
```

The final packet must bind:

- exact approved model branch commit;
- exact candidate/source SHA;
- exact bare and dressed GLB SHA-256;
- verified Phase 9 exit evidence;
- exact standalone runtime branch + commit;
- exact-SHA standalone and browser gates;
- runtime v4 contract hash;
- prompt-to-exercise mapping;
- deterministic duration/config/frame times;
- real solver frames;
- real equipment transforms;
- contact/range/smoothness results;
- bare/dressed equivalence;
- export/reimport measurements;
- actual images/clips with source identities.

Do not fill the template from Blender interpolation or test fixtures. Real runtime
execution must use the runtime's own generation, IK/contact, equipment and export
paths.

## Exit boundary for this preparation stage

Stage 10 preparation is complete when the discovery contract/verifier, tests,
runner, incomplete evidence template and authority documents are committed and CI
is green on the model branch.

It does **not** make roadmap Phase 10 complete. Actual Phase 10 still waits for:

1. Phase 9 approved exact asset evidence;
2. a current live runtime HEAD with standalone verification and browser smoke green
   on that same exact SHA;
3. real runtime exercise/contact capture;
4. export/reimport round-trip evidence;
5. owner/release gates at their proper later boundaries.
