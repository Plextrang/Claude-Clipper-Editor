"""Sound pack catalogue, step 3: audition summary per file (run by sfx_catalog.py).
usage: python work/scripts/sfx_audition.py"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, json, io, subprocess, numpy as np, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from client_style import sound_lib, catalogue
LIB = sound_lib()  # the active client style's sound pack
ev = json.load(open(catalogue('sfx_events.json')))
out = {}
for f, evs in ev.items():
    if f.endswith('Audio Extracted.wav') or f.endswith('_1.wav'): continue
    raw = subprocess.run(['ffmpeg','-v','error','-i',os.path.join(LIB,f),'-ac','1','-ar','48000','-f','wav','-'],capture_output=True).stdout
    x, sr = sf.read(io.BytesIO(raw))
    res = []
    for i,e in enumerate(evs):
        seg = x[int(e['s']*sr):int(e['e']*sr)]
        if len(seg) < 512: continue
        S = np.abs(np.fft.rfft(seg*np.hanning(len(seg))))
        fr = np.fft.rfftfreq(len(seg), 1/sr)
        cen = float(np.sum(fr*S)/np.sum(S))
        low = float(np.sum(S[fr<250])/np.sum(S)); hi = float(np.sum(S[fr>5000])/np.sum(S))
        # attack: time from start to peak; release: peak to end
        res.append({'v':i,'s':e['s'],'pk':e['pk'],'e':e['e'],'len':round(e['e']-e['s'],2),'attack':round(e['pk']-e['s'],2),
                    'centroid':int(cen),'low':round(low,2),'hi':round(hi,2),'pkdb':e['pkdb']})
    out[f] = res
json.dump(out, open(catalogue('sfx_audition.json'),'w'), indent=1)
for f,res in out.items():
    if not any(k in f for k in ['whoosh/','scifi/','risers','Activate','Camera','pops/','UI/','clicks/','gears/','Glitch','Gizmo','Scan','Success','Choir','Select']): continue
    print(f.split('/')[-1][:62])
    for r in res[:8]: print(f"   v{r['v']} {r['s']:6.2f}-{r['e']:6.2f} len {r['len']:5.2f} atk {r['attack']:5.2f} cen {r['centroid']:5d}Hz low {r['low']:.2f} hi {r['hi']:.2f} pk {r['pkdb']}")
