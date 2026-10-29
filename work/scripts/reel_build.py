"""REEL KIT builder: turn the short creative plan work/plan/reel.json into every per-video file of a kit-style edit.
usage: python work/scripts/reel_build.py            (after words_consensus.py, integrate.py and face_track.py)
       python work/scripts/reel_build.py --check    (validate reel.json and print the plan, write nothing)

Reads: the active style's style.json + sound_map.json, remotion/src/data/words.json, work/plan/video.json,
work/plan/faces.json, work/plan/reel.json, the sound pack's _catalogue/sfx_events.json.
Writes: remotion/src/scenes/OS00_Reel.tsx (captions, hook headline, name tags, progress bar), OS<n>_Card<k>.tsx,
FS<n>_Slam<k>.tsx, remotion/src/data/edit.ts (speaker-aware CAMERA, JUMP_CUTS, SHADE, FLASHES), work/plan/cue_sheet.json
(sound design), work/plan/scene_reports.json and work/plan/reel_summary.md (the animation map for EDIT_NOTES.md).

work/plan/reel.json (word numbers are the `i` of remotion/src/data/words.json; `python work/scripts/reel_build.py --words`
prints them):
{
  "hook":   {"lines": ["small first line", "THE BIG LINE"], "accent": 1, "untilWord": 14},
  "emphasis": [3, 17, 18],                       accent-coloured words (numbers, money, the key idea), ~1 per 2-3 s
  "speakers": {"A": {"name": "Real Name", "role": "Host"}, "B": {...}},   keys = `look` letters in faces.json;
                                                 only with 2+ people on camera AND real names from the video's metadata
  "inserts": [                                   FULL-SCREEN inserts (the ready-made styles use these, not cards):
     {"kind": "image", "fromWord": 40, "toWord": 47, "media": ["walmart.jpg", "gopro.jpg"], "beatWords": [44]},
                                                 real B-roll stills (several = a cut on each beat word); captions stay on top
     {"kind": "video", "fromWord": 60, "toWord": 66, "media": ["crowd.mp4"]},       real B-roll footage, muted
                                                 a clip from 2.5 s in: "crowd.mp4#t=2.5" (no need to fetch it twice)
                                                 a wide picture: "gopro.jpg#x=0.3" keeps x=30% of its width in the 9:16
                                                 frame (0 = left edge, 0.5 = centre, 1 = right edge)
     {"kind": "wall",  "fromWord": 31, "toWord": 40, "media": ["r1.jpg", ...], "title": "references", "titleWord": 33},
                                                 a moving wall of many pictures ("tons of examples"), optional big word
     {"kind": "logo",  "fromWord": 53, "toWord": 57, "brand": "claude", "text": "edits in your style"},
                                                 a real logo, big, with its words popping in (captions hidden)
     {"kind": "number", "fromWord": 70, "toWord": 75, "atWord": 72, "value": 100000000, "prefix": "$", "label": "on one video"}],
                                                 media = files in remotion/public/broll/ (python work/scripts/broll_fetch.py)
  "cards":  [{"atWord": 40, "untilWord": 52, "spec": {"type": "number", "value": 100, "prefix": "$", "suffix": "M",
              "label": "spent on one video"}}],  spec types: number | keyword | logo | list | quote (see Reel.tsx CardSpec);
                                                 list items: {"t": "text", "word": <i>} (shown when that word is said);
                                                 a card lasts card.minSec..maxSec of style.json, except a list card, which
                                                 stays until 1 s after its last item
  "slams":  [{"fromWord": 60, "toWord": 66, "split": [3], "accentLine": 1, "kicker": "optional", "dark": false}],
                                                 full-screen text scenes (only if the style allows them); split = words
                                                 per line before the last line
  "punchWords": [25],                            extra camera punch-ins on these words
  "gains":  {"riser": -13},                      optional: change one sound role's level (e.g. a mix.py hot spot)
  "music": {"mood": "calm" | "energetic"}
}"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
RM = os.path.join(PROJ, 'remotion')
SC = os.path.join(RM, 'src', 'scenes')
PLAN = os.path.join(ROOT, 'plan')
from client_style import style_dir, rel, catalogue  # noqa: E402

FPS = 30
J = lambda p: json.load(open(p, encoding='utf-8'))
WORDS = J(os.path.join(RM, 'src', 'data', 'words.json'))

if '--words' in sys.argv:
    line = []
    for w in WORDS:
        line.append(f"{w['i']}:{w['w']}")
        if w['w'][-1:] in '.?!' or len(line) >= 14:
            print(f"[f{WORDS[int(line[0].split(':')[0])]['f']}] " + ' '.join(line)); line = []
    if line:
        print(' '.join(line))
    sys.exit(0)

SD = style_dir()
STYLE = J(os.path.join(SD, 'style.json'))
SMAP = J(os.path.join(SD, 'sound_map.json')) if os.path.exists(os.path.join(SD, 'sound_map.json')) else {}
VID = J(os.path.join(PLAN, 'video.json'))
FACES = J(os.path.join(PLAN, 'faces.json')) if os.path.exists(os.path.join(PLAN, 'faces.json')) else {'shots': []}
REEL = J(os.path.join(PLAN, 'reel.json'))
TOTAL = VID['total']
JUMPS = [j for j in VID.get('jumpCuts', []) if 0 < j < TOTAL]
CAP, HOOK, CAM = STYLE['captions'], STYLE['hook'], STYLE['camera']
problems = []


def wf(i):  # start frame of word i
    return WORDS[max(0, min(len(WORDS) - 1, i))]['f']


def we(i):  # end frame of word i
    return int(round(WORDS[max(0, min(len(WORDS) - 1, i))]['e'] * FPS))


def clamp(v, a, b):
    return max(a, min(b, v))


def snap_start(a, fr):
    """A full-screen moment whose line starts a new take begins ON that jump cut: the first frames of a take (the speaker
    still looking at notes) must never show before it."""
    prev_end = we(a - 1) if a > 0 else 0
    cs = [c for c in JUMPS if prev_end < c <= wf(a)]
    return max(1, min(cs)) if cs else fr


# ---------------------------------------------------------------- slams (full-screen text scenes)
slams = []
if REEL.get('slams') and not STYLE.get('slam', {}).get('enabled'):
    problems.append('this style has no full-screen slams (style.json slam.enabled is false): slams ignored')
for k, s in enumerate(REEL.get('slams', []) if STYLE.get('slam', {}).get('enabled') else [], 1):
    a, b = s['fromWord'], s['toWord']
    idx = list(range(a, b + 1))
    split = s.get('split') or []
    lines, cur, li = [], [], 0
    bounds = []
    acc = 0
    for n in split:
        acc += n
        bounds.append(acc)
    for j, i in enumerate(idx):
        if li < len(bounds) and j >= bounds[li]:
            li += 1
        lines.append({'t': WORDS[i]['w'], 'f': wf(i), 'line': li})
    fr = snap_start(a, max(1, wf(a) - 6))
    if lines and lines[0]['f'] > fr + 5:  # Whisper can time a line's first word late: never open on an empty page
        lines[0]['f'] = fr + 5
    to = min(TOTAL - 1, we(b) + 8)
    if to - fr < 45:
        to = min(TOTAL - 1, fr + 45)
    on_cut = fr in JUMPS
    slams.append({'k': k, 'from': fr, 'to': to, 'words': lines, 'accentLine': s.get('accentLine', len(bounds)),
                  'kicker': s.get('kicker'), 'dark': bool(s.get('dark')), 'onCut': on_cut,
                  'opaqueFrom': fr + (4 if on_cut else 9), 'opaqueUntil': to})
slams.sort(key=lambda x: x['from'])
for x, y in zip(slams, slams[1:]):
    if y['from'] < x['to'] + 30:
        problems.append(f"slams {x['k']} and {y['k']} are too close (need 1 s of talking head between them)")
HIDE = [(s['opaqueFrom'], s['to']) for s in slams]
in_slam = lambda f: any(s['from'] <= f < s['to'] for s in slams)

shots = FACES.get('shots') or [{'from': 0, 'to': TOTAL, 'face': None}]


def face_box(f):
    for s in shots:
        if s['from'] <= f < s['to'] and s.get('face'):
            return s['face']
    return None


def card_top(f):
    """A card sits right under the speaker's chin (never on the face), at least at the style's top."""
    fb = face_box(f)
    top = STYLE['card']['top']
    if fb:
        top = max(top, int(fb['y'] + 0.62 * fb['h'] + 24))
    return min(top, 1240)


# ---------------------------------------------------------------- cards (on-screen)
cards = []
cmin, cmax = int(STYLE['card']['minSec'] * FPS), int(STYLE['card']['maxSec'] * FPS)
for k, c in enumerate(REEL.get('cards', []), 1):
    spec = dict(c['spec'])
    land = wf(c['atWord'])
    fr = max(1, land - 4)
    to = we(c.get('untilWord', c['atWord'])) + 10
    to = clamp(to, fr + cmin, fr + cmax)
    to = min(to, TOTAL - 1)
    if spec['type'] == 'list' and len(spec['items']) > 4:
        problems.append(f'card {k}: lists show at most 4 items (extra items dropped)')
        spec['items'] = spec['items'][:4]
    if spec['type'] == 'list':
        spec['items'] = [{'t': it['t'], 'f': wf(it['word']) if 'word' in it else land + 8 * n} for n, it in enumerate(spec['items'])]
        to = max(to, min(TOTAL - 1, spec['items'][-1]['f'] + 30))
    if spec['type'] == 'logo':
        name = spec['brand'] if spec['brand'].endswith('.svg') else spec['brand'] + '.svg'
        slug = spec['brand'].replace('.svg', '').replace('si_', '')
        if not os.path.exists(os.path.join(RM, 'public', 'brand', name)) and os.path.exists(os.path.join(RM, 'public', 'brand', f'si_{slug}.svg')):
            spec['glyph'] = slug  # simple-icons brand glyph, in its brand colour on a white tile
        elif not os.path.exists(os.path.join(RM, 'public', 'brand', name)):
            problems.append(f"card {k}: no logo remotion/public/brand/{name} (fetch it: fetch_brand_assets.py --si <slug> | --commons ...) - shown as a keyword card")
            spec = {'type': 'keyword', 'kicker': spec.get('label'), 'text': spec['brand'].replace('si_', '').replace('_', ' ').title()}
    for s in slams:  # a card that runs into a slam ends where the slam starts; one that starts inside a slam is dropped
        if fr < s['from'] < to:
            to = s['from']
    if any(s['from'] <= fr < s['to'] for s in slams) or to - fr < 30:
        problems.append(f'card {k} overlaps a slam (or is under 1 s): dropped')
        continue
    cards.append({'k': k, 'from': fr, 'to': to, 'land': land, 'spec': spec, 'top': card_top(land)})
cards.sort(key=lambda x: x['from'])
for x, y in zip(cards, cards[1:]):
    if y['from'] < x['to']:
        x['to'] = y['from']  # never two cards at once
card_at = lambda f: any(c['from'] <= f < c['to'] for c in cards)


def cap_y_card(f0, f1):
    bot = [c['top'] + card_h(c['spec']) for c in cards if c['from'] < f1 and f0 < c['to']]
    return min(1700, max(CAP['yWithCard'], max(bot) + 90)) if bot else None


def card_h(spec):  # rough rendered height of a card (px), so the captions go below it
    t = spec['type']
    if t == 'list':
        return 110 + (52 if spec.get('title') else 0) + 72 * len(spec['items'])
    return {'number': 270, 'keyword': 250 if spec.get('kicker') else 200, 'logo': 240, 'quote': 330}.get(t, 260)

# ---------------------------------------------------------------- full-screen inserts (B-roll, image wall, logo, number)
BROLL = os.path.join(RM, 'public', 'broll')
ICFG = STYLE.get('insert', {'minSec': 1.2, 'maxSec': 4.5})
if cards and not STYLE.get('card', {}).get('enabled', True):
    problems.append('this style has no on-screen UI cards (style.json card.enabled is false): use full-screen "inserts" '
                    '(B-roll, wall, logo, number); cards ignored')
    cards = []
inserts = []
for k, d in enumerate(REEL.get('inserts', []), 1):
    kind = d.get('kind')
    a = d['fromWord']
    b = d.get('toWord', a)
    fr = snap_start(a, max(1, wf(a) - 3))
    to = min(TOTAL - 1, we(b) + 6)
    to = clamp(to, fr + int(ICFG['minSec'] * FPS), fr + int(ICFG['maxSec'] * FPS))
    if b + 1 < len(WORDS) and wf(b + 1) - 2 > wf(b):  # end before the next caption pops
        to = min(to, max(wf(b + 1) - 2, we(b) + 1))
    if b >= len(WORDS) - 1 or TOTAL - to < 10:  # on the last words: hold to the very last frame
        to = TOTAL
    spec = {'kind': kind}
    if kind in ('image', 'video', 'wall'):
        med = d.get('media') or []
        missing = [m for m in med if not os.path.exists(os.path.join(BROLL, m.split('#')[0]))]  # 'x.jpg#x=0.3' = focus
        if not med or missing:
            problems.append(f'insert {k}: media missing in remotion/public/broll/: {missing or "none given"} (fetch it with '
                            f'python work/scripts/broll_fetch.py) - dropped')
            continue
        spec['media'] = med
        if kind == 'image' and len(med) > 1:
            bw = d.get('beatWords') or [a + round((b - a) * n / len(med)) for n in range(1, len(med))]
            spec['beats'] = [wf(i) for i in bw][:len(med) - 1]
        if kind == 'wall' and d.get('title'):
            spec['title'] = d['title']
            spec['titleAt'] = wf(d.get('titleWord', a))
    elif kind == 'logo':
        brand = d['brand'].replace('.svg', '')
        slug = brand.replace('si_', '')
        if os.path.exists(os.path.join(RM, 'public', 'brand', brand + '.svg')):
            spec['brand'] = brand
        elif os.path.exists(os.path.join(RM, 'public', 'brand', f'si_{slug}.svg')):
            spec['brand'], spec['glyph'] = brand, slug
        else:
            problems.append(f"insert {k}: no logo {brand} in remotion/public/brand (fetch_brand_assets.py --si <slug>) - dropped")
            continue
        if d.get('text'):
            ws = d['text'].split()
            spec['lines'] = [{'t': w, 'f': wf(a) + 4 + 4 * n} for n, w in enumerate(ws)]
        else:
            spec['lines'] = [{'t': WORDS[i]['w'].strip(',.'), 'f': wf(i)} for i in range(a, b + 1)]
    elif kind == 'number':
        spec.update({'value': d['value'], 'label': d.get('label', ''), 'land': wf(d.get('atWord', a))})
        for key in ('prefix', 'suffix', 'decimals'):
            if key in d:
                spec[key] = d[key]
    else:
        problems.append(f'insert {k}: unknown kind {kind!r} - dropped')
        continue
    if any(not (to <= s['from'] or fr >= s['to']) for s in slams):
        problems.append(f'insert {k} overlaps a slam - dropped')
        continue
    keep_caps = kind in ('image', 'video') or (kind == 'wall' and not d.get('title'))
    inserts.append({'k': k, 'from': fr, 'to': to, 'spec': spec, 'captions': keep_caps})
inserts.sort(key=lambda x: x['from'])
for x, y in zip(inserts, inserts[1:]):
    if y['from'] < x['to'] + 18:
        x['to'] = max(x['from'] + 20, y['from'] - 18)  # at least 0.6 s of the speaker between two inserts
in_insert = lambda f: any(x['from'] <= f < x['to'] for x in inserts)
HIDE += [(x['from'], x['to']) for x in inserts if not x['captions']]  # from the insert's first frame: no caption flash

# ---------------------------------------------------------------- hook headline
hk = REEL.get('hook') or {}
if hk.get('lines'):
    until_w = hk.get('untilWord')
    if until_w is None:
        until_w = next((w['i'] for w in WORDS if w['w'][-1:] in '.?!'), min(len(WORDS) - 1, 10))
    hook_to = clamp(we(until_w) + 6, int(HOOK['minSec'] * FPS), int(HOOK['maxSec'] * FPS))
    if slams:
        hook_to = min(hook_to, slams[0]['from'])
else:
    hook_to = 0
    problems.append('reel.json has no hook.lines: no hook headline (every kit style expects one)')

# ---------------------------------------------------------------- captions
emph = set(REEL.get('emphasis', []))
groups, cur = [], []
SHOT_CUTS = [s['from'] for s in (FACES.get('shots') or []) if s['from'] > 0]
cut_set = set(JUMPS) | set(SHOT_CUTS) | {s['from'] for s in slams} | {s['to'] for s in slams} | {x['from'] for x in inserts} | {x['to'] for x in inserts}


def flush():
    global cur
    if cur:
        groups.append(cur)
    cur = []


for n, w in enumerate(WORDS):
    if in_slam(w['f']) and any(s['opaqueFrom'] <= w['f'] < s['to'] for s in slams):
        flush(); continue
    if cur:
        prev = cur[-1]
        text = ' '.join(x['w'] for x in cur + [w])
        gap = w['s'] - prev['e']
        crossed = any(prev['f'] < c <= w['f'] for c in cut_set)
        span = (w['e'] - cur[0]['s'])
        if (len(cur) >= CAP['maxWords'] or len(text) > CAP['maxChars'] or span > CAP['maxDur'] or gap > 0.35
                or prev['w'][-1:] in '.?!,' or crossed):
            flush()
    cur.append(w)
flush()
cap_groups = []
for gi, g in enumerate(groups):
    fr = max(0, g[0]['f'] - 2)
    end = int(round(g[-1]['e'] * FPS)) + 8
    nxt = groups[gi + 1][0]['f'] - 2 if gi + 1 < len(groups) else TOTAL
    to = nxt if nxt - end < 12 else end
    to = min(to, TOTAL)
    for s in slams:  # a caption before a slam ends where the slam covers the frame
        if fr < s['opaqueFrom'] <= to:
            to = s['opaqueFrom']
    last_f = g[-1]['f']
    for c in sorted(cut_set):  # never hold a caption across a cut or a camera change after its last word
        if last_f < c < to:
            to = c
            break
    if cap_groups and fr < cap_groups[-1]['to']:
        fr = cap_groups[-1]['to']
    if to - fr < 3:
        continue
    y = cap_y_card(fr, to) or CAP['y']
    words = [{'t': re.sub(r'^[,.;:]+|[,;:]+$', '', w['w']) or w['w'], 'f': w['f'], 'e': int(round(w['e'] * FPS)),
              **({'accent': True} if w['i'] in emph else {})} for w in g]
    cap_groups.append({'from': fr, 'to': to, 'words': words, 'y': y})

# ---------------------------------------------------------------- name tags (two or more people on camera, real names only)
spk = REEL.get('speakers') or {}
tags = []
if len(spk) >= 2 and REEL.get('nameTags', True):
    nt = STYLE['nameTag']
    for look, info in spk.items():
        for s in FACES.get('shots', []):
            if s.get('look') != look or (s['to'] - s['from']) < nt['minShotSec'] * FPS:
                continue
            fr = s['from'] + 8
            to = min(s['to'] - 2, fr + int(nt['sec'] * FPS))
            if in_slam(fr) or card_at(fr) or in_insert(fr) or in_insert(to - 1) or to - fr < 30:
                continue
            fb = s.get('face')
            ty = min(1200, max(nt['y'], int(fb['y'] + 0.62 * fb['h'] + 16))) if fb else nt['y']
            tags.append({'name': info['name'], 'role': info.get('role', ''), 'from': fr, 'to': to, 'y': ty})
            break
        else:
            problems.append(f'speaker {look} ({info.get("name")}): no shot of {nt["minShotSec"]} s+ free of cards and inserts: no name tag')

for t_ in tags:  # captions under a name tag move down while it is up
    for g in cap_groups:
        if g['from'] < t_['to'] and t_['from'] < g['to']:
            g['y'] = min(1660, max(g['y'], t_['y'] + 200))

# ---------------------------------------------------------------- camera (speaker-aware)
def face_at(f):
    for s in shots:
        if s['from'] <= f < s['to']:
            fc = s.get('face')
            return (fc['x'], fc['y']) if fc else (540, 760)
    return 540, 760


base, punch = CAM['base'], CAM['punch']
keys = []


def key(f, s, ease, dur=None):
    x, y = face_at(f)
    k = {'f': int(f), 's': round(s, 4), 'x': int(x), 'y': int(y), 'ease': ease}
    if dur:
        k['dur'] = dur
    keys.append(k)


SMOOTH = CAM.get('mode') == 'smooth'
if SMOOTH:
    # SMOOTH: slow zooms that span several seconds, never a punch. Jump cuts simply happen inside a move; the only cut keys
    # are where the speaker comes back after a full-screen moment, and the camera holds still before each one.
    covers = sorted((x['from'], x['to']) for x in slams + inserts)
    levels = CAM.get('levels', [base, base + 0.08, base + 0.03, base + 0.11])
    span = int(CAM.get('spanSec', 4.0) * FPS)
    hold = int(CAM.get('holdBeforeInsert', 24))
    key(0, CAM['openFrom'], 'cut')
    key(18, base, 'smooth', 18)
    li = 0
    for st in [18] + [b for a, b in covers if b < TOTAL - 6]:
        stop = next((a for a, b in covers if a > st), TOTAL)
        if st != 18:
            li += 1
            key(st, levels[li % len(levels)], 'cut')
        t = st
        limit = stop - (hold if stop < TOTAL else 1)
        while limit - t >= 45:
            t2 = min(limit, t + span)
            if limit - t2 < 45:
                t2 = limit
            li += 1
            key(t2, levels[li % len(levels)], 'smooth', t2 - t)
            t = t2
else:
    change = sorted({0, *[s['from'] for s in shots], *JUMPS, *[s['to'] for s in slams], *[x['to'] for x in inserts]})
    # rhythm punches on sentence ends, every everySec[0]..everySec[1] seconds, where no cut already changes the framing
    lo, hi = CAM['everySec'][0] * FPS, CAM['everySec'][1] * FPS
    rhythm, last = [], 0
    for w in WORDS:
        nf = w['f']
        if w['w'][-1:] in '.?!,' and nf - last >= lo:
            nxt = next((x for x in WORDS if x['i'] == w['i'] + 1), None)
            if nxt and not any(abs(nxt['f'] - c) < 20 for c in change):
                rhythm.append(nxt['f'] - 1)
                last = nxt['f']
        elif nf - last > hi:
            if not any(abs(nf - c) < 20 for c in change):
                rhythm.append(nf - 1)
                last = nf
    points = sorted({*change, *rhythm})
    points = [p for p in points if p < TOTAL - 6 and not any(s['from'] < p < s['to'] for s in slams + inserts)]
    level = 0  # 0 = wide, 1 = punched in
    shot_starts = {s['from'] for s in shots}
    for n, p in enumerate(points):
        if p == 0:
            key(0, CAM['openFrom'], 'cut')
            key(9, base, 'snap', 9)
            level = 0
        else:
            if p in shot_starts and p not in JUMPS:
                level = 0  # a new camera angle: back to the wide framing on the new face
            else:
                level = 1 - level
            key(p, punch if level else base, 'cut')
        nxt = points[n + 1] if n + 1 < len(points) else TOTAL
        for s in slams:  # stop drifting where a slam covers the frame
            if p < s['from'] < nxt:
                nxt = s['from']
        span = nxt - 1 - keys[-1]['f']
        if span > 12:
            key(nxt - 1, keys[-1]['s'] + CAM['pushPerSec'] * span / FPS, 'linear')
    for pw in REEL.get('punchWords', []):  # emphasis snaps: +0.1 over 6 frames on the word, inside the current segment
        f = wf(pw) - 1
        prev = [k for k in keys if k['f'] <= f]
        if not prev or in_slam(f):
            continue
        nxt = next((k for k in keys if k['f'] > f + 8), None)
        if nxt and nxt['ease'] == 'linear':
            pass
        s0 = prev[-1]['s']
        key(f + 6, s0 + 0.1, 'snap', 6)
keys.sort(key=lambda k: k['f'])
dedup = []
for k in keys:
    if dedup and dedup[-1]['f'] == k['f']:
        dedup[-1] = k
    else:
        dedup.append(k)
keys = dedup

# ---------------------------------------------------------------- SHADE (blurred lower band behind captions and cards) + FLASHES
sh = STYLE['shade']
shade, t = [], 0
for s in slams:
    if s['opaqueFrom'] + 1 > t:
        shade.append({'from': t, 'to': s['opaqueFrom'] + 1, 'top': sh['top'], 'blur': sh['blur'], 'dark': sh['dark']})
    t = s['to']
if t < TOTAL:
    shade.append({'from': t, 'to': TOTAL, 'top': sh['top'], 'blur': sh['blur'], 'dark': sh['dark']})
flashes = [{'peak': s['to'], 'up': 1, 'down': 5, 'max': 0.85} for s in slams]

# ---------------------------------------------------------------- sound design
EVP = catalogue('sfx_events.json')
EV = J(EVP) if os.path.exists(EVP) else {}
cues, used = [], {}


def cue(role, frame, note):
    m = SMAP.get(role)
    if not m or not EV:
        return
    files = [f for f in m['files'] if f in EV and EV[f]]
    if not files:
        problems.append(f'sound role {role}: none of its files are in the sound pack catalogue')
        return
    if m['family'] == 'whoosh' and any(c['family'] == 'whoosh' and abs(c['frame'] - frame) <= 3 for c in cues):
        return  # one whoosh per movement: a camera punch and an insert exit on the same frame share it
    n = used.get(role, 0); used[role] = n + 1
    fl = files[n % len(files)]
    v = max(EV[fl], key=lambda e: e['pkdb'])
    if frame < 0 or frame >= TOTAL:
        return
    gain = REEL.get('gains', {}).get(role, m['gainDb'])  # reel.json "gains": {"riser": -13} overrides a role's level
    cues.append({'frame': int(frame), 'family': m['family'], 'file': fl, 'peak': v['pk'], 'gainDb': gain, 'note': note})


cue('open', 5, 'opening zoom-out')
if hook_to:
    cue('hook', 2, 'hook headline pops in')
    cue('hook_out', hook_to - 4, 'hook headline exits')
last_w = -99
for k in keys[2:]:
    if k['ease'] == 'cut' and k['f'] - last_w >= 45 and not any(s['to'] == k['f'] for s in slams):
        cue('punch', k['f'], 'camera punch'); last_w = k['f']
    if k['ease'] == 'snap':
        cue('punch', k['f'] - 3, 'emphasis zoom')
for t_ in tags:
    cue('nametag', t_['from'] + 6, f"name tag {t_['name']}")
for c in cards:
    cue('card_in', c['from'] + 5, f"card {c['k']} slides in")
    cue('card_pop', c['from'] + 10, f"card {c['k']} lands")
    if c['spec']['type'] == 'number':
        cue('count', c['land'] + 16, f"card {c['k']} counter lands")
    if c['spec']['type'] == 'list':
        for it in c['spec']['items']:
            cue('list_item', it['f'] + 3, f"card {c['k']} item")
    cue('card_out', c['to'] - 4, f"card {c['k']} exits")
for x in inserts:
    cue('insert_in', x['from'] + 3, f"insert {x['k']} ({x['spec']['kind']}) zooms in")
    cue('insert_pop', x['from'] + 8, f"insert {x['k']} lands")
    for bt in x['spec'].get('beats', []):
        cue('insert_pop', bt, f"insert {x['k']} next picture")
    if x['spec']['kind'] == 'number':
        cue('count', x['spec']['land'] + 16, f"insert {x['k']} counter lands")
    if x['spec'].get('titleAt'):
        cue('insert_pop', x['spec']['titleAt'] + 4, f"insert {x['k']} title")
    if x['to'] < TOTAL - 3:
        cue('insert_out', x['to'], f"insert {x['k']} back to the speaker")
for s in slams:
    cue('riser', s['from'], f"slam {s['k']} riser")
    cue('hit', s['from'] + 7, f"slam {s['k']} lands")
    cue('slam_in', s['from'] + 3, f"slam {s['k']} reveal")
    cue('slam_out', s['to'], f"slam {s['k']} flash back to the speaker")
emph_seen = 0
for g in cap_groups:
    for w in g['words']:
        if w.get('accent'):
            emph_seen += 1
            if emph_seen % 2 == 1:
                cue('accent', w['f'], f"accent word {w['t']}")
cues.sort(key=lambda c: c['frame'])

# ---------------------------------------------------------------- report / check
print(f"style {rel(SD)}: {len(cap_groups)} caption groups, hook 0-{hook_to}, {len(tags)} name tag(s), {len(cards)} card(s), "
      f"{len(slams)} slam(s), {len(inserts)} full-screen insert(s), {len(keys)} camera keys, {len(cues)} sound cues")
for p in problems:
    print('WARNING:', p)
if '--check' in sys.argv:
    sys.exit(0)

# ---------------------------------------------------------------- write files
os.makedirs(SC, exist_ok=True)
for p in os.listdir(SC):  # regenerate the kit's own scenes; hand-written scenes stay
    if re.match(r'^(OS00_Reel|OS\d+_Card\d+|FS\d+_Slam\d+)\.tsx$', p):
        os.remove(os.path.join(SC, p))
js = lambda o: json.dumps(o, ensure_ascii=False)
look = {k: CAP[k] for k in ('mode', 'upper', 'size', 'weight', 'font', 'stroke', 'maxW', 'y', 'accentScale', 'active')}
open(os.path.join(SC, 'OS00_Reel.tsx'), 'w', encoding='utf-8', newline='\n').write(f"""// Generated by work/scripts/reel_build.py from work/plan/reel.json - edit reel.json and re-run, not this file.
import React from 'react';
import {{AbsoluteFill}} from 'remotion';
import {{HookHeadline, Insert, InsertDef, NameTag, ProgressBar, ReelCaptions, RGroup, CapLook}} from '../components/Reel';
export const OS00_Reel_FROM = 0;
export const OS00_Reel_TO = {TOTAL};
const LOOK: CapLook = {js(look)};
const GROUPS: RGroup[] = {js(cap_groups)};
const TAGS: {{name: string; role: string; from: number; to: number; y: number}}[] = {js(tags)};
const HIDE: [number, number][] = {js([list(h) for h in HIDE])};
const INSERTS: InsertDef[] = {js([{'from': x['from'], 'to': x['to'], 'spec': x['spec']} for x in inserts])};
export const OS00_Reel: React.FC = () => (
  <AbsoluteFill>
    {{INSERTS.map((d, i) => <Insert key={{i}} d={{d}} />)}}
    {{{'true' if STYLE.get('progressBar') else 'false'} ? <ProgressBar total={{{TOTAL}}} /> : null}}
    {'<HookHeadline lines={' + js(hk.get('lines', [])) + '} accent={' + str(hk.get('accent', 1)) + '} to={' + str(hook_to) + '} y={' + str(HOOK['y']) + '} boxed={' + ('true' if HOOK.get('boxed') else 'false') + '} upper={' + ('true' if HOOK.get('upper') else 'false') + '} size={' + str(HOOK.get('size', 58)) + '} accentSize={' + str(HOOK.get('accentSize', 112)) + '} stroke={' + str(HOOK.get('stroke', 4)) + '} />' if hook_to else ''}
    {{TAGS.map((t, i) => <NameTag key={{i}} name={{t.name}} role={{t.role}} from={{t.from}} to={{t.to}} y={{t.y}} right={{i % 2 === 1}} />)}}
    <ReelCaptions groups={{GROUPS}} look={{LOOK}} hidden={{HIDE}} />
  </AbsoluteFill>
);
""")
reports = {}
n = 1
for c in cards:
    sid = f"OS{n}_Card{c['k']}"; n += 1
    open(os.path.join(SC, sid + '.tsx'), 'w', encoding='utf-8', newline='\n').write(f"""// Generated by work/scripts/reel_build.py from work/plan/reel.json.
