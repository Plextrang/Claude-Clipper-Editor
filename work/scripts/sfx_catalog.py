"""Make sure the SFX catalogue matches the active client style's sound pack; rebuild it if not.
usage: python work/scripts/sfx_catalog.py
The catalogue (<sound pack>/_catalogue/sfx_analysis.json, sfx_events.json, sfx_audition.json) lists every file and every
variation inside it (start / peak / end seconds) - the sound-design step picks cues from it. It is rebuilt automatically
whenever the pack's files change (about a minute). The sound pack is clients/<client>/sound-pack/ (see client_style.py)."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from client_style import sound_lib, catalogue, rel
LIB = sound_lib()
EV = catalogue('sfx_events.json')

files = set()
for dp, dn, fn in os.walk(LIB):
    for f in fn:
        if f.lower().endswith(('.mp3', '.wav')):
            files.add(os.path.relpath(os.path.join(dp, f), LIB).replace(os.sep, '/'))
if not files:
    print(f'no audio in {rel(LIB)}/ - this edit runs without sound effects (add the client\'s SFX there to use them)')
    sys.exit(0)
cat = set(json.load(open(EV))) if os.path.exists(EV) else set()
if cat and cat <= files and len(files - cat) <= len(files) * 0.1:
    print(f'SFX catalogue OK: {len(cat)} of {len(files)} library files catalogued')
    sys.exit(0)
print(f'rebuilding SFX catalogue ({len(files)} files; catalogue had {len(cat)}, {len(cat - files)} missing from the library) ...', flush=True)
for s in ['sfx_analyze.py', 'sfx_segments.py', 'sfx_audition.py']:
    subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', s)], check=True, stdout=subprocess.DEVNULL)
print('SFX catalogue rebuilt:', len(json.load(open(EV))), 'files')
