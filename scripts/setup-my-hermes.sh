#!/usr/bin/env bash
# setup-my-hermes.sh — bootstrap a personal my-hermes git repo
# Usage: bash setup-my-hermes.sh [repo-path]
#   repo-path defaults to ~/my-hermes
set -euo pipefail

REPO="${1:-$HOME/my-hermes}"
HERMES="$HOME/.hermes"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "→ Creating repo at $REPO..."
mkdir -p "$REPO"/{memories,patches,scripts,my-skills}

# ── Copy templates ────────────────────────────────────────────────────────────
cp "$SKILL_DIR/../templates/Makefile" "$REPO/Makefile"

# ── Symlinks: repo files ← ~/.hermes ─────────────────────────────────────────
echo "→ Creating symlinks..."

symlink() {
    local target="$1" link="$2"
    if [ -L "$link" ]; then
        echo "  ~ $link already symlinked, skipping"
    elif [ -e "$link" ]; then
        echo "  ! $link exists (not a symlink) — skipping. Move it manually."
    else
        ln -s "$target" "$link"
        echo "  ✓ $link → $target"
    fi
}

symlink "$REPO/config.yaml"          "$HERMES/config.yaml"
symlink "$REPO/SOUL.md"              "$HERMES/SOUL.md"
symlink "$REPO/memories/MEMORY.md"   "$HERMES/memories/MEMORY.md"
symlink "$REPO/memories/USER.md"     "$HERMES/memories/USER.md"

# ── Copy current config files if not yet in repo ─────────────────────────────
echo "→ Copying current hermes files to repo..."
for f in config.yaml SOUL.md; do
    if [ ! -f "$REPO/$f" ] && [ -f "$HERMES/$f" ] && [ ! -L "$HERMES/$f" ]; then
        cp "$HERMES/$f" "$REPO/$f"
        echo "  ✓ copied $f"
    fi
done
for f in MEMORY.md USER.md; do
    if [ ! -f "$REPO/memories/$f" ] && [ -f "$HERMES/memories/$f" ] && [ ! -L "$HERMES/memories/$f" ]; then
        cp "$HERMES/memories/$f" "$REPO/memories/$f"
        echo "  ✓ copied memories/$f"
    fi
done

# ── .gitignore ────────────────────────────────────────────────────────────────
cat > "$REPO/.gitignore" << 'EOF'
.env
auth.json
*.key
*.pem
EOF

# ── Git init ──────────────────────────────────────────────────────────────────
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
    echo "  ~ git repo already exists, skipping init"
fi

# ── Cron ──────────────────────────────────────────────────────────────────────
CRON_CMD="0 3 * * * MY_HERMES_REPO=$REPO bash $SKILL_DIR/hermes-git-sync.sh >> /tmp/hermes-git-sync.log 2>&1"
if crontab -l 2>/dev/null | grep -qF "hermes-git-sync.sh"; then
    echo "→ Cron already registered, skipping"
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "→ Cron registered: daily sync at 03:00"
fi

echo ""
echo "✓ Done! my-hermes repo is at $REPO"
echo "  Run 'make sync' to sync skills and commit changes."
