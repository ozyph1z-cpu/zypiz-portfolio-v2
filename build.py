"""Static build for the Zypiz portfolio.

    python build.py            validate content.json, then write index.html, sitemap.xml and robots.txt
    python build.py --check    validate only, and fail if index.html is not what the build would write

Everything editable lives in content.json. src/page.html is the page skeleton, src/style.css and
src/main.js are inlined into it. All text from the JSON is HTML-escaped; the only markup allowed in
it is <em>...</em>. The build stops with a list of problems instead of writing a broken page.
Python 3.9+, standard library only.
"""
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = ('https://fonts.googleapis.com/css2?family=Bowlby+One+SC&family=Barlow:wght@400;500;600'
         '&family=Barlow+Condensed:wght@500;600;700&family=JetBrains+Mono:wght@400;600&family=Permanent+Marker&display=swap')
SOUND_ICON = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 6h3l4-3v10l-4-3H2z"/><path d="M11 5.5a3.5 3.5 0 0 1 0 5M12.8 3.5a6 6 0 0 1 0 9" '
              'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>')
PLAY_ICON = '<svg viewBox="0 0 10 12" aria-hidden="true"><path d="M0 0 L10 6 L0 12 Z"/></svg>'


# ---------------------------------------------------------------- validation

class Invalid(Exception):
    pass


class V:
    """Walks content.json and collects every problem before failing."""

    def __init__(self, data):
        self.data, self.errors = data, []

    def err(self, path, msg):
        self.errors.append(f'{path}: {msg}')

    def get(self, obj, key, typ, path, required=True):
        if not isinstance(obj, dict):
            self.err(path, 'expected an object')
            return None
        if key not in obj:
            if required:
                self.err(f'{path}.{key}', 'missing')
            return None
        val = obj[key]
        types = typ if isinstance(typ, tuple) else (typ,)
        if bool in types or not isinstance(val, bool):
            if isinstance(val, types):
                if isinstance(val, str) and not val.strip():
                    self.err(f'{path}.{key}', 'empty text')
                return val
        self.err(f'{path}.{key}', f'expected {" or ".join(t.__name__ for t in types)}, got {type(val).__name__}')
        return None

    def text(self, obj, key, path, required=True):
        val = self.get(obj, key, str, path, required)
        if isinstance(val, str):
            bare = re.sub(r'</?em>', '', val)
            if '<' in bare or '>' in bare:
                self.err(f'{path}.{key}', 'raw HTML is not allowed (only <em>...</em>)')
            if val.count('<em>') != val.count('</em>'):
                self.err(f'{path}.{key}', 'unbalanced <em>')
        return val

    def file(self, rel, path):
        if not isinstance(rel, str) or not os.path.isfile(os.path.join(ROOT, rel)):
            self.err(path, f'file not found: {rel}')

    def link(self, href, path, anchors):
        if not isinstance(href, str):
            return
        if href.startswith('#'):
            if href[1:] not in anchors:
                self.err(path, f'link to missing section {href}')
        elif href.startswith('mailto:'):
            if not re.fullmatch(r'mailto:[^@\s]+@[^@\s]+\.[a-z]{2,}', href):
                self.err(path, f'bad email link {href}')
        elif not re.fullmatch(r'https://[a-z0-9.-]+\.[a-z]{2,}(/[^\s]*)?', href):
            self.err(path, f'links must be https:// (got {href})')


SECTIONS = {'main', 'top', 'work', 'cases', 'statics', 'systems', 'process', 'stack', 'about', 'contact', 'faq'}


