"""Music bed for an edit, fitted to its exact length -> remotion/public/music.wav (48 kHz stereo).
usage: python work/scripts/music_fit.py [--mood calm|energetic] [--style podcast] [--pick N] [--file path]
Order (the skill's step 4 runs the Epidemic Sound connector first when it is connected; this script is the fallback):
  1. --file, or the track you put in input/music/ (used as is: trimmed to length with a 1.5 s fade-out);
  2. otherwise a bundled royalty-free track from assets/music/<style>/<mood>/ (CC0 / public domain, see
     assets/music/MUSIC_LICENSES.md); --pick N chooses one (default: rotates with the video so clips differ).
Tracks shorter than the edit are looped with a 2 s crossfade. Prints the credit line for EDIT_NOTES.md.
LEVEL: every track is mastered differently, so the exact stretch used is MEASURED (EBU R128) and set to the style's music
loudness (style.json "music": {"lufs": -24}; --lufs overrides; default -18). mix.py then places it under the voice the
same way every time, so every track sits the same distance below the speaker."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, re, sys, glob, json, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
OUT = os.path.join(PROJ, 'remotion', 'public', 'music.wav')
AUD = ('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac')
opt = {a.split('=')[0]: a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
for i, a in enumerate(sys.argv[1:], 1):  # also accept "--mood calm"
    if a.startswith('--') and '=' not in a and i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
        opt[a] = sys.argv[i + 1]


def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


edl = os.path.join(ROOT, 'transcript', 'edl.json')
if not os.path.exists(edl):
    sys.exit('no work/transcript/edl.json yet: run the cut first (the music is fitted to the cut length)')
length = json.load(open(edl))['total_frames'] / 30.0

src, credit = None, None
if '--file' in opt:
    src = opt['--file']
    credit = os.path.basename(src) + (' (bundled CC0, assets/music; licence: assets/music/MUSIC_LICENSES.md)'
                                      if 'assets' in os.path.abspath(src).replace(os.sep, '/').split('/') else ' (your track)')
else:
    own = [p for p in glob.glob(os.path.join(PROJ, 'input', 'music', '*')) if p.lower().endswith(AUD)]
    if own:
        src = sorted(own)[0]
        credit = os.path.basename(src) + ' (your track from input/music/)'
if not src:
    style = opt.get('--style')
    if not style:
        a = os.path.join(ROOT, 'active_style.json')
        style = json.load(open(a))['style'] if os.path.exists(a) else 'podcast'
    mood = opt.get('--mood')
    if not mood:  # the style's default mood
        try:
            from client_style import style_dir
            sj = os.path.join(style_dir(), 'style.json')
            mood = json.load(open(sj)).get('music', {}).get('default') if os.path.exists(sj) else None
        except BaseException:
            mood = None
        mood = mood or 'energetic'
    d = os.path.join(PROJ, 'assets', 'music', style, mood)
    if not os.path.isdir(d):
        d = os.path.join(PROJ, 'assets', 'music', 'podcast', mood)
    tracks = sorted(p for p in glob.glob(os.path.join(d, '*')) if p.lower().endswith(AUD))
    if not tracks:
        sys.exit(f'no music: nothing in input/music/ and no bundled tracks in {os.path.relpath(d, PROJ)} - edit runs without music')
    if '--pick' in opt:
        k = int(opt['--pick']) % len(tracks)
    else:  # rotate with the video so a batch of clips doesn't all use the same track
        vids = sorted(glob.glob(os.path.join(PROJ, 'input', '*.*')))
        names = [os.path.basename(v) for v in vids]
        seed = ('|'.join(names) or open(edl, encoding='utf-8').read()[:200]).encode()  # stable across re-cuts
        k = int(hashlib.md5(seed).hexdigest(), 16) % len(tracks)
        num = next((int(n.split('-')[0]) for n in names if n.split('-')[0].isdigit()), None)
        if num:  # a router clip "NN-title.mp4": consecutive clips of one video take consecutive tracks,
            rs = os.path.join(ROOT, 'run_state.json')  # starting from a track that depends on the video
            vid = json.load(open(rs, encoding='utf-8'))['video']['source'] if os.path.exists(rs) else ''
            k = (int(hashlib.md5(vid.encode()).hexdigest(), 16) + num - 1) % len(tracks)
    src = tracks[k]
    lic = os.path.join(PROJ, 'assets', 'music', 'MUSIC_LICENSES.md')
    name = os.path.splitext(os.path.basename(src))[0]
    credit = f'{name} (bundled CC0, ' + os.path.relpath(src, PROJ).replace(os.sep, '/') + '; licence: assets/music/MUSIC_LICENSES.md)'

T = dur(src)
fade = 1.5
# start a little into the track (skips slow intros) when it is long enough
start = 0.0
if T > length + 12:
    start = min(8.0, T - length - 2)
loops = 1 if T - start >= length else int((length - (T - start)) // (T - 2)) + 2
if loops == 1:
    filt = (f'[0:a]atrim=start={start:.3f}:duration={length:.3f},asetpts=PTS-STARTPTS,aresample=48000,'
            f'aformat=channel_layouts=stereo,afade=t=out:st={max(0, length - fade):.3f}:d={fade}[out]')
    inputs = ['-i', src]
else:
    inputs = []
    for _ in range(loops):
        inputs += ['-i', src]
    chain, last = [], '[0:a]'
    for i in range(1, loops):
        chain.append(f'{last}[{i}:a]acrossfade=d=2:c1=tri:c2=tri[x{i}]')
        last = f'[x{i}]'
    filt = (';'.join(chain) + f';{last}atrim=duration={length:.3f},asetpts=PTS-STARTPTS,aresample=48000,'
            f'aformat=channel_layouts=stereo,afade=t=out:st={max(0, length - fade):.3f}:d={fade}[out]')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
RAW = OUT[:-4] + '_raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', filt, '-map', '[out]', '-c:a', 'pcm_s16le', RAW], check=True)


def loudness(path):
    """Integrated loudness (EBU R128) of the stretch of music actually used."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)
    return float(m[-1]) if m else None


target = opt.get('--lufs')
if target is None:
    try:
        from client_style import style_dir
        sj = os.path.join(style_dir(), 'style.json')
        target = json.load(open(sj)).get('music', {}).get('lufs') if os.path.exists(sj) else None
    except BaseException:
        target = None
target = float(target if target is not None else -18)
measured = loudness(RAW)
gain = 0.0 if measured is None or measured < -60 else target - measured
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', RAW, '-af', f'volume={gain:.2f}dB', '-c:a', 'pcm_s16le', OUT], check=True)
os.remove(RAW)
json.dump({'file': os.path.relpath(src, PROJ).replace(os.sep, '/'), 'credit': credit, 'length': round(length, 2),
           'measured_lufs': measured, 'target_lufs': target, 'gain_db': round(gain, 2)},
          open(os.path.join(ROOT, 'plan', 'music.json'), 'w'), indent=1)
print(f'music: {credit}\n  -> remotion/public/music.wav ({length:.1f} s{", looped x" + str(loops) if loops > 1 else ""}); '
      f'level: measured {measured} LUFS -> {target} LUFS ({gain:+.1f} dB)')
