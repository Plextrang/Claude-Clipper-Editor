"""Where the ACTIVE style lives. Every script that needs the style or the sound pack imports this.
The active style is set with `python work/scripts/use_style.py <name>` and stored in work/active_style.json.

Two layouts are supported:
  styles/<name>/                          a ready-made or your own style (one level), e.g. styles/podcast
    STYLE_GUIDE.md, theme.ts              the look (or inside style/, like the client layout)
    source/  examples/  sound-pack/       optional: creative direction, approved past edits, the style's own SFX
    (no sound-pack audio -> the shared pack in assets/sfx/pack/)
  clients/<client>/<style>/               one client's style (agencies; everything in clients/ is git-ignored)
    source/, style/STYLE_GUIDE.md, style/theme.ts, style/board/, examples/, optional sound-pack/
  clients/<client>/sound-pack/            the client's SFX (shared by all of the client's styles)
  <sound pack>/_catalogue/                sfx_analysis.json, sfx_events.json, sfx_audition.json (built by sfx_catalog.py)"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # work/
PROJ = os.path.dirname(ROOT)
CLIENTS = os.path.join(PROJ, 'clients')
STYLES = os.path.join(PROJ, 'styles')
SHARED_PACK = os.path.join(PROJ, 'assets', 'sfx', 'pack')
ACTIVE = os.path.join(ROOT, 'active_style.json')
AUDIO = ('.mp3', '.wav')


def _load():
    if not os.path.exists(ACTIVE):
        sys.exit('no active style - run: python work/scripts/use_style.py <style>   (e.g. podcast, or <client>/<style>)')
    return json.load(open(ACTIVE))


def active():
    """(client, style) of the active style; client is None for a styles/<name> style."""
    a = _load()
    return a.get('client'), a['style']


def style_dir():
    a = _load()
    if a.get('path'):
        return os.path.join(PROJ, a['path'])
    return os.path.join(CLIENTS, a['client'], a['style'])


def client_dir():
    """The client folder (clients/<client>), or the style folder itself for a styles/<name> style."""
    c, _ = active()
    return os.path.join(CLIENTS, c) if c else style_dir()


def style_file(sd, name):
    """<style>/<name> if it exists (flat styles/ layout), else <style>/style/<name> (client layout)."""
    flat = os.path.join(sd, name)
    return flat if os.path.exists(flat) else os.path.join(sd, 'style', name)


def has_audio(d):
    for dp, dn, fn in os.walk(d):
        if '_catalogue' in dp:
            continue
        if any(f.lower().endswith(AUDIO) for f in fn):
            return True
    return False


def sound_lib():
    """The style's own sound-pack/ if it has audio; else the client's sound-pack/ (client styles) or the shared pack
    in assets/sfx/pack/ (styles/ styles)."""
    own = os.path.join(style_dir(), 'sound-pack')
    if has_audio(own):
        return own
    c, _ = active()
    return os.path.join(CLIENTS, c, 'sound-pack') if c else SHARED_PACK


def catalogue(name):
    """Path of a catalogue file (sfx_analysis.json / sfx_events.json / sfx_audition.json) for the active sound pack."""
    d = os.path.join(sound_lib(), '_catalogue')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def rel(p):
    return os.path.relpath(p, PROJ).replace(os.sep, '/')