def validate(d):
    v = V(d)
    site = v.get(d, 'site', dict, 'site') or {}
    for k in ('url', 'lang', 'locale', 'name', 'title', 'description', 'og_image', 'og_image_alt', 'theme_color', 'favicon', 'apple_touch_icon', 'logo'):
        v.text(site, k, 'site')
    v.link(site.get('url'), 'site.url', SECTIONS)
    if isinstance(site.get('url'), str) and not site['url'].endswith('/'):
        v.err('site.url', 'must end with /')
    if isinstance(site.get('description'), str) and not 50 <= len(site['description']) <= 170:
        v.err('site.description', f'keep it 50-170 characters for search results (now {len(site["description"])})')
    for k in ('og_image', 'favicon', 'apple_touch_icon', 'logo'):
        v.file(site.get(k), f'site.{k}')

    c = v.get(d, 'contact', dict, 'contact') or {}
    for k in ('email', 'discord', 'x_handle', 'x_url'):
        v.text(c, k, 'contact')
    v.link(f'mailto:{c.get("email")}', 'contact.email', SECTIONS)
    v.link(c.get('x_url'), 'contact.x_url', SECTIONS)

    for i, n in enumerate(v.get(d, 'nav', list, 'nav') or []):
        v.text(n, 'label', f'nav[{i}]')
        v.link(v.text(n, 'href', f'nav[{i}]'), f'nav[{i}].href', SECTIONS)
    v.text(d, 'cta_label', '')

    h = v.get(d, 'hero', dict, 'hero') or {}
    for k in ('title', 'sub', 'hint_mouse', 'hint_touch'):
        v.text(h, k, 'hero')
    for i, e in enumerate(v.get(h, 'eyebrow', list, 'hero') or []):
        if not isinstance(e, str):
            v.err(f'hero.eyebrow[{i}]', 'expected text')

    work = v.get(d, 'work', list, 'work') or []
    keys = set()
    for i, w in enumerate(work):
        p = f'work[{i}]'
        k = v.text(w, 'k', p)
        for f in ('title', 'tag', 'pill'):
            v.text(w, f, p)
        if v.text(w, 'filter', p) not in ('anim', 'ugc', None):
            v.err(f'{p}.filter', 'must be "anim" or "ugc"')
        dur = v.get(w, 'duration', (int, float), p)
        if k:
            if k in keys:
                v.err(f'{p}.k', f'duplicate key {k}')
            keys.add(k)
            for f in (f'media/{k}.mp4', f'media/full/{k}.mp4', f'assets/poster-{k}.webp'):
                v.file(f, f'{p} ({k})')
            if dur is not None and dur <= 0:
                v.err(f'{p}.duration', 'must be > 0')
    for i, r in enumerate(v.get(h, 'reel', list, 'hero') or []):
        if v.text(r, 'k', f'hero.reel[{i}]') not in keys:
            v.err(f'hero.reel[{i}].k', 'not in work')
        v.text(r, 'label', f'hero.reel[{i}]')
    for k in v.get(h, 'reel_cuts', list, 'hero') or []:
        v.file(f'media/reel_{k}.mp4', f'hero.reel_cuts ({k})')

    for i, s in enumerate(v.get(d, 'stats', list, 'stats') or []):
        v.get(s, 'to', (int, float), f'stats[{i}]')
        v.get(s, 'dec', int, f'stats[{i}]')
        v.get(s, 'suf', str, f'stats[{i}]', required=False)
        v.text(s, 'label', f'stats[{i}]')
    for i, f in enumerate(v.get(d, 'formats', list, 'formats') or []):
        if not isinstance(f, str) or not f.strip():
            v.err(f'formats[{i}]', 'expected text')

    v.text(d, 'cases_intro', '')
    for i, cs in enumerate(v.get(d, 'cases', list, 'cases') or []):
        p = f'cases[{i}]'
        if not v.get(cs, 'publish', bool, p):
            continue
        if v.text(cs, 'k', p) not in keys:
            v.err(f'{p}.k', 'not in work')
        for f in ('title', 'client', 'problem', 'did'):
            t = v.text(cs, f, p)
            if isinstance(t, str) and 'TODO' in t:
                v.err(f'{p}.{f}', 'published case still has a TODO')
        res = v.get(cs, 'results', list, p) or []
        if not res:
            v.err(f'{p}.results', 'a published case needs at least one real result')
        for j, r in enumerate(res):
            for f in ('value', 'label', 'measures'):
                v.text(r, f, f'{p}.results[{j}]')
        if cs.get('proof') is not None:
            v.file(cs['proof'], f'{p}.proof')

    for i, t in enumerate(v.get(d, 'testimonials', list, 'testimonials') or []):
        for f in ('quote', 'name', 'role', 'company'):
            v.text(t, f, f'testimonials[{i}]')

    st = v.get(d, 'statics', dict, 'statics') or {}
    for k in ('kicker', 'title', 'note'):
        v.text(st, k, 'statics')
    for g in ('ads', 'thumbs'):
        for i, im in enumerate(v.get(st, g, list, 'statics') or []):
            v.file(v.text(im, 'src', f'statics.{g}[{i}]'), f'statics.{g}[{i}].src')
            v.text(im, 'alt', f'statics.{g}[{i}]')
            v.text(im, 'label', f'statics.{g}[{i}]')

    sy = v.get(d, 'systems', dict, 'systems') or {}
    ft = v.get(sy, 'featured', dict, 'systems') or {}
    for k in ('role', 'title', 'tagline', 'before', 'after'):
        v.text(ft, k, 'systems.featured')
    for k in ('paras', 'flow', 'badges'):
        v.get(ft, k, list, 'systems.featured')
    for i, cd in enumerate(v.get(sy, 'cards', list, 'systems') or []):
        for k in ('role', 'title', 'text'):
            v.text(cd, k, f'systems.cards[{i}]')
        if cd.get('viz') not in ('chain', 'plate', 'box'):
            v.err(f'systems.cards[{i}].viz', 'must be chain, plate or box')

    for i, s in enumerate(v.get(d, 'process', list, 'process') or []):
        for k in ('title', 'text', 'who_label'):
            v.text(s, k, f'process[{i}]')
        if s.get('who') not in ('me', 'ai'):
            v.err(f'process[{i}].who', 'must be "me" or "ai"')

    for i, g in enumerate(v.get(d, 'tools', list, 'tools') or []):
        v.text(g, 'group', f'tools[{i}]')
        for j, it in enumerate(v.get(g, 'items', list, f'tools[{i}]') or []):
            if not (isinstance(it, list) and len(it) == 2 and all(isinstance(x, str) for x in it)):
                v.err(f'tools[{i}].items[{j}]', 'expected ["Name", "logo-id"]')
                continue
            logo = next((f'assets/logo-{it[1]}.{e}' for e in ('png', 'svg', 'webp') if os.path.isfile(os.path.join(ROOT, f'assets/logo-{it[1]}.{e}'))), None)
            if not logo:
                v.err(f'tools[{i}].items[{j}]', f'no logo file assets/logo-{it[1]}.png/svg/webp')

    ab = v.get(d, 'about', dict, 'about') or {}
    for k in ('photo', 'photo_alt', 'title', 'bio'):
        v.text(ab, k, 'about')
    v.file(ab.get('photo'), 'about.photo')
    for i, r in enumerate(v.get(ab, 'roles', list, 'about') or []):
        v.text(r, 'y', f'about.roles[{i}]')
        v.text(r, 'label', f'about.roles[{i}]')
    for i, e in enumerate(v.get(ab, 'edu', list, 'about') or []):
        for k in ('name', 'where', 'status'):
            v.text(e, k, f'about.edu[{i}]')

    cta = v.get(d, 'cta', dict, 'cta') or {}
    v.text(cta, 'title', 'cta')
    v.text(cta, 'text', 'cta')

    for i, f in enumerate(v.get(d, 'faq', list, 'faq') or []):
        if v.get(f, 'publish', bool, f'faq[{i}]'):
            for k in ('q', 'a'):
                t = v.text(f, k, f'faq[{i}]')
                if isinstance(t, str) and 'TODO' in t:
                    v.err(f'faq[{i}].{k}', 'published answer still has a TODO')

    ftr = v.get(d, 'footer', dict, 'footer') or {}
    v.text(ftr, 'place', 'footer')
    v.get(ftr, 'year', int, 'footer')

    # published text must not leak internal notes
    def scan(o, path):
        if isinstance(o, dict):
            if o.get('publish') is False:
                return
            for k, x in o.items():
                if k not in ('todo', 'testimonials_todo'):
                    scan(x, f'{path}.{k}' if path else k)
        elif isinstance(o, list):
            for i, x in enumerate(o):
                scan(x, f'{path}[{i}]')
        elif isinstance(o, str) and re.search(r'\b(TODO|confirmar|definir)\b', o):
            v.err(path, f'internal note in published text: "{o[:60]}"')
    scan(d, '')

    if v.errors:
        raise Invalid('\n'.join(v.errors))


