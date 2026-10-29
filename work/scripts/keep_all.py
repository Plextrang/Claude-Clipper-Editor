"""Write work/plan/keep.json with EVERY Whisper segment as a keeper (reel kit: clips that are already one clean moment,
e.g. a podcast clip cut by the router). Then open keep.json and delete only false starts, retakes or a trailing half
sentence before running build_edl.py.
usage: python work/scripts/keep_all.py [--model small.en]"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = sys.argv[sys.argv.index('--model') + 1] if '--model' in sys.argv else 'small.en'
segs = json.load(open(os.path.join(ROOT, 'transcript', f'whisper_{model}.json'), encoding='utf-8'))
keep, n = [], 0
for s in segs:
    ws = s.get('words') or []
    if not ws or s.get('no_speech_prob', 0) > 0.8:
        continue
    a, b = ws[0]['s'], ws[-1]['e']
    if keep and a <= keep[-1][2] + 0.35:  # touching / near segments: merge (build_edl's handles would make them overlap)
        keep[-1][2] = max(keep[-1][2], b)
        keep[-1][3] += ' ' + s['text'].strip()
        continue
    n += 1
    keep.append([f'S{n:02d}', round(a, 2), round(b, 2), s['text'].strip()])
json.dump(keep, open(os.path.join(ROOT, 'plan', 'keep.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for k in keep:
    print(f'{k[0]} [{k[1]:.2f}-{k[2]:.2f}] {k[3]}')
print(f'{len(keep)} keeper ranges -> work/plan/keep.json')
