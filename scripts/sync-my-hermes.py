#!/usr/bin/env python3
"""
sync-my-hermes.py — mirror user Hermes customizations into my-hermes.

Currently syncs:
- my-skills/: user-created and user-modified skills
- scripts/: user-created and user-modified scripts from ~/.hermes/scripts
"""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

SKILLS_DIR = Path.home() / ".hermes/skills"
BUNDLED_SKILLS_DIR = Path.home() / ".hermes/hermes-agent/skills"
SCRIPTS_DIR = Path.home() / ".hermes/scripts"
BUNDLED_SCRIPTS_DIR = Path.home() / ".hermes/hermes-agent/scripts"
MY_HERMES_REPO = Path(os.environ.get("MY_HERMES_REPO", str(Path.home() / "my-hermes")))
MY_SKILLS_DIR = MY_HERMES_REPO / "my-skills"
MY_SCRIPTS_DIR = MY_HERMES_REPO / "scripts"
MANIFEST = SKILLS_DIR / ".bundled_manifest"


def dir_hash(path: Path) -> str:
    """Hash full directory contents relative to the directory root."""
    hasher = hashlib.md5()
    for fpath in sorted(path.rglob("*")):
        if fpath.is_file():
            rel = fpath.relative_to(path)
            hasher.update(str(rel).encode("utf-8"))
            hasher.update(fpath.read_bytes())
    return hasher.hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


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


def find_bundled_skill_path(name: str):
    for p in BUNDLED_SKILLS_DIR.rglob("SKILL.md"):
        if p.parent.name == name:
            return p.parent
    return None


def write_skill_diff(dest: Path, bundled_path: Path):
    result = subprocess.run(
        ["diff", "-rU", "3", str(bundled_path), str(dest)],
        capture_output=True,
        text=True,
    )
    diff_text = result.stdout
    diff_file = dest / "bundled.diff"
    if diff_text.strip():
        diff_file.write_text(diff_text)
    elif diff_file.exists():
        diff_file.unlink()


def sync_skills():
    manifest = read_manifest()
    MY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # rel_path -> (skill_dir, name, is_modified_bundled)
    want = {}

    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        skill_dir = skill_md.parent
        rel = skill_dir.relative_to(SKILLS_DIR)
        name = skill_dir.name
        if any(p.startswith(".") for p in rel.parts):
            continue
        if name in manifest:
            if dir_hash(skill_dir) != manifest[name]:
                want[rel] = (skill_dir, name, True)
        else:
            want[rel] = (skill_dir, name, False)

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

        if is_modified:
            bundled_path = find_bundled_skill_path(name)
            if bundled_path:
                write_skill_diff(dest, bundled_path)

    want_dests = {MY_SKILLS_DIR / rel for rel in want}
    for skill_md in list(MY_SKILLS_DIR.rglob("SKILL.md")):
        dest = skill_md.parent
        if dest not in want_dests:
            shutil.rmtree(dest)
            removed.append(dest.name)
            try:
                dest.parent.rmdir()
            except OSError:
                pass

    n_modified = sum(1 for _, (_, _, modified) in want.items() if modified)
    n_created = len(want) - n_modified

    if copied:
        print(f"  + {len(copied)} skills added: {', '.join(sorted(copied))}")
    if updated:
        print(f"  ↑ {len(updated)} skills updated: {', '.join(sorted(updated))}")
    if removed:
        print(f"  − {len(removed)} skills removed: {', '.join(sorted(removed))}")
    if not copied and not updated and not removed:
        print("  ✓ my-skills up to date")
    print(
        f"  = {len(want)} skills tracked "
        f"({n_modified} modified bundled, {n_created} user-created)"
    )


def build_scripts_diff(modified_pairs):
    diff_chunks = []
    for rel, user_file, bundled_file in sorted(modified_pairs, key=lambda x: str(x[0])):
        result = subprocess.run(
            ["diff", "-u", str(bundled_file), str(user_file)],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            diff_chunks.append(f"# {rel}\n{result.stdout}")
    return "\n".join(diff_chunks).strip()


def sync_scripts():
    MY_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    want = {}  # rel -> (src_file, is_modified_bundled, bundled_file_or_none)
    modified_pairs = []

    if SCRIPTS_DIR.exists():
        for src in sorted(SCRIPTS_DIR.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(SCRIPTS_DIR)
            if any(part.startswith(".") for part in rel.parts):
                continue

            bundled = BUNDLED_SCRIPTS_DIR / rel
            if bundled.exists() and bundled.is_file():
                if file_hash(src) == file_hash(bundled):
                    continue
                want[rel] = (src, True, bundled)
                modified_pairs.append((rel, src, bundled))
            else:
                want[rel] = (src, False, None)

    copied, updated, removed = [], [], []

    for rel, (src, _is_modified, _bundled) in want.items():
        dest = MY_SCRIPTS_DIR / rel
        existed = dest.exists()

        needs_update = True
        if existed and dest.is_file():
            needs_update = file_hash(src) != file_hash(dest)

        if needs_update:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and dest.is_dir():
                shutil.rmtree(dest)
            shutil.copy2(src, dest)
            if existed:
                updated.append(str(rel))
            else:
                copied.append(str(rel))

    want_dests = {MY_SCRIPTS_DIR / rel for rel in want}
    diff_file = MY_SCRIPTS_DIR / "bundled.diff"

    for existing in sorted(MY_SCRIPTS_DIR.rglob("*"), reverse=True):
        if existing == diff_file:
            continue
        if existing.is_file() and existing not in want_dests:
            existing.unlink()
            removed.append(str(existing.relative_to(MY_SCRIPTS_DIR)))
        elif existing.is_dir():
            try:
                existing.rmdir()
            except OSError:
                pass

    diff_text = build_scripts_diff(modified_pairs)
    if diff_text:
        diff_file.write_text(diff_text + "\n")
    elif diff_file.exists():
        diff_file.unlink()

    n_modified = sum(1 for _, (_, modified, _) in want.items() if modified)
    n_created = len(want) - n_modified

    if copied:
        print(f"  + {len(copied)} scripts added: {', '.join(sorted(copied))}")
    if updated:
        print(f"  ↑ {len(updated)} scripts updated: {', '.join(sorted(updated))}")
    if removed:
        print(f"  − {len(removed)} scripts removed: {', '.join(sorted(removed))}")
    if not copied and not updated and not removed:
        print("  ✓ scripts up to date")
    print(
        f"  = {len(want)} scripts tracked "
        f"({n_modified} modified bundled, {n_created} user-created)"
    )


def main():
    print("Skills:")
    sync_skills()
    print("Scripts:")
    sync_scripts()


if __name__ == "__main__":
    main()