# ---------------------------------------------------------------- rendering

def e(s):
    return html.escape(str(s), quote=True)


def rich(s):
    """Escaped text where <em>...</em> survives."""
    return e(s).replace('&lt;em&gt;', '<em>').replace('&lt;/em&gt;', '</em>')


def mmss(t):
    t = int(round(t))
    return f'{t // 60}:{t % 60:02d}'


def num_text(s):
    return f'{s["to"]:.{s["dec"]}f}{s.get("suf", "")}'


def logo_of(ic):
    return next(f'assets/logo-{ic}.{x}' for x in ('png', 'svg', 'webp') if os.path.isfile(os.path.join(ROOT, f'assets/logo-{ic}.{x}')))


def badges(items):
    return '<div class="badges">' + ''.join(f'<span class="badge{" g" if b["hi"] else ""}">{e(b["text"])}</span>' for b in items) + '</div>'


def contact_links(c, cls):
    return (f'<ul class="{cls}">'
            f'<li><a href="mailto:{e(c["email"])}" data-copy="{e(c["email"])}"><b>Email</b><span>{e(c["email"])}</span></a></li>'
            f'<li><a href="https://discord.com/app" data-copy="{e(c["discord"])}" target="_blank" rel="noopener"><b>Discord</b><span>{e(c["discord"])}</span></a></li>'
            f'<li><a href="{e(c["x_url"])}" target="_blank" rel="noopener"><b>X</b><span>{e(c["x_handle"])}</span></a></li>'
            '</ul>')


