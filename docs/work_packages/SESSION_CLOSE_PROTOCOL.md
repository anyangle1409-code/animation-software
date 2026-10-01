# ORIGINAL v1 laptop session-close protocol

Use this at the end of every Claude/Blender laptop session:

```bat
RUN_ORIGINAL_V1_SESSION_CLOSE.bat
```

Optional machine output:

```bat
RUN_ORIGINAL_V1_SESSION_CLOSE.bat --json
```

The checker is read-only. It never commits, pushes, fetches, deletes, saves Blender
files or changes generated state.

## Possible results

### READY_TO_END_SESSION

The model branch is correct, local/remote HEAD are synchronized, the working tree
is clean, generated status/dashboard verifies, the O4 handoff names the current
candidate and evidence-selected next action, and there is no unresolved local
candidate identity problem.

Routine pending owner review is non-blocking.

### PARTIAL_WORK_PRESERVED

A newer incomplete candidate exists, but:

- its candidate manifest exists;
- the local Blend exists;
- the Blend hash matches the manifest;
- the O4 handoff records the partial revision/recovery state;
- repository state is otherwise clean and pushed.

This means it is safe to stop the work session without pretending the candidate is
complete. Resume with the existing interrupted-run inspection/recovery tools.

The Blend binary remains local under current project policy. Hash/manifest identity
is preservation evidence, not remote backup of the binary.

### NEEDS_ATTENTION_BEFORE_ENDING

The checker found one or more conditions such as:

- local commits not pushed;
- remote branch has newer work;
- local/remote divergence is unresolved;
- working tree has uncommitted/unknown files;
- generated status is stale;
- O4 handoff does not identify current revision/next action;
- partial candidate manifest/Blend is missing or mismatched;
- a local candidate Blend lacks a matching identity manifest.

Follow the printed `closing_actions`. Never force-push or delete evidence merely
to obtain a green close status.

## What it checks

The checker reuses the real generated production-control state and inspects:

- expected model branch;
- local HEAD;
- live remote branch HEAD;
- best available local/remote ancestry relation;
- full working-tree porcelain state;
- `build_original_v1_daily_status.py --check`;
- current candidate and candidate state;
- evidence-selected next action;
- incomplete candidate revisions;
- local candidate Blend files at/current-after the active revision;
- adjacent candidate manifest hashes;
- O4 handoff coverage.

It deliberately does not make owner-review status a close blocker.

## Suggested session sequence

At session start:

```bat
RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
RUN_ORIGINAL_V1_NEXT.bat
RUN_ORIGINAL_V1_EXECUTION_PLAN.bat
```

Perform only the selected work.

Before stopping:

1. save the newest numbered Blend/checkpoint;
2. generate all evidence currently available;
3. update O4 handoff/status for complete or partial work;
4. commit relevant repository evidence;
5. re-read remote HEAD and push without force;
6. run `RUN_ORIGINAL_V1_SESSION_CLOSE.bat`.

A clean session should end with either `READY_TO_END_SESSION` or an explicitly
preserved partial state, not an ambiguous laptop-only handoff.
