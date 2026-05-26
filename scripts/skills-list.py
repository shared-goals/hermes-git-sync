#!/usr/bin/env python3
"""List all Hermes skills with custom/patched/builtin status."""

import subprocess, pathlib, sys

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

# Get skills from hermes
raw = run("hermes skills list 2>/dev/null")
skills = []
for line in raw.split('\n'):
    if '│' not in line:
        continue
    parts = [p.strip() for p in line.split('│') if p.strip()]
    if len(parts) < 3 or parts[0] == 'Name':
        continue
    name, category, source = parts[0], parts[1] if len(parts) > 1 else '', parts[2] if len(parts) > 2 else ''
    skills.append((name, category, source))

# Get our tracked skills from my-skills snapshot
my_skills_dir = pathlib.Path.home() / 'my-hermes' / 'my-skills'
my_tracked = set()
for p in my_skills_dir.rglob('SKILL.md'):
    rel = str(p.relative_to(my_skills_dir).parent)
    my_tracked.add(rel.split('/')[-1])  # leaf name
    my_tracked.add(rel)                 # full path

output = []
current_cat = None
custom_count = patched_count = builtin_count = 0

for name, category, source in sorted(skills, key=lambda x: (x[1] or 'root', x[0])):
    cat = category if category else 'root'
    if cat != current_cat:
        if current_cat is not None:
            output.append('')
        output.append(f"{cat}/")
        current_cat = cat

    in_my = name in my_tracked or any(name == p.split('/')[-1] for p in my_tracked)

    if source == 'local':
        status = '●'
        custom_count += 1
    elif source == 'builtin' and in_my:
        status = '◑'
        patched_count += 1
    else:
        status = '○'
        builtin_count += 1

    output.append(f"  {status} {name}")

print('\n'.join(output))
print(f"\n● custom ({custom_count})  ◑ patched-builtin ({patched_count})  ○ builtin ({builtin_count})")
print(f"Total: {len(skills)} skills")
