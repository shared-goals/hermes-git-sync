#!/usr/bin/env bash
# hermes-git-sync.sh — sync my-skills and commit changes in ~/my-hermes (or your repo)
# Usage:
#   hermes-git-sync.sh             — sync skills + commit + push
#   hermes-git-sync.sh --dry-run    — sync skills + show diff, no commit
#   hermes-git-sync.sh --commit-only — sync skills + commit locally, no push
#   hermes-git-sync.sh --sync-only   — sync skills only, no git at all
#
# Env: MY_HERMES_REPO (default: ~/my-hermes)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="${MY_HERMES_REPO:-$HOME/my-hermes}"
DIFF_FILE="/tmp/last-commit-full-diff.txt"
ARG="${1:-}"

# ── Python: prefer hermes venv, fall back to system python3 ──────────────────
HERMES_PYTHON="$(dirname "$(dirname "$(realpath "$(which hermes)")")")/venv/bin/python3"
if [ ! -x "$HERMES_PYTHON" ]; then
    HERMES_PYTHON="python3"
fi

cd "$REPO"

# ── Sync my-skills (user-modified and user-created skills) ───────────────────
echo "→ Syncing my-skills..."
"$HERMES_PYTHON" "$SCRIPT_DIR/sync-my-skills.py"

if [ "$ARG" = "--sync-only" ]; then
    echo "✓ Skills synced (no commit)."
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

# ── Dry run: show what would be committed ─────────────────────────────────────
if [ "$ARG" = "--dry-run" ]; then
    echo "── Staged changes (dry run) ──────────────────────────────────────────"
    git diff --cached --stat
    echo "──────────────────────────────────────────────────────────────────────"
    echo "No commit made. Run without --dry-run to commit and push."
    git reset HEAD -- . >/dev/null
    exit 0
fi

# ── Commit, optionally push ──────────────────────────────────────────────────
git commit -m "chore: sync $(date +%Y-%m-%d\ %H:%M)"

HASH=$(git rev-parse --short HEAD)

# ── Write diff (optional integration point for morning-brief etc.) ────────────
git diff HEAD~1 --stat > "$DIFF_FILE"
echo "" >> "$DIFF_FILE"
git diff HEAD~1 -- \
    SOUL.md config.yaml Makefile \
    memories/ my-skills/ patches/ \
    >> "$DIFF_FILE"

echo "✓ Diff written to $DIFF_FILE"

if [ "$ARG" = "--commit-only" ]; then
    echo "✓ Committed locally: $HASH"
    echo "Push skipped (--commit-only). Run git push after approval."
    exit 0
fi

git push
echo "✓ Synced: $HASH"
