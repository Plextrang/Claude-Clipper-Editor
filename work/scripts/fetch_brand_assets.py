"""Fetch REAL logos and UI glyphs for the scenes (never draw stand-in logos).
usage: python work/scripts/fetch_brand_assets.py                    everything in work/brand_assets.json (skips what exists)
       python work/scripts/fetch_brand_assets.py --si notion canva  extra simple-icons glyphs (slugs: https://simpleicons.org)
       python work/scripts/fetch_brand_assets.py --ui rocket_launch extra Material Symbols (https://fonts.google.com/icons)
       python work/scripts/fetch_brand_assets.py --commons "File title.svg" name.svg   one official logo from Wikimedia Commons
       add --force to re-download.
Writes (all git-ignored, so third-party trademarks never enter this repo):
  remotion/public/brand/<name>.svg     official full-colour logos (Wikimedia Commons, see work/brand_assets.json "commons")
  remotion/public/brand/si_<slug>.svg  monochrome brand glyphs (simple-icons, CC0) + brand_colors.json {slug: {title, hex}}
  remotion/public/ui/<name>[-fill].svg real UI glyphs (Google Material Symbols Rounded, Apache-2.0)
  remotion/public/brand/README.md      how to use them (from work/templates/brand_README.md) + an index of what is on disk
Sources are cached in work/brand_cache/. setup_check.py runs this when remotion/public/brand/ is missing."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json, glob, shutil, tarfile, subprocess, time, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # work/
PROJ = os.path.dirname(ROOT)
PUB = os.path.join(PROJ, 'remotion', 'public')
BRAND, UI = os.path.join(PUB, 'brand'), os.path.join(PUB, 'ui')
CACHE = os.path.join(ROOT, 'brand_cache')
MANIFEST = json.load(open(os.path.join(ROOT, 'brand_assets.json'), encoding='utf-8'))
UA = 'Claude-Clipper-Editor/2.0 (brand asset fetch; https://github.com/Plextrang/Claude-Clipper-Editor)'
FORCE = '--force' in sys.argv
problems = []


def opt(flag):
    """Values after --flag up to the next --option."""
    if flag not in sys.argv:
        return []
    out = []
    for a in sys.argv[sys.argv.index(flag) + 1:]:
        if a.startswith('--'):
            break
        out.append(a)
    return out


def npm_package(pkg):
    """Extract an npm package into work/brand_cache/<safe name>/package (once) and return that folder."""
    dest = os.path.join(CACHE, pkg.replace('@', '').replace('/', '_'))
    pdir = os.path.join(dest, 'package')
    if os.path.isdir(pdir) and not FORCE:
        return pdir
    os.makedirs(dest, exist_ok=True)
    npm = shutil.which('npm') or shutil.which('npm.cmd')
    if not npm:
        problems.append('npm not found: cannot fetch ' + pkg)
        return None
    r = subprocess.run([npm, 'pack', pkg, '--silent', '--pack-destination', dest], capture_output=True, text=True)
    tgz = sorted(glob.glob(os.path.join(dest, '*.tgz')))
    if r.returncode != 0 or not tgz:
        problems.append(f'npm pack {pkg} failed: {r.stderr.strip()[-300:]}')
        return None
    with tarfile.open(tgz[-1]) as t:
        t.extractall(dest)
    for f in tgz:
        os.remove(f)
    return pdir


def simple_icons(slugs):
    pdir = npm_package('simple-icons')
    if not pdir:
        return
    data = json.load(open(os.path.join(pdir, 'data', 'simple-icons.json'), encoding='utf-8'))
    data = data.get('icons', data) if isinstance(data, dict) else data
    by_slug = {}
    for x in data:  # the package names files by slug; titles map to slugs the same way the package does
        s = x.get('slug') or ''.join(ch for ch in x['title'].lower().replace('+', 'plus').replace('.', 'dot').replace('&', 'and') if ch.isalnum())
        by_slug[s] = x
    cpath = os.path.join(BRAND, 'brand_colors.json')
    colors = json.load(open(cpath, encoding='utf-8')) if os.path.exists(cpath) else {}
    for s in slugs:
        src = os.path.join(pdir, 'icons', s + '.svg')
        if not os.path.exists(src):
            problems.append(f'simple-icons has no "{s}" (check https://simpleicons.org; some brands, e.g. Adobe, are only on Commons)')
            continue
        dst = os.path.join(BRAND, 'si_' + s + '.svg')
        if FORCE or not os.path.exists(dst):
            shutil.copy(src, dst)
        x = by_slug.get(s, {})
        colors[s] = {'title': x.get('title', s), 'hex': '#' + x['hex'] if x.get('hex') else None}
    json.dump(colors, open(cpath, 'w', encoding='utf-8'), indent=1)


def material(names):
    pdir = npm_package('@material-symbols/svg-400')
    if not pdir:
        return
    for n in names:
        for v in ('', '-fill'):
            src = os.path.join(pdir, 'rounded', n + v + '.svg')
            dst = os.path.join(UI, n + v + '.svg')
            if not os.path.exists(src):
                if v == '':
                    problems.append(f'Material Symbols has no "{n}" (see https://fonts.google.com/icons)')
                continue
            if FORCE or not os.path.exists(dst):
                shutil.copy(src, dst)


def commons(name, title):
    dst = os.path.join(BRAND, name)
    if os.path.exists(dst) and not FORCE:
        return
    url = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(title.removeprefix('File:'))
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            body = urllib.request.urlopen(req, timeout=30).read()
            if name.endswith('.svg') and b'<svg' not in body[:4000]:
                raise ValueError('not an SVG')
            open(dst, 'wb').write(body)
            return
        except Exception as e:  # Commons rate-limits bursts: back off and retry
            err = e
            time.sleep(2 + 3 * attempt)
    problems.append(f'Commons "{title}" -> {name} failed: {err}')


def readme():
    tpl = open(os.path.join(ROOT, 'templates', 'brand_README.md'), encoding='utf-8').read()
    logos = sorted(f for f in os.listdir(BRAND) if f.endswith('.svg') and not f.startswith('si_'))
    glyphs = sorted(f[3:-4] for f in os.listdir(BRAND) if f.startswith('si_') and f.endswith('.svg'))
    ui = sorted({f[:-4].removesuffix('-fill') for f in os.listdir(UI) if f.endswith('.svg')})
    idx = ('\n\n## On disk now (generated)\n- Official logos (brand/): ' + ', '.join(logos)
           + '\n- simple-icons glyphs (brand/si_<slug>.svg; hex in brand/brand_colors.json): ' + ', '.join(glyphs)
           + '\n- Material Symbols (ui/<name>.svg + <name>-fill.svg): ' + ', '.join(ui) + '\n')
    open(os.path.join(BRAND, 'README.md'), 'w', encoding='utf-8', newline='\n').write(tpl + idx)


os.makedirs(BRAND, exist_ok=True)
os.makedirs(UI, exist_ok=True)
extra_si, extra_ui, extra_c = opt('--si'), opt('--ui'), opt('--commons')
one_off = bool(extra_si or extra_ui or extra_c)
simple_icons(extra_si if one_off else MANIFEST['simple_icons']['slugs'])
material(extra_ui if one_off else MANIFEST['material_symbols']['names'])
if one_off:
    if len(extra_c) == 2:
        commons(extra_c[1], extra_c[0])
    elif extra_c:
        problems.append('--commons takes exactly two values: "<Commons file title>" <name.svg>')
else:
    for name, title in MANIFEST['commons'].items():
        if not name.startswith('_'):
            commons(name, title)
            time.sleep(0.6)
readme()
n_logo = len([f for f in os.listdir(BRAND) if f.endswith('.svg') and not f.startswith('si_')])
n_si = len([f for f in os.listdir(BRAND) if f.startswith('si_')])
n_ui = len([f for f in os.listdir(UI) if f.endswith('.svg')])
print(f'brand assets: {n_logo} official logos, {n_si} brand glyphs, {n_ui} UI glyph files -> remotion/public/brand, remotion/public/ui')
for p in problems:
    print('  WARNING: ' + p)
