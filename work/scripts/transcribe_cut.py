"""Re-transcribe the CUT voice (after render_cut.py), with work/plan/vocabulary.txt as the prompt.
usage: python work/scripts/transcribe_cut.py <model>   (run with small.en and medium.en; words_consensus.py merges them)"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pylibs'))
os.environ['HF_HOME'] = os.path.join(ROOT, 'hf_cache'); os.environ['HF_HUB_DISABLE_XET']='1'
from faster_whisper import WhisperModel
import soundfile as sf
name = sys.argv[1] if len(sys.argv)>1 else 'small.en'
# PER VIDEO: names / brand words / jargon spoken in this video (one line in work/plan/vocabulary.txt) so Whisper spells them right
_vp = os.path.join(ROOT, 'plan', 'vocabulary.txt')
PROMPT = open(_vp, encoding='utf-8').read().strip() if os.path.exists(_vp) else 'Short talking-head video.'
x, sr = sf.read(os.path.join(ROOT,'audio','voice_cut16k.wav'), dtype='float32')
m = WhisperModel(name, device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 4, download_root=os.path.join(ROOT,'hf_cache','models'))
segs,_ = m.transcribe(x, language='en', beam_size=5, word_timestamps=True, vad_filter=False, condition_on_previous_text=True,
     initial_prompt=PROMPT)
out = [{'w': w.word.strip(), 's': round(w.start,3), 'e': round(w.end,3), 'p': round(w.probability,3)} for s in segs for w in s.words]
os.makedirs(os.path.join(ROOT, 'transcript'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT,'transcript',f'cut_words_{name}.json'),'w'), indent=1)
print(len(out)); print(' '.join(f"{w['w']}[{w['s']:.2f}]" for w in out))
