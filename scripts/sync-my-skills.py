#!/usr/bin/env python3
"""
sync-my-skills.py — copy user-modified and user-created skills to my-hermes/my-skills/

Logic:
- reads .bundled_manifest from ~/.hermes/skills/
- for each skill in ~/.hermes/skills/:
    - if in manifest AND hash matches → skip (pure bundled, untouched)
    - if in manifest AND hash differs → copy (mirroring category structure) + write bundled.diff
    - if not in manifest → copy (user-created)
- removes skills from my-skills/ that went back to bundled state

Directory structure mirrors ~/.hermes/skills/:
  ~/.hermes/skills/devops/hermes-git-sync  →  my-skills/devops/hermes-git-sync
  ~/.hermes/skills/morning-brief           →  my-skills/morning-brief
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

SKILLS_DIR = Path.home() / ".hermes/skills"
BUNDLED_DIR = Path.home() / ".hermes/hermes-agent/skills"
MY_SKILLS_DIR = Path(os.environ.get("MY_HERMES_REPO", str(Path.home() / "my-hermes"))) / "my-skills"
MANIFEST = SKILLS_DIR / ".bundled_manifest"


def dir_hash(path: Path) -> str:
    """Same algorithm as skills_sync._dir_hash"""
    hasher = hashlib.md5()
    for fpath in sorted(path.rglob("*")):
        if fpath.is_file():
            rel = fpath.relative_to(path)
            hasher.update(str(rel).encode("utf-8"))
            hasher.update(fpath.read_bytes())
    return hasher.hexdigest()


def read_manifest():
    if not MANIFEST.exists():
        return {}
    result = {}
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if ":" in line:
            name, _, h = line.partition(":")
            result[name.strip()] = h.strip()
    return result


def find_bundled_path(name: str):
    """Find skill in bundled dir (may be in a category subdir)"""
    for p in BUNDLED_DIR.rglob("SKILL.md"):
        if p.parent.name == name:
            return p.parent
    return None


def write_diff(dest: Path, bundled_path: Path):
    """Write diff between user version and bundled version"""
    result = subprocess.run(
        ["diff", "-rU", "3", str(bundled_path), str(dest)],
        capture_output=True, text=True
    )
    diff_text = result.stdout
    diff_file = dest / "bundled.diff"
    if diff_text.strip():
        diff_file.write_text(diff_text)
    elif diff_file.exists():
        diff_file.unlink()


def main():
    manifest = read_manifest()
    MY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # rel_path -> (skill_dir, name, is_modified_bundled)
    want = {}

    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        skill_dir = skill_md.parent
        rel = skill_dir.relative_to(SKILLS_DIR)  # e.g. devops/hermes-git-sync or morning-brief
        name = skill_dir.name
        if any(p.startswith(".") for p in rel.parts):
            continue
        if name in manifest:
            if dir_hash(skill_dir) != manifest[name]:
                want[rel] = (skill_dir, name, True)   # modified bundled
        else:
            want[rel] = (skill_dir, name, False)       # user-created

    copied, updated, removed = [], [], []

    for rel, (src, name, is_modified) in want.items():
        dest = MY_SKILLS_DIR / rel
        needs_update = not dest.exists() or dir_hash(src) != dir_hash(dest)

        if needs_update:
            if dest.exists():
                shutil.rmtree(dest)
                updated.append(name)
            else:
                copied.append(name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest)

        # write/update bundled.diff for modified bundled skills
        if is_modified:
            bundled_path = find_bundled_path(name)
            if bundled_path:
                write_diff(dest, bundled_path)

    # Remove skills no longer modified (walk my-skills/ looking for SKILL.md)
    want_dests = {MY_SKILLS_DIR / rel for rel in want}
    for skill_md in list(MY_SKILLS_DIR.rglob("SKILL.md")):
        dest = skill_md.parent
        if dest not in want_dests:
            shutil.rmtree(dest)
            removed.append(dest.name)
            # remove empty category dirs
            try:
                dest.parent.rmdir()
            except OSError:
                pass

    n_modified = sum(1 for _, (_, _, m) in want.items() if m)
    n_created = len(want) - n_modified

    if copied:
        print(f"  + {len(copied)} added: {', '.join(sorted(copied))}")
    if updated:
        print(f"  ↑ {len(updated)} updated: {', '.join(sorted(updated))}")
    if removed:
        print(f"  − {len(removed)} removed: {', '.join(sorted(removed))}")
    if not copied and not updated and not removed:
        print("  ✓ my-skills up to date")
    print(f"  = {len(want)} skills tracked ({n_modified} modified bundled, {n_created} user-created)")


if __name__ == "__main__":
    main()
