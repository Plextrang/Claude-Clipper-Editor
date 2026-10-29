"""Score music candidates for phones (intro energy, voice band, air, low end). Run inside work/music_audition/.
usage: cd work/music_audition && python ../scripts/music_audition.py"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, glob, io, subprocess, numpy as np, soundfile as sf, librosa, json
res = {}
for p in sorted(glob.glob('*.mp3')):
    raw = subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar','22050','-f','wav','-'],capture_output=True).stdout
    y, sr = sf.read(io.BytesIO(raw)); y = y.astype(np.float32)
    dur = len(y)/sr
    hop = 2205  # 100ms
    rms = librosa.feature.rms(y=y, frame_length=4410, hop_length=hop)[0]; db = 20*np.log10(rms+1e-9)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    band = lambda a,b: float(np.mean(S[(f>=a)&(f<b)]))
    tot = band(20,11000)
    voice_band = band(300,3500)/tot; low = band(20,150)/tot; air = band(6000,11000)/tot
    # energy curve in 10s windows
    win = [round(float(np.mean(db[i:i+100])),1) for i in range(0, len(db), 100)]
    # time to reach 80% of median loudness
    med = np.median(db); intro = next((i*0.1 for i,v in enumerate(db) if v > med-3), 0)
    res[p] = dict(dur=round(dur,1), tempo=round(float(np.atleast_1d(tempo)[0]),1), centroid=int(np.median(cent)),
                  dyn_std=round(float(np.std(db[db>med-20])),2), intro_s=round(intro,1), voiceband=round(voice_band,3),
                  low=round(low,3), air=round(air,3), beat_strength=round(float(np.mean(onset)),2), energy_10s=win)
    print(p, res[p])
json.dump(res, open('audition.json','w'), indent=1)
