---
name: hermes-git-sync
description: Version-control Hermes config, memories, skills, and scripts in a personal git repo. Also provides `skills-list.py` — a richer skills listing with ●/◑/○ status (custom / patched-builtin / builtin). Load this skill when the user asks to list skills, sync hermes, or check what's been customized.
triggers:
  - "skills list"
  - "list skills"
  - "list my skills"
  - "show skills"
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
**What stays out:** bundled skills, `.env`, `auth.json`, `cron/jobs.json` — anything Hermes manages directly or updates frequently at runtime.

See `references/repo-structure.md` for the full pattern explanation.

## Setup

```bash
bash ~/.hermes/skills/devops/hermes-git-sync/scripts/setup-my-hermes.sh ~/my-hermes
cd ~/my-hermes
git remote add origin <your-repo-url>
git push -u origin main
```

`setup-my-hermes.sh` is **idempotent** — safe to run multiple times. It reconciles the current state: creates missing directories, fixes symlinks, copies files, updates `.gitignore`. On re-run it reports what's already correct.

Copy `templates/Makefile` into your repo for convenient shortcuts.

## Daily sync

## Usage

```bash
make git-sync         # sync skills/scripts + commit + push
make sync             # sync my-skills + scripts snapshots only, no commit — inspect changes in IDE
```

`--sync-only` skips git entirely — useful for inspecting skill/script changes without staging anything:

```bash
MY_HERMES_REPO=~/my-hermes bash ~/.hermes/skills/devops/hermes-git-sync/scripts/hermes-git-sync.sh --sync-only
```

If a skill disappears from the bundled set after an update (but is still
listed in `.bundled_manifest`), `make sync` prompts to either:

- convert it to user custom (keep and mirror)
- remove it from `~/.hermes/skills`

Use `HERMES_ORPHAN_SKILL_POLICY=keep` or `=remove` to run non-interactively.

The script writes `/tmp/last-commit-full-diff.txt` after each commit — useful as input
for other routines (morning-brief, summary crons, etc.).

## Personal operational Make targets

Sergey's `~/my-hermes/Makefile` is the preferred home for repeatable local operational commands that are useful across sessions. It is tracked by `hermes-git-sync`, so add small stable targets there rather than leaving long one-off commands in chat history.

Current targets with operational relevance:

| Target | Description |
|--------|-------------|
| `make ui` | Launch Hermes web dashboard on port 9119 (checks conflicts first, binds `0.0.0.0`) |
| `make git-sync` | Full sync + commit skills/scripts/config to git |
| `make sync` | Snapshot-only sync (no commit) — inspect in IDE |
| `make update` | Check and apply Hermes updates |
| `make hindsight-status` / `hstat` | Check Hindsight health on rock |

Guidelines:
- Keep commands DRY by using existing host aliases and config (`ssh rock`, not `ssh -i ~/.ssh/id_key shag@rock`).
- Use short primary targets plus readable aliases when helpful (`hstat` + `hindsight-status`).
- After editing Makefile, verify both syntax and discoverability:
  ```bash
  make -n <target>
  make help | grep <target>
  ```
- If the command only reads state and is safe, run it once to catch quoting/runtime errors before reporting success.
- Show `git diff -- Makefile`; do not commit until Сергей explicitly approves.

## Dashboard ↔ Nous Portal wiring

The Hermes web dashboard (`hermes dashboard`) can use Nous Portal for OAuth authentication.

### Registration workflow

```bash
# 1. Confirm Portal is logged in and Tool Gateway is active
hermes portal info

# 2. Register dashboard as an OAuth client with Portal
hermes dashboard register --name "<label>"

# 3. Restart dashboard to pick up new .env
hermes dashboard --stop
hermes dashboard --no-open
```

### OAuth client ID: source of truth

The registered client ID goes into **`~/.hermes/.env`** (`HERMES_DASHBOARD_OAUTH_CLIENT_ID=agent:...`), **not** `config.yaml`. The `config.yaml` `dashboard.oauth.client_id` section should be replaced with a comment:

