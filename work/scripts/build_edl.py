"""Build the EDL from keeper ranges: refine boundaries on the 5ms energy envelope, trim internal pauses,
and map every transcript word into the output timeline.
usage: python work/scripts/build_edl.py            (pauses over 0.24 s are trimmed to 0.14 s)
       MAX_PAUSE=0.7 python work/scripts/build_edl.py   (only trim pauses over 0.7 s: conversation / podcast clips)
       (a kit style's style.json "maxPause" sets the same thing for that style)"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json, numpy as np, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
x, sr = sf.read(os.path.join(ROOT,'audio','voice48k.wav')); x = x.mean(axis=1) if x.ndim>1 else x
HOP = 0.005; h = int(sr*HOP)
db = 20*np.log10(np.array([np.sqrt(np.mean(x[i*h:(i+1)*h]**2)+1e-12) for i in range(len(x)//h)]))
T = lambda i: i*HOP; I = lambda t: int(round(t/HOP))

# Keeper sentences (source seconds, rough) + label. Bad takes / breaths / retakes are simply not listed.
# Keeper sentences per video: work/plan/keep.json = [["S01", 3.70, 9.05, "Exact sentence text"], ...] (source seconds, rough)
_kp = os.path.join(ROOT, 'plan', 'keep.json')
assert os.path.exists(_kp), 'write work/plan/keep.json with the keeper sentences first (see SKILL step 2)'
KEEP = [tuple(k) for k in json.load(open(_kp, encoding='utf-8'))]
ON_DB, OFF_DB = -40.0, -44.0
PRE, POST = 0.045, 0.085           # handles kept around speech
def _style_pause():  # a kit style can set "maxPause" in its style.json (podcast: 0.7 s, so a conversation keeps its breath)
    try:
        from client_style import style_dir
        sj = os.path.join(style_dir(), 'style.json')
        return json.load(open(sj)).get('maxPause') if os.path.exists(sj) else None
    except BaseException:
        return None
MAX_GAP_IN = float(os.environ.get('MAX_PAUSE') or _style_pause() or 0.24)  # internal pauses longer than this get trimmed...
KEEP_GAP = 0.14                    # ...down to this
MIN_SIL = 0.20

NDB = len(db)
DUR = NDB * HOP
try:  # the picture can be a few ms shorter than its audio: never cut past the last video frame
    import glob as _g, subprocess as _sp
    _raw = [p for p in _g.glob(os.path.join(os.path.dirname(ROOT), 'input', '*')) if p.lower().endswith(('.mp4', '.mov', '.mkv', '.m4v'))]
    if len(_raw) == 1:
        _vd = float(_sp.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0',
                             _raw[0]], capture_output=True, text=True).stdout.strip() or 0)
        if _vd > 0:
            DUR = min(DUR, _vd - 1.0 / 30)
except Exception:
    pass
clip_i = lambda i: max(0, min(NDB, i))  # never read outside the audio (ranges at the very start or end)

def refine_in(t):
    a, b = clip_i(I(t-0.15)), clip_i(I(t+0.45))
    for i in range(a, b):
        if db[i] > ON_DB and np.all(db[i:i+6] > -52): return T(i)
    return t
def refine_out(t):
    a, b = clip_i(I(t-0.35)), clip_i(I(t+0.15))
    last = None
    for i in range(a, b):
        if db[i] > OFF_DB: last = i
    return T(last+1) if last is not None else t

# Whisper's words (source seconds): the cut never keeps silent frames before a range's first word or after its last word,
# and drops tiny pieces with no word in them. Between takes the speaker often looks down at notes while breathing: those
# frames read as "dead frames" in the edit.
SRC_WORDS = [w for s_ in json.load(open(os.path.join(ROOT, 'transcript', 'whisper_small.en.json'))) for w in s_['words']]
LEAD_MAX, TAIL_MAX = 0.12, 0.18   # at most this much before the first word / after the last word of a range
MIN_PIECE = 0.40                  # a piece shorter than this with no word in it is dropped


def has_word(a, b):
    return any(a - 0.02 <= (w['s'] + w['e']) / 2 <= b + 0.02 for w in SRC_WORDS)


edl = []
for sid, a, b, txt in KEEP:
    on, off = refine_in(a), refine_out(b)
    inside = [w for w in SRC_WORDS if a - 0.3 <= (w['s'] + w['e']) / 2 <= b + 0.3]
    if inside:
        on2 = max(on, inside[0]['s'] - LEAD_MAX + PRE)
        off2 = min(off, inside[-1]['e'] + TAIL_MAX - POST)
        if on2 < off2:
            on, off = on2, off2
    s, e = max(0.0, on - PRE), min(DUR, off + POST)  # a negative start would shift every later cut by a frame
    if edl and s < edl[-1]['src_out']:  # handles of touching ranges must not overlap (the audio would repeat)
        s = edl[-1]['src_out']
    # internal silences
    i0, i1 = I(on), I(off)
    sil = db[i0:i1] < -48
    cuts = []; k = 0
    while k < len(sil):
        if sil[k]:
            j = k
            while j < len(sil) and sil[j]: j += 1
            dur = (j-k)*HOP
            if dur >= MAX_GAP_IN:
                ss, se = T(i0+k), T(i0+j)
                mid_keep = KEEP_GAP/2
                cuts.append((ss+mid_keep, se-mid_keep))
            k = j
        else: k += 1
    pieces = []; cur = s
    for cs, ce in cuts:
        pieces.append((cur, cs)); cur = ce
    pieces.append((cur, e))
    dropped = [(round(x, 2), round(y, 2)) for x, y in pieces if y - x < MIN_PIECE and not has_word(x, y)]
    pieces = [(x, y) for x, y in pieces if y - x >= MIN_PIECE or has_word(x, y)]
    if dropped:
        print(f'{sid}: dropped wordless micro-pieces {dropped}')
    for pi, (ps, pe) in enumerate(pieces):
        edl.append({'id': f'{sid}.{pi}', 'sent': sid, 'src_in': round(ps,3), 'src_out': round(pe,3)})
    print(f'{sid}: on {on:.3f} off {off:.3f}  -> [{s:.3f},{e:.3f}]  internal trims: {[(round(c[0],2),round(c[1],2)) for c in cuts]}')

# frame-quantize to 30fps on the output timeline
FPS = 30
t = 0.0
for c in edl:
    # snap source in/out to frame boundaries of source (source is 30fps CFR)
    c['src_in_f'] = int(round(c['src_in']*FPS)); c['src_out_f'] = int(round(c['src_out']*FPS))
    c['out_in_f'] = int(round(t*FPS)) if not edl.index(c) else edl[edl.index(c)-1]['out_out_f']
    c['out_out_f'] = c['out_in_f'] + (c['src_out_f'] - c['src_in_f'])
total_f = edl[-1]['out_out_f']
print('pieces', len(edl), 'total frames', total_f, f'= {total_f/FPS:.2f}s')

# map words to output timeline
words = [w for s in json.load(open(os.path.join(ROOT,'transcript','whisper_small.en.json'))) for w in s['words']]
def src2out(ts):
    for c in edl:
        a, b = c['src_in_f']/FPS, c['src_out_f']/FPS
        if a - 1e-6 <= ts <= b + 1e-6:
            return c['out_in_f']/FPS + (ts - a)
    return None
out_words = []
for w in words:
    mid = (w['s']+w['e'])/2
    if src2out(mid) is None: continue
    # refine word start on energy: nearest onset within +-0.12s
    s_out = src2out(max(w['s'], 0)); e_out = src2out(w['e'])
    if s_out is None: s_out = src2out(mid) - 0.1
    if e_out is None: e_out = src2out(mid) + 0.1
    out_words.append({'w': w['w'].strip(), 'src_s': w['s'], 'src_e': w['e'], 's': round(s_out,3), 'e': round(e_out,3), 'p': w['p']})
json.dump({'fps': FPS, 'total_frames': total_f, 'edl': edl}, open(os.path.join(ROOT,'transcript','edl.json'),'w'), indent=1)
json.dump(out_words, open(os.path.join(ROOT,'transcript','words_out.json'),'w'), indent=1)
print(len(out_words), 'words mapped')
print(' '.join(w['w'] for w in out_words))
