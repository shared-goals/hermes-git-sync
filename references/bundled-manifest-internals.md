# Bundled Manifest Internals

`~/.hermes/skills/.bundled_manifest` — v2 format, one line per skill:
```
skill-name:md5hash
```

Hash algorithm (`tools/skills_sync._dir_hash`):
```python
hasher = hashlib.md5()
for fpath in sorted(directory.rglob("*")):
    if fpath.is_file():
        rel = fpath.relative_to(directory)
        hasher.update(str(rel).encode("utf-8"))  # filename included!
        hasher.update(fpath.read_bytes())
```

**Important:** both filename AND content are hashed. A naive `md5_dir` that only
hashes content will produce wrong results and mark all skills as modified.

## Update logic (skills_sync.sync_skills)

| State | Action |
|---|---|
| Not in manifest | NEW — copy from bundled, record hash |
| In manifest, hash matches user copy | CLEAN — update if bundled changed |
| In manifest, hash differs from user copy | USER-MODIFIED — skip |
| In manifest, absent from user dir | DELETED BY USER — respect, don't re-add |
| In manifest, gone from bundled | REMOVED upstream — clean from manifest |

## sync-my-skills.py strategy

Reads manifest → for each skill in `~/.hermes/skills/`:
- if `name in manifest` and `dir_hash(user_copy) != manifest[name]` → **user-modified** → copy to my-skills/
- if `name not in manifest` → **user-created** → copy to my-skills/
- removes from my-skills/ any skill that no longer qualifies (reset to bundled)
