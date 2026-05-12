# my-hermes repo — structure and pattern

A personal git repository for versioning your Hermes Agent configuration, memories, and skills.

## Philosophy

Hermes manages `~/.hermes/` directly — skills are synced on update, memories are written by the agent. This repo does **not** replace that. Instead it:

- **symlinks** core files (config, SOUL, memories) so they live in git
- **mirrors** only *your* skills (`my-skills/`) — not the entire bundled library
- **tracks patches** you maintain against upstream with linked PRs

## Directory structure

```
my-hermes/
├── config.yaml          ← real file, symlinked from ~/.hermes/config.yaml
├── SOUL.md              ← real file, symlinked from ~/.hermes/SOUL.md
├── Makefile             ← shortcuts (see templates/Makefile)
├── .gitignore           ← excludes .env, auth.json, keys
│
├── memories/
│   ├── MEMORY.md        ← symlinked from ~/.hermes/memories/MEMORY.md
│   └── USER.md          ← symlinked from ~/.hermes/memories/USER.md
│
├── my-skills/           ← auto-synced snapshot (see below)
│   ├── morning-brief/   ← user-created skill (full copy)
│   ├── github-auth/     ← modified bundled skill
│   │   └── bundled.diff ← what you changed vs upstream
│   └── ...
│
└── patches/
    ├── registry.yaml    ← patch status + linked PRs
    └── *.patch          ← patches to re-apply after hermes update
```

## my-skills/ — how it works

`sync-my-skills.py` runs before every commit. It:

1. Reads `~/.hermes/skills/.bundled_manifest` — MD5 hashes of all bundled skills
2. Scans `~/.hermes/skills/` for skills that differ from bundled (modified) or aren't in the manifest at all (user-created)
3. Copies only those into `my-skills/`
4. For each **modified bundled** skill — writes `bundled.diff` showing the exact diff vs upstream

Pure bundled skills (untouched) are **not** copied. `my-skills/` contains only what's yours.

## What lives where

| Location | What | Managed by |
|---|---|---|
| `~/.hermes/skills/` | All skills: bundled + modified + created | Hermes (`hermes update`) |
| `~/.hermes/hermes-agent/skills/` | Bundled skills source | Hermes |
| `my-hermes/my-skills/` | Mirror: only your skills | `sync-my-skills.py` |
| `my-hermes/patches/` | Local patches with PR refs | You |
| `my-hermes/memories/` | Agent memory (symlinked) | Hermes agent |

## After hermes update

Hermes protects user-modified skills (skips them during sync). But to re-apply code patches:

```bash
make patch
```

Check `patches/registry.yaml` — if a patch's PR was merged upstream, remove the patch.
