"""Optional: waveform plot of the cut voice (needs matplotlib).
usage: python work/scripts/waveplot.py"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import json, os, sys, numpy as np, soundfile as sf
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
x, sr = sf.read(os.path.join(ROOT,'audio','voice48k.wav')); x = x.mean(axis=1) if x.ndim>1 else x
words = [w for s in json.load(open(os.path.join(ROOT,'transcript','whisper_small.en.json'))) for w in s['words']]
hop = sr//200  # 5ms
db = 20*np.log10(np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)+1e-12) for i in range(len(x)//hop)]))
os.makedirs(os.path.join(ROOT,'frames','wave'), exist_ok=True)
win = 8.0
for k in range(int(np.ceil(92.1/win))):
    a, b = k*win, (k+1)*win
    fig, ax = plt.subplots(figsize=(22,4.2), dpi=80)
    t = np.arange(len(db))*0.005
    m = (t>=a)&(t<b)
    ax.plot(t[m], db[m], lw=0.8, color='#1f77b4'); ax.set_ylim(-75,-5); ax.set_xlim(a,b)
    ax.axhline(-50, color='#ccc', lw=0.6)
    ax.set_xticks(np.arange(a,b+0.001,0.25)); ax.tick_params(axis='x', labelsize=7, rotation=90)
    ax.grid(axis='x', color='#eee')
    for i,w in enumerate(words):
        if w['e']<a or w['s']>b: continue
        ax.axvspan(w['s'], w['e'], ymin=0.0, ymax=0.06, color=('#999' if i%2 else '#555'), alpha=0.8)
        ax.text((w['s']+w['e'])/2, -12 - (i%3)*5, w['w'].strip(), ha='center', fontsize=9)
        ax.axvline(w['s'], color='green', lw=0.4, alpha=0.6)
    plt.tight_layout(); plt.savefig(os.path.join(ROOT,'frames','wave',f'wave_{k:02d}.png')); plt.close()
print('ok')
