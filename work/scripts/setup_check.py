"""Health check (step 0 of every edit). Safe to run every time; it only installs what is missing.
usage: python work/scripts/setup_check.py
The full first-run setup is `python install.py` at the repo root (system tools, .venv, Whisper models, Node packages);
this check runs at its end and before every edit.
- Python packages (requirements.txt): looked up the same way the scripts do (work/pylibs first, then the normal environment);
  missing ones are installed with pip into the current Python environment.
- Node packages for the video engine: `npm ci` in remotion/ if node_modules is missing.
- ffmpeg + ffprobe must be on PATH (python install.py installs them).
- Real brand logos + UI glyphs for the scenes: runs fetch_brand_assets.py when remotion/public/brand/ is missing."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, shutil, subprocess, importlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pylibs'))
ok = True
HINT = {'win32': 'winget install -e --id {w}', 'darwin': 'brew install {b}'}.get(sys.platform, 'sudo apt install {a}')

DATA = os.path.join(PROJ, 'remotion', 'src', 'data')
for f in ['edit.ts', 'words.json', 'scenes.ts', 'style_theme.ts', 'palette.ts']:  # git-ignored files: start from the templates
    if not os.path.exists(os.path.join(DATA, f)):
        shutil.copy(os.path.join(ROOT, 'templates', f), os.path.join(DATA, f))
        print('created remotion/src/data/' + f + ' from work/templates')

missing = []
for mod in ['faster_whisper', 'soundfile', 'numpy', 'PIL', 'librosa', 'cv2', 'yt_dlp']:
    try:
        importlib.import_module(mod)
    except Exception:
        missing.append(mod)
if missing and os.environ.get('SETUP_FROM_INSTALL'):
    print('MISSING Python packages: ' + ', '.join(missing)); ok = False
elif missing:
    print('Python packages missing (' + ', '.join(missing) + '): running python install.py ...', flush=True)
    r = subprocess.run([sys.executable, os.path.join(PROJ, 'install.py'), '--no-models'])
    ok &= r.returncode == 0
else:
    print('python packages: ok')

nm = os.path.join(PROJ, 'remotion', 'node_modules')
if not os.path.isdir(nm):
    npm = shutil.which('npm')
    if not npm:
        print('MISSING: Node.js/npm - run python install.py (or: ' + HINT.format(w='OpenJS.NodeJS.LTS', b='node', a='nodejs npm') + ')'); ok = False
    else:
        print('installing Node packages (npm ci) ...', flush=True)
        r = subprocess.run([npm, 'ci', '--no-audit', '--no-fund'], cwd=os.path.join(PROJ, 'remotion'), shell=(os.name == 'nt'))
        ok &= r.returncode == 0
else:
    print('node packages: ok')

for tool in ['ffmpeg', 'ffprobe']:
    if not shutil.which(tool):
        print(f'MISSING: {tool} - run python install.py (or: ' + HINT.format(w='Gyan.FFmpeg', b='ffmpeg', a='ffmpeg') + ')'); ok = False
if ok:
    print('ffmpeg: ok')
brand = os.path.join(PROJ, 'remotion', 'public', 'brand', 'README.md')
if not os.path.exists(brand) and shutil.which('npm'):
    print('fetching real brand logos + UI glyphs (fetch_brand_assets.py) ...', flush=True)
    subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'fetch_brand_assets.py')])
if os.path.exists(brand):
    print('brand assets: ok')
else:
    print('WARNING: no brand assets - run python work/scripts/fetch_brand_assets.py (scenes need real logos/UI glyphs)')
print('SETUP OK' if ok else 'SETUP INCOMPLETE - fix the MISSING items above')
sys.exit(0 if ok else 1)
