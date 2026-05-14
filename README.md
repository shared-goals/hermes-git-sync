# hermes-git-sync

A [Hermes Agent](https://hermes-agent.nousresearch.com) skill that version-controls your skills, memories, and config in a personal git repository.

## What it does

- Mirrors your user-created and user-modified skills to `~/my-hermes/my-skills/`
- For modified bundled skills, writes a `bundled.diff` so you can see exactly what you changed vs upstream
- Commits and pushes daily (integrates with `morning-brief` cron)
- Handles deletions — skills that revert to bundled state are removed from the mirror

This solves the problem described in [NousResearch/hermes-agent#20352](https://github.com/NousResearch/hermes-agent/issues/20352): `~/.hermes/skills/` is unversioned — no history, no rollback, no diff. Instead of making the hermes directory itself a git repo (which conflicts with `hermes update`), we sync only your changes to a separate repo.

## Works well with

[hermes-update-workflow](https://github.com/shared-goals/hermes-update-workflow) — safe `hermes update` with patch re-application. The template `Makefile` from this skill includes `make update`, `make check-update`, and `make patch` targets that call into that skill's scripts.

## Install

```bash
hermes skills tap add shared-goals/hermes-git-sync
hermes skills install hermes-git-sync
```

## Setup

```bash
bash ~/.hermes/skills/devops/hermes-git-sync/scripts/setup-my-hermes.sh ~/my-hermes
cd ~/my-hermes
git remote add origin <your-repo-url>
git push -u origin main
```

## Usage

The `make` targets work from anywhere because `setup-my-hermes.sh` creates a symlink `~/Makefile → ~/my-hermes/Makefile`. Hermes Agent's terminal runs with `~` as the working directory, so `make git-sync` resolves correctly without `cd`.

```bash
make git-sync        # sync skills, commit, push
make git-sync-dry    # preview changes without committing
make skills-sync     # sync skills only, no commit — inspect in IDE
make install         # re-bootstrap symlinks on a new machine
make dashboard       # start Hermes dashboard on port 9119
```

If you also have `hermes-update-workflow` installed:

```bash
make update          # safe hermes update with confirmation + patch re-apply
make check-update    # check for new releases and patch PR statuses (no changes)
make patch           # re-apply patches only
```

Set `MY_HERMES_REPO` env var if your repo lives somewhere other than `~/my-hermes`.

## Example repo structure

```
my-hermes/
├── config.yaml         # symlinked from ~/.hermes/config.yaml
├── SOUL.md             # symlinked from ~/.hermes/SOUL.md
├── Makefile            # shortcuts (template from this skill)
├── memories/
│   ├── MEMORY.md       # symlinked from ~/.hermes/memories/MEMORY.md
│   └── USER.md         # symlinked from ~/.hermes/memories/USER.md
├── my-skills/          # mirror of your skills (category structure preserved)
│   └── devops/
│       └── hermes-git-sync/   # example: your own copy of this skill
│           └── bundled.diff   # what you changed vs upstream
└── patches/            # *.patch + *.yaml pairs for upstream PRs
```

## Author

[shag](https://github.com/sg-shag) · [Shared Goals](https://github.com/shared-goals)
