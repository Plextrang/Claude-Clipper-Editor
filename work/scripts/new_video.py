"""Start a new video in this repo: archive the previous video's per-video files and reset the per-video data.
usage: python work/scripts/new_video.py <slug-of-the-PREVIOUS-video> [--dry-run]
   e.g. python work/scripts/new_video.py my-last-video --dry-run         (then without --dry-run)

MOVES (relative paths preserved) into archive/<slug>/ :
  deliverables/* (except video folders made by the edit-any-video router: they hold clips.md), remotion/public/broll/ (work/broll/ search results stay: the next clip of the video reuses them), remotion/out/, remotion/public/{aroll.mp4,voice.wav,music.wav,mix.wav}, remotion/src/scenes/*,
  remotion/src/preview/*, remotion/src/data/{edit.ts,words.json,scenes.ts,palette.ts}, work/{audio,frames,music,music_audition}/*,
  work/transcript/*, work/plan/* (except CRAFT_DEFAULTS.md, ENGINE.md), work/*.log
COPIES (they stay, you edit the per-video part): work/scripts/build_edl.py (KEEP list), work/scripts/transcribe_cut.py
  (initial_prompt vocabulary), work/active_style.json (records which client style the video used).
ALSO MOVES the raw video in input/ when it is the PREVIOUS video's footage (same duration as work/audio/voice48k.wav, which was
  extracted from it), so it can never be re-edited by mistake. A NEW recording already dropped into input/ is kept.
KEEPS: the engine (components, lib, Main/Root, scripts), styles/ and clients/ (styles, sound packs and their catalogues), remotion/public/{brand,ui}/ (the real logo + UI glyph library),
  work/pylibs + work/hf_cache (Whisper install), archive/ (old scenes = worked examples).
Then copies fresh edit.ts / words.json / scenes.ts / palette.ts from work/templates so the project still typechecks."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, glob, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
args = [a for a in sys.argv[1:] if not a.startswith('--')]
DRY = '--dry-run' in sys.argv
if not args:
    sys.exit(__doc__)
ARC = os.path.join(PROJ, 'archive', args[0])
if os.path.exists(ARC) and not DRY:
    sys.exit(f'archive/{args[0]} already exists - pick another slug')

rel = lambda p: os.path.relpath(p, PROJ).replace('\\', '/')
moves, copies = [], []
def _dur(path, stream='format'):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return None


ref = os.path.join(ROOT, 'audio', 'voice48k.wav')
QUIET = '--quiet' in sys.argv
b = _dur(ref) if os.path.exists(ref) else None
cands = glob.glob(os.path.join(PROJ, 'input', '*')) + [os.path.join(PROJ, 'Raw Footage.mp4')]
for raw in [p for p in cands if os.path.isfile(p) and p.lower().endswith(('.mp4', '.mov', '.mkv', '.m4v'))]:
    a = _dur(raw)
    if a is not None and b is not None and abs(a - b) < 0.1:
        moves.append(raw)  # the PREVIOUS video's footage
    else:
        print(f'keep  {rel(raw)} (looks NEW: {a}s vs previous {b}s)')
# deliverables/: the engine's own outputs move; folders made by the edit-any-video router (they hold clips.md) stay
for p in glob.glob(os.path.join(PROJ, 'deliverables', '*')):
    if not (os.path.isdir(p) and os.path.exists(os.path.join(p, 'clips.md'))):
        moves.append(p)
if os.path.exists(os.path.join(PROJ, 'remotion', 'out')): moves.append(os.path.join(PROJ, 'remotion', 'out'))
for f in ['aroll.mp4', 'voice.wav', 'music.wav', 'mix.wav', 'broll']:  # broll/ = this video's B-roll (broll_fetch.py)
    moves += glob.glob(os.path.join(PROJ, 'remotion', 'public', f))
moves += glob.glob(os.path.join(PROJ, 'remotion', 'src', 'scenes', '*'))
moves += glob.glob(os.path.join(PROJ, 'remotion', 'src', 'preview', '*'))
moves += [os.path.join(PROJ, 'remotion', 'src', 'data', f) for f in ['edit.ts', 'words.json', 'scenes.ts', 'palette.ts']]
for d in ['audio', 'frames', 'music', 'music_audition']:
    moves += glob.glob(os.path.join(ROOT, d, '*'))
moves += glob.glob(os.path.join(ROOT, 'transcript', '*'))
moves += [p for p in glob.glob(os.path.join(ROOT, 'plan', '*')) if os.path.basename(p) not in ('CRAFT_DEFAULTS.md', 'ENGINE.md')]
moves += glob.glob(os.path.join(ROOT, '*.log'))
copies += [os.path.join(ROOT, 'scripts', f) for f in ['build_edl.py', 'transcribe_cut.py']] + [os.path.join(ROOT, 'active_style.json')]
moves = [p for p in moves if os.path.exists(p)]
copies = [p for p in copies if os.path.exists(p)]

if not QUIET or DRY:
    for p in moves: print('move ', rel(p))
    for p in copies: print('copy ', rel(p))
if DRY:
    print(f'\n(dry run) {len(moves)} moves, {len(copies)} copies -> archive/{args[0]}/'); sys.exit(0)

for p in copies:
    dst = os.path.join(ARC, rel(p)); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(p, dst)
for p in moves:
    dst = os.path.join(ARC, rel(p)); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.move(p, dst)
os.makedirs(os.path.join(PROJ, 'deliverables'), exist_ok=True)
open(os.path.join(PROJ, 'deliverables', '.gitkeep'), 'a').close()

DATA = os.path.join(PROJ, 'remotion', 'src', 'data')
for f in ['edit.ts', 'words.json', 'scenes.ts', 'palette.ts']:  # fresh per-video data from work/templates
    shutil.copy(os.path.join(ROOT, 'templates', f), os.path.join(DATA, f))
print(f'\narchived {len(moves)} items to archive/{args[0]}/ and reset per-video data. Next: put the NEW raw video in input/.')
