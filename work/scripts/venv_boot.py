"""Run every engine script inside the repo's own Python environment (.venv, made by install.py).
Scripts start with `import venv_boot`: when they were started with another Python (e.g. `python work/scripts/x.py` from a
plain shell), this re-runs the same command with .venv's Python and exits with its return code. No .venv yet -> nothing
happens (the script then uses whatever packages the current Python has, e.g. work/pylibs from an older install).
Uses a child process rather than os.exec*: on Windows exec returns to the shell early and breaks pipes."""
import os, subprocess, sys

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VENV = os.path.join(PROJ, '.venv')
VPY = os.path.join(VENV, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(VENV, 'bin', 'python')


def _inside():
    return os.path.normcase(os.path.realpath(sys.prefix)) == os.path.normcase(os.path.realpath(VENV))


def _help():
    """`python work/scripts/<x>.py --help`: print the script's docstring (or its header comment) and exit, instead of
    running it. Scripts with their own argparse help are left alone."""
    main = sys.modules.get('__main__')
    path = os.path.abspath(sys.argv[0])
    try:
        src = open(path, encoding='utf-8').read()
    except OSError:
        return
    if 'argparse' in src:
        return
    doc = (getattr(main, '__doc__', None) or '').strip()
    if not doc:
        lines = []
        for ln in src.splitlines():
            if ln.startswith('#'):
                lines.append(ln.lstrip('# ').rstrip())
            elif lines or (ln.strip() and not ln.startswith(('import', 'from'))):
                break
        doc = '\n'.join(lines).strip()
    name = os.path.basename(path)
    print(doc or f'usage: python work/scripts/{name}   (no options; the short-form-edit skill says when to run it)')
    sys.exit(0)


if any(a in ('-h', '--help') for a in sys.argv[1:]):
    _help()

if os.path.exists(VPY) and not _inside() and not os.environ.get('VENV_BOOT_DONE'):
    env = dict(os.environ, VENV_BOOT_DONE='1', PYTHONIOENCODING='utf-8', PYTHONUTF8='1', HF_HUB_DISABLE_XET='1',
               HF_HUB_DISABLE_SYMLINKS_WARNING='1')
    sys.exit(subprocess.call([VPY, os.path.abspath(sys.argv[0]), *sys.argv[1:]], env=env))
