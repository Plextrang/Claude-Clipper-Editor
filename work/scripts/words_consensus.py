"""Word timings on the CUT timeline = consensus of two Whisper models (run transcribe_cut.py small.en and medium.en first).
usage: python work/scripts/words_consensus.py
reads work/transcript/cut_words_small.en.json + cut_words_medium.en.json -> writes remotion/src/data/words.json
fields: w (text), s/e (seconds), p (prob), i (index), f (frame of word start @30fps). Spelling fixes (a name both models
miss, a lost capital): work/plan/text_fixes.json = {"<word index>": "Text"}, applied last; re-run this script after editing it. Text comes from small.en; where both
models agree on a word its start/end are averaged. Split tokens are merged ("50"+"%", "high"+"-quality", "2"+".0")."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json, difflib, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
T = os.path.join(ROOT, 'transcript')
a = json.load(open(os.path.join(T, 'cut_words_small.en.json')))
b = json.load(open(os.path.join(T, 'cut_words_medium.en.json')))
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
sm = difflib.SequenceMatcher(a=[norm(x['w']) for x in a], b=[norm(x['w']) for x in b], autojunk=False)
out = [dict(x) for x in a]
agree, dev = 0, []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        for k in range(i2 - i1):
            dev.append(abs(a[i1 + k]['s'] - b[j1 + k]['s']))
            out[i1 + k]['s'] = round((a[i1 + k]['s'] + b[j1 + k]['s']) / 2, 3)
            out[i1 + k]['e'] = round((a[i1 + k]['e'] + b[j1 + k]['e']) / 2, 3)
            agree += 1
    else:
        print('DISAGREE', tag, [x['w'] for x in a[i1:i2]], '<->', [x['w'] for x in b[j1:j2]])
merged = []
for w in out:
    if merged and (w['w'] in ('%', '.0') or w['w'].startswith('-')):
        merged[-1]['w'] += w['w']; merged[-1]['e'] = w['e']; continue
    merged.append(w)
for i, w in enumerate(merged):
    w['i'] = i; w['f'] = round(w['s'] * 30)
# optional spelling fixes the transcript can't get right: work/plan/text_fixes.json = {"<word index>": "Text", ...}
_fx = os.path.join(ROOT, 'plan', 'text_fixes.json')
if os.path.exists(_fx):
    for k, v in json.load(open(_fx, encoding='utf-8')).items():
        if 0 <= int(k) < len(merged):
            print(f'text fix {k}: {merged[int(k)]["w"]!r} -> {v!r}')
            merged[int(k)]['w'] = v
json.dump(merged, open(os.path.join(PROJ, 'remotion', 'src', 'data', 'words.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(merged), 'words;', agree, 'agreed; mean start deviation', round(1000 * sum(dev) / max(1, len(dev))), 'ms')