def r_header(d):
    nav = ''.join(f'<a href="{e(n["href"])}">{e(n["label"])}</a>' for n in d['nav'])
    return f'''<header class="top">
  <div class="wrap">
    <a href="#main" aria-label="{e(d["site"]["name"])} home"><img class="logo" src="{e(d["site"]["logo"])}" width="89" height="34" alt="{e(d["site"]["name"])}"></a>
    <nav class="nav" aria-label="Sections">{nav}</nav>
    <div class="top-r">
      <a class="pill" href="#contact" data-open="talk">{e(d["cta_label"])}</a>
      <button class="burger" id="burger" type="button" aria-expanded="false" aria-controls="mnav" aria-label="Menu"><i></i></button>
    </div>
  </div>
  <nav class="mnav" id="mnav" aria-label="Sections (mobile)" hidden>{nav}</nav>
</header>'''


def r_hero(d):
    h = d['hero']
    title = rich(h['title']).replace('<em>', '<span class="bite">', 1).replace(
        '</em>', '<svg viewBox="0 0 200 20" preserveAspectRatio="none" aria-hidden="true"><path d="M4 14 C 50 4, 110 18, 196 6"/></svg></span>', 1)
    eyebrow = ' <i>·</i> '.join(e(x) for x in h['eyebrow'])
    cuts = set(h['reel_cuts'])
    vids = []
    for i, r in enumerate(h['reel']):
        src = f'media/reel_{r["k"]}.mp4' if r['k'] in cuts else f'media/{r["k"]}.mp4'
        vids.append(f'<video{" class=\"on\"" if i == 0 else ""} muted loop playsinline preload="none" poster="assets/poster-{e(r["k"])}.webp" '
                    f'data-src="{src}" data-k="{e(r["k"])}" data-label="{e(r["label"])}" aria-hidden="true"></video>')
    first = h['reel'][0]
    return f'''<section class="hero" aria-label="Intro">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p class="sub">{e(h["sub"])}</p>
      <div class="hero-cta"><a class="pill big" href="#contact" data-open="talk">{e(d["cta_label"])} →</a><a class="link-btn" href="#work">See the work</a></div>
      <div class="mascot-row">
        <a class="mascot" id="mascot" href="#contact" data-open="talk" aria-label="{e(d["cta_label"])}">
          <span class="glow"></span>
          <span class="gob" id="gob">
            <span class="lay ear-l" data-d="3"><img src="assets/gob-ear-l.webp" width="240" height="240" alt=""></span>
            <span class="lay ear-r" data-d="3"><img src="assets/gob-ear-r.webp" width="240" height="240" alt=""></span>
            <span class="lay head" data-d="3.5">
              <img class="st on" data-st="rest" src="assets/gob-rest.webp" width="240" height="240" alt="">
              <img class="st" data-st="open" src="assets/gob-open.webp" width="240" height="240" alt="" loading="lazy">
              <img class="st" data-st="bite" src="assets/gob-bite.webp" width="240" height="240" alt="" loading="lazy">
            </span>
            <span class="lay hairw" data-d="8"><img class="hair" src="assets/gob-hair.webp" width="240" height="240" alt=""></span>
          </span>
          <span class="plaque" aria-hidden="true">{e(d["cta_label"]).upper()}</span>
        </a>
        <svg class="arrow" viewBox="0 0 200 110" aria-hidden="true">
          <path d="M194 30 C 172 8, 140 12, 132 34 C 124 56, 156 60, 158 40 C 160 20, 124 20, 100 40 C 76 60, 48 68, 14 64"/>
          <path d="M30 50 L12 64 L32 78"/>
        </svg>
        <p class="arrow-note" aria-hidden="true"><span class="hint-mouse">{e(h["hint_mouse"])}</span><span class="hint-touch">{e(h["hint_touch"])}</span></p>
      </div>
    </div>
    <div class="phone-col">
      <div class="handphone" id="handphone">
        <div class="hp-float">
          <a class="phone" id="phone" href="media/full/{e(first["k"])}.mp4" data-play="{e(first["k"])}" aria-label="Play the reel clip with sound">
            {"".join(vids)}
            <span class="tagline" id="phoneTag">{e(first["label"])}</span>
            <span class="snd">{SOUND_ICON}Tap for sound</span>
            <span class="dots" id="dots" aria-hidden="true">{"<i></i>" * len(h["reel"])}</span>
          </a>
          <img class="hand" src="assets/hand.webp" width="540" height="746" alt="" fetchpriority="high">
        </div>
        <svg class="burst b1" viewBox="0 0 60 60" aria-hidden="true"><path d="M30 6 L32 24 M12 14 L22 28 M6 34 L20 36"/></svg>
        <svg class="burst b2" viewBox="0 0 60 60" aria-hidden="true"><path d="M30 6 L28 24 M48 14 L38 28 M54 34 L40 36"/></svg>
      </div>
    </div>
  </div>
</section>'''


