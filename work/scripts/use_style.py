"""Select the style an edit uses, or re-sync the active one.
usage: python work/scripts/use_style.py <style>            a style in styles/ (e.g. podcast, talking-head, my-style)
       python work/scripts/use_style.py <client>/<style>   a client's style in clients/ (e.g. acme-media/talking-head)
       python work/scripts/use_style.py                    re-sync the active style (finalize.sh runs this); if none is set
                                                           and exactly one style exists, select that one
       python work/scripts/use_style.py --list             list every style and whether it is onboarded
Selecting writes work/active_style.json and copies the style's theme.ts to remotion/src/data/style_theme.ts (the engine's
theme.ts re-exports it). Edit the style's own theme.ts, never the copy: the copy is overwritten on every run.
A styles/<name> style keeps STYLE_GUIDE.md and theme.ts at its root (or in style/); a client style keeps them in style/.
styles/clip is not an engine style (the clipper renders it) and styles/_template is the template: neither can be selected.
Prints ONBOARDED, or NEEDS ONBOARDING (STYLE_GUIDE.md or theme.ts missing: see the skill's references/ONBOARDING.md)."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json
from client_style import CLIENTS, STYLES, ACTIVE, PROJ, SHARED_PACK, rel, has_audio, style_file

THEME_COPY = os.path.join(PROJ, 'remotion', 'src', 'data', 'style_theme.ts')
NOT_ENGINE = ('clip',)  # rendered by the clipper, not by this engine


def styles():
    """[(client or None, style, folder)] for every style in styles/ and clients/."""
    out = []
    if os.path.isdir(STYLES):
        for s in sorted(os.listdir(STYLES)):
            sd = os.path.join(STYLES, s)
            if os.path.isdir(sd) and not s.startswith(('_', '.')) and s not in NOT_ENGINE:
                out.append((None, s, sd))
    if os.path.isdir(CLIENTS):
        for c in sorted(os.listdir(CLIENTS)):
            cd = os.path.join(CLIENTS, c)
            if c.startswith(('_', '.')) or not os.path.isdir(cd):
                continue
            for s in sorted(os.listdir(cd)):
                if os.path.isdir(os.path.join(cd, s, 'source')) or os.path.isdir(os.path.join(cd, s, 'style')):
                    out.append((c, s, os.path.join(cd, s)))
    return out


def name(c, s):
    return f'{c}/{s}' if c else s


def onboarded(sd):
    return all(os.path.exists(style_file(sd, f)) for f in ('STYLE_GUIDE.md', 'theme.ts'))


def resolve(arg):
    """'podcast' -> styles/podcast; 'client/style' -> clients/client/style."""
    a = arg.replace('\\', '/').strip('/')
    if a.startswith('styles/'):
        a = a[len('styles/'):]
    if a.startswith('clients/'):
        a = a[len('clients/'):]
    c, _, s = a.partition('/')
    if s:
        return c, s, os.path.join(CLIENTS, c, s)
    if a in NOT_ENGINE:
        sys.exit(f'styles/{a} is rendered by the clipper, not by this engine (see styles/{a}/README.md)')
    return None, a, os.path.join(STYLES, a)


if '--list' in sys.argv:
    for c, s, sd in styles():
        print(f'{name(c, s)}: ' + ('ONBOARDED' if onboarded(sd) else 'NEEDS ONBOARDING') + f'   ({rel(sd)})')
    sys.exit(0)

args = [a for a in sys.argv[1:] if not a.startswith('--')]
quiet = False
if args:
    c, s, sd = resolve(args[0])
elif os.path.exists(ACTIVE):
    a = json.load(open(ACTIVE))
    c, s = a.get('client'), a['style']
    sd = os.path.join(PROJ, a['path']) if a.get('path') else os.path.join(CLIENTS, c, s)
    quiet = True
else:
    found = styles()
    if len(found) != 1:
        sys.exit('no active style. Run: python work/scripts/use_style.py <style>\navailable: '
                 + (', '.join(name(a, b) for a, b, _ in found) or 'none - add one to styles/ (see styles/_template/README.md)'))
    c, s, sd = found[0]

if not os.path.isdir(sd):
    sys.exit(f'{rel(sd)} does not exist. available: ' + (', '.join(name(a, b) for a, b, _ in styles()) or 'none'))
json.dump({'client': c, 'style': s, 'path': rel(sd)}, open(ACTIVE, 'w'), indent=1)

theme = style_file(sd, 'theme.ts')
if os.path.exists(theme):
    new = open(theme, encoding='utf-8').read()
    old = open(THEME_COPY, encoding='utf-8').read() if os.path.exists(THEME_COPY) else None
    if new != old:
        with open(THEME_COPY, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(new)
        if quiet:
            print('use_style: theme re-synced from ' + rel(theme))

if quiet:
    sys.exit(0)
own = os.path.join(sd, 'sound-pack')
if has_audio(own):
    pack = own
else:
    pack = os.path.join(CLIENTS, c, 'sound-pack') if c else SHARED_PACK
print(f'active style: {name(c, s)}  ->  ' + ('ONBOARDED' if onboarded(sd) else 'NEEDS ONBOARDING (see references/ONBOARDING.md)'))
print('  folder:      ' + rel(sd))
print('  style guide: ' + rel(style_file(sd, 'STYLE_GUIDE.md')))
print('  source:      ' + (rel(os.path.join(sd, 'source')) if os.path.isdir(os.path.join(sd, 'source')) else '(none)'))
print('  examples:    ' + (rel(os.path.join(sd, 'examples')) if os.path.isdir(os.path.join(sd, 'examples')) else '(none)'))
print('  sound pack:  ' + rel(pack) + ('' if has_audio(pack) else '  (EMPTY - no .mp3/.wav)'))
kit = os.path.join(sd, 'style.json')
if os.path.exists(kit):
    print('  reel kit:    ' + rel(kit) + '  (this style is built with the reel kit: SKILL section 4)')
