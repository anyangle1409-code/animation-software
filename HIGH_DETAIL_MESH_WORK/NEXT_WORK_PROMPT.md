# GPT Work — Resume V15f After Power Restored

Power has now been restored. The laptop is plugged in and charging.

Current user-reported Work allowance:
- five-hour: 90%
- weekly: 87%

Resume from the current saved state on:

`work/v15-deep-hand-rebuild-prep-20260925`

Current remote HEAD:

`878956500bc099faa0f325ba6b82a7fa92f7aeb0`

The low-battery stop condition no longer applies.

IMPORTANT: Do NOT simply execute the old controller recommendation to “repair ring_L again”.

Three materially different legal ring_L strategies have already been exhausted and the final heartbeat records a genuine blocker:

“No visually effective repair remains under the full four-edge anchor-buffer position freeze.”

Checkpoint 004 is the protected recovery point and must remain intact.

## First action

Recover the local state and restart only the required project/controller/Blender processes.

Then locate the local files referenced by the final heartbeat:

- `V15F_RING_L_PROTECTED_BLOCKER.md`
- `reports/v15f_ring_l_unattended_stop.json`

These were referenced locally but are not currently available in the GitHub remote snapshot.

Sanitise them if necessary and push them to the prep branch so normal Chat can inspect the full evidence remotely.

Do not expose credentials, private paths, account data or unrelated files.

## Main technical task

Do not repeat any of these already-exhausted strategies:

1. fixed-boundary bridge trial
2. fixed-anchor reroute/normal trial
3. profile redistribution trial

Instead, perform a project-level blocker analysis comparing these two routes:

### Route A — constrained anchor-buffer movement

Determine whether the non-contact anchor-buffer vertices can be allowed limited candidate-only positional movement while:

- keeping every actual/direct contact vertex exactly fixed;
- keeping accepted contact coordinates bit-identical where required;
- preserving all frozen bone/hierarchy rules;
- preserving digit weights;
- preserving grip/contact semantics;
- preserving push-up/pull-up/curl contact behaviour;
- preserving all accepted production references;
- changing only the experimental V15f candidate.

Explicitly identify:
- direct-contact vertices;
- anchor-buffer-only vertices;
- why each buffer vertex was originally frozen;
- maximum legal movement if any;
- which invariants would prove this safe.

Do not weaken the rule merely because it blocks progress.

If evidence shows that buffer-only movement is genuinely safe and the original freeze was broader than necessary, create a separate experimental candidate/checkpoint and perform ONE bounded ring_L proof-of-concept.

Require:
- direct contacts exact;
- numeric proof PASS;
- visibly meaningful anatomical improvement over V13e;
- no new deformation/contact failures.

If it fails, preserve and reject it.

### Route B — upstream topology rebuild

If Route A cannot be proven safe, or if the required movement would alter genuine contact constraints, do not relax the protection.

Instead design and implement the smallest upstream topology rebuild in which the ring_L topology is reconstructed BEFORE the contact/anchor freeze is applied.

The objective is to create intrinsically better anatomical edge flow so the final protected-contact state does not lock in the existing segmented shape.

Keep this as a new experimental candidate.

Do not overwrite checkpoint 004 or V13e.

## Decision rule

Choose between Route A and Route B based on evidence, not convenience.

Prefer Route A only if it can be demonstrated that:
- direct contact invariants remain exactly intact, and
- only unnecessary buffer overconstraint is being relaxed.

Otherwise use Route B.

Do not ask the user to make this technical choice unless the evidence leaves two genuinely equivalent project-level options.

## Validation

For any new ring_L candidate:

- checkpoint first;
- run focused Blender audit;
- run `AUDIT_V15F_RING_PROOF.bat`;
- generate matched V13e comparison;
- perform visual gate;
- verify protected contacts;
- verify weights;
- verify topology invariants;
- preserve rejected attempts.

Do not continue to ring_R until ring_L has BOTH numeric PASS and visual PASS.

Do not begin Phase C.

## Remote visibility

Restart the remote heartbeat.

Publish `REMOTE_PROGRESS.md` approximately every 20 minutes while active and immediately at:

- blocker diagnosis completion;
- route selection;
- new checkpoint;
- numeric result;
- visual result;
- technical failure;
- final stop.

Keep `progress_counter` increasing.

Also update `REMOTE_STATUS.md` and handoff files on meaningful changes.

## Usage

Update the controller:

`SET_AI_BUDGET.bat work_window 90 "user reported after power restored"`

`SET_AI_BUDGET.bat work_week 87 "user reported after power restored"`

Use GPT-5.6 Sol Medium, Fast OFF unless project preflight gives a strong reason to change.

Continue independently while the work is safe, reversible and within V15f scope.

Do not stop merely to provide routine progress.

Before stopping for any reason, checkpoint and sync everything required for normal Chat to reconstruct the exact state.