```yaml
dashboard:
  theme: default
  show_token_analytics: false
  # oauth — managed via HERMES_DASHBOARD_OAUTH_CLIENT_ID in .env
```

`.env` survives updates and overrides `config.yaml` for this key. If both exist, the env var wins.

### Auth behaviour

| Bind | Auth required | Use case |
|------|--------------|----------|
| `127.0.0.1` (default) | No | Local-only, your machine |
| `0.0.0.0` | Yes (Portal login at `/login`) | LAN/public, other devices |

The `--insecure` flag is deprecated/no-op since June 2026 — it no longer disables auth on public binds.

### Managing registered dashboards

List/revoke at `https://portal.nousresearch.com/local-dashboards`. If you have stale registrations (e.g. both `config.yaml` and `.env` had client IDs), remove the orphan from the Portal UI.

### Makefile target

The dashboard is launched via `make ui` (not `make dashboard`). The Makefile target checks for port 9119 conflicts first:

```makefile
ui: ## Start Hermes dashboard on default port 9119 (checks for conflicts first)
	@PID=$$(lsof -nP -iTCP:9119 -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $$2}'); \
	if [ -n "$$PID" ]; then \
		echo "⚠️  Port 9119 is in use by PID $$PID:"; \
		ps -p $$PID -o pid,command 2>/dev/null | tail -1; \
		echo "Kill it first: kill $$PID"; \
		exit 1; \
	fi
	hermes dashboard --host 0.0.0.0 --no-open
```

## Path conventions

