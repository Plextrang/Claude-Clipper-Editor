"""Real B-roll for the full-screen inserts of the kit styles: find it, look at it, save it, credit it.
usage:
  python work/scripts/broll_fetch.py search "walmart store" [--video] [--n 12]
        searches Wikimedia Commons (free licences, no account or key needed), saves a numbered contact sheet to
        work/frames/broll_<query>.png (Read it to choose) and prints each candidate's licence and author
  python work/scripts/broll_fetch.py get <n> --as walmart          candidate n of the LAST search
  python work/scripts/broll_fetch.py get "<query>:<n>" --as walmart  candidate n of an earlier search
  python work/scripts/broll_fetch.py get <direct media URL> --as gopro --source <page URL> --license "<licence>" [--author "<who>"] [--title "<what>"]
        any picture or clip you found yourself, e.g. with the Claude in Chrome extension on Pexels / Unsplash / Commons:
        pass the FILE's URL (.jpg/.png/.webp/.mp4/.webm), the page it came from and its licence. Pexels videos: the page's
        download link works as the URL, e.g. https://www.pexels.com/download/video/8100345/ --license "Pexels License"
        (skip Pexels' "aigc" ad clips: they are AI-generated)
  python work/scripts/broll_fetch.py list                          what is in remotion/public/broll/ + the credits
  options for clips: --start 2.5 (seconds into the source) --dur 6 (max seconds kept, default 8)
Files go to remotion/public/broll/<name>.jpg|.mp4 (git-ignored, archived with the video): pictures as JPEG (long side <=
1600 px), clips conformed to 1080x1920 30 fps H.264 without sound. Credits go to work/plan/broll_credits.json and into
the edit's notes. Only use media whose licence allows reuse (CC0, public domain, CC BY, CC BY-SA, Pexels, Unsplash);
never NC/ND, never "fair use", never a random image search result without a licence."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, io, json, re, subprocess, urllib.request, urllib.parse, html
try:  # file titles can be in any language
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
OUT = os.path.join(PROJ, 'remotion', 'public', 'broll')
SEARCHES = os.path.join(ROOT, 'broll')
CREDITS = os.path.join(ROOT, 'plan', 'broll_credits.json')
UA = 'ClaudeClipperEditor/2.0 (https://github.com/Plextrang/Claude-Clipper-Editor; video B-roll)'
API = 'https://commons.wikimedia.org/w/api.php'
BAD = re.compile(r'(?:\bNC\b|\bND\b|non[- ]?commercial|no ?deriv|fair use|non-free|all rights reserved)', re.I)
VID = ('.mp4', '.webm', '.ogv', '.mov', '.m4v')


def opt(name, default=None):
    a = sys.argv
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0 Safari/537.36'


def fetch(url, timeout=60):
    # Wikimedia asks for a descriptive agent; stock sites (Pexels, Unsplash) only serve browser-like ones
    ua = UA if 'wikimedia.org' in url else BROWSER_UA
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get('Content-Type', '')


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:40] or 'broll'


def clean(htmltext):
    return html.unescape(re.sub(r'<[^>]+>', '', htmltext or '')).strip()[:120]


def search():
    q = sys.argv[2]
    n = int(opt('--n', 12))
    video = '--video' in sys.argv
    params = {'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': '6', 'gsrlimit': str(n * 3),
              'gsrsearch': f'{q} filetype:{"video" if video else "bitmap"}', 'prop': 'imageinfo',
              'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': '1280'}
    data = json.loads(fetch(API + '?' + urllib.parse.urlencode(params))[0])
    pages = sorted((data.get('query') or {}).get('pages', {}).values(), key=lambda p: p.get('index', 0))
    cands = []
    for pg in pages:
        ii = (pg.get('imageinfo') or [{}])[0]
        md = ii.get('extmetadata') or {}
        lic = clean((md.get('LicenseShortName') or {}).get('value', ''))
        if not lic or BAD.search(lic) or (md.get('NonFree') or {}).get('value') in ('true', True):
            continue
        if not video and min(ii.get('width', 0), ii.get('height', 0)) < 600:
            continue
        cands.append({'title': pg['title'].replace('File:', ''), 'license': lic,
                      'author': clean((md.get('Artist') or {}).get('value', '')) or 'unknown',
                      'source': ii.get('descriptionurl'), 'url': ii.get('url'), 'thumb': ii.get('thumburl'),
                      'width': ii.get('width'), 'height': ii.get('height'), 'video': video,
                      'duration': ii.get('duration')})
        if len(cands) >= n:
            break
    if not cands:
        sys.exit(f'nothing with a reusable licence for "{q}" on Wikimedia Commons: try other words, or find it with the '
                 'Claude in Chrome extension (Pexels / Unsplash) and use: broll_fetch.py get <file URL> --source ... --license ...')
    os.makedirs(SEARCHES, exist_ok=True)
    json.dump({'query': q, 'candidates': cands}, open(os.path.join(SEARCHES, slug(q) + '.json'), 'w'), indent=1)
    json.dump({'last': slug(q)}, open(os.path.join(SEARCHES, '_last.json'), 'w'))
    # numbered contact sheet
    from PIL import Image, ImageDraw
    cw, ch = 270, 340
    cols = 4
    rows = (len(cands) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cw, rows * (ch + 26)), (22, 22, 24))
    dr = ImageDraw.Draw(sheet)
    for i, c in enumerate(cands):
        x, y = (i % cols) * cw, (i // cols) * (ch + 26)
        try:
            im = Image.open(io.BytesIO(fetch(c['thumb'])[0])).convert('RGB')
            r = max(cw / im.width, ch / im.height)
            im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
            im = im.crop(((im.width - cw) // 2, (im.height - ch) // 2, (im.width - cw) // 2 + cw, (im.height - ch) // 2 + ch))
            sheet.paste(im, (x, y + 26))
        except Exception as e:  # a broken thumbnail just leaves its cell empty
            dr.text((x + 8, y + 60), f'no preview ({type(e).__name__})', fill=(200, 80, 80))
        dr.text((x + 6, y + 6), f"#{i + 1} {c['license'][:22]}", fill=(255, 214, 10))
    os.makedirs(os.path.join(ROOT, 'frames'), exist_ok=True)
    sp = os.path.join(ROOT, 'frames', f'broll_{slug(q)}.png')
    sheet.save(sp)
    for i, c in enumerate(cands, 1):
        extra = f", {float(c['duration']):.0f} s" if c.get('duration') else ''
        print(f"#{i:2d} {c['width']}x{c['height']}{extra} | {c['license']} | {c['author'][:40]} | {c['title'][:60]}")
    print(f'contact sheet: work/frames/{os.path.basename(sp)}  (Read it, then: broll_fetch.py get <n> --as <name>)')


def save_media(raw, ctype, src_url, name, is_video):
    os.makedirs(OUT, exist_ok=True)
    if is_video:
        tmp = os.path.join(OUT, f'_{name}.src')
        open(tmp, 'wb').write(raw)
        dst = os.path.join(OUT, name + '.mp4')
        start = float(opt('--start', 0))
        dur = float(opt('--dur', 8))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-i', tmp, '-t', str(dur), '-an', '-vf',
                        'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,format=yuv420p',
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-g', '15', '-bf', '0', '-movflags', '+faststart', dst],
                       check=True)
        os.remove(tmp)
        return dst
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    r = min(1.0, 1600 / max(im.size))
    if r < 1:
        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    dst = os.path.join(OUT, name + '.jpg')
    im.save(dst, quality=90)
    return dst


def get():
    ref = sys.argv[2]
    name = slug(opt('--as') or '')
    if not opt('--as'):
        sys.exit('give the file a short name: --as <name> (it becomes remotion/public/broll/<name>.jpg|.mp4)')
    if ref.startswith(('http://', 'https://')):
        if not opt('--license') or not opt('--source'):
            sys.exit('a direct URL needs --source <page it came from> and --license "<its licence>" (only reusable licences)')
        if BAD.search(opt('--license')):
            sys.exit(f'licence "{opt("--license")}" does not allow reuse in an edit: pick another file')
        c = {'title': opt('--title', ''), 'author': opt('--author', 'unknown'), 'license': opt('--license'), 'source': opt('--source'),
             'url': ref, 'video': ref.split('?')[0].lower().endswith(VID)}
        raw, ctype = fetch(ref, timeout=180)
        if 'video' in ctype:
            c['video'] = True
    else:
        if ':' in ref:
            q, _, k = ref.rpartition(':')
            path = os.path.join(SEARCHES, slug(q) + '.json')
        else:
            last = json.load(open(os.path.join(SEARCHES, '_last.json')))['last']
            path, k = os.path.join(SEARCHES, last + '.json'), ref
        c = json.load(open(path))['candidates'][int(k) - 1]
        raw, ctype = fetch(c['url'] if c['video'] else c['thumb'], timeout=180)
    dst = save_media(raw, ctype, c['url'], name, c['video'])
    os.makedirs(os.path.dirname(CREDITS), exist_ok=True)
    cr = json.load(open(CREDITS, encoding='utf-8')) if os.path.exists(CREDITS) else {}
    cr[os.path.basename(dst)] = {k: c.get(k) for k in ('title', 'author', 'license', 'source')}
    json.dump(cr, open(CREDITS, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'saved remotion/public/broll/{os.path.basename(dst)}  ({c["license"]}, {c["author"][:40]})  -> use "media": ["{os.path.basename(dst)}"]')


def listing():
    cr = json.load(open(CREDITS, encoding='utf-8')) if os.path.exists(CREDITS) else {}
    for f in sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []:
        c = cr.get(f, {})
        print(f"{f}: \"{c.get('title', '')}\" by {c.get('author', '?')}, {c.get('license', 'NO CREDIT RECORDED')}, {c.get('source', '')}")


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    {'search': search, 'get': get, 'list': listing}.get(cmd, lambda: print(__doc__))()
