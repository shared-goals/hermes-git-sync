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

## Community skill

Published at: https://github.com/shared-goals/hermes-git-sync

Users can install via tap:
```bash
hermes skills tap add shared-goals/hermes-git-sync
hermes skills install hermes-git-sync
```

When publishing a skill publicly: use a dedicated public repo per skill (KISS/YAGNI — not a monorepo of skills). Repo name = skill name. Org: `shared-goals/`. Cross-reference related skills via "Works well with" in README — don't merge them. Use SSH remote (`git@github.com:...`) for push, HTTPS fails in terminal without interactive auth.

**Related skills worth publishing together:** `hermes-update-workflow` (`shared-goals/hermes-update-workflow`) — cross-link both READMEs with "works well with". The template Makefile covers both: `update` and `check-update` targets call `hermes-update-workflow` scripts.

## Critical rules

- **Always show `git diff --stat` and wait for explicit confirmation before committing** — never commit silently. This applies to ALL paths: running the sync script, direct `git commit` via terminal, Makefile targets, or any other mechanism. There is no exception for "small" changes. `make git-sync-dry` exists specifically to create a technical barrier — use it before `make git-sync`. This rule was violated multiple times in one session; the `--dry-run` flag was added as a structural fix.
- **Never commit secrets** — script checks for sensitive patterns in `memories/` and `config.yaml`.

## Script ownership principle

Scripts belong in skills, not in `~/my-hermes/scripts/`. The Makefile calls scripts via skill paths:

```makefile
GIT_SYNC_SCRIPTS := $(HOME)/.hermes/skills/devops/hermes-git-sync/scripts
UPDATE_SCRIPTS   := $(HOME)/.hermes/skills/devops/hermes-update-workflow/scripts
```

`~/my-hermes/scripts/` is legacy — if it exists, delete it. `apply-patches.sh` lives in `hermes-update-workflow`, `setup-my-hermes.sh` lives here. KISS/DRY.

The template `Makefile` (in `templates/`) is the public/generic version — **no user-specific targets** (e.g. `voice-memos`). The user's real `~/my-hermes/Makefile` extends it with machine-specific targets. When updating the template, copy it to `~/my-hermes/Makefile` and re-add any user-specific targets manually — do NOT blindly overwrite.

## Pitfalls

- **`hermes skills reset` removes from manifest** — `hermes skills reset <name>` clears the manifest entry, so `sync-my-skills.py` treats the skill as user-created (no `bundled.diff`, always copied). Fix: after reverting a skill to bundled state, re-add its hash manually:
  ```python
  import hashlib
  from pathlib import Path
  skill_dir = Path.home() / ".hermes/hermes-agent/skills/<category>/<name>"
  hasher = hashlib.md5()
  for fpath in sorted(skill_dir.rglob("*")):
      if fpath.is_file():
          rel = fpath.relative_to(skill_dir)
          hasher.update(str(rel).encode()); hasher.update(fpath.read_bytes())
  manifest = Path.home() / ".hermes/skills/.bundled_manifest"
  with open(manifest, "a") as f: f.write(f"<name>: {hasher.hexdigest()}\n")
  ```
  Then run `make skills-sync` — skill should appear as `− removed` from my-skills.
- **Curator duplication** — Curator can create bundled skill copies in `~/.hermes/skills/` that appear as "user-created". Detect with `make sync-skills` and look for unexpected names. Delete dupes before committing.
- **Script portability** — use `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` at the top of any script that calls sibling scripts. Hardcoded paths break when the skill moves or is cloned. Both `hermes-git-sync.sh` and `setup-my-hermes.sh` use this pattern.
- **MY_HERMES_REPO env var** — scripts use `MY_HERMES_REPO` (default: `~/my-hermes`). Set it if your repo lives elsewhere.
- **Python version** — `hermes-git-sync.sh` auto-detects the hermes venv python (`~/.hermes/hermes-agent/venv/bin/python3`, currently 3.11) and falls back to system `python3` only if the venv is missing.
- **Cron fires at wrong time** — hermes cron schedules use **local system time** (not UTC). `0 8 * * *` fires at 8am local. Verify with `hermes cron list` — check `Next run` timestamp with timezone offset. A schedule `0 4 * * *` on UTC+4 fires at 4am Samara, not 8am.
- **git remote still shows old name after repo rename** — `git remote -v` may still point to `shag-hermes.git`; update with `git remote set-url origin <new-url>`.
- **`make` targets fail without ~/Makefile symlink** — Hermes Agent's terminal runs with `~` as cwd. `make git-sync` only resolves if `~/Makefile` exists. `setup-my-hermes.sh` creates `~/Makefile → ~/my-hermes/Makefile` automatically. If the symlink is missing: `ln -s ~/my-hermes/Makefile ~/Makefile`.
- **Template Makefile drifts from the real Makefile** — `templates/Makefile` is copied once during `setup-my-hermes.sh` and never auto-updated. When you add new targets to `~/my-hermes/Makefile` (e.g. `update`, `check-update`, `dashboard`, `install`), update `templates/Makefile` in the skill too. Run `diff ~/my-hermes/Makefile ~/.hermes/skills/devops/hermes-git-sync/templates/Makefile` periodically to catch drift. The template should contain all shared targets **except** user-specific ones (e.g. `voice-memos` with hardcoded usernames).
- **Published skill repos in `my-skills/` don't have `.git`** — `my-skills/devops/<skill-name>/` is a plain directory (snapshot), not a git clone. If you want to `git push` changes directly from there, you need to initialize `.git` manually by moving it from a fresh clone:
  ```bash
  git clone https://github.com/shared-goals/<skill-name>.git /tmp/<skill-name>-tmp
  mv /tmp/<skill-name>-tmp/.git ~/my-hermes/my-skills/devops/<skill-name>/.git
  cd ~/my-hermes/my-skills/devops/<skill-name>
  git status   # should show modified files
  ```
  After this, the skill directory behaves as a normal git repo — `git diff`, `git push`, etc. work directly.
- **grep false positive in secrets check** — scope grep to data files: `git diff -- memories/ config.yaml | grep -qE '^\+[^+].*(secret|password|api_key)'`.