- **`~/Work/`** — repos where Шаг collaborates (e.g. `~/Work/prd/`). Not in `~/my-hermes/` (that's the personal config repo). Not in serpo-owned dirs (ownership issues).
- **Relative paths in skills** — a skill should reference its own files with relative paths (`references/foo.md`, `templates/bar.yaml`), not absolute (`~/.hermes/skills/<cat>/<skill>/references/foo.md`). Cross-skill references (e.g. sg-daily-compass reading shared-goals areas) must be absolute since they're in different directories.
- **`~/my-hermes/cron/jobs.json`** — the original lives here (git-controlled). Symlinked from `~/.hermes/cron/jobs.json`. Do NOT symlink the entire `cron/` directory — Hermes writes runtime files there (`.tick.lock`, `output/`).

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

`sync-my-hermes.py` syncs both snapshots. Skills still use `.bundled_manifest` (MD5 hashes) to detect modifications.  
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

## Skill category management

When creating skills, always specify `category=` explicitly in `skill_manage(action='create')` — omitting it may accidentally inherit the category of the last-loaded skill.

When reorganizing skills between categories, use `mv` in terminal (Hermes picks up changes on next load). Then `make skills-sync` to snapshot, `make git-sync` to commit.

Good category structure (our convention):
- `shared-goals/` — Sergey's personal life areas (health, finance, music, photo, weather, etc.)
- `devops/` — infrastructure (backup, NAS, uptime monitoring, photo pipeline), Hermes tooling and workflow (git-sync, update, kanban)
- `note-taking/` — Obsidian, voice memos
- `media/` — media tools (movie-recommend, spotify, etc.)

## Editing files in repos owned by other users (serpo)

When a repo is cloned under `/Users/serpo/` and shag has no write access to the working copy, use the clone-fix-push pattern:

```bash
# 1. Clone fresh to /tmp (shag has push rights via SSH key)
git clone git@github.com:bongiozzo/photos.git /tmp/photos-fix

# 2. Apply changes (shag can write to /tmp)
cp /tmp/patched-file /tmp/photos-fix/file

# 3. Commit as shag and push
cd /tmp/photos-fix
git config user.name "Shag"
git config user.email "shag@agentmail.to"
git commit -am "message"
git push

# 4. Tell user to git pull in their working copy
```

Never `sudo cp` into serpo's directories or commit as serpo. Shag pushes as shag, serpo pulls.

## Critical rules

- **Secret detector false positives** — the regex `password` without value check triggers on mentions like `restic-password` in memory notes. Fixed regex: `password\s*[:=]\s*\S{6,}` — only flags `password = actualvalue`, not bare word mentions.
- **`skills-sync` target uses `--sync-only` flag** — exact command: `@MY_HERMES_REPO=$(HERMES_DIR) bash $(GIT_SYNC_SCRIPTS)/hermes-git-sync.sh --sync-only`. Do NOT change it to `skills-only` or any other argument. The flag controls no-commit mode. Breaking this makes `make skills-sync` commit silently.
- **Always show `git diff --stat` and wait for explicit confirmation before committing** — never commit silently. This applies to ALL paths: running the sync script, direct `git commit` via terminal, Makefile targets, or any other mechanism. There is no exception for "small" changes.
- **Never commit secrets** — script checks for sensitive patterns in `memories/` and `config.yaml`.
- **Cron prompt minimalism** — cron job prompts should be one-line directives ("Run skill X for Y"), not full algorithms. All execution logic lives in the skill's SKILL.md, loaded via the `skills` array. The prompt's only job is to tell the agent *what* to do, not *how*. A 6000-char cron prompt duplicating SKILL.md content is a maintenance liability — update the skill, and the cron job follows automatically. Exception: only add prompt detail for cron-specific concerns (pre-flight steps, delivery format) that don't belong in the skill itself.

## Cron job design — minimal prompts, logic in skills

Cron job prompts should be **one line directing to the skill**. All algorithm, pitfalls, and workflow logic lives in the SKILL.md, not in the prompt. The `skills` array loads skills automatically; the prompt is just the task instruction.

```json
"prompt": "Run the Daily Compass for Sergey.",
"skills": ["sg-daily-compass", "shared-goals", "hermes-git-sync"]
```

**Why:** Long prompts with embedded algorithm steps become stale when SKILL.md evolves. The agent reads loaded skills as context — the prompt just tells it what to do.

**Pitfall:** If `model` and `provider` are set in jobs.json, they override global config. After restoring from backup, clear these to `null` so the job inherits from `~/.hermes/config.yaml`.

## Cron/jobs.json — symlink pattern

`jobs.json` changes frequently (Hermes updates it on every cronjob call). Keep it in `~/my-hermes/cron/` with a symlink, but **gitignore it** — too much noise in git status:

```bash
mkdir -p ~/my-hermes/cron
cp ~/.hermes/cron/jobs.json ~/my-hermes/cron/jobs.json
rm ~/.hermes/cron/jobs.json
ln -s ~/my-hermes/cron/jobs.json ~/.hermes/cron/jobs.json
echo "cron/jobs.json" >> ~/my-hermes/.gitignore
```

## Script ownership principle

Scripts belong in skills, not in `~/my-hermes/scripts/`. The Makefile calls scripts via skill paths:

```makefile
GIT_SYNC_SCRIPTS := $(HOME)/.hermes/skills/devops/hermes-git-sync/scripts
UPDATE_SCRIPTS   := $(HOME)/.hermes/skills/devops/hermes-update-workflow/scripts
```

`~/my-hermes/scripts/` is legacy — if it exists, delete it. `apply-patches.sh` lives in `hermes-update-workflow`, `setup-my-hermes.sh` lives here. KISS/DRY.

The template `Makefile` (in `templates/`) is the public/generic version — **no user-specific targets** (e.g. `voice-memos`). The user's real `~/my-hermes/Makefile` extends it with machine-specific targets. When updating the template, copy it to `~/my-hermes/Makefile` and re-add any user-specific targets manually — do NOT blindly overwrite.

## skills-list.py

Script at `scripts/skills-list.py` — lists all Hermes skills with status:
- `●` custom (local-only, user-created)
- `◑` patched-builtin (bundled but modified in my-skills)
- `○` builtin (unmodified)

Invoke via `make skills-list` (target in `~/my-hermes/Makefile`).

Output groups skills by category, shows counts at bottom.

## Secret Detection — False Positive Fix

The safety check regex was tightened to avoid false positives on words like `restic-password` in memory:

```bash
# ✅ Correct — only triggers on actual key=value assignments
if git diff -- memories/ config.yaml | grep -qE '^\+[^+].*(secret|api_key|password\s*[:=]\s*\S{6,})'; then

# ❌ Old — triggers on any mention of the word 'password'
if git diff -- memories/ config.yaml | grep -qE '^\+[^+].*(secret|password|api_key)'; then
```



- **`hermes skills reset` removes from manifest** — `hermes skills reset <name>` clears the manifest entry, so `sync-my-hermes.py` treats the skill as user-created (no `bundled.diff`, always copied). Fix: after reverting a skill to bundled state, re-add its hash manually:
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
- **HTTPS remote blocks push in terminal** — always set SSH remote: `git remote set-url origin git@github.com:shared-goals/<name>.git`. HTTPS fails silently in terminal with `failed to get: -25308` (macOS keychain auth error).
- **git remote still shows old name after repo rename** — `git remote -v` may still point to `shag-hermes.git`; update with `git remote set-url origin <new-url>`.
- **`make` targets fail without ~/Makefile symlink** — Hermes Agent's terminal runs with `~` as cwd. `make git-sync` only resolves if `~/Makefile` exists. `setup-my-hermes.sh` creates `~/Makefile → ~/my-hermes/Makefile` automatically. If the symlink is missing: `ln -s ~/my-hermes/Makefile ~/Makefile`.
- **Template Makefile drifts from the real Makefile** — `templates/Makefile` is copied once during `setup-my-hermes.sh` and never auto-updated. When you add new targets to `~/my-hermes/Makefile` (e.g. `update`, `update-check`, `dashboard`, `install-my-hermes`), update `templates/Makefile` in the skill too. Run `diff ~/my-hermes/Makefile ~/.hermes/skills/devops/hermes-git-sync/templates/Makefile` periodically to catch drift. The template should contain all shared targets **except** user-specific ones (e.g. `voice-memos` with hardcoded usernames).
- **`.git` must live in the concrete skill directory, not in `my-skills/` and not at the category root.** For a categorized skill this means `~/.hermes/skills/<category>/<skill-name>/.git` (example: `~/.hermes/skills/shared-goals/shared-goals/.git`), not `~/.hermes/skills/<category>/.git`. `skill_manage` writes to `~/.hermes/skills/`, and `make skills-sync` mirrors into `my-skills/` as a plain snapshot (no `.git`). The working git repo (the one you `git push` from) must be the concrete `~/.hermes/skills/<category>/<skill-name>/` copy. To wire a published skill repo to its working directory:\n  ```bash\n  git clone https://github.com/shared-goals/<skill-name>.git /tmp/<skill-name>-tmp\n  mv /tmp/<skill-name>-tmp/.git ~/.hermes/skills/<category>/<skill-name>/.git\n  cd ~/.hermes/skills/<category>/<skill-name>\n  git remote set-url origin git@github.com:shared-goals/<skill-name>.git  # switch to SSH\n  git status  # should show modified files vs last push\n  ```\n  Any `.git` that ended up in `my-skills/` or at a category root should be moved/removed after verifying tracked files.\n- **Published skill repos in `my-skills/` don't have `.git`** — `my-skills/devops/<skill-name>/` is a plain directory (snapshot), not a git clone. If you want to `git push` changes directly from there, you need to initialize `.git` manually by moving it from a fresh clone:
  ```bash
  git clone https://github.com/shared-goals/<skill-name>.git /tmp/<skill-name>-tmp
  mv /tmp/<skill-name>-tmp/.git ~/my-hermes/my-skills/devops/<skill-name>/.git
  cd ~/my-hermes/my-skills/devops/<skill-name>
  git status   # should show modified files
  ```
  After this, the skill directory behaves as a normal git repo — `git diff`, `git push`, etc. work directly.
- **Model vs execution split** — when a domain has both a data model and a workflow (e.g. shared-goals has area definitions AND the Daily Compass algorithm), separate them into different skills. The model skill (shared-goals) stays publishable; the execution skill (sg-daily-compass) carries prompts, pitfalls, and operational details. Prompts for the workflow live in the execution skill's `references/prompts.yaml`, not in the model's area yamls.
- **grep false positive in secrets check** — scope grep to data files: `git diff -- memories/ config.yaml | grep -qE '^\+[^+].*(secret|password|api_key)'`.
