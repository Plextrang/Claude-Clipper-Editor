"""Platform subtitles from the word timings.
usage: python work/scripts/make_srt.py   (reads remotion/src/data/words.json -> deliverables/captions.srt)
Lines break on . ? , (once >= 3 words) or every 6 words; each line lasts until the next one starts."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
W = json.load(open(os.path.join(PROJ, 'remotion', 'src', 'data', 'words.json'), encoding='utf-8'))
END = json.load(open(os.path.join(ROOT, 'transcript', 'edl.json')))['total_frames'] / 30
groups, cur = [], []
for w in W:
    cur.append(w)
    if (w['w'].endswith(('.', '?', ',')) and len(cur) >= 3) or len(cur) >= 6:
        groups.append(cur); cur = []
if cur:
    groups.append(cur)


def ts(t):
    ms = int(round(t * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


out = []
for i, g in enumerate(groups):
    a = g[0]['s']
    b = groups[i + 1][0]['s'] if i + 1 < len(groups) else min(END, g[-1]['e'] + 0.4)
    out.append(f"{i + 1}\n{ts(a)} --> {ts(b - 0.02)}\n{' '.join(x['w'] for x in g)}\n")
os.makedirs(os.path.join(PROJ, 'deliverables'), exist_ok=True)
open(os.path.join(PROJ, 'deliverables', 'captions.srt'), 'w', encoding='utf-8').write('\n'.join(out))
print(len(groups), 'subtitle lines')
