"""Sound pack catalogue, step 1: per-file stats (run by sfx_catalog.py).
usage: python work/scripts/sfx_analyze.py"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json, subprocess, numpy as np, io, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from client_style import sound_lib, catalogue
LIB = sound_lib()  # the active client style's sound pack
res = []
for dp, dn, fn in os.walk(LIB):
    for f in sorted(fn):
        if not f.lower().endswith(('.mp3','.wav')): continue
        p = os.path.join(dp, f)
        raw = subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar','48000','-f','wav','-'],capture_output=True).stdout
        x, sr = sf.read(io.BytesIO(raw))
        hop = 480
        n = max(1,len(x)//hop)
        rms = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)+1e-12) for i in range(n)])
        db = 20*np.log10(rms)
        pk = int(np.argmax(db))
        onset = int(np.argmax(db > db.max()-30))
        # tail: last frame above peak-40
        above = np.where(db > db.max()-40)[0]
        tail = int(above[-1]) if len(above) else n
        rel = os.path.relpath(p, LIB).replace(os.sep,'/')
        res.append({'file': rel, 'dur': round(len(x)/sr,3), 'peak_t': round(pk*0.01,3), 'onset_t': round(onset*0.01,3),
                    'tail_t': round(tail*0.01,3), 'peak_db': round(float(db.max()),1), 'mean_db': round(float(np.mean(db[onset:tail+1])),1)})
json.dump(res, open(catalogue('sfx_analysis.json'),'w'), indent=1)
for r in res: print(f"{r['dur']:6.2f}s pk@{r['peak_t']:5.2f} on@{r['onset_t']:5.2f} tail@{r['tail_t']:5.2f} peak{r['peak_db']:6.1f} mean{r['mean_db']:6.1f}  {r['file']}")
