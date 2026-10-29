"""Step 1 of a new edit: extract the analysis audio and a contact sheet from the raw footage.
usage: python work/scripts/prep_audio.py [path/to/raw.mp4]   (default: the single video in input/)
writes work/audio/voice16k.wav (Whisper), work/audio/voice48k.wav (cut refinement), work/frames/contact.png"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, glob, subprocess, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)

def raw_footage(arg=None):
    """The raw recording: an explicit path (relative to the project root), else the single video file in input/."""
    if arg:
        return os.path.join(PROJ, arg)
    vids = [p for p in glob.glob(os.path.join(PROJ, 'input', '*')) if p.lower().endswith(('.mp4', '.mov', '.mkv', '.m4v'))]
    if len(vids) != 1:
        sys.exit(f'put exactly ONE raw video in input/ (found {len(vids)}: {vids}) or pass its path')
    return vids[0]

src = raw_footage(sys.argv[1] if len(sys.argv) > 1 else None)
print('raw footage:', src)
os.makedirs(os.path.join(ROOT, 'audio'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'frames'), exist_ok=True)
run = lambda *a: subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, *a], check=True)
run('-vn', '-ac', '1', '-ar', '16000', os.path.join(ROOT, 'audio', 'voice16k.wav'))
run('-vn', '-c:a', 'pcm_s16le', '-ar', '48000', os.path.join(ROOT, 'audio', 'voice48k.wav'))
run('-vf', 'fps=1/4,scale=270:480,tile=12x2', '-frames:v', '1', os.path.join(ROOT, 'frames', 'contact.png'))
p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,duration', '-of', 'json', src],
                   capture_output=True, text=True, check=True)
for s in json.loads(p.stdout)['streams']:
    print(s)
print('ok -> work/audio/voice16k.wav, voice48k.wav, work/frames/contact.png')
