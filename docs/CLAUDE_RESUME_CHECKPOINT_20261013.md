# Claude resume checkpoint — ORIGINAL_v1 master execution

**Machine ledger:** `docs/CLAUDE_MASTER_TASK_LEDGER_20261013.json` on `claude/master-execution-20261013`. It is the source of truth for task status.

## Where things are

| Workstream | Branch | Head | Status |
|---|---|---|---|
| Ledger / checkpoint, E1 GLB round trip, W3 proposal | `claude/master-execution-20261013` (from PR108 `bd162c50`) | see `git log` | live; E1 TESTED (CI green); A1 TESTED; W3 BLOCKED (owner + Lane G) |
| Feet C2/C3, F4 breadth C2W/C3W, F6 posed sweep | `claude/original-v1-foot-shape-20261013` | `c16ec280` | TESTED; C3 BLOCKED on owner sign-off |
| W1 shoulder guides | `claude/functional-original-shoulder-correction-20261013` (draft PR #111) | `13cea5a5` | TESTED, CI green |
| W2 correctives (diagnostic) | `claude/functional-shoulder-coupled-corrective-20261013` (draft PR #112) | `a8942ae3` | TESTED as diagnostic, CI green |
| M1/M2 benchmarks (9), W4 (rejected), K1 hinge correctives, W3-A feasibility data | `claude/movement-benchmarks-20261013` (draft PR #113) | `05a4a17f` | M1/M2/K1 TESTED, CI green through `6a6aaf9a` |
| P4 families (forearm, wrist, deadlift, push-up; 13 benchmarks), H1/H2, W3A reference drive | `claude/movement-benchmarks-20261013` (draft PR #113) | `ba05f924` | TESTED (13 native tests pass locally) |
| R1 consolidated review candidate (C5 feet + W3A + K1), validation vs a003, phone sequences; R2 = R1 + S1 shoulder relax keys; **R3 = R2 + K1 wrist-extension keys (current single candidate)** | `claude/original-v1-consolidated-review-20261014` | `7cdb2e05` | TESTED (6 + 6 + 5 native tests); NOT accepted |

- **Blender source (unchanged):** `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend`, SHA-256 `670a37bf…cbbe56`.
- **Candidates:** C2/C3 BLENDs are committed under `ORIGINAL_V1_WORK/anatomy/candidates/claude_foot_20261013/`. The W candidates are rebuilt in memory by their scripts; there are no binary outputs.

## Environment

- **Runtime:** a cloud Linux container, with Blender 5.2.1 run as a Python module: `PYTHONPATH=<bpy52> python3.13 <script>`, run from outside the script's directory.
- **Battery:** no Windows battery telemetry exists here. Protection is a commit and push after every task.
- **Not reachable:** the starter-ZIP trial BLENDs (chatgpt.com).
- **Blocked by the proxy:** PMC, DTIC and publisher sites. GitHub raw content is reachable.

## Resume procedure

1. `git fetch`; compare each branch head in the table above with the remote.
2. Read the ledger and pick the highest-priority task that is TODO or IN_PROGRESS and not BLOCKED.
3. Never redo COMPLETE or TESTED tasks. Never change the a003 skeleton or production assets.
4. Update the ledger, commit and push after each task. Post meaningful checkpoints to PR #26.

## Next unblocked

**14 Oct (late):** R4 built (owner approved all four shoulder fixes incl. the pivot): `docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R4_20261014.md`, review branch `52e375bd`. R4 is the current single review candidate. Resume point: (1) row arm-chest contact key (spine_03/upperarm 46 pairs per side), (2) posterior-axillary curl at 140-160 deg, (3) mid-range collapsed faces; then the hip fold. Check CI on `52e375bd` first.

As of 14 Oct, none. Every open item needs an owner decision, a Lane G agreement, or a primary source that is unreachable from this cloud environment:

| Item | Needs |
|---|---|
| F3 | C3 foot skeleton decision |
| F4 remainder | toe-breadth source |
| F5 / W3 / K1 shipping | runtime-contract extension (owner + Lane G) |
| A1 fibula / MC1 | soft-tissue cover source |
| Hip fold | three-body contact model |
| Thumb opposition | thumb axis source |
| E1 GLB leak | Icosphere leak is in the Lane G / Work exporter |

## Owner decisions pending

1. **C3 foot skeleton:** accept, accept with a different heel value, or keep a003 + C2.
2. **Rest-pose hand clearance:** the A-pose hand hangs almost on the thigh, so thumb/thigh contact appears in the lunge, walk and trunk rotation (M2).
3. **Thumb opposition axis:** the grip benchmark cannot oppose the thumb without a sourced axis (M2).
4. **Runtime-contract extension:** a shoulder-top helper (W3; 14 Oct feasibility data: needs a mid-elevation reference), individual toe controls (F5) and the K1 knee/elbow driven morphs all need it; Lane G must agree as well.
