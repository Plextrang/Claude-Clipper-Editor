"""First-run setup. Claude runs this for you the first time you ask for an edit; it is safe to run again at any time
(it only installs what is missing).

    python install.py                  # everything
    python install.py --no-models      # skip the Whisper model download (~2 GB; it then happens on the first edit)
    python install.py --clipper-remotion   # also the optional Remotion renderer of the clip style

What it does:
  1. ffmpeg and Node.js: installs them if missing (Windows: winget, macOS: Homebrew, Linux: apt).
  2. A private Python environment in .venv/ with every Python package (yt-dlp, faster-whisper, OpenCV, ...).
  3. The Whisper speech models (small.en, medium.en, tiny) into work/hf_cache/.
  4. The video engine's Node packages (Remotion) in remotion/.
  5. The real brand-logo and UI-glyph library, and the engine's starter data files.
Nothing outside this folder changes except the two system tools in step 1.
"""
import os
import shutil
import subprocess
import sys
import time
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / '.venv'
PY = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
MODELS = ROOT / 'work' / 'hf_cache' / 'models'
OS = 'win' if os.name == 'nt' else ('mac' if sys.platform == 'darwin' else 'linux')
INSTALL = {
    'ffmpeg': {'win': ['winget', 'install', '-e', '--id', 'Gyan.FFmpeg', '--accept-source-agreements', '--accept-package-agreements'],
               'mac': ['brew', 'install', 'ffmpeg'], 'linux': ['sudo', 'apt-get', 'install', '-y', 'ffmpeg']},
    'node': {'win': ['winget', 'install', '-e', '--id', 'OpenJS.NodeJS.LTS', '--accept-source-agreements', '--accept-package-agreements'],
             'mac': ['brew', 'install', 'node'], 'linux': ['sudo', 'apt-get', 'install', '-y', 'nodejs', 'npm']},
}
log = []


def say(msg):
    print(msg, flush=True)
    log.append(msg)


def refresh_path():
    """After winget/brew installs, the current process doesn't see the new PATH yet: add the usual install folders."""
    extra = []
    if OS == 'win':
        la = os.environ.get('LOCALAPPDATA', '')
        extra += [os.path.join(la, 'Microsoft', 'WinGet', 'Links'), r'C:\Program Files\nodejs']
        pkgs = Path(la) / 'Microsoft' / 'WinGet' / 'Packages'
        if pkgs.exists():
            extra += [str(p) for p in pkgs.glob('Gyan.FFmpeg*/*/bin')]
    else:
        extra += ['/opt/homebrew/bin', '/usr/local/bin']
    for d in extra:
        if d and os.path.isdir(d) and d not in os.environ['PATH']:
            os.environ['PATH'] = d + os.pathsep + os.environ['PATH']


def ensure_tool(name, exe):
    if shutil.which(exe):
        say(f'[ok] {name} already installed')
        return True
    cmd = INSTALL[name][OS]
    if not shutil.which(cmd[0]):
        say(f'[X] {name} is missing and {cmd[0]} is not available to install it. Install {name} yourself, then run '
            f'python install.py again. (macOS: install Homebrew from https://brew.sh first.)')
        return False
    say(f'-> installing {name}: {" ".join(cmd)}')
    t0 = time.time()
    subprocess.run(cmd)
    refresh_path()
    if shutil.which(exe):
        say(f'[ok] {name} installed ({time.time() - t0:.0f} s)')
        return True
    say(f'[!] {name} was installed but this window does not see it yet: close and reopen Claude Code (or your terminal),'
        f' then run python install.py again.')
    return False


def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print(__doc__)
        sys.exit(0)
    t_all = time.time()
    say('== Claude Clipper Editor: setup ==')
    if sys.version_info < (3, 10):
        say(f'[X] Python 3.10+ needed (you have {sys.version.split()[0]}). Install it from python.org (Windows: tick "Add to PATH").')
        sys.exit(1)
    say(f'[ok] Python {sys.version.split()[0]}')
    refresh_path()
    ok = ensure_tool('ffmpeg', 'ffmpeg') & ensure_tool('node', 'npm')

    # 2. python environment
    t0 = time.time()
    if not PY.exists():
        say('-> creating .venv (a private Python environment for this folder) ...')
        venv.create(VENV, with_pip=True)
    say('-> installing Python packages (the first time takes a few minutes) ...')
    subprocess.run([str(PY), '-m', 'pip', 'install', '--upgrade', 'pip', '-q'], check=False)
    r = subprocess.run([str(PY), '-m', 'pip', 'install', '-q', '-r', str(ROOT / 'requirements.txt')])
    if r.returncode != 0:
        ok = False
        say('[X] pip install failed (see the error above)')
    else:
        subprocess.run([str(PY), '-m', 'pip', 'install', '-q', '-U', 'yt-dlp[default]'], check=False)  # YouTube changes often
        say(f'[ok] Python packages ({time.time() - t0:.0f} s)')

    # 3. whisper models
    if '--no-models' not in sys.argv and r.returncode == 0:
        t0 = time.time()
        say('-> downloading the Whisper speech models (small.en, medium.en, tiny; ~2 GB, once) ...')
        code = ('import os; os.environ["HF_HUB_DISABLE_XET"]="1"; os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"]="1";'
                'from faster_whisper import download_model as d; root=r"%s";'
                '[print("   ", m, d(m, cache_dir=root), flush=True) for m in ("tiny", "small.en", "medium.en")]' % MODELS)
        env = dict(os.environ, HF_HOME=str(ROOT / 'work' / 'hf_cache'))
        rr = subprocess.run([str(PY), '-c', code], env=env)
        if rr.returncode == 0:
            say(f'[ok] Whisper models ({time.time() - t0:.0f} s)')
        else:
            say('[!] model download failed: they will download on the first edit instead')

    # 4. node packages
    npm = shutil.which('npm')
    for folder, wanted in ((ROOT / 'remotion', True), (ROOT / 'clipper' / 'remotion', '--clipper-remotion' in sys.argv)):
        if not wanted:
            continue
        if (folder / 'node_modules').is_dir():
            say(f'[ok] Node packages in {folder.relative_to(ROOT)}')
            continue
        if not npm:
            ok = False
            say(f'[X] Node.js/npm missing: cannot install {folder.relative_to(ROOT)}')
            continue
        t0 = time.time()
        say(f'-> installing the video engine (npm ci in {folder.relative_to(ROOT)}) ...')
        rn = subprocess.run([npm, 'ci', '--no-audit', '--no-fund'], cwd=folder, shell=(os.name == 'nt'))
        if rn.returncode == 0:
            say(f'[ok] Node packages ({time.time() - t0:.0f} s)')
        else:
            ok = False
            say('[X] npm ci failed (see above)')

    # 5. engine data files + brand library (setup_check also re-checks everything)
    if PY.exists():
        t0 = time.time()
        rs = subprocess.run([str(PY), str(ROOT / 'work' / 'scripts' / 'setup_check.py')], env=dict(os.environ, SETUP_FROM_INSTALL='1'))
        ok = ok and rs.returncode == 0
        say(f'[ok] engine check ({time.time() - t0:.0f} s)' if rs.returncode == 0 else '[X] engine check reported problems (above)')

    say('')
    say(f'Setup {"complete" if ok else "finished with problems"} in {(time.time() - t_all) / 60:.1f} min.')
    say('Next, ask Claude:  edit this: <YouTube link or video file>' if ok else 'Fix the [X] items above and run python install.py again.')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
