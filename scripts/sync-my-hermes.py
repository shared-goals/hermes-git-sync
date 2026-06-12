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
import sys
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


def write_manifest(manifest):
    lines = [f"{name}: {manifest[name]}" for name in sorted(manifest)]
    MANIFEST.write_text("\n".join(lines) + ("\n" if lines else ""))


def find_bundled_skill_path(name: str, rel: Path):
    # Prefer exact category/path match first.
    candidate = BUNDLED_SKILLS_DIR / rel
    if (candidate / "SKILL.md").exists():
        return candidate

    # Fall back to leaf-name lookup for legacy moved skills.
    for p in BUNDLED_SKILLS_DIR.rglob("SKILL.md"):
        if p.parent.name == name:
            return p.parent
    return None


def resolve_orphan_policy():
    policy = os.environ.get("HERMES_ORPHAN_SKILL_POLICY", "ask").strip().lower()
    if policy not in {"ask", "keep", "remove"}:
        policy = "ask"
    if policy == "ask" and not (sys.stdin.isatty() and sys.stdout.isatty()):
        policy = "keep"
    return policy


def choose_orphan_action(rel: Path, name: str, policy: str):
    if policy in {"keep", "remove"}:
        return policy

    prompt = (
        f"Skill disappeared from bundled set: {rel} ({name}). "
        "[k]eep as custom / [r]emove from ~/.hermes/skills? [k/r, default:k]: "
    )
    answer = input(prompt).strip().lower()
    return "remove" if answer in {"r", "remove"} else "keep"


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
    orphan_policy = resolve_orphan_policy()
    manifest_changed = False
    orphan_kept, orphan_removed = [], []
    MY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # rel_path -> (skill_dir, name, is_modified_bundled)
    want = {}

    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        skill_dir = skill_md.parent
        rel = skill_dir.relative_to(SKILLS_DIR)
        name = skill_dir.name
        if any(p.startswith(".") for p in rel.parts):
            continue
        bundled_path = find_bundled_skill_path(name, rel)

        # Skill was bundled previously (manifest entry) but no longer exists in
        # bundled set. Ask whether to keep as custom or remove.
        if name in manifest and bundled_path is None:
            action = choose_orphan_action(rel, name, orphan_policy)
            if action == "remove":
                shutil.rmtree(skill_dir)
                manifest.pop(name, None)
                manifest_changed = True
                orphan_removed.append(str(rel))
                continue

            # keep as custom -> remove bundled marker from manifest
            manifest.pop(name, None)
            manifest_changed = True
            orphan_kept.append(str(rel))
            want[rel] = (skill_dir, name, False)
            continue

        if name in manifest:
            if dir_hash(skill_dir) != manifest[name]:
                want[rel] = (skill_dir, name, True)
            continue

        # Skill not in manifest: if it now exists in bundled roots and
        # content matches, treat it as bundled and do not mirror into my-skills.
        if bundled_path and dir_hash(skill_dir) == dir_hash(bundled_path):
            continue

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
            bundled_path = find_bundled_skill_path(name, rel)
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
    if orphan_kept:
        print(f"  ↻ {len(orphan_kept)} orphaned skills converted to custom: {', '.join(sorted(orphan_kept))}")
    if orphan_removed:
        print(f"  ⊘ {len(orphan_removed)} orphaned skills removed from ~/.hermes/skills: {', '.join(sorted(orphan_removed))}")
    if not copied and not updated and not removed:
        print("  ✓ my-skills up to date")
    print(
        f"  = {len(want)} skills tracked "
        f"({n_modified} modified bundled, {n_created} user-created)"
    )

    if manifest_changed:
        write_manifest(manifest)


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