def r_stats(d):
    cells = ''.join(f'<div class="stat"><p class="num" data-to="{s["to"]}" data-dec="{s["dec"]}" data-suf="{e(s.get("suf", ""))}">{e(num_text(s))}</p>'
                    f'<p class="lab">{e(s["label"])}</p></div>' for s in d['stats'])
    return f'''<section class="results" id="results" aria-label="Results">
  <div class="wrap"><div class="stats">{cells}</div></div>
  <div class="full"><button class="link-btn" type="button" data-open="formats">See every format I cut →</button></div>
</section>'''


def r_marquee(d):
    track = ''.join(f'<span>{e(f)}</span><i>·</i>' for f in d['formats'])
    return f'<div class="marquee" aria-hidden="true"><div class="mtrack" id="mtrack">{track}{track}</div></div>'


def card(w):
    k = e(w['k'])
    return (f'<a class="card" href="media/full/{k}.mp4" data-play="{k}" data-f="{e(w["filter"])}" data-title="{e(w["title"])}">'
            f'<span class="vid"><video muted loop playsinline preload="none" poster="assets/poster-{k}.webp" data-src="media/{k}.mp4" aria-hidden="true"></video>'
            f'<span class="stat-pill">{e(w["pill"])}</span>'
            f'<span class="play"><span>{PLAY_ICON}</span><em>Click for sound · drag to scrub</em></span>'
            f'<span class="dur">{SOUND_ICON}<span class="sr">Length </span>{mmss(w["duration"])}</span>'
            f'<i class="sbar"><b></b></i><span class="stc"></span></span>'
            f'<span class="meta"><b>{e(w["title"])}</b><span>{e(w["tag"])}</span></span></a>')


def r_work(d):
    w = d['work']
    half = (len(w) + 1) // 2
    return f'''<section id="work">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="kicker">Recent work</p><h2>Fresh from the cave</h2></div>
      <div class="chips" role="group" aria-label="Filter work">
        <button class="chip" type="button" aria-pressed="true" data-f="all">All</button>
        <button class="chip" type="button" aria-pressed="false" data-f="ugc">AI UGC</button>
        <button class="chip" type="button" aria-pressed="false" data-f="anim">AI Animation</button>
      </div>
    </div>
  </div>
  <div class="lanes" id="lanes">
    <div class="lane"><div class="row" id="row1">{"".join(card(x) for x in w[:half])}</div></div>
    <div class="lane rev"><div class="row" id="row2" style="--dur:84s">{"".join(card(x) for x in w[half:])}</div></div>
  </div>
  <p class="wrap lanes-hint">Every clip opens the full cut with sound.</p>
</section>'''


def r_cases(d):
    pub = [c for c in d['cases'] if c['publish']]
    if not pub:
        return '<!-- cases: none published yet -->'
    work = {w['k']: w for w in d['work']}
    out = []
    for c in pub:
        w = work[c['k']]
        res = ''.join(f'<li><b>{e(r["value"])}</b><span>{e(r["label"])}</span><small>{e(r["measures"])}</small></li>' for r in c['results'])
        proof = (f'<figure class="proof"><img src="{e(c["proof"])}" alt="Analytics screenshot for {e(c["title"])}" loading="lazy"></figure>'
                 if c.get('proof') else f'<!-- TODO proof: {e(c.get("todo", "screenshot"))} -->')
        out.append(f'''<article class="case">
      <a class="case-vid" href="media/full/{e(c["k"])}.mp4" data-play="{e(c["k"])}" data-title="{e(w["title"])}">
        <img src="assets/poster-{e(c["k"])}.webp" width="270" height="480" alt="" loading="lazy">
        <span class="play"><span>{PLAY_ICON}</span></span><span class="dur">{SOUND_ICON}<span class="sr">Watch with sound, </span>{mmss(w["duration"])}</span>
      </a>
      <div class="case-body">
        <p class="role">{e(c["client"])}</p>
        <h3>{e(c["title"])}</h3>
        <dl class="pdr">
          <div><dt>Problem</dt><dd>{e(c["problem"])}</dd></div>
          <div><dt>What I did</dt><dd>{e(c["did"])}</dd></div>
        </dl>
        <p class="res-h">Result</p>
        <ul class="res">{res}</ul>
        {proof}
      </div>
    </article>''')
    return f'''<section class="bt" id="cases">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">Proof, not promises</p><h2>Mini cases</h2></div><p class="sec-note">{e(d["cases_intro"])}</p></div>
    <div class="cases">{"".join(out)}</div>
  </div>
</section>'''


