# Claude resume checkpoint — ORIGINAL_v1 master execution

**Machine ledger:** `docs/CLAUDE_MASTER_TASK_LEDGER_20261013.json` on `claude/master-execution-20261013`. It is the source of truth for task status.

## Where things are

| Workstream | Branch | Head | Status |
|---|---|---|---|
| Ledger / checkpoint | `claude/master-execution-20261013` (from PR108 `bd162c50`) | see `git log` | live |
| Feet C2/C3 | `claude/original-v1-foot-shape-20261013` | `eb7716cd` | C2 TESTED; C3 BLOCKED on owner sign-off |
| W1 shoulder guides | `claude/functional-original-shoulder-correction-20261013` (draft PR #111) | `13cea5a5` | TESTED, CI green |
| W2 correctives | `claude/functional-shoulder-coupled-corrective-20261013` | `69a2f344` (local until pushed) | IN_PROGRESS |

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

## Owner decisions pending

1. **C3 foot skeleton:** accept, accept with a different heel value, or keep a003 + C2.
2. **Runtime-contract extension:** a shoulder-top helper (W3) and individual toe controls (F5) both need it; Lane G must agree as well.
