"""Build work/plan/sound_cues.json (the mixer's input) from the per-video cue sheet + automatic music automation.

Inputs
- work/plan/cue_sheet.json  (PER VIDEO, authored by the sound-design step):
    {"musicNoDip": [scene ids (on-screen or full-screen) that should NOT dip or silence the music],
     "cues": [{"frame", "family", "file", "peak", "gainDb", "note", optional "start", "end", "fadeIn", "fadeOut"}]}
    frame  = output frame where the cue's PEAK lands (fastest frame of a move / the event frame / the cut a riser ends on)
    family = whoosh | texture | riser | hit   (stem routing)
    file   = path inside the active sound pack (clients/<client>/sound-pack/, see client_style.py)
    peak   = seconds inside the file of the chosen variation's peak (pick from <sound pack>/_catalogue/sfx_events.json)
    start/end default to that variation's bounds (+50 ms tail); fadeOut defaults to 40 ms.
- work/plan/video.json  (written by integrate.py): total frames + full-screen / on-screen scene ranges.

Music automation (dB relative to the base -19; mix.py adds the mobile boost on top):
talking head 0 dB | on-screen cards -2.5 dB | full-screen scenes silent | talking-head islands < 40 frames silent |
-5 dB dip under every riser build | 6-frame fade-in at the start, 16-frame tail at the end |
4-frame pre-ramp into a silence (lands on the cut), 6-frame recovery after it."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from client_style import catalogue
_EV = catalogue('sfx_events.json')
EV = json.load(open(_EV)) if os.path.exists(_EV) else {}  # empty sound pack: no catalogue, the cue sheet has no cues
VID = json.load(open(os.path.join(ROOT, 'plan', 'video.json')))
SHEET = json.load(open(os.path.join(ROOT, 'plan', 'cue_sheet.json'), encoding='utf-8'))
TOTAL = VID['total']
FS = [(x['from'], x['to']) for x in VID['fullscreen'] if x['id'] not in set(SHEET.get('musicNoDip', []))]  # musicNoDip: the music keeps playing
OS = [(x['from'], x['to']) for x in VID['onscreen'] if x['id'] not in set(SHEET.get('musicNoDip', []))]


def variation(file, peak):
    return min(EV[file], key=lambda e: abs(e['pk'] - peak))


def music_automation(cues):
    tgt = np.zeros(TOTAL + 1)
    for a, b in FS:
        tgt[a:b] = -70
    islands, t = [], 0  # talking-head stretches = gaps between full-screen scenes
    for a, b in sorted(FS):
        if a > t: islands.append((t, a))
        t = max(t, b)
    if t < TOTAL: islands.append((t, TOTAL))
    for a, b in islands:
        if b - a < 40:
            tgt[a:b] = -70
    for a, b in OS:
        for k in range(a, b):
            if tgt[k] > -60: tgt[k] = -2.5
    tgt[0] = -30
    lin = 10 ** (tgt / 20)
    out = lin.copy()
    for k in range(1, TOTAL + 1):
        if lin[k] < lin[k - 1] - 1e-6:  # going down at k: pre-ramp over the 4 frames before
            for j in range(max(0, k - 4), k):
                out[j] = min(out[j], lin[k - 1] + (lin[k] - lin[k - 1]) * ((j - (k - 4)) / 4))
    for k in range(1, TOTAL + 1):
        if lin[k] > lin[k - 1] + 1e-6:  # going up at k: post-ramp over 6 frames
            for j in range(k, min(TOTAL + 1, k + 6)):
                out[j] = min(out[j], lin[k - 1] + (lin[k] - lin[k - 1]) * ((j - k + 1) / 6))
    out[0:6] = np.linspace(10 ** (-30 / 20), out[6], 6)
    for c in cues:  # duck under riser builds
        if c['family'] != 'riser':
            continue
        lead = int(round((c['peak'] - c['start']) * 30))
        a, b = max(0, c['frame'] - lead), c['frame']
        for j in range(a, min(TOTAL + 1, b + 1)):
            out[j] *= 10 ** ((-5 * min(1, ((j - a) / max(1, b - a)) * 2)) / 20)
    for k in range(TOTAL - 16, TOTAL + 1):  # gentle tail into the track's own ending
        out[k] *= 10 ** ((-6 * (k - (TOTAL - 16)) / 16) / 20)
    return [[k, round(float(20 * np.log10(max(out[k], 1e-4))), 2)] for k in range(TOTAL + 1)]


def main():
    cues = []
    for i, c in enumerate(sorted(SHEET['cues'], key=lambda c: c['frame']), 1):
        assert c['family'] in ('whoosh', 'texture', 'riser', 'hit'), c
        v = variation(c['file'], c['peak'])
        cues.append({'id': f"{c['family'][:3]}{i:03d}", 'family': c['family'], 'file': c['file'], 'start': c.get('start', v['s']),
                     'peak': c['peak'], 'end': c.get('end', v['e'] + 0.05), 'frame': c['frame'], 'gainDb': c['gainDb'],
                     'fadeIn': c.get('fadeIn', 0.0), 'fadeOut': c.get('fadeOut', 0.04), 'note': c.get('note', '')})
    automation = music_automation(cues)
    out = {'cues': cues, 'music': {'file': 'remotion/public/music.wav', 'baseDb': -19, 'automation': automation}, 'targetLUFS': -14.0}
    json.dump(out, open(os.path.join(ROOT, 'plan', 'sound_cues.json'), 'w'), indent=1)
    print('cues', len(cues))
    print('music automation points', len(automation))


if __name__ == '__main__':
    main()
