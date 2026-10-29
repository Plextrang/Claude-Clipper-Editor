"""Word-level Whisper transcript of the raw recording (work/audio/voice16k.wav, from prep_audio.py).
usage: python work/scripts/transcribe.py [model]   (default small.en) -> work/transcript/whisper_<model>.json"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pylibs'))
os.environ['HF_HOME'] = os.path.join(ROOT, 'hf_cache')
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_XET'] = '1'
from faster_whisper import WhisperModel
import soundfile as sf, numpy as np

model_name = sys.argv[1] if len(sys.argv) > 1 else 'small.en'
os.makedirs(os.path.join(ROOT, 'transcript'), exist_ok=True)
t0 = time.time()
model = WhisperModel(model_name, device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 4,
                     download_root=os.path.join(ROOT, 'hf_cache', 'models'))
print('loaded', time.time()-t0, flush=True)
segments, info = model.transcribe(
    sf.read(os.path.join(ROOT, 'audio', 'voice16k.wav'), dtype='float32')[0],
    language='en', beam_size=5, word_timestamps=True, vad_filter=False,
    condition_on_previous_text=False,
    initial_prompt="Umm, so, uh, I was like, you know... I mean, okay. Let me, let me start again.",
)
out = []
for s in segments:
    seg = {'start': s.start, 'end': s.end, 'text': s.text, 'avg_logprob': s.avg_logprob,
           'no_speech_prob': s.no_speech_prob,
           'words': [{'w': w.word, 's': round(w.start, 3), 'e': round(w.end, 3), 'p': round(w.probability, 3)} for w in s.words]}
    out.append(seg)
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
json.dump(out, open(os.path.join(ROOT, 'transcript', f'whisper_{model_name}.json'), 'w'), indent=1)
print('done', time.time()-t0)
