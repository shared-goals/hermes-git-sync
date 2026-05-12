# hermes-git-sync

A [Hermes Agent](https://hermes-agent.nousresearch.com) skill that version-controls your skills, memories, and config in a personal git repository.

## What it does

- Mirrors your user-created and user-modified skills to `~/my-hermes/my-skills/`
- For modified bundled skills, writes a `bundled.diff` so you can see exactly what you changed vs upstream
- Commits and pushes daily (integrates with `morning-brief` cron)
- Handles deletions — skills that revert to bundled state are removed from the mirror

This solves the problem described in [NousResearch/hermes-agent#20352](https://github.com/NousResearch/hermes-agent/issues/20352): `~/.hermes/skills/` is unversioned — no history, no rollback, no diff. Instead of making the hermes directory itself a git repo (which conflicts with `hermes update`), we sync only your changes to a separate repo.

## Install

```bash
hermes skills tap add shared-goals/hermes-git-sync
hermes skills install hermes-git-sync
```

## Setup

```bash
bash ~/.hermes/skills/devops/hermes-git-sync/scripts/setup-my-hermes.sh ~/my-hermes
cd ~/my-hermes
git remote set-url origin <your-repo-url>
```

## Usage

```bash
make git-sync        # sync, commit, push
make git-sync-dry    # preview changes without committing
make skills-sync     # sync skills only, no commit
```

Set `MY_HERMES_REPO` env var if your repo lives somewhere other than `~/my-hermes`.

## Example repo structure

```
my-hermes/
├── my-skills/          # mirror of your skills (category structure preserved)
│   └── devops/
│       └── hermes-git-sync/   # example: shag's own copy of this skill
├── patches/            # bundled.diff files for modified bundled skills
├── memories/           # symlink → ~/.hermes/memories/
└── Makefile
```

## Author

[shag](https://github.com/sg-shag) · [Shared Goals](https://github.com/shared-goals)
