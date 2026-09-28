#!/usr/bin/env python3
"""Build the Sublinieri page: entries/*.md + template.html -> _site/.

Usage: python3 build.py [out_dir]   (default: _site)
"""
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '_site')

MONTHS = ['ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie', 'iulie',
          'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie']
KINDS = {'quote': 'Citat', 'note': 'Notă'}
FIELDS = {'date', 'kind', 'source', 'intro', 'note', 'style', 'photos'}
MORE = '<!-- more -->'
# a long quote without an explicit <!-- more --> is folded after this many words
FOLD_WORDS = 100

TOGGLE = ('<span class="toggle"><span class="lbl-more"> arată tot</span>'
          '<span class="lbl-less"> arată mai puțin</span>'
          '<span class="chevron" aria-hidden="true">&#8250;</span></span>')


def esc(s):
    return html.escape(s, quote=False).replace('\n', '<br>')


def attr(s):
    return html.escape(s, quote=True)


def parse(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n?(.*)', raw, re.S)
    if not m:
        sys.exit(f'{path}: lipsește antetul --- ... ---')
    meta = {}
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(':')
        key = key.strip()
        if key not in FIELDS:
            sys.exit(f'{path}: câmp necunoscut "{key}"')
        meta[key] = value.strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', meta.get('date', '')):
        sys.exit(f'{path}: date trebuie să fie AAAA-LL-ZZ')
    if 'source' not in meta:
        sys.exit(f'{path}: lipsește source')
    meta.setdefault('kind', 'quote')
    if meta['kind'] not in KINDS:
        sys.exit(f'{path}: kind trebuie să fie quote sau note')
    meta['photos'] = [p.strip() for p in meta.get('photos', '').split(',') if p.strip()]
    for p in meta['photos']:
        photo = os.path.join(ROOT, 'photos', p)
        if not os.path.exists(photo):
            sys.exit(f'{path}: poza photos/{p} nu există')
        # the repo is public: refuse photos that still carry camera/GPS metadata
        if b'Exif\x00\x00' in open(photo, 'rb').read(65536):
            sys.exit(f'photos/{p} are metadate EXIF (posibil GPS) — curăță-le înainte de commit')
    meta['id'] = os.path.basename(path)[:-3]
    meta['body'] = m.group(2).strip()
    return meta


def paragraphs(text):
    return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]


def split_body(body):
    """-> (head paragraphs, rest paragraphs); rest empty means no folding."""
    if MORE in body:
        head, rest = body.split(MORE, 1)
        return paragraphs(head), paragraphs(rest)
    paras = paragraphs(body)
    words = 0
    for i, p in enumerate(paras):
        words += len(p.split())
        if words > FOLD_WORDS and i > 0:
            return paras[:i], paras[i:]
    return paras, []


def render_quote(e):
    dialogue = e.get('style') == 'dialogue'
    cls = 'entry-quote entry-quote--dialogue' if dialogue else 'entry-quote'
    head, rest = split_body(e['body'])
    if not rest:
        inner = ''.join(f'\n          <p>{esc(p)}</p>' for p in head)
        return f'      <blockquote class="{cls}">{inner}\n        </blockquote>\n'
    if dialogue:
        lines = [f'<span class="dl">{esc(p)}' for p in head]
        summary = '</span>'.join(lines) + TOGGLE + '</span>'
    else:
        summary = '<br>'.join(esc(p) for p in head) + TOGGLE
    rest_html = ''.join(f'\n            <p>{esc(p)}</p>' for p in rest)
    return (f'      <blockquote class="{cls}">\n'
            f'          <details>\n'
            f'            <summary>{summary}</summary>\n'
            f'            <div class="quote-rest">{rest_html}\n'
            f'            </div>\n'
            f'          </details>\n'
            f'        </blockquote>\n')


def render_entry(e):
    y, m, d = (int(x) for x in e['date'].split('-'))
    classes = ['entry', f'entry--{e["kind"]}'] + (['entry--photoset'] if e['photos'] else [])
    out = [f'    <article class="{" ".join(classes)}">\n'
           f'      <div class="entry-meta">\n'
           f'        <span class="entry-kind">{KINDS[e["kind"]]}</span>\n'
           f'        <time class="entry-date">{d} {MONTHS[m - 1]} {y}</time>\n'
           f'      </div>\n'
           f'      <p class="entry-source">{esc(e["source"])}</p>\n']
    if e.get('intro'):
        out.append(f'      <p class="entry-intro">{esc(e["intro"])}</p>\n')
    if e['body']:
        out.append(render_quote(e))
    if e.get('note'):
        out.append(f'      <p class="entry-note">{esc(e["note"])}</p>\n')
    if e['photos']:
        srcs = [f'photos/{p}' for p in e['photos']]
        gallery = attr(json.dumps(srcs, ensure_ascii=False))
        btns = ''.join(
            f'\n          <button type="button" class="thumb-btn" data-gallery=\'{gallery}\' '
            f'data-index="{i}" data-caption="{attr(e["source"])}"><img src="{s}" alt="" loading="lazy"></button>'
            for i, s in enumerate(srcs))
        out.append(f'      <div class="entry-photos">{btns}\n        </div>\n')
    out.append('    </article>\n')
    return ''.join(out)


def main():
    entry_dir = os.path.join(ROOT, 'entries')
    entries = [parse(os.path.join(entry_dir, f)) for f in sorted(os.listdir(entry_dir)) if f.endswith('.md')]
    # newest first; same-day entries keep file-name order
    entries.sort(key=lambda e: e['id'])
    entries.sort(key=lambda e: e['date'], reverse=True)

    years = {}
    for e in entries:
        years.setdefault(e['date'][:4], []).append(e)

    nav = ''.join(f'      <a href="#y{y}" class="year-nav-item"><strong>{y}</strong> ({len(es)})</a>\n'
                  for y, es in years.items())
    nav = f'    <nav class="year-nav" aria-label="Navigare pe ani">\n{nav}    </nav>\n'
    body = ''.join(
        f'\n    <div class="year-marker" id="y{y}" aria-hidden="true">{y}</div>\n'
        + '\n'.join(render_entry(e) for e in es)
        for y, es in years.items())

    page = open(os.path.join(ROOT, 'template.html'), encoding='utf-8').read()
    page = (page.replace('{{NAV}}', nav).replace('{{ENTRIES}}', body)
            .replace('{{FIRST_YEAR}}', min(years)).replace('{{LAST_YEAR}}', max(years)))

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)
    shutil.copy(os.path.join(ROOT, 'avatar.jpg'), OUT)
    os.makedirs(os.path.join(OUT, 'photos'))
    for e in entries:
        for p in e['photos']:
            shutil.copy(os.path.join(ROOT, 'photos', p), os.path.join(OUT, 'photos', p))
    print(f'{len(entries)} intrări, {sum(len(e["photos"]) for e in entries)} poze -> {OUT}')


if __name__ == '__main__':
    main()