def r_testimonials(d):
    if not d['testimonials']:
        return '<!-- TODO testimonials: add them to content.json (see testimonials_todo); the section renders when the list is not empty -->'
    q = ''.join(f'<figure class="quote"><blockquote>{rich(t["quote"])}</blockquote><figcaption><b>{e(t["name"])}</b> {e(t["role"])}, {e(t["company"])}</figcaption></figure>'
                for t in d['testimonials'])
    return f'<section class="bt" id="words"><div class="wrap"><div class="sec-head"><div><p class="kicker">Clients</p><h2>In their words</h2></div></div><div class="quotes">{q}</div></div></section>'


def r_statics(d):
    s = d['statics']

    def still(im, cls, w, h):
        return (f'<button class="still {cls}" type="button" data-full="{e(im["src"])}" aria-label="Enlarge: {e(im["alt"])}">'
                f'<img src="{e(im["src"])}" width="{w}" height="{h}" alt="" loading="lazy" decoding="async"><span aria-hidden="true">{e(im["label"])}</span></button>')
    return f'''<section class="bt" id="statics">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">{e(s["kicker"])}</p><h2>{e(s["title"])}</h2></div><p class="sec-note">{e(s["note"])}</p></div>
    <div class="sgal">{"".join(still(i, "ad", 360, 540) for i in s["ads"])}</div>
    <div class="tgal">{"".join(still(i, "th", 480, 270) for i in s["thumbs"])}</div>
  </div>
</section>'''


def r_systems(d):
    f = d['systems']['featured']
    flow = ''.join(f'<li class="node"><span class="k">{i + 1:02d}</span>{e(x)}</li>' for i, x in enumerate(f['flow']))
    viz = {
        'chain': '<div class="chain">' + ''.join(f'<span style="--i:{i}">{x}</span>' for i, x in enumerate(['script', 'voice', '3D scenes', 'sound', 'QA', 'export'])) + '</div>',
        'plate': '<div class="plate"><span>ZYP1Z26</span><i class="scan"></i></div>',
        'box': '<div class="box3"><div class="b"></div><div class="lidb"></div><span class="star" style="left:-14px;top:4px">✦</span><span class="star" style="right:-14px;top:0">✦</span></div>',
    }
    cards = ''.join(f'''<article class="sc">
          <div class="viz" aria-hidden="true">{viz[c["viz"]]}</div>
          <p class="role">{e(c["role"])}</p>
          <h3>{e(c["title"])}</h3>
          <p>{e(c["text"])}</p>
          {badges(c["badges"])}
        </article>''' for c in d['systems']['cards'])
    return f'''<section class="bt" id="systems">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">Dev and AI engineering</p><h2>Systems I built</h2></div></div>
    <div class="sys">
      <article class="feat">
        <div>
          <p class="role">{e(f["role"])}</p>
          <h3>{e(f["title"])}</h3>
          <p class="tagl">{e(f["tagline"])}</p>
          {"".join(f"<p>{e(p)}</p>" for p in f["paras"])}
          {badges(f["badges"])}
        </div>
        <div>
          <ol class="flow" id="flow">{flow}</ol>
          <div class="bars" id="bars">
            <div class="bar"><span>Before</span><div class="t"><i style="--w:100%"></i></div><b>{e(f["before"])}</b></div>
            <div class="bar after"><span>After</span><div class="t"><i style="--w:2%"></i></div><b>{e(f["after"])}</b></div>
          </div>
        </div>
      </article>
      <div class="sgrid">{cards}</div>
    </div>
  </div>
</section>'''


def r_process(d):
    steps = ''.join(f'<li class="step"><p class="n" aria-hidden="true">{i + 1:02d}</p><h3>{e(s["title"])}</h3><p>{e(s["text"])}</p>'
                    f'<span class="who {s["who"]}">{e(s["who_label"])}</span></li>' for i, s in enumerate(d['process']))
    return f'''<section class="bt" id="process">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">Process</p><h2>Where AI works, where I decide</h2></div><p class="sec-note">Scroll to scrub</p></div>
    <div class="tl" id="tl" aria-hidden="true">
      <div class="tl-top"><span>ad_v3_final_FINAL.prproj</span><span class="tc" id="tc">00:00:00:00</span></div>
      <div class="tracks">
        <div class="ruler"></div>
        <div class="trk" data-n="V2"><span class="clip" style="left:28%;width:20%;background:var(--paper)">hooks ×3</span><span class="clip" style="left:76%;width:22%;background:var(--paper)">captions</span></div>
        <div class="trk" data-n="V1"><span class="clip" style="left:0;width:24%;background:var(--soft)">refs + brief</span><span class="clip" style="left:50%;width:24%;background:var(--lilac)">AI scenes</span><span class="clip" style="left:76%;width:22%;background:var(--lime)">motion</span></div>
        <div class="trk" data-n="A1"><span class="clip wave" style="left:50%;width:24%">AI voice</span><span class="clip wave" style="left:76%;width:22%">mix −20 dB SFX</span></div>
        <div class="head-line" id="playhead"></div>
      </div>
    </div>
    <ol class="steps" id="steps">{steps}</ol>
  </div>
</section>'''


