"""Footage palette: colour the animations from THIS video (the speaker's clothing, the set, the practical lights) instead of
re-using one stock accent on every video. A blue shirt gives blue scenes; a lavender room gives orchid and plum.
usage: python work/scripts/palette.py                     sample the footage, pick the palette, write it
       python work/scripts/palette.py --accent "#5B8DEF"  steer: use this accent as-is and derive the other tokens from its hue
       python work/scripts/palette.py --warm "#F2C6A8"    steer the secondary colour (e.g. a lamp, a neon sign), used as-is
       python work/scripts/palette.py --off               keep the client style's own colours (writes PALETTE = null)
       python work/scripts/palette.py --src <video> --dry-run   preview any video's palette without writing anything
Footage: remotion/public/aroll.mp4 (the cut) if it exists, else the single raw video in input/.
Writes remotion/src/data/palette.ts (merged over the style's C tokens by remotion/src/theme.ts), work/plan/palette.json, and
work/frames/palette.png (footage frames + the swatches on dark and light, to check by eye). Re-run any time before the render.
A style can opt out of footage palettes with a line "Palette: fixed" in its STYLE_GUIDE.md (then this writes null).

How it picks: k-means on 12 frames; each colour cluster is scored by area x saturation, skin-like clusters are down-weighted
(a saturated orange shirt still wins), near-greys are ignored. The best cluster's hue becomes the accent family; the best
cluster at least 35 degrees away becomes the secondary ("warm"). Neutral footage (no cluster with real colour) keeps the
style's accent hue but still takes the footage's ink/paper temperature."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, glob, json, colorsys, subprocess, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pylibs'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

OUT_TS = os.path.join(PROJ, 'remotion', 'src', 'data', 'palette.ts')
OUT_JSON = os.path.join(ROOT, 'plan', 'palette.json')
OUT_PNG = os.path.join(ROOT, 'frames', 'palette.png')
TEMPLATE = os.path.join(ROOT, 'templates', 'palette.ts')


def arg(flag):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv and sys.argv.index(flag) + 1 < len(sys.argv) else None


def hexrgb(h):
    h = h.strip().lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def hsl_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(1, l)), max(0, min(1, s)))
    return '#%02X%02X%02X' % (round(r * 255), round(g * 255), round(b * 255))


def rgb_str(hx):
    return ','.join(str(round(v * 255)) for v in hexrgb(hx))


def write_null(reason):
    tpl = open(TEMPLATE, encoding='utf-8').read()
    open(OUT_TS, 'w', encoding='utf-8', newline='\n').write(tpl)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump({'palette': None, 'reason': reason}, open(OUT_JSON, 'w'), indent=1)
    print('palette: OFF (' + reason + ') - the client style colours are used')
    sys.exit(0)


# --- opt-outs
if '--off' in sys.argv:
    write_null('--off')
try:
    from client_style import style_dir, style_file
    guide = style_file(style_dir(), 'STYLE_GUIDE.md')
    if os.path.exists(guide) and re.search(r'^\W*palette\W*:\W*fixed', open(guide, encoding='utf-8').read(), re.I | re.M):
        write_null('the style guide says "Palette: fixed"')
except SystemExit:
    raise
except Exception:
    pass

# --- footage
src = arg('--src') or os.path.join(PROJ, 'remotion', 'public', 'aroll.mp4')
if not os.path.exists(src):
    vids = [p for p in glob.glob(os.path.join(PROJ, 'input', '*')) if p.lower().endswith(('.mp4', '.mov', '.mkv', '.m4v'))]
    if len(vids) != 1:
        sys.exit('no footage: render the cut first (remotion/public/aroll.mp4) or put exactly one video in input/')
    src = vids[0]
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                           capture_output=True, text=True).stdout.strip() or 0)
W, H, N = 108, 192, 12
frames = []
for i in range(N):
    t = dur * (i + 0.5) / N
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', '-vf', f'scale={W}:{H}',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    if len(raw) == W * H * 3:
        frames.append(np.frombuffer(raw, np.uint8).reshape(H, W, 3))
if not frames:
    sys.exit('could not read frames from ' + src)
px = np.concatenate([f.reshape(-1, 3) for f in frames]).astype(float) / 255

# --- k-means (deterministic)
K = 10
rng = np.random.default_rng(7)
cent = px[rng.choice(len(px), K, replace=False)]
for _ in range(25):
    lab = ((px[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1)
    cent = np.array([px[lab == k].mean(0) if (lab == k).any() else cent[k] for k in range(K)])
area = np.bincount(lab, minlength=K) / len(px)
clusters = []
for c, a in zip(cent, area):
    h, l, s = colorsys.rgb_to_hls(*c)
    h *= 360
    skin = 5 <= h <= 45 and s < 0.62 and 0.25 <= l <= 0.85
    chroma = s * (1 - abs(2 * l - 1))  # real colourfulness (HSL saturation explodes near black/white)
    score = a * chroma ** 1.2 * (0.3 if skin else 1.0) * (0 if chroma < 0.05 or l < 0.08 or l > 0.95 else 1)
    clusters.append(dict(hex='#%02X%02X%02X' % tuple(round(float(v) * 255) for v in c), h=float(h), s=float(s), l=float(l),
                         area=float(a), chroma=float(chroma), skin=bool(skin), score=float(score)))
clusters.sort(key=lambda x: -x['score'])

# --- choose hues
acc_arg, warm_arg, exact = arg('--accent'), arg('--warm'), '--exact' in sys.argv
neutral = bool(clusters[0]['score'] < 0.004)
if acc_arg:
    ah, al, as_ = colorsys.rgb_to_hls(*hexrgb(acc_arg))
    H1, S1 = ah * 360, as_
elif neutral:
    try:  # keep the style's accent hue
        txt = open(os.path.join(PROJ, 'remotion', 'src', 'data', 'style_theme.ts'), encoding='utf-8').read()
        m = re.search(r"accent:\s*'(#[0-9A-Fa-f]{6})'", txt)
        ah, al, as_ = colorsys.rgb_to_hls(*hexrgb(m.group(1)))
        H1, S1 = ah * 360, as_
    except Exception:
        H1, S1 = 220, 0.5
else:
    top = clusters[0]
    H1, S1 = float(top['h']), float(top['s'])
hd = lambda a, b: min(abs(a - b) % 360, 360 - abs(a - b) % 360)
sec = next((c for c in clusters[1:] if c['score'] > 0.12 * max(clusters[0]['score'], 1e-6) and hd(c['h'], H1) >= 35
            and c['chroma'] >= 0.08), None)
if warm_arg:
    wh, wl, ws = colorsys.rgb_to_hls(*hexrgb(warm_arg))
    H2, S2 = wh * 360, ws
elif sec:
    H2, S2 = sec['h'], sec['s']
else:
    H2, S2 = (H1 + 40) % 360, 0.6  # analogous fallback

# --- tokens (lightness/saturation rules tuned on the approved v2 edit: the accent must glow on the dark caption band
#     AND read on light paper; deep = shirt-shadow tone for strokes and small text; ink/paper carry the hue faintly)
sat = lambda base, lo, hi: max(lo, min(hi, base))
tok = {
    'accent': hsl_hex(H1, sat(S1 * 1.6, 0.45, 0.72), 0.68),
    'accentDeep': hsl_hex(H1, sat(S1 * 1.2, 0.32, 0.55), 0.44),
    'accentSoft': hsl_hex(H1, sat(S1 * 1.6, 0.40, 0.62), 0.91),
    'warm': hsl_hex(H2, sat(S2 * 1.3, 0.55, 0.80), 0.80),
    'warmDeep': hsl_hex(H2, sat(S2 * 1.3, 0.50, 0.70), 0.67),
    'ink': hsl_hex(H1, 0.19, 0.14),
    'inkSoft': hsl_hex(H1, 0.14, 0.25),
    'grey': hsl_hex(H1, 0.07, 0.58),
    'paper': hsl_hex(H1, 0.33, 0.955),
    'paperCool': hsl_hex(H1 - 12, 0.30, 0.945),
}
if acc_arg:  # a steered colour is the designer's pick: use it exactly
    tok['accent'] = '#' + acc_arg.strip().lstrip('#').upper()
    tok['accentDeep'] = hsl_hex(H1, sat(S1 * 0.85, 0.30, 0.55), 0.44)
    tok['accentSoft'] = hsl_hex(H1, sat(S1, 0.35, 0.60), 0.91)
if warm_arg:
    tok['warm'] = '#' + warm_arg.strip().lstrip('#').upper()
tok['accentRgb'] = rgb_str(tok['accent'])
tok['grid'] = 'rgba(' + rgb_str(tok['ink']) + ',0.07)'

if '--dry-run' in sys.argv:
    print('palette (dry run) accent hue %d secondary hue %d neutral=%s' % (H1, H2, neutral))
    for k in ['accent', 'accentDeep', 'accentSoft', 'warm', 'ink', 'paper']:
        print(f'  {k:10s} {tok[k]}')
    print('  top clusters: ' + ', '.join('%s(%.0f%%%s)' % (c['hex'], 100 * c['area'], ',skin' if c['skin'] else '') for c in clusters[:4]))
    sys.exit(0)

# --- write
tpl = open(TEMPLATE, encoding='utf-8').read()
body = 'export const PALETTE: Palette | null = {\n' + ''.join(f"  {k}: '{v}',\n" for k, v in tok.items()) + '};\n'
ts = re.sub(r'export const PALETTE: Palette \| null = null;\n?', body, tpl)
ts = ts.replace('// PER-VIDEO footage palette.', '// PER-VIDEO footage palette (from ' + os.path.relpath(src, PROJ).replace('\\', '/') + ').', 1)
open(OUT_TS, 'w', encoding='utf-8', newline='\n').write(ts)
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
json.dump({'palette': tok, 'accentHue': round(H1), 'secondaryHue': round(H2), 'neutralFootage': neutral,
           'steered': {'accent': acc_arg, 'warm': warm_arg, 'exact': exact}, 'source': os.path.relpath(src, PROJ),
           'clusters': [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items()} for c in clusters]},
          open(OUT_JSON, 'w'), indent=1)

try:  # check sheet: 6 frames, then swatches on the dark band colour and on paper
    from PIL import Image, ImageDraw
    fw, fh = 216, 384
    sheet = Image.new('RGB', (fw * 6, fh + 150), (20, 20, 20))
    for i, f in enumerate(frames[::2][:6]):
        sheet.paste(Image.fromarray(f).resize((fw, fh)), (i * fw, 0))
    d = ImageDraw.Draw(sheet)
    names = ['accent', 'accentDeep', 'accentSoft', 'warm', 'warmDeep', 'ink', 'inkSoft', 'grey', 'paper', 'paperCool']
    sw = fw * 6 // len(names)
    for i, k in enumerate(names):
        x = i * sw
        d.rectangle([x, fh, x + sw, fh + 75], fill=tok[k])
        d.rectangle([x, fh + 75, x + sw, fh + 150], fill=tok['paper'] if k != 'paper' else tok['ink'])
        d.ellipse([x + sw // 2 - 22, fh + 90, x + sw // 2 + 22, fh + 134], fill=tok[k])
        d.text((x + 4, fh + 4), k + ' ' + tok[k], fill=(255, 255, 255) if colorsys.rgb_to_hls(*hexrgb(tok[k]))[1] < 0.6 else (0, 0, 0))
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    sheet.save(OUT_PNG)
except Exception as e:
    print('  (no check sheet: ' + str(e) + ')')

print(('palette: NEUTRAL footage, kept the style accent hue %d' % H1) if neutral and not acc_arg else
      'palette: accent hue %d (%s), secondary hue %d%s' % (H1, 'steered' if acc_arg else clusters[0]['hex'] + ' area %.0f%%' % (100 * clusters[0]['area']),
                                                          H2, ' (steered)' if warm_arg else (' (' + sec['hex'] + ')' if sec else ' (analogous fallback)')))
for k in ['accent', 'accentDeep', 'accentSoft', 'warm', 'warmDeep', 'ink', 'paper']:
    print(f'  {k:10s} {tok[k]}')
print('wrote remotion/src/data/palette.ts, work/plan/palette.json, work/frames/palette.png (check it by eye)')
