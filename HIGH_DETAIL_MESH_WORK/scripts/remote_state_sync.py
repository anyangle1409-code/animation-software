"""Generate and safely publish a compact, sanitised project-state snapshot."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORTS = ROOT / "reports"
PREP_BRANCH = "work/v15-deep-hand-rebuild-prep-20260925"
APPROVED_RELATIVE_PATHS = (
    "HIGH_DETAIL_MESH_WORK/REMOTE_STATUS.md",
    "HIGH_DETAIL_MESH_WORK/REMOTE_V15F_LATEST_HANDOFF.md",
    "HIGH_DETAIL_MESH_WORK/REMOTE_PROJECT_CONTROLLER_NEXT.md",
    "HIGH_DETAIL_MESH_WORK/REMOTE_PROJECT_CONTROLLER_STATE.json",
)
OUTPUT_NAMES = tuple(Path(path).name for path in APPROVED_RELATIVE_PATHS)
SYNC_LOG = REPORTS / "project_state_sync.log"
SYNC_LOCK = REPORTS / "project_state_sync.lock"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path, default: dict | None = None) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else (default or {})
    except (OSError, ValueError, TypeError):
        return default or {}


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=120,
    )


def git_value(repo: Path, *args: str) -> str | None:
    result = run_git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else None


def process_is_running(pid: int) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def sanitise_text(value: object) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    extensions = r"blend\d?|json|md|txt|bat|py|jpg|jpeg|png|log|glb"
    text = re.sub(rf"(?i)[a-z]:\\[^,;\r\n]*?\.(?:{extensions})", "[local file]", text)
    text = re.sub(rf"(?i)[a-z]:/[^,;\r\n]*?\.(?:{extensions})", "[local file]", text)
    text = re.sub(rf"(?i)\\\\[^,;\r\n]*?\.(?:{extensions})", "[local file]", text)
    text = re.sub(rf"(?i)/(?:home|users|private|tmp|var/tmp)/[^,;\r\n]*?\.(?:{extensions})", "[local file]", text)
    text = re.sub(r"(?i)[a-z]:\\[^,;\r\n]+", "[local path]", text)
    text = re.sub(r"(?i)[a-z]:/[^,;\r\n]+", "[local path]", text)
    text = re.sub(r"(?i)\\\\[^,;\r\n]+", "[local path]", text)
    text = re.sub(r"(?i)/(?:home|users|private|tmp|var/tmp)/[^,;\r\n]+", "[local path]", text)
    text = re.sub(r"(?i)https://[^/@\s]+:[^/@\s]+@", "https://", text)
    text = re.sub(r"(?i)\b(?:token|password|secret|account[_ -]?id)\s*[:=]\s*\S+", "[redacted]", text)
    return text[:1000]


def relative_name(value: object) -> str | None:
    if not value:
        return None
    return Path(str(value).replace("\\", "/")).name


def state_from_lock(lock_path: Path, checker: Callable[[int], bool]) -> str:
    if not lock_path.exists():
        return "stopped"
    data = read_json(lock_path)
    pid = data.get("pid")
    if isinstance(pid, int):
        return "running" if checker(pid) else "stopped"
    return "unknown"


def git_worktree_summary(repo: Path) -> str:
    result = run_git(repo, "status", "--porcelain", "--untracked-files=normal")
    if result.returncode != 0:
        return "unknown"
    ignored = set(APPROVED_RELATIVE_PATHS)
    rows = []
    for line in result.stdout.splitlines():
        path = line[3:].replace("\\", "/") if len(line) > 3 else ""
        if path not in ignored:
            rows.append(line)
    if not rows:
        return "clean"
    modified = sum(1 for row in rows if not row.startswith("??"))
    untracked = sum(1 for row in rows if row.startswith("??"))
    return f"dirty ({modified} modified, {untracked} untracked)"


def project_head(repo: Path) -> str | None:
    """Return the newest non-snapshot commit, avoiding a self-referential status loop."""
    commit = git_value(repo, "rev-parse", "HEAD")
    seen: set[str] = set()
    while commit and commit not in seen:
        seen.add(commit)
        if not commit:
            return None
        subject = git_value(repo, "show", "-s", "--format=%s", commit)
        names = git_value(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
        changed = {name for name in (names or "").splitlines() if name}
        if subject != "chore: publish sanitized project state" or not changed or not changed <= set(APPROVED_RELATIVE_PATHS):
            return commit
        commit = git_value(repo, "rev-parse", f"{commit}^")
    return None


def infer_current_stage(v15f: dict) -> str:
    action = str(v15f.get("next_action") or "")
    match = re.search(r"\b(ring_[LR]|pinky_[LR]|index_[LR]|middle_[LR]|stage[_ ]?[AB])\b", action, re.I)
    return match.group(1) if match else "unknown"


def gate_lines(v15f: dict) -> tuple[str, str]:
    gates = v15f.get("gates") if isinstance(v15f.get("gates"), dict) else {}
    numeric = "none"
    visual = "none"
    for name, gate in gates.items():
        if not isinstance(gate, dict) or not gate.get("exists", gate.get("current", False)):
            continue
        label = name.replace("_proof", " proof").replace("_visual", " visual")
        status = "PASS" if gate.get("pass") is True else "FAIL" if gate.get("pass") is False else "UNKNOWN"
        if "visual" in name.lower():
            current = gate.get("current", True)
            decision = "STALE" if not current else sanitise_text(gate.get("decision") or status)
            note = sanitise_text(gate.get("notes")) if current else ""
            visual = f"{label}: {decision}" + (f" — {note}" if note else "")
        elif gate.get("current", True):
            numeric = f"{label}: {status}"
    return numeric, visual


def latest_report_paths(work: Path) -> list[str]:
    reports = work / "reports"
    candidates = []
    for pattern in ("audit_v15f*.json", "v15f*proof_gate.json", "v15f*visual_decision.json"):
        candidates.extend(reports.glob(pattern))
    unique = sorted(set(candidates), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    return [f"reports/{path.name}" for path in unique[:4]]


def collect_snapshot(
    repo: Path = REPO,
    work: Path = ROOT,
    process_checker: Callable[[int], bool] = process_is_running,
) -> dict:
    controller = read_json(work / "reports" / "project_controller_state.json")
    safe = read_json(work / "reports" / "v15f_safe_runner_state.json")
    v15f = controller.get("v15f") if isinstance(controller.get("v15f"), dict) else {}
    repository = controller.get("repository") if isinstance(controller.get("repository"), dict) else {}
    numeric, visual = gate_lines(v15f)
    candidates = sorted(work.glob("*CANDIDATE_v15f*.blend"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    checkpoints = sorted((work / "checkpoints" / "v15_manual").glob("*v15f*.blend"), key=lambda p: p.stat().st_mtime_ns)
    next_action = sanitise_text(v15f.get("next_action") or safe.get("last_action") or "Run V15F_STATUS.bat")
    reason = sanitise_text(v15f.get("reason"))
    last_error = None
    if "fail" in visual.lower():
        last_error = visual
    elif "fail" in reason.lower() or "error" in reason.lower():
        last_error = reason
    return {
        "controller_state": state_from_lock(work / "reports" / "project_controller.lock", process_checker),
        "safe_runner_state": sanitise_text(safe.get("state") or "unknown"),
        "branch": sanitise_text(git_value(repo, "branch", "--show-current") or repository.get("branch") or "unknown"),
        "head": sanitise_text(project_head(repo) or repository.get("head") or "unknown"),
        "working_tree": git_worktree_summary(repo),
        "candidate": candidates[0].name if candidates else relative_name(v15f.get("blend")) or "missing",
        "checkpoint": f"checkpoints/v15_manual/{checkpoints[-1].name}" if checkpoints else "none",
        "current_stage": infer_current_stage(v15f),
        "latest_numeric_gate": numeric,
        "latest_visual_gate": visual,
        "reports": latest_report_paths(work),
        "last_action": sanitise_text(safe.get("last_action") or next_action),
        "last_error": last_error,
        "next_action": next_action,
        "reason": reason,
        "route": sanitise_text(controller.get("route") or "unknown"),
    }


def render_snapshot_files(snapshot: dict, generated_utc: str) -> dict[str, str]:
    reports = snapshot.get("reports") or []
    report_text = ", ".join(reports) if reports else "none"
    error = snapshot.get("last_error") or "none"
    status = "\n".join([
        "# Remote project status", "",
        f"- timestamp: {generated_utc}",
        f"- controller state: {snapshot['controller_state']}",
        f"- safe-runner state: {snapshot['safe_runner_state']}",
        f"- current branch: {snapshot['branch']}",
        f"- current HEAD: {snapshot['head']}",
        f"- working-tree state: {snapshot['working_tree']}",
        f"- active V15 candidate: {snapshot['candidate']}",
        f"- latest checkpoint: {snapshot['checkpoint']}",
        f"- current digit/stage: {snapshot['current_stage']}",
        f"- latest completed numeric gate: {snapshot['latest_numeric_gate']}",
        f"- latest visual gate status: {snapshot['latest_visual_gate']}",
        f"- latest audit/report paths: {report_text}",
        f"- last meaningful action: {snapshot['last_action']}",
        f"- last meaningful error: {error}",
        f"- exact next recommended command/action: {snapshot['next_action']}", "",
    ])
    handoff = "\n".join([
        "# V15f remote handoff", "",
        f"- generated: {generated_utc}",
        f"- candidate: {snapshot['candidate']}",
        f"- checkpoint: {snapshot['checkpoint']}",
        f"- digit/stage: {snapshot['current_stage']}",
        f"- numeric gate: {snapshot['latest_numeric_gate']}",
        f"- visual gate: {snapshot['latest_visual_gate']}",
        f"- next action: {snapshot['next_action']}",
        f"- reason: {snapshot['reason'] or 'none'}", "",
        "Do not promote geometry or begin Phase C from this handoff alone.", "",
    ])
    next_md = "\n".join([
        "# Project Controller — remote next action", "",
        f"- generated: {generated_utc}",
        f"- route: {snapshot['route']}",
        f"- controller: {snapshot['controller_state']}",
        f"- safe runner: {snapshot['safe_runner_state']}",
        f"- next action: {snapshot['next_action']}",
        f"- reason: {snapshot['reason'] or 'none'}", "",
    ])
    remote_state = dict(snapshot)
    remote_state["snapshot_generated_utc"] = generated_utc
    remote_state["schema"] = 1
    return {
        "REMOTE_STATUS.md": status,
        "REMOTE_V15F_LATEST_HANDOFF.md": handoff,
        "REMOTE_PROJECT_CONTROLLER_NEXT.md": next_md,
        "REMOTE_PROJECT_CONTROLLER_STATE.json": json.dumps(remote_state, indent=2, ensure_ascii=True) + "\n",
    }


def snapshot_fingerprint(snapshot: dict) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()


def generate_snapshot(
    repo: Path = REPO,
    work: Path = ROOT,
    process_checker: Callable[[int], bool] = process_is_running,
) -> bool:
    snapshot = collect_snapshot(repo, work, process_checker)
    state_path = work / "REMOTE_PROJECT_CONTROLLER_STATE.json"
    old_full = read_json(state_path)
    old_timestamp = old_full.get("snapshot_generated_utc")
    old = dict(old_full)
    old.pop("snapshot_generated_utc", None)
    old.pop("schema", None)
    generated_utc = old_timestamp if old == snapshot and old_timestamp else utcnow()
    rendered = render_snapshot_files(snapshot, generated_utc)
    if all(
        (work / name).is_file()
        and (work / name).read_text(encoding="utf-8") == content
        for name, content in rendered.items()
    ):
        return False
    for name, content in rendered.items():
        path = work / name
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8", newline="\n")
    return True


def safe_log(message: str, reports: Path = REPORTS) -> None:
    reports.mkdir(parents=True, exist_ok=True)
    clean = sanitise_text(message)
    with (reports / "project_state_sync.log").open("a", encoding="utf-8") as handle:
        handle.write(f"[{utcnow()}] {clean}\n")


def handle_push_result(
    result: subprocess.CompletedProcess[str], automatic: bool, reports: Path = REPORTS
) -> int:
    if result.returncode == 0:
        safe_log("push succeeded", reports)
        return 0
    detail = (result.stderr or result.stdout or "push failed").strip().splitlines()[-1]
    safe_log(f"push failed: {detail}", reports)
    print(f"PROJECT_STATE_PUSH_FAILED: {sanitise_text(detail)}", file=sys.stderr)
    return 0 if automatic else result.returncode or 1


def acquire_sync_lock() -> int | None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(SYNC_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("ascii"))
        return fd
    except FileExistsError:
        try:
            owner_text = SYNC_LOCK.read_text(encoding="ascii").strip()
            owner = int(owner_text) if owner_text.isdigit() else 0
            if not process_is_running(owner):
                SYNC_LOCK.unlink()
                fd = os.open(SYNC_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode("ascii"))
                return fd
        except OSError:
            pass
        return None


def unstage_approved(repo: Path) -> None:
    run_git(repo, "reset", "--quiet", "HEAD", "--", *APPROVED_RELATIVE_PATHS)


def staged_paths(repo: Path) -> list[str]:
    result = run_git(repo, "diff", "--cached", "--name-only")
    if result.returncode != 0:
        raise RuntimeError("cannot inspect staged files")
    return [name for name in result.stdout.splitlines() if name]


def remote_branch_head(repo: Path) -> tuple[str | None, subprocess.CompletedProcess[str]]:
    result = run_git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{PREP_BRANCH}")
    if result.returncode != 0:
        return None, result
    row = result.stdout.strip().splitlines()
    return (row[0].split()[0] if row else None), result


def outgoing_paths(repo: Path, remote_head: str | None, local_head: str) -> set[str]:
    revision = local_head if not remote_head else f"{remote_head}..{local_head}"
    commits_result = run_git(repo, "rev-list", revision)
    if commits_result.returncode != 0:
        raise RuntimeError("cannot inspect outgoing commit list")
    paths: set[str] = set()
    for commit in commits_result.stdout.splitlines():
        names_result = run_git(
            repo, "diff-tree", "-m", "--root", "--no-commit-id", "--name-only", "-r", commit
        )
        if names_result.returncode != 0:
            raise RuntimeError(f"cannot inspect outgoing commit {commit[:12]}")
        paths.update(name for name in names_result.stdout.splitlines() if name)
    return paths


def sync_snapshot(automatic: bool = False) -> int:
    lock_fd = acquire_sync_lock()
    if lock_fd is None:
        safe_log("sync skipped: another sync is active")
        return 0 if automatic else 2
    os.close(lock_fd)
    staged_by_sync = False
    try:
        branch = git_value(REPO, "branch", "--show-current")
        if branch != PREP_BRANCH:
            safe_log(f"sync refused on branch {branch or 'unknown'}")
            print(f"PROJECT_STATE_SYNC_REFUSED: expected {PREP_BRANCH}, found {branch or 'unknown'}", file=sys.stderr)
            return 0 if automatic else 2

        pre_staged = staged_paths(REPO)
        if pre_staged:
            safe_log("sync refused: pre-existing staged files")
            print("PROJECT_STATE_SYNC_REFUSED: pre-existing staged files were left untouched", file=sys.stderr)
            return 0 if automatic else 2

        generate_snapshot(REPO, ROOT)
        remote_head, remote_check = remote_branch_head(REPO)
        if remote_check.returncode != 0:
            return handle_push_result(remote_check, automatic)
        pre_commit_head = git_value(REPO, "rev-parse", "HEAD")
        if not pre_commit_head:
            safe_log("sync refused: cannot resolve local HEAD")
            return 0 if automatic else 2
        preexisting_outgoing = outgoing_paths(REPO, remote_head, pre_commit_head)
        if preexisting_outgoing - set(APPROVED_RELATIVE_PATHS):
            safe_log("sync refused: outgoing commits contain non-status files")
            print("PROJECT_STATE_SYNC_REFUSED: push implementation or other project commits separately first", file=sys.stderr)
            return 0 if automatic else 2

        if (
            git_value(REPO, "branch", "--show-current") != PREP_BRANCH
            or git_value(REPO, "rev-parse", "HEAD") != pre_commit_head
        ):
            safe_log("sync refused: branch or HEAD changed before staging")
            print("PROJECT_STATE_SYNC_REFUSED: branch or HEAD changed before staging", file=sys.stderr)
            return 0 if automatic else 2

        staged_by_sync = True
        add = run_git(REPO, "add", "--", *APPROVED_RELATIVE_PATHS)
        if add.returncode != 0:
            unstage_approved(REPO)
            staged_by_sync = False
            safe_log(f"stage failed: {add.stderr or add.stdout}")
            return 0 if automatic else add.returncode or 1

        staged = staged_paths(REPO)
        unexpected = sorted(set(staged) - set(APPROVED_RELATIVE_PATHS))
        if unexpected:
            unstage_approved(REPO)
            staged_by_sync = False
            safe_log("sync refused: staged allowlist check failed")
            print("PROJECT_STATE_SYNC_REFUSED: staged allowlist check failed", file=sys.stderr)
            return 0 if automatic else 2

        if staged:
            if (
                git_value(REPO, "branch", "--show-current") != PREP_BRANCH
                or git_value(REPO, "rev-parse", "HEAD") != pre_commit_head
            ):
                unstage_approved(REPO)
                staged_by_sync = False
                safe_log("sync refused: branch or HEAD changed before commit")
                print("PROJECT_STATE_SYNC_REFUSED: branch or HEAD changed before commit", file=sys.stderr)
                return 0 if automatic else 2
            commit = run_git(REPO, "commit", "-m", "chore: publish sanitized project state", "--", *APPROVED_RELATIVE_PATHS)
            if commit.returncode != 0:
                unstage_approved(REPO)
                staged_by_sync = False
                safe_log(f"commit failed: {commit.stderr or commit.stdout}")
                return 0 if automatic else commit.returncode or 1
            staged_by_sync = False

        local_head = git_value(REPO, "rev-parse", "HEAD")
        current_branch = git_value(REPO, "branch", "--show-current")
        current_head = git_value(REPO, "rev-parse", "HEAD")
        if current_branch != PREP_BRANCH or not local_head or current_head != local_head:
            safe_log("sync refused: branch or HEAD changed during publication")
            print("PROJECT_STATE_SYNC_REFUSED: branch or HEAD changed during publication", file=sys.stderr)
            return 0 if automatic else 2
        pushed_files: list[str] = []
        if remote_head and local_head and remote_head != local_head:
            names = git_value(REPO, "diff", "--name-only", f"{remote_head}..{local_head}") or ""
            pushed_files = [name for name in names.splitlines() if name]

        outgoing = outgoing_paths(REPO, remote_head, local_head)
        if outgoing - set(APPROVED_RELATIVE_PATHS):
            safe_log("sync refused: outgoing allowlist check failed")
            print("PROJECT_STATE_SYNC_REFUSED: outgoing allowlist check failed", file=sys.stderr)
            return 0 if automatic else 2

        push = run_git(REPO, "push", "origin", f"{local_head}:refs/heads/{PREP_BRANCH}")
        result = handle_push_result(push, automatic)
        if push.returncode == 0:
            verified_head, verify = remote_branch_head(REPO)
            if verify.returncode != 0 or verified_head != local_head:
                safe_log("push verification failed")
                print("PROJECT_STATE_PUSH_FAILED: remote verification mismatch", file=sys.stderr)
                return 0 if automatic else 1
            print(f"PUSHED_COMMIT {local_head}")
            if pushed_files:
                for path in pushed_files:
                    print(f"PUSHED_FILE {path}")
            else:
                print("PUSHED_FILE none (remote already current)")
        return result
    except Exception as exc:
        if staged_by_sync:
            try:
                unstage_approved(REPO)
            except Exception:
                pass
        safe_log(f"sync error: {type(exc).__name__}: {exc}")
        print(f"PROJECT_STATE_SYNC_ERROR: {type(exc).__name__}", file=sys.stderr)
        return 0 if automatic else 1
    finally:
        SYNC_LOCK.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--automatic", action="store_true")
    args = parser.parse_args()
    if args.sync:
        return sync_snapshot(automatic=args.automatic)
    changed = generate_snapshot()
    print("PROJECT_STATE_SNAPSHOT_UPDATED" if changed else "PROJECT_STATE_SNAPSHOT_UNCHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
