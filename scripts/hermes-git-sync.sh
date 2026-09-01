#!/usr/bin/env bash
# hermes-git-sync.sh — sync my-hermes snapshots and commit changes in ~/my-hermes (or your repo)
# Usage:
#   hermes-git-sync.sh               — sync skills/scripts + commit
#   hermes-git-sync.sh --sync-only   — sync skills/scripts only, no git at all
#
# Env: MY_HERMES_REPO (default: ~/my-hermes)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="${MY_HERMES_REPO:-$HOME/my-hermes}"
DIFF_FILE="/tmp/last-commit-full-diff.txt"
ARG="${1:-}"

# ── Python: prefer hermes venv, fall back to system python3 ──────────────────
HERMES_BIN="$(command -v hermes 2>/dev/null || true)"
if [ -n "$HERMES_BIN" ]; then
    HERMES_PYTHON="$(dirname "$(dirname "$(realpath "$HERMES_BIN")")")/venv/bin/python3"
fi
if [ ! -x "${HERMES_PYTHON:-}" ]; then
    HERMES_PYTHON="python3"
fi

cd "$REPO"

# ── Sync my-hermes snapshots (skills + scripts) ─────────────────────────────
echo "→ Syncing my-hermes snapshots..."
"$HERMES_PYTHON" "$SCRIPT_DIR/sync-my-hermes.py"

if [ "$ARG" = "--sync-only" ]; then
    echo "✓ Skills/scripts synced (no commit)."
    exit 0
fi

# ── Safety check ─────────────────────────────────────────────────────────────
if git diff -- memories/ config.yaml | grep -qE '^\+[^+].*(secret|api_key|password\s*[:=]\s*\S{6,})'; then
    echo "⛔ Possible secrets detected — aborting." >&2
    exit 1
fi

# ── Stage all changes ─────────────────────────────────────────────────────────
git add -A
if git diff --cached --quiet; then
    echo "✓ Nothing to commit."
    echo "No changes." > "$DIFF_FILE"
    exit 0
fi

# ── Commit ───────────────────────────────────────────────────────────────────
git commit -m "chore: sync $(date +%Y-%m-%d\ %H:%M)"

HASH=$(git rev-parse --short HEAD)

# ── Write diff (optional integration point for morning-brief etc.) ────────────
git diff HEAD~1 --stat > "$DIFF_FILE"
echo "" >> "$DIFF_FILE"
git diff HEAD~1 -- \
    SOUL.md config.yaml Makefile \
    memories/ my-skills/ scripts/ patches/ \
    >> "$DIFF_FILE"

echo "✓ Diff written to $DIFF_FILE"

echo "✓ Synced: $HASH"
