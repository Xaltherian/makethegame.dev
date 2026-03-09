#!/usr/bin/env python3
"""
sync_lessons.py  —  Make The Game full course sync

Usage:
  python scripts/sync_lessons.py

What it does:
  1. Wipes src/content/lessons/ completely
  2. Rebuilds src/data/course.json from scratch
  3. Converts every .md in lessons-source/ and writes it as .mdx
  4. Prints a summary of everything that was published

Folder structure expected in lessons-source/:
  lessons-source/
    <module-slug>/
      <chapter-slug>/
        <lesson-slug>.md

Each .md file must have this frontmatter:
  ---
  title: "Lesson Title"
  module: "module-slug"
  moduleTitle: "Module Title"
  chapter: "chapter-slug"
  chapterTitle: "Chapter Title"
  order: 1
  description: "Optional one-liner."
  ---

Module-level metadata (icon, description) lives in an optional
  lessons-source/<module-slug>/_module.json
file. If it doesn't exist, sensible defaults are used and you'll
be reminded to fill it in.

Chapter-level metadata lives in an optional
  lessons-source/<module-slug>/<chapter-slug>/_chapter.json
file. Currently only used if you want to override the chapter title
derived from the lesson frontmatter.
"""

import os
import re
import json
import shutil
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def parse_frontmatter(content: str, filepath: Path) -> tuple[dict, str]:
    match = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', content, re.DOTALL)
    if not match:
        print(f"  ✗  SKIP {filepath.name} — no frontmatter found")
        return None, None

    fm_text = match.group(1)
    body = content[match.end():]
    fm = {}

    for line in fm_text.splitlines():
        if ':' not in line or line.strip().startswith('#'):
            continue
        key, _, val = line.partition(':')
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        fm[key] = val

    required = ['title', 'module', 'moduleTitle', 'chapter', 'chapterTitle', 'order']
    missing = [r for r in required if r not in fm]
    if missing:
        print(f"  ✗  SKIP {filepath.name} — missing fields: {', '.join(missing)}")
        return None, None

    try:
        fm['order'] = int(fm['order'])
    except ValueError:
        print(f"  ✗  SKIP {filepath.name} — 'order' must be an integer")
        return None, None

    return fm, body


# ──────────────────────────────────────────────────────────────────────────────
# SYNTAX TRANSFORMERS  (identical to before)
# ──────────────────────────────────────────────────────────────────────────────

CALLOUT_CONFIG = {
    'tip':     ('💡', 'Tip'),
    'warning': ('⚠️',  'Warning'),
    'info':    ('ℹ️',  'Note'),
    'check':   ('✅', 'Checkpoint'),
}


def make_callout(block_type: str, inner: str) -> str:
    icon, label = CALLOUT_CONFIG.get(block_type, ('', block_type.title()))
    return (
        f'<div class="callout {block_type}">\n'
        f'<div class="callout-stripe"></div>\n'
        f'<div class="callout-body">\n'
        f'<p class="callout-title">{icon} {label}</p>\n'
        f'<div class="callout-text">\n\n'
        f'{inner.strip()}\n\n'
        f'</div>\n'
        f'</div>\n'
        f'</div>'
    )


def make_split(inner: str) -> str:
    parts = inner.split('|||', 1)
    left  = parts[0].strip() if parts else ''
    right = parts[1].strip() if len(parts) > 1 else ''
    return (
        f'<div class="lesson-split">\n'
        f'<div class="split-left">\n\n'
        f'{left}\n\n'
        f'</div>\n'
        f'<div class="split-right">\n\n'
        f'{right}\n\n'
        f'</div>\n'
        f'</div>'
    )


def make_steps(inner: str) -> str:
    raw_steps = re.split(r'(?=###\s)', inner.strip())
    raw_steps = [s.strip() for s in raw_steps if s.strip()]
    parts = ['<div class="steps-list">']
    for num, step in enumerate(raw_steps, start=1):
        lines = step.split('\n', 1)
        title = re.sub(r'^###\s*', '', lines[0]).strip()
        body  = lines[1].strip() if len(lines) > 1 else ''
        parts.append(
            f'<div class="step-box">\n'
            f'<div class="step-num">{num}</div>\n'
            f'<div class="step-body">\n'
            f'<div class="step-title">{title}</div>\n'
            f'<div class="step-desc">\n\n'
            f'{body}\n\n'
            f'</div>\n'
            f'</div>\n'
            f'</div>'
        )
    parts.append('</div>')
    return '\n'.join(parts)


def replace_block(match: re.Match) -> str:
    block_type = match.group(1).strip().lower()
    inner      = match.group(2)
    if block_type in CALLOUT_CONFIG:
        return make_callout(block_type, inner)
    if block_type == 'split':
        return make_split(inner)
    if block_type == 'steps':
        return make_steps(inner)
    print(f"    ⚠  Unknown block type ':::{block_type}' — left unchanged.")
    return match.group(0)


def transform_body(body: str) -> str:
    return re.sub(r':::(\w+)\n(.*?):::', replace_block, body, flags=re.DOTALL)


def build_mdx(fm: dict, body: str) -> str:
    description_line = f'\ndescription: "{fm["description"]}"' if 'description' in fm else ''
    return (
        f'---\n'
        f'title: "{fm["title"]}"\n'
        f'module: "{fm["module"]}"\n'
        f'moduleTitle: "{fm["moduleTitle"]}"\n'
        f'chapter: "{fm["chapter"]}"\n'
        f'chapterTitle: "{fm["chapterTitle"]}"\n'
        f'order: {fm["order"]}'
        f'{description_line}\n'
        f'---\n'
        f'{transform_body(body)}'
    )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN SYNC
