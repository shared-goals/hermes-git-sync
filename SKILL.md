---
name: hermes-git-sync
description: Version-control your Hermes config, memories, and skills in a personal git repo. Tracks user-modified and user-created skills with diffs against upstream bundled versions.
triggers:
  - "sync hermes"
  - "hermes git sync"
  - "backup hermes"
  - "commit config"
  - "save settings"
  - "setup my-hermes"
  - "skills-sync"
  - "sync skills"
  - "git-sync"
---

# Hermes Git Sync

A pattern for versioning your Hermes Agent personalisation in a separate git repo.

**What gets versioned:** `config.yaml`, `SOUL.md`, `memories/`, your skills, local patches.  
**What stays out:** bundled skills, `.env`, `auth.json` — anything Hermes manages directly.

See `references/repo-structure.md` for the full pattern explanation.

## Setup (first time)

```bash
bash ~/.hermes/skills/devops/hermes-git-sync/scripts/setup-my-hermes.sh ~/my-hermes
cd ~/my-hermes
git remote add origin <your-repo-url>
git push -u origin main
```

`setup-my-hermes.sh` creates the repo structure, symlinks `~/.hermes/` files, registers a daily cron.

Copy `templates/Makefile` into your repo for convenient shortcuts.

## Daily sync

## Usage

```bash
make git-sync         # sync skills + commit + push
make git-sync-dry     # preview changes without committing
make skills-sync      # sync my-skills snapshot only, no commit — inspect changes in IDE
```

`--sync-only` skips git entirely — useful for inspecting skill changes without staging anything:

```bash
MY_HERMES_REPO=~/my-hermes bash ~/.hermes/skills/devops/hermes-git-sync/scripts/hermes-git-sync.sh --sync-only
```

The script writes `/tmp/last-commit-full-diff.txt` after each commit — useful as input
for other routines (morning-brief, summary crons, etc.).

## Skill storage architecture

```
~/.hermes/skills/              ALL skills: bundled + modified + user-created
~/.hermes/hermes-agent/skills/ bundled source (hermes manages)
~/my-hermes/my-skills/         git mirror: only your skills, MIRRORS category structure
  ├── devops/
  │   └── hermes-git-sync/     modified bundled
  │       └── bundled.diff     ← what changed vs upstream
  ├── github/
  │   └── github-auth/
  ├── morning-brief/            user-created (no category, lives at root)
  └── ...
```

`sync-my-skills.py` reads `.bundled_manifest` (MD5 hashes) to detect modifications.  
No `external_dirs` needed — custom skills live directly in `~/.hermes/skills/`.

## Critical rules

- **Always show `git diff --stat` and wait for explicit confirmation before committing** — never commit silently. This applies to ALL paths: running the sync script, direct `git commit` via terminal, Makefile targets, or any other mechanism. There is no exception for "small" changes. `make git-sync-dry` exists specifically to create a technical barrier — use it before `make git-sync`. This rule was violated multiple times in one session; the `--dry-run` flag was added as a structural fix.
- **Never commit secrets** — script checks for sensitive patterns in `memories/` and `config.yaml`.

## Pitfalls

- **Curator duplication** — Curator can create bundled skill copies in `~/.hermes/skills/` that appear as "user-created". Detect with `make sync-skills` and look for unexpected names. Delete dupes before committing.
- **Script portability** — use `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` at the top of any script that calls sibling scripts. Hardcoded paths break when the skill moves or is cloned. Both `hermes-git-sync.sh` and `setup-my-hermes.sh` use this pattern.
- **MY_HERMES_REPO env var** — scripts use `MY_HERMES_REPO` (default: `~/my-hermes`). Set it if your repo lives elsewhere.
- **Python version** — `hermes-git-sync.sh` auto-detects the hermes venv python (`~/.hermes/hermes-agent/venv/bin/python3`, currently 3.11) and falls back to system `python3` only if the venv is missing.
- **Cron fires at wrong time** — hermes cron schedules use **local system time** (not UTC). `0 8 * * *` fires at 8am local. Verify with `hermes cron list` — check `Next run` timestamp with timezone offset. A schedule `0 4 * * *` on UTC+4 fires at 4am Samara, not 8am.
- **git remote still shows old name after repo rename** — `git remote -v` may still point to `shag-hermes.git`; update with `git remote set-url origin <new-url>`.
- **grep false positive in secrets check** — scope grep to data files: `git diff -- memories/ config.yaml | grep -qE '^\+[^+].*(secret|password|api_key)'`.
