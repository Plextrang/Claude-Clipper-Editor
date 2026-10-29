import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
# Split multi-variation SFX files into individual events (start, peak, end) for precise selection
import os, json, subprocess, numpy as np, io, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from client_style import sound_lib, catalogue
LIB = sound_lib()  # the active client style's sound pack
info = json.load(open(catalogue('sfx_analysis.json')))
out = {}
for r in info:
    p = os.path.join(LIB, r['file'])
    raw = subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar','48000','-f','wav','-'],capture_output=True).stdout
    x, sr = sf.read(io.BytesIO(raw))
    hop=480; n=max(1,len(x)//hop)
    db = 20*np.log10(np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)+1e-12) for i in range(n)]))
    thr = db.max()-45
    act = db > thr
    evs=[]; i=0
    while i<n:
        if act[i]:
            j=i; gap=0
            while j<n and gap<25:  # allow 250ms internal gaps
                gap = 0 if act[j] else gap+1
                j+=1
            end = j-gap
            if end-i >= 3:
                seg = db[i:end]; pk = i+int(np.argmax(seg))
                evs.append({'s':round(i*0.01,2),'pk':round(pk*0.01,2),'e':round(end*0.01,2),'pkdb':round(float(db[pk]),1)})
            i=j
        else: i+=1
    out[r['file']] = evs
    if len(evs)>1:
        print(f"{len(evs):2d} events  {r['file']}")
        print('     ', ' | '.join(f"{e['s']}-{e['e']}(pk{e['pk']},{e['pkdb']})" for e in evs[:14]))
json.dump(out, open(catalogue('sfx_events.json'),'w'), indent=1)
