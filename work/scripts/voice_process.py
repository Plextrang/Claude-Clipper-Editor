"""Voice polish after render_cut.py: clean-up chain, then gain to land the voice at -16 LUFS (true peak <= -1.5).
usage: python work/scripts/voice_process.py
reads work/audio/voice_cut_raw.wav -> writes remotion/public/voice.wav (+ work/audio/voice_cut16k.wav for Whisper)
The final master gain in mix.py is computed from this voice-led balance, so the voice is the anchor of the mix."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
A = os.path.join(ROOT, 'audio')
RAW, PRE = os.path.join(A, 'voice_cut_raw.wav'), os.path.join(A, 'voice_proc_pre.wav')
OUT = os.path.join(PROJ, 'remotion', 'public', 'voice.wav')
TARGET = -16.0

CHAIN = ('highpass=f=75:poles=2,equalizer=f=230:t=q:w=1.2:g=-1.5,equalizer=f=3200:t=q:w=1.0:g=1.5,'
         'equalizer=f=11000:t=h:w=0.7:g=1.0,acompressor=threshold=-21dB:ratio=2.6:attack=8:release=140:makeup=2dB:knee=4,'
         'alimiter=limit=-2dB:attack=3:release=50:level=false')


def integrated(path):
    r = subprocess.run(['ffmpeg', '-v', 'info', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
    I = tp = None
    for line in r.stderr.splitlines():
        line = line.strip()
        if line.startswith('I:'): I = float(line.split()[1])
        if line.startswith('Peak:'): tp = float(line.split()[1])
    return I, tp


subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', RAW, '-af', CHAIN, '-ar', '48000', '-c:a', 'pcm_s24le', PRE], check=True)
I, _ = integrated(PRE)
gain = round(TARGET - I, 2)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', PRE, '-af', f'volume={gain}dB,alimiter=limit=-1.5dB:attack=2:release=40:level=false',
                '-ar', '48000', '-c:a', 'pcm_s16le', OUT], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', OUT, '-ac', '1', '-ar', '16000', os.path.join(A, 'voice_cut16k.wav')], check=True)
print('pre', I, 'LUFS; gain', gain, 'dB ->', integrated(OUT))
