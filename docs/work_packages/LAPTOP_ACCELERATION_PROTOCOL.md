# ORIGINAL v1 laptop acceleration protocol

Purpose: minimise Claude laptop setup/recovery overhead while preserving the existing
authority, provenance and fail-closed evidence rules.

This protocol is operational convenience only. It does not replace the master plan,
O4 handoff, generated status or execution orchestration.

## 1. Start a laptop session

Preferred command:

```bat
RUN_ORIGINAL_V1_CLAUDE_START.bat
```

It runs, in order:

1. model session preflight;
2. evidence-derived next-action selector;
3. read-only cross-phase execution plan;
4. compact live Claude session brief.

It never launches Blender or starts the selected modelling command automatically.

The brief includes:

- exact branch/HEAD;
- current candidate and SHA;
- phase/subphase;
- blocker and strict-R2-regression counts;
- selected execution node;
- exact next work command;
- support tooling relevant to that node;
- non-negotiable protections;
- end-of-session commands.

If any start check disagrees with the live state, stop rather than using stale work
instructions.

### Blender smoke gate

`RUN_ORIGINAL_V1_CLAUDE_START.bat` now runs `RUN_ORIGINAL_V1_BLENDER_SMOKE.bat`
after repository preflight. The smoke check opens the current complete candidate in
Blender background/factory-startup mode and verifies the candidate hash/manifest,
candidate-only scene marker, canonical 63-bone v4 rig, single owned body mesh,
evaluated mesh availability, NumPy/BVHTree APIs and absence of linked Blender
libraries. It never saves the Blend. A smoke failure blocks the start wrapper before
the expensive modelling command runs.

## 2. Execute only the selected work

The actual modelling command remains separate.

At the current prepared state the expected command is:

```bat
RUN_ORIGINAL_V1_R30.bat
```

but the generated selector/orchestrator controls the real answer at runtime.

Do not:

- work from main;
- force-push;
- overwrite a candidate/evidence path;
- modify V15f;
- copy third-party/V-series implementation data;
- move R2;
- change the canonical-v4 frozen structure, stress poses or thresholds without
  explicit authority;
- merge the model branch wholesale into the runtime branch.

## 3. Close a complete candidate

For a newly completed numbered candidate:

```bat
RUN_ORIGINAL_V1_CANDIDATE_CLOSE.bat <rN>
```

This checks:

- candidate manifest hash/identity;
- full merged pose evidence;
- every declared comparison baseline;
- comparison evidence hashes;
- ledger classification/state/reason;
- optional local Blend hash if present;
- existing review-package identities.

A successful result is:

`EVIDENCE_CLOSED`

That means the candidate evidence package is coherent. It does **not** mean the
candidate passed all gates or was accepted.

## 4. Review-package state

Use:

```bat
RUN_ORIGINAL_V1_REVIEW_PACKAGE.bat <rN>
```

It indexes only already-existing, hash-verified real review images and comparison
boards.

If there is no review capture yet it reports:

`NO_REVIEW_CAPTURE_YET`

and points to the existing milestone-review command. Routine review remains
non-blocking.

No image is generated or altered by this packager.

## 5. Combined candidate handoff

Use:

```bat
RUN_ORIGINAL_V1_CANDIDATE_HANDOFF.bat <rN>
```

It combines:

- candidate evidence closure;
- review-package state;
- local Blend inventory identity;
- current generated phase/subphase;
- blocker counts;
- evidence-selected next action.

A successful result is:

`HANDOFF_READY`

This is handoff readiness only, not candidate acceptance.

## 6. Local Blend safety

Check local candidate files:

```bat
RUN_ORIGINAL_V1_BLEND_INVENTORY.bat
```

It hashes every local numbered candidate Blend and checks:

- adjacent manifest;
- manifest candidate filename;
- manifest SHA;
- ledger SHA when the candidate is already in the ledger;
- current complete candidate presence;
- incomplete candidate presence.

Missing current/incomplete Blends are explicit identity gaps.

### Optional local recovery copy

Because Blend binaries remain local under project policy, a deliberate local
recovery copy can be useful before long sessions or battery-sensitive work:

```bat
RUN_ORIGINAL_V1_LOCAL_BACKUP.bat <fresh-directory-outside-repo>
```

The destination must:

- be outside the repository;
- not already exist.

The command copies only:

- current complete candidate Blend + adjacent manifest;
- any incomplete candidate Blend + adjacent manifest;
- small status/handoff/orchestration context files.

All copied Blend/manifest bytes are re-hashed after copy.

This is **local recovery only**:

- no network;
- no upload;
- no production evidence;
- no source deletion;
- no automatic restore.

## 7. End a laptop session

Preferred read-only summary sequence:

```bat
RUN_ORIGINAL_V1_CLAUDE_END.bat [rN]
```

If a revision is supplied it first runs the candidate handoff summary.

It then runs:

1. concise progress;
2. local Blend inventory;
3. session-close safety checker.

A safe final state is either:

- `READY_TO_END_SESSION`; or
- `PARTIAL_WORK_PRESERVED`.

Anything else prints exact blockers/actions.

The session-close checker now also requires the current complete candidate Blend
to exist locally and match its adjacent manifest.

## 8. Phone-friendly status

Use:

```bat
RUN_ORIGINAL_V1_PROGRESS.bat
```

It reports actual roadmap state separately from prepared infrastructure and does not
invent a synthetic completion percentage.

## 9. Partial Blender work

If the laptop/usage window ends during a new candidate:

- preserve the numbered Blend;
- preserve/create its exact manifest without overwriting history;
- record it as incomplete in the existing evidence/handoff flow;
- do not call it complete;
- run the session-close checker.

`PARTIAL_WORK_PRESERVED` is a valid safe session end.

## 10. Current project boundary

All of these commands reduce context switching, evidence bookkeeping and laptop
recovery risk. None replaces the remaining real Blender work.

Current prepared expectation remains:

- r29;
- Phase 3B;
- next actual modelling experiment r30.

Live generated state always wins over this prose.
