"""Debug helper: transcribe one source range with Whisper small.en.
usage: python work/scripts/range_tx.py <start>:<end> [<start>:<end> ...]   (source seconds)"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pylibs'))
os.environ['HF_HOME'] = os.path.join(ROOT, 'hf_cache'); os.environ['HF_HUB_DISABLE_XET']='1'
from faster_whisper import WhisperModel
import soundfile as sf, numpy as np
x, sr = sf.read(os.path.join(ROOT,'audio','voice16k.wav'), dtype='float32')
m = WhisperModel('small.en', device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 4, download_root=os.path.join(ROOT,'hf_cache','models'))
for rng in sys.argv[1:]:
    a,b = map(float, rng.split(':'))
    seg = x[int(a*sr):int(b*sr)]
    segs,_ = m.transcribe(seg, language='en', beam_size=5, word_timestamps=True, vad_filter=False, condition_on_previous_text=False,
                          initial_prompt="Umm, uh, so, like, you know, I mean.")
    ws = [(w.word.strip(), round(a+w.start,2), round(a+w.end,2), round(w.probability,2)) for s in segs for w in s.words]
    print(f'[{a}-{b}]', ws)
