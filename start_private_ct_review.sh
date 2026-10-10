#!/bin/sh
# Run from any shell on macOS/Linux: sh start_private_ct_review.sh
set -eu
cd -- "$(dirname -- "$0")"
echo "Home Gym PT - private original CT anatomical review (no Claude/pip)"
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/anatomy_fit/nlm_ct_laptop_review.py --open
elif command -v python >/dev/null 2>&1; then
  python scripts/anatomy_fit/nlm_ct_laptop_review.py --open
else
  echo "Python 3 is required; no third-party Python packages are required." >&2
  exit 1
fi