def r_stack(d):
    i = 0
    cols = []
    for g in d['tools']:
        rows = []
        for name, ic in g['items']:
            rows.append(f'<li class="tr" style="--i:{i}"><span class="ico"><img src="{logo_of(ic)}" width="24" height="24" alt="" loading="lazy"></span>{e(name)}</li>')
            i += 1
        cols.append(f'<div class="tcol"><h3>{e(g["group"])}</h3><ul>{"".join(rows)}</ul></div>')
    return f'''<section class="bt" id="stack">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">The stack</p><h2>Tools in the cave</h2></div></div>
    <div class="term">
      <div class="term-bar" aria-hidden="true"><i></i><i></i><i></i><span>zypiz@cave — tools</span></div>
      <p class="cmd" aria-hidden="true"><b>zypiz@cave</b>:~$ <span id="typed">ls ./tools --by-use</span><span class="caret"></span></p>
      <div class="tgrid" id="tgrid">{"".join(cols)}</div>
    </div>
  </div>
</section>'''


def r_about(d):
    a = d['about']
    roles = ''.join(f'<div class="rolec"><p class="y{" na" if r["na"] else ""}">{e(r["y"])}</p><p>{e(r["label"])}</p></div>' for r in a['roles'])
    edu = ''.join(f'<li><span><b>{e(x["name"])}</b><small>{e(x["where"])}</small></span><em class="{"done" if x["done"] else ""}">{e(x["status"])}</em></li>' for x in a['edu'])
    return f'''<section class="bt" id="about">
  <div class="wrap about-grid">
    <figure class="photo"><img src="{e(a["photo"])}" width="300" height="447" alt="{e(a["photo_alt"])}" loading="lazy" decoding="async"></figure>
    <div>
      <p class="kicker">About</p>
      <h2>{e(a["title"])}</h2>
      <p class="bio">{rich(a["bio"])}</p>
      <div class="roles">{roles}</div>
      <ul class="edu">{edu}</ul>
    </div>
  </div>
</section>'''


def r_contact(d):
    c = d['cta']
    return f'''<section class="bt cta" id="contact">
  <div class="wrap">
    <img class="peek" src="assets/peek.webp" width="120" height="125" alt="" loading="lazy">
    <h2>{rich(c["title"])}</h2>
    <p>{e(c["text"])}</p>
    <a class="pill big" href="#contact" data-open="talk">{e(d["cta_label"])} →</a>
    {contact_links(d["contact"], "socials")}
  </div>
</section>'''


def r_faq(d):
    items = ''.join(f'<details><summary>{e(f["q"])}<span class="x" aria-hidden="true"></span></summary><div class="ans">{rich(f["a"])}</div></details>'
                    for f in d['faq'] if f['publish'])
    todo = ''.join(f'<!-- TODO faq hidden: {e(f["q"])} ({e(f.get("todo", ""))}) -->' for f in d['faq'] if not f['publish'])
    return f'''<section class="bt faq" id="faq">
  <div class="wrap">
    <div class="sec-head"><div><p class="kicker">FAQ</p><h2>Before you send it</h2></div></div>
    {items}{todo}
    <p class="faq-cta">Still unsure? <a href="#contact" data-open="talk">{e(d["cta_label"])}</a> and ask.</p>
  </div>
</section>'''


def r_footer(d):
    f = d['footer']
    return f'''<footer>
  <div class="wrap">
    <p><b>{e(d["site"]["name"])}</b> · {e(f["place"])}</p>
    {contact_links(d["contact"], "fcontacts")}
    <p>© {f["year"]} {e(d["site"]["name"])}</p>
  </div>
</footer>'''


def r_dialogs(d):
    c = d['contact']
    fl = ''.join(f'<li>{e(x)}</li>' for x in d['formats'])
    return f'''<dialog id="talk" aria-labelledby="talkTitle">
  <button class="close" type="button" data-close aria-label="Close">✕</button>
  <h2 id="talkTitle">I know you want to work with me.</h2>
  <p>Message me here:</p>
  <button class="opt" type="button" data-copy="{e(c["email"])}"><span><b>Email</b><small>{e(c["email"])}</small></span><em>Copy</em></button>
  <button class="opt" type="button" data-copy="{e(c["discord"])}"><span><b>Discord</b><small>{e(c["discord"])}</small></span><em>Copy</em></button>
  <a class="opt" href="{e(c["x_url"])}" target="_blank" rel="noopener"><span><b>X</b><small>{e(c["x_handle"])}</small></span><em>Open ↗</em></a>
</dialog>
<dialog id="player" class="player" aria-labelledby="playerTitle">
  <button class="close" type="button" data-close aria-label="Close">✕</button>
  <h2 id="playerTitle">Video</h2>
  <video id="playerVid" playsinline controls preload="metadata"></video>
</dialog>
<dialog id="imgbox" class="imgbox" aria-label="Enlarged image">
  <button class="close" type="button" data-close aria-label="Close">✕</button>
  <img id="imgboxImg" alt="">
</dialog>
<dialog id="formats" aria-labelledby="formatsTitle">
  <button class="close" type="button" data-close aria-label="Close">✕</button>
  <h2 id="formatsTitle">Formats I cut</h2>
  <p>From real deliveries and my own channel.</p>
  <ul class="flist">{fl}</ul>
</dialog>'''


