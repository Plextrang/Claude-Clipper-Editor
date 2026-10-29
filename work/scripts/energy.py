"""Debug helper: energy statistics of work/audio/voice48k.wav (peak, median, percentiles of the 10 ms envelope).
usage: python work/scripts/energy.py"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json, numpy as np, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
x, sr = sf.read(os.path.join(ROOT,'audio','voice48k.wav'))
if x.ndim > 1: x = x.mean(axis=1)
hop = sr//100  # 10ms
n = len(x)//hop
rms = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)+1e-12) for i in range(n)])
db = 20*np.log10(rms)
print('frames', n, 'peak dB', db.max().round(1), 'median', np.median(db).round(1), 'p10', np.percentile(db,10).round(1), 'p90', np.percentile(db,90).round(1))
json.dump({'hop_s':0.01,'db':[round(float(v),1) for v in db]}, open(os.path.join(ROOT,'transcript','energy_10ms.json'),'w'))
# silences: below threshold for >= 150ms
thr = np.percentile(db,10) + 8
print('threshold', round(thr,1))
sil = db < thr
runs=[]; i=0
while i<n:
    if sil[i]:
        j=i
        while j<n and sil[j]: j+=1
        if (j-i)>=15: runs.append((i/100,(j)/100))
        i=j
    else: i+=1
for a,b in runs: print(f'silence {a:6.2f} - {b:6.2f}  ({b-a:.2f}s)')
