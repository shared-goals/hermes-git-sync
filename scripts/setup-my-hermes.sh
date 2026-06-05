#!/usr/bin/env bash
# setup-my-hermes.sh — bootstrap or reconcile a personal my-hermes git repo
# Idempotent: safe to run multiple times. Detects current state, fixes drift.
#
# Pattern: originals live in ~/my-hermes (git-controlled),
# symlinks point from ~/.hermes to ~/my-hermes.
#
# Usage: bash setup-my-hermes.sh [repo-path]
#   repo-path defaults to ~/my-hermes
set -euo pipefail

REPO="${1:-$HOME/my-hermes}"
HERMES="$HOME/.hermes"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "→ Reconciling my-hermes at $REPO..."
echo "  HERMES=$HERMES"
echo ""

# ── Directories ───────────────────────────────────────────────────────────────
echo "→ Ensuring directories..."
for dir in memories patches my-skills scripts hindsight migration cron; do
    if [ ! -d "$REPO/$dir" ]; then
        mkdir -p "$REPO/$dir"
        echo "  ✓ created $dir/"
    else
        echo "  ~ $dir/ exists"
    fi
done

# ── Symlinks: ~/.hermes → ~/my-hermes ────────────────────────────────────────
# Pattern: original in my-hermes, symlink in .hermes
echo ""
echo "→ Ensuring symlinks..."

symlink() {
    local target="$1" link="$2"
    if [ -L "$link" ]; then
        local current resolved_target resolved_current link_dir
        current="$(readlink "$link")"
        resolved_target="$(cd "$(dirname "$target")" 2>/dev/null && pwd)/$(basename "$target")" || resolved_target="$target"
        link_dir="$(dirname "$link")"
        if [[ "$current" = /* ]]; then
            resolved_current="$current"
        else
            resolved_current="$(cd "$link_dir" 2>/dev/null && cd "$(dirname "$current")" 2>/dev/null && pwd)/$(basename "$current")" || resolved_current="$current"
        fi
        if [ "$resolved_current" = "$resolved_target" ]; then
            echo "  ~ $link → ok"
        else
            echo "  ! $link points to $current (expected $target) — fix manually"
        fi
    elif [ -e "$link" ]; then
        echo "  ! $link exists as real file — move content to my-hermes, then symlink"
    else
        ln -s "$target" "$link"
        echo "  ✓ $link → $target"
    fi
}

# Core config files
symlink "$REPO/config.yaml"          "$HERMES/config.yaml"
symlink "$REPO/SOUL.md"              "$HERMES/SOUL.md"
symlink "$REPO/.env"                 "$HERMES/.env"

# Memory files
symlink "$REPO/memories/MEMORY.md"   "$HERMES/memories/MEMORY.md"
symlink "$REPO/memories/USER.md"     "$HERMES/memories/USER.md"

# Hindsight config
symlink "$REPO/hindsight/config.json" "$HERMES/hindsight/config.json"

# Cron jobs
symlink "$REPO/cron/jobs.json"       "$HERMES/cron/jobs.json"

# Makefile convenience
symlink "$REPO/Makefile"             "$HOME/Makefile"

# ── Copy originals into my-hermes if not yet there ───────────────────────────
echo ""
echo "→ Copying hermes files to repo (if missing)..."

copy_if_missing() {
    local src="$1" dst="$2"
    if [ ! -f "$dst" ]; then
        if [ -L "$src" ]; then
            # src is already a symlink — nothing to copy
            :
        elif [ -f "$src" ]; then
            mkdir -p "$(dirname "$dst")"
            cp "$src" "$dst"
            echo "  ✓ copied $(basename "$dst")"
        fi
    fi
}

copy_if_missing "$HERMES/config.yaml"        "$REPO/config.yaml"
copy_if_missing "$HERMES/SOUL.md"            "$REPO/SOUL.md"
copy_if_missing "$HERMES/.env"               "$REPO/.env"
copy_if_missing "$HERMES/memories/MEMORY.md" "$REPO/memories/MEMORY.md"
copy_if_missing "$HERMES/memories/USER.md"   "$REPO/memories/USER.md"
copy_if_missing "$HERMES/cron/jobs.json"     "$REPO/cron/jobs.json"

# ── .gitignore ───────────────────────────────────────────────────────────────
echo ""
echo "→ Ensuring .gitignore..."

GITIGNORE="$REPO/.gitignore"
REQUIRED_LINES=(
    ".env"
    "auth.json"
    "*.key"
    "*.pem"
    "sessions/"
    "logs/"
    "cache/"
    "__pycache__/"
    "*.pyc"
    "*.pyo"
    "hermes-agent/"
    ".DS_Store"
    "cron/jobs.json"
)

touch "$GITIGNORE"
ADDED=0
for line in "${REQUIRED_LINES[@]}"; do
    if ! grep -qxF "$line" "$GITIGNORE" 2>/dev/null; then
        echo "$line" >> "$GITIGNORE"
        echo "  + added: $line"
        ADDED=$((ADDED + 1))
    fi
done
if [ "$ADDED" -eq 0 ]; then
    echo "  ~ .gitignore up to date"
fi

# ── Git init ─────────────────────────────────────────────────────────────────
echo ""
if [ ! -d "$REPO/.git" ]; then
    echo "→ Initialising git repo..."
    cd "$REPO"
    git init -b main
    git add -A
    git commit -m "chore: initial my-hermes setup"
    echo "  ✓ git repo initialised"
    echo ""
    echo "  Next: add remote and push:"
    echo "    cd $REPO && git remote add origin <your-repo-url> && git push -u origin main"
else
    echo "~ git repo already exists"
    cd "$REPO"
    MODIFIED=$(git status --porcelain | wc -l | tr -d ' ')
    BRANCH=$(git branch --show-current)
    REMOTE=$(git remote get-url origin 2>/dev/null || echo "no remote")
    echo "  branch: $BRANCH | remote: $REMOTE | modified: $MODIFIED files"
fi

echo ""
echo "✓ Done! my-hermes repo at $REPO"
echo "  Run 'make sync' to preview snapshots, 'make git-sync' to commit and push."