import React from 'react';
import {{ReelCard, CardSpec}} from '../components/Reel';
export const {sid}_FROM = {c['from']};
export const {sid}_TO = {c['to']};
const SPEC: CardSpec = {js(c['spec'])};
export const {sid}: React.FC = () => <ReelCard spec={{SPEC}} from={{{c['from']}}} to={{{c['to']}}} land={{{c['land']}}} top={{{c['top']}}} />;
""")
    reports[sid] = {'summary': f"{c['spec']['type']} card", 'events': [{'frame': c['from'] + 10, 'what': 'card lands'}],
                    'opaqueFrom': -1, 'opaqueUntil': -1, 'knownIssues': []}
for s in slams:
    sid = f"FS{s['k']}_Slam{s['k']}"
    cx, cy = face_at(s['from'] - 1)
    open(os.path.join(SC, sid + '.tsx'), 'w', encoding='utf-8', newline='\n').write(f"""// Generated by work/scripts/reel_build.py from work/plan/reel.json.
import React from 'react';
import {{Slam, SlamWord}} from '../components/Reel';
export const {sid}_FROM = {s['from']};
export const {sid}_TO = {s['to']};
export const {sid}_OPAQUE_FROM = {s['opaqueFrom']};
export const {sid}_OPAQUE_UNTIL = {s['opaqueUntil']};
const WORDS: SlamWord[] = {js(s['words'])};
export const {sid}: React.FC = () => (
  <Slam words={{WORDS}} accentLine={{{s['accentLine']}}} from={{{s['from']}}} to={{{s['to']}}} cx={{{cx}}} cy={{{cy}}} kicker={{{js(s['kicker']) if s['kicker'] else 'undefined'}}} dark={{{'true' if s['dark'] else 'false'}}} onCut={{{'true' if s['onCut'] else 'false'}}} />
);
""")
    reports[sid] = {'summary': 'full-screen text slam', 'events': [{'frame': s['from'] + 7, 'what': 'circle reveal lands'}],
                    'opaqueFrom': s['opaqueFrom'], 'opaqueUntil': s['opaqueUntil'], 'knownIssues': []}
json.dump(reports, open(os.path.join(PLAN, 'scene_reports.json'), 'w', encoding='utf-8'), indent=1)

tpl = open(os.path.join(ROOT, 'templates', 'edit.ts'), encoding='utf-8').read()
tpl = re.sub(r'export const CAMERA: CamKey\[\] = \[.*?\];', 'export const CAMERA: CamKey[] = ' + js(keys) + ';', tpl, flags=re.S)
tpl = re.sub(r'export const JUMP_CUTS: number\[\] = \[\];', 'export const JUMP_CUTS: number[] = ' + js(JUMPS) + ';', tpl)
tpl = re.sub(r'export const SHADE: BandRange\[\] = \[\];', 'export const SHADE: BandRange[] = ' + js(shade) + ';', tpl)
tpl = re.sub(r'export const FLASHES: (\{[^=]*\}\[\]) = \[\];', lambda m: 'export const FLASHES: ' + m.group(1) + ' = ' + js(flashes) + ';', tpl)
tpl = '// Generated by work/scripts/reel_build.py (reel kit) from work/plan/reel.json + faces.json.\n' + tpl
open(os.path.join(RM, 'src', 'data', 'edit.ts'), 'w', encoding='utf-8', newline='\n').write(tpl)

json.dump({'musicNoDip': ['OS00_Reel'] + [f"FS{x['k']}_Slam{x['k']}" for x in slams], 'cues': cues}, open(os.path.join(PLAN, 'cue_sheet.json'), 'w', encoding='utf-8'), indent=1)

md = [f'# Reel plan ({rel(SD)})', '', f'- Hook headline 0-{hook_to}: ' + ' / '.join(hk.get('lines', [])),
      f'- Captions: {len(cap_groups)} groups ({CAP["mode"]}), {len(emph)} accent words',
      f'- Camera: {len(keys)} keys over {len(shots)} shot(s), {len(JUMPS)} jump cut(s) hidden by framing changes']
md += [f"- Name tag {t['name']} ({t['role']}) {t['from']}-{t['to']}" for t in tags]
md += [f"- Card {c['k']} [{c['from']}-{c['to']}) {c['spec']['type']}: " + js(c['spec'])[:120] for c in cards]
md += [f"- Insert {x['k']} [{x['from']}-{x['to']}) {x['spec']['kind']}: " + js(x['spec'])[:140] for x in inserts]
_cr = os.path.join(PLAN, 'broll_credits.json')
if os.path.exists(_cr):
    _used = {m for x in inserts for m in x['spec'].get('media', [])}
    for name, c in J(_cr).items():
        if name in _used:
            md.append(f"- B-roll credit: {name}: \"{c.get('title', '')}\" by {c.get('author', 'unknown')}, {c.get('license', '?')}, {c.get('source', '')}")
md += [f"- Slam {s['k']} [{s['from']}-{s['to']}) " + ' '.join(w['t'] for w in s['words']) for s in slams]
md += [f'- Sound: {len(cues)} cues (' + ', '.join(sorted({c["note"].split(" ")[0] for c in cues})) + ')']
md += ['- Warnings: ' + ('; '.join(problems) if problems else 'none')]
open(os.path.join(PLAN, 'reel_summary.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print('wrote OS00_Reel + %d card(s) + %d slam(s), edit.ts, cue_sheet.json, scene_reports.json, reel_summary.md' % (len(cards), len(slams)))
print('next: python work/scripts/integrate.py && (cd remotion && npx tsc --noEmit -p .)')
