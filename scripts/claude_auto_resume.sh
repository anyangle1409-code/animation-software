#!/usr/bin/env bash
set -u

SESSION_URL="${1:-https://claude.ai/code/session_01EPKohHG29Xe8qKuNMT5Fv9}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="${PROMPT_FILE:-$SCRIPT_DIR/CLAUDE_AUTO_RESUME_PROMPT.txt}"
RETRY_MINUTES="${RETRY_MINUTES:-5}"
MAX_HOURS="${MAX_HOURS:-3}"
LOG_DIR="$SCRIPT_DIR/../ORIGINAL_V1_WORK/anatomy/automation"
LOG_FILE="$LOG_DIR/claude_auto_resume.log"

mkdir -p "$LOG_DIR"
log(){ printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')" "$*" >> "$LOG_FILE"; }

command -v claude >/dev/null 2>&1 || { log "ERROR claude CLI not found in PATH"; exit 3; }
[[ -f "$PROMPT_FILE" ]] || { log "ERROR prompt missing: $PROMPT_FILE"; exit 2; }

PROMPT="$(cat "$PROMPT_FILE")"
DEADLINE=$(( $(date +%s) + MAX_HOURS*3600 ))
log "Watcher started; retry every $RETRY_MINUTES minutes for up to $MAX_HOURS hours"

while [[ "$(date +%s)" -lt "$DEADLINE" ]]; do
  OUT="$(claude --cloud "$SESSION_URL" -p "$PROMPT" 2>&1)"
  CODE=$?

  if [[ $CODE -eq 0 ]]; then
    log "SUCCESS continuation prompt queued. $(printf '%s' "$OUT" | tr '\n' ' ')"
    exit 0
  fi

  if printf '%s' "$OUT" | grep -Eiq '(usage|rate.?limit|limit.*reset|reset.*limit|capacity|quota)'; then
    log "WAIT usage unavailable; retrying"
  else
    log "WARN exit $CODE: $(printf '%s' "$OUT" | tr '\n' ' ')"
  fi

  sleep $(( RETRY_MINUTES*60 ))
done

log "TIMEOUT without successful queue"
exit 4