# ──────────────────────────────────────────────────────────────────────────────

def main():
    script_dir   = Path(__file__).parent.resolve()
    project_root = script_dir.parent

    if not (project_root / 'src').exists():
        print(f"ERROR: Could not find project root (no 'src/' at {project_root})")
        return

    source_root  = project_root / 'lessons-source'
    content_root = project_root / 'src' / 'content' / 'lessons'
    course_json  = project_root / 'src' / 'data' / 'course.json'

    print("\n  Make The Game — syncing lessons\n")

    # ── 1. Collect all .md lesson files ─────────────────────────
    md_files = sorted([
        p for p in source_root.rglob('*.md')
        if not p.name.startswith('_')   # skip _template.md etc.
    ])

    if not md_files:
        print("  lessons-source/ is empty (or has no .md files).")
        print("  Clearing site content...\n")

    # ── 2. Wipe existing generated content ──────────────────────
    if content_root.exists():
        shutil.rmtree(content_root)
    content_root.mkdir(parents=True)

    # Also wipe readmes
    readmes_root = project_root / 'src' / 'content' / 'readmes'
    if readmes_root.exists():
        shutil.rmtree(readmes_root)
    readmes_root.mkdir(parents=True)

    # ── 3. Parse all lessons and build course structure ──────────
    # modules dict: slug -> { meta, chapters: { slug -> { meta, lessons: [] } } }
    modules: dict = {}
    published = 0
    skipped   = 0

    for md_path in md_files:
        raw = md_path.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(raw, md_path)
        if fm is None:
            skipped += 1
            continue

        mod_slug  = fm['module']
        ch_slug   = fm['chapter']
        les_slug  = md_path.stem

        # ── Module metadata ──────────────────────────────────────
        if mod_slug not in modules:
            # Check for optional _module.json
            mod_meta_path = source_root / mod_slug / '_module.json'
            if mod_meta_path.exists():
                with open(mod_meta_path) as f:
                    mod_meta = json.load(f)
            else:
                mod_meta = {
                    'icon':        '📦',
                    'description': f'Learn to build {fm["moduleTitle"]}.',
                }
                print(f"  ⚠  No _module.json for '{mod_slug}'")
                print(f"     → Create lessons-source/{mod_slug}/_module.json to set icon & description.\n")

            modules[mod_slug] = {
                'slug':     mod_slug,
                'title':    fm['moduleTitle'],
                'icon':     mod_meta.get('icon', '📦'),
                'chapters': {},
            }

        # ── Chapter metadata ─────────────────────────────────────
        mod = modules[mod_slug]
        if ch_slug not in mod['chapters']:
            mod['chapters'][ch_slug] = {
                'slug':    ch_slug,
                'title':   fm['chapterTitle'],
                'lessons': [],
            }

        # ── Register lesson ──────────────────────────────────────
        mod['chapters'][ch_slug]['lessons'].append({
            'slug':  les_slug,
            'title': fm['title'],
            'order': fm['order'],
        })

        # ── Write .mdx ───────────────────────────────────────────
        dest_dir  = content_root / mod_slug / ch_slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f'{les_slug}.mdx'
        dest_path.write_text(build_mdx(fm, body), encoding='utf-8')

        print(f"  ✦  {mod_slug}/{ch_slug}/{les_slug}")
        published += 1

    # ── 4. Sort lessons within each chapter by order ─────────────
    course_modules = []
    for mod_slug, mod in modules.items():
        chapters = []
        for ch_slug, ch in mod['chapters'].items():
            ch['lessons'].sort(key=lambda l: l['order'])
            chapters.append({
                'slug':    ch['slug'],
                'title':   ch['title'],
                'lessons': ch['lessons'],
            })
        course_modules.append({
            'slug':     mod['slug'],
            'title':    mod['title'],
            'icon':     mod['icon'],
            'chapters': chapters,
        })

    # ── 5. Copy and convert _readme.md files ─────────────────────
    readme_count = 0
    for mod_slug in modules:
        readme_src = source_root / mod_slug / '_readme.md'
        if readme_src.exists():
            raw = readme_src.read_text(encoding='utf-8')
            # Strip frontmatter if present, otherwise use body as-is
            fm_match = re.match(r'^---\r?\n.*?\r?\n---\r?\n', raw, re.DOTALL)
            body = raw[fm_match.end():] if fm_match else raw
            # Apply same custom syntax transforms
            converted = transform_body(body)
            dest = readmes_root / f'{mod_slug}.mdx'
            dest.write_text(converted, encoding='utf-8')
            print(f"  📋  readme → {mod_slug}")
            readme_count += 1

    # ── 6. Write course.json ─────────────────────────────────────
    with open(course_json, 'w', encoding='utf-8') as f:
        json.dump({'modules': course_modules}, f, indent=2, ensure_ascii=False)

    # ── 7. Summary ───────────────────────────────────────────────
    print(f"\n  ✅  Sync complete.")
    print(f"      {published} lesson(s) published, {skipped} skipped, {readme_count} readme(s).")
    if course_modules:
        print(f"      {len(course_modules)} module(s), "
              f"{sum(len(m['chapters']) for m in course_modules)} chapter(s)\n")
    else:
        print(f"      Course is now empty.\n")


if __name__ == '__main__':
    main()
    input("Press any key to Exit")