def render(d):
    s, c = d['site'], d['contact']
    jsonld = json.dumps({
        '@context': 'https://schema.org', '@type': 'Person', 'name': 'Marcelo', 'alternateName': s['name'],
        'url': s['url'], 'image': s['url'] + d['about']['photo'], 'jobTitle': 'Video editor, AI engineer and developer',
        'email': f'mailto:{c["email"]}', 'sameAs': [c['x_url']],
    }, ensure_ascii=False).replace('</', '<\\/')
    css = open(os.path.join(ROOT, 'src/style.css'), encoding='utf-8').read()
    js = open(os.path.join(ROOT, 'src/main.js'), encoding='utf-8').read()
    work_js = json.dumps({w['k']: {'t': w['title']} for w in d['work']}, ensure_ascii=False).replace('</', '<\\/')
    js = js.replace('/*@WORK@*/{}', work_js)
    parts = {
        'lang': e(s['lang']), 'title': e(s['title']), 'description': e(s['description']), 'url': e(s['url']),
        'theme_color': e(s['theme_color']), 'favicon': e(s['favicon']), 'apple_touch_icon': e(s['apple_touch_icon']),
        'name': e(s['name']), 'locale': e(s['locale']), 'og_image_url': e(s['url'] + s['og_image']), 'og_image_alt': e(s['og_image_alt']),
        'x_handle': e(c['x_handle']), 'jsonld': jsonld, 'fonts': e(FONTS), 'css': css, 'js': js,
        'header': r_header(d), 'hero': r_hero(d), 'stats': r_stats(d), 'marquee': r_marquee(d), 'work': r_work(d),
        'cases': r_cases(d), 'testimonials': r_testimonials(d), 'statics': r_statics(d), 'systems': r_systems(d),
        'process': r_process(d), 'stack': r_stack(d), 'about': r_about(d), 'contact': r_contact(d), 'faq': r_faq(d),
        'footer': r_footer(d), 'dialogs': r_dialogs(d),
    }
    page = open(os.path.join(ROOT, 'src/page.html'), encoding='utf-8').read()
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: parts[m.group(1)], page)
    left = re.findall(r'\{\{\w+\}\}', out)
    if left:
        raise Invalid(f'template placeholders without content: {left}')
    return out


def sitemap(d):
    today = datetime.date.today().isoformat()
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <url><loc>{e(d["site"]["url"])}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>\n</urlset>\n')


def robots(d):
    return f'User-agent: *\nAllow: /\n\nSitemap: {d["site"]["url"]}sitemap.xml\n'


def main():
    check = '--check' in sys.argv
    try:
        with open(os.path.join(ROOT, 'content.json'), encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as x:
        sys.exit(f'content.json is not valid JSON: line {x.lineno}, column {x.colno}: {x.msg}')
    try:
        validate(data)
        page = render(data)
    except Invalid as x:
        sys.exit('Build stopped, nothing was written. Fix content.json:\n  ' + str(x).replace('\n', '\n  '))
    out = {'index.html': page, 'robots.txt': robots(data)}
    if check:
        cur = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read() if os.path.exists(os.path.join(ROOT, 'index.html')) else ''
        if cur != page:
            sys.exit('index.html is out of date: run python build.py and commit the result.')
        print('content.json is valid and index.html is up to date.')
        return
    out['sitemap.xml'] = sitemap(data)
    for name, text in out.items():
        with open(os.path.join(ROOT, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    pub = sum(1 for c in data['cases'] if c['publish'])
    print(f'Built index.html ({len(page) // 1024} KB), sitemap.xml, robots.txt: {len(data["work"])} videos, {pub} cases, '
          f'{sum(1 for f in data["faq"] if f["publish"])} FAQ answers.')
    todo = [c['title'] for c in data['cases'] if not c['publish']] + [f['q'] for f in data['faq'] if not f['publish']]
    if todo or not data['testimonials']:
        print('Hidden until you fill them in:', '; '.join(todo + (['testimonials'] if not data['testimonials'] else [])))


if __name__ == '__main__':
    main()
