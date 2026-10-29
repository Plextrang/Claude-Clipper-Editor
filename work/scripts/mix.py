"""Sound-design session renderer.

Reads work/plan/sound_cues.json:
{
  "cues": [ {"id": "...", "family": "whoosh|texture|riser|hit", "file": "<path inside the sound pack>",
             "start": s, "peak": s, "end": s,      # variation bounds inside the file (seconds)
             "frame": F,                            # output frame where the PEAK must land
             "gainDb": -12, "fadeIn": 0.0, "fadeOut": 0.05, "note": "..."} ],
  "music": {"file": "remotion/public/music.wav", "baseDb": -19,
            "automation": [ [frame, dB], ... ]   # breakpoints, linear-in-dB between them
  }
}
Writes per-family stems + final master into deliverables/ and remotion/public/mix.wav.
"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json, io, subprocess, sys
import numpy as np, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
from client_style import sound_lib
LIB = sound_lib()  # the active client style's sound pack
SR = 48000
FPS = 30
TOTAL_F = json.load(open(os.path.join(ROOT, 'transcript', 'edl.json')))['total_frames']
N = int(round(TOTAL_F / FPS * SR))


def load(path, af=None):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path] + (['-af', af] if af else []) + ['-ac', '2', '-ar', str(SR), '-f', 'wav', '-acodec', 'pcm_f32le', '-'],
                         capture_output=True, check=True).stdout
    x, sr = sf.read(io.BytesIO(raw), dtype='float32')
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    return x


def db2g(db):
    return 10 ** (db / 20)


# Mobile translation (client feedback 2026-10-02): on phone speakers the music bed and SFX disappear, so both sit
# higher than the headphone-balanced mix. The VOICE is locked: the master gain is computed from the un-boosted mix
# (the approved balance), and these boosts are added on top of it.
MUSIC_BOOST_DB = 6.0
SFX_BOOST_DB = 4.0
SFX_UNDER_VOICE_DB = 1.0  # boosted SFX are capped to stay at least this far under the voice (400 ms windows)
MUSIC_EQ = 'highshelf=f=2500:g=4'  # presence lift: phone speakers can't play the bed's low end, so give it top end


def lufs(x):
    """ITU-R BS.1770 integrated loudness via ffmpeg ebur128 (robust, matches deliverable checks)."""
    buf = io.BytesIO(); sf.write(buf, x, SR, format='WAV', subtype='FLOAT'); buf.seek(0)
    r = subprocess.run(['ffmpeg', '-v', 'info', '-f', 'wav', '-i', '-', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       input=buf.read(), capture_output=True)
    txt = r.stderr.decode(errors='ignore')
    I = tp = None
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith('I:'): I = float(line.split()[1])
        if line.startswith('Peak:'): tp = float(line.split()[1])
    return I, tp


def short_term_db(x, win=0.4):
    m = x.mean(axis=1)
    h = int(SR * 0.1)
    w = int(SR * win)
    out = []
    for i in range(0, len(m) - w, h):
        out.append(10 * np.log10(np.mean(m[i:i + w] ** 2) + 1e-12))
    return np.array(out)


def limit(x, ceiling_db):
    """Transparent peak limiter: ffmpeg alimiter run at 4x sample rate (catches inter-sample peaks), 5 ms look-ahead."""
    buf = io.BytesIO(); sf.write(buf, x, SR, format='WAV', subtype='FLOAT'); buf.seek(0)
    af = (f'aresample={SR * 4},alimiter=limit={db2g(ceiling_db):.4f}:attack=5:release=60:level=false:latency=true,'
          f'aresample={SR}')
    r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'wav', '-i', '-', '-af', af, '-f', 'wav', '-acodec', 'pcm_f32le', '-'],
                       input=buf.read(), capture_output=True, check=True)
    y, _ = sf.read(io.BytesIO(r.stdout), dtype='float32')
    y = y[:len(x)]
    return np.pad(y, ((0, len(x) - len(y)), (0, 0)))


def sfx_cap(voice, sfx):
    """Per-sample gain (<=1) that keeps the boosted SFX under the voice wherever he is talking. Smooth, never pumps."""
    vs = short_term_db(voice); ss = short_term_db(sfx)
    n = min(len(vs), len(ss))
    cap = np.array([min(0.0, (vs[i] - SFX_UNDER_VOICE_DB) - ss[i]) if vs[i] > -45 else 0.0 for i in range(n)])
    cap = np.array([cap[max(0, i - 2):i + 3].min() for i in range(n)])  # spread +-200 ms
    cap = np.convolve(cap, np.ones(3) / 3, mode='same')
    env = np.interp(np.arange(N) / SR, np.arange(n) * 0.1 + 0.2, cap)  # window centres
    return db2g(env).astype(np.float32)


def main():
    spec = json.load(open(os.path.join(ROOT, 'plan', 'sound_cues.json')))
    stems = {k: np.zeros((N, 2), np.float32) for k in ['whoosh', 'texture', 'riser', 'hit']}
    cache = {}
    report = []
    for c in spec['cues']:
        p = os.path.join(LIB, c['file'])
        if p not in cache:
            cache[p] = load(p)
        x = cache[p]
        a = int(round(c['start'] * SR)); b = int(round(c['end'] * SR)); pk = int(round(c['peak'] * SR))
        seg = x[a:b].copy()
        if len(seg) == 0:
            print('EMPTY SEGMENT', c); continue
        fi = int(c.get('fadeIn', 0.0) * SR); fo = int(c.get('fadeOut', 0.04) * SR)
        if fi > 0: seg[:fi] *= np.linspace(0, 1, fi)[:, None]
        if fo > 0: seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        seg *= db2g(c['gainDb'])
        t_peak = c['frame'] / FPS
        pos = int(round(t_peak * SR)) - (pk - a)
        s0 = max(0, pos); s1 = min(N, pos + len(seg))
        if s1 <= s0:
            print('OUT OF RANGE', c['id']); continue
        piece = seg[s0 - pos:s1 - pos].copy()
        if pos < 0:  # lead-in clipped by the start of the video -> micro fade to avoid a click
            k = min(len(piece), int(0.012 * SR)); piece[:k] *= np.linspace(0, 1, k)[:, None]
        stems[c['family']][s0:s1] += piece
        report.append((c['id'], c['family'], c['frame'], round((pos) / SR, 3), c['gainDb'], c['file'].split('/')[-1][:50]))

    voice = load(os.path.join(PROJ, 'remotion', 'public', 'voice.wav'))[:N]
    voice = np.pad(voice, ((0, N - len(voice)), (0, 0)))

    # music + automation (linear in dB between breakpoints, evaluated per sample)
    m = spec['music']
    mpath = os.path.join(PROJ, m['file'])
    mus = load(mpath, MUSIC_EQ)[:N] if os.path.exists(mpath) else np.zeros((N, 2), np.float32)  # no track -> no music
    mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
    bps = sorted(m['automation'])
    tf = np.array([b[0] / FPS for b in bps]); dbs = np.array([b[1] for b in bps], dtype=np.float64)
    t = np.arange(N) / SR
    env_db = np.interp(t, tf, dbs) + m.get('baseDb', 0)
    env = np.where(env_db <= -79, 0.0, 10 ** (env_db / 20)).astype(np.float32)
    mus *= env[:, None]

    # master gain from the approved (un-boosted) balance -> the voice level never changes
    pre_I, pre_tp = lufs(voice + sum(stems.values()) + mus)
    target = spec.get('targetLUFS', -14.0)
    g = db2g(target - pre_I)
    # mobile boosts on top
    mus = mus * db2g(MUSIC_BOOST_DB)
    cap = sfx_cap(voice, sum(stems.values()) * db2g(SFX_BOOST_DB))
    for k in stems:
        stems[k] = stems[k] * db2g(SFX_BOOST_DB) * cap[:, None]
    sfx_sum = sum(stems.values())
    mixbus = voice + sfx_sum + mus
    # soft safety: transparent limiter-ish (tanh above -1 dBFS)
    raw = mixbus * g
    for lim_db in (-1.6, -2.0, -2.4, -2.8):  # 4x-oversampled look-ahead limiter until TRUE peak <= -1.0 dBTP
        master = limit(raw, lim_db)
        I, tp = lufs(master)
        if tp <= -1.0:
            break
    print(f'limiter ceiling {lim_db} dBFS; raw peak {20 * np.log10(np.abs(raw).max() + 1e-12):+.1f} dBFS')

    out = os.path.join(PROJ, 'deliverables', 'audio_stems')
    os.makedirs(out, exist_ok=True)
    names = {'whoosh': 'WHOOSHES', 'texture': 'TEXTURES', 'riser': 'RISERS', 'hit': 'HITS'}
    for k, v in stems.items():
        sf.write(os.path.join(out, names[k] + '.wav'), v * g, SR, subtype='PCM_24')
    sf.write(os.path.join(out, 'MUSIC.wav'), mus * g, SR, subtype='PCM_24')
    sf.write(os.path.join(out, 'VOICE.wav'), voice * g, SR, subtype='PCM_24')
    sf.write(os.path.join(PROJ, 'remotion', 'public', 'mix.wav'), master, SR, subtype='PCM_24')
    sf.write(os.path.join(out, 'MASTER_MIX.wav'), master, SR, subtype='PCM_24')

    # QC: SFX must never be louder than the voice (short-term, 400ms windows)
    vs = short_term_db(voice); ss = short_term_db(sfx_sum); ms = short_term_db(mus)
    hot = [(round(i * 0.1, 1), round(float(ss[i] - vs[i]), 1)) for i in range(min(len(vs), len(ss))) if vs[i] > -45 and ss[i] > vs[i] - 2]
    loud_sfx_in_gaps = [(round(i * 0.1, 1), round(float(ss[i]), 1)) for i in range(len(ss)) if vs[i] <= -45 and ss[i] > -14]
    print('cues placed:', len(report))
    for r in report: print('  ', r)
    print(f'pre-norm I={pre_I} TP={pre_tp}  -> master I={I} LUFS  TP={tp} dBFS (gain {20*np.log10(g):+.2f} dB)')
    print('voice-relative hot spots (SFX within 2 dB of / above voice):', hot[:40])
    print('loud SFX in voice gaps (> -14 dBFS short-term):', loud_sfx_in_gaps[:20])
    json.dump({'I': I, 'TP': tp, 'hot': hot, 'cues': len(report)}, open(os.path.join(ROOT, 'plan', 'mix_report.json'), 'w'))


if __name__ == '__main__':
    main()
