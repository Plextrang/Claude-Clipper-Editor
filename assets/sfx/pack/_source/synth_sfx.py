"""Synthesise original SFX (risers, whooshes, sub hits). Output: float WAVs, 48 kHz.
Original works made for this repo, dedicated CC0 1.0. Usage: python synth_sfx.py <outdir>"""
import sys, os, wave, numpy as np
SR = 48000
rng = np.random.default_rng(20261028)

def stft_band(noise, fc_curve, q=1.2, n=2048, hop=512):
    """Time-varying band-pass via STFT: gaussian band (in log-frequency) centred at fc_curve(t)."""
    win = np.hanning(n)
    pad = np.concatenate([np.zeros(n), noise, np.zeros(n)])
    out = np.zeros(len(pad)); norm = np.zeros(len(pad))
    f = np.fft.rfftfreq(n, 1 / SR); lf = np.log2(np.maximum(f, 1))
    for s in range(0, len(pad) - n, hop):
        t = max(0, min(len(noise) - 1, s + n // 2 - n)) / SR
        fc = fc_curve(t)
        g = np.exp(-0.5 * ((lf - np.log2(fc)) / q) ** 2)
        X = np.fft.rfft(pad[s:s + n] * win) * g
        out[s:s + n] += np.fft.irfft(X) * win; norm[s:s + n] += win ** 2
    out = out / np.maximum(norm, 1e-6)
    return out[n:n + len(noise)]

def riser(D, f0, f1, tone_f0, tone_f1):
    N = int(D * SR); t = np.arange(N) / SR; u = t / D
    noise = rng.standard_normal(N)
    fc = lambda tt: f0 * (f1 / f0) ** (min(tt, D) / D)
    band = stft_band(noise, fc, q=0.9)
    band /= np.abs(band).max() + 1e-9
    # rising tone pair (slightly detuned) for pitch movement
    fr = tone_f0 * (tone_f1 / tone_f0) ** (u ** 1.3)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    tone = 0.5 * np.sin(ph) + 0.35 * np.sin(ph * 1.007) + 0.15 * np.sin(2 * ph)
    env = u ** 2.2                      # fade-in, ends on its peak
    y = (0.75 * band + 0.35 * tone) * env
    y[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))  # 4 ms de-click only
    return y

def pink(N):
    X = np.fft.rfft(rng.standard_normal(N)); f = np.fft.rfftfreq(N, 1 / SR)
    return np.fft.irfft(X / np.sqrt(np.maximum(f, 20)), N)

def whoosh(D, f_lo, f_hi, peak_pos=0.45, stereo_pan=False):
    N = int(D * SR); t = np.arange(N) / SR; u = t / D
    noise = pink(N)                     # pink noise: softer, airier than white
    def fc(tt):
        x = min(tt, D) / D
        ramp = x / peak_pos if x < peak_pos else max(0.0, 1 - (x - peak_pos) / (1 - peak_pos))
        return f_lo * (f_hi / f_lo) ** ramp   # band sweeps up to the peak, then back down
    y = stft_band(noise, fc, q=0.7)
    env = np.where(u < peak_pos, (u / peak_pos) ** 2, ((1 - u) / (1 - peak_pos)) ** 1.6)
    y = y * env; y /= np.abs(y).max() + 1e-9
    if stereo_pan:
        p = u  # pan left -> right
        return np.stack([y * np.cos(p * np.pi / 2), y * np.sin(p * np.pi / 2)], 1)
    return y

def sub_hit(D, f_start, f_end, decay):
    N = int(D * SR); t = np.arange(N) / SR
    fr = f_end + (f_start - f_end) * np.exp(-t / 0.05)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    body = np.sin(ph) * np.exp(-t / decay)
    harm = 0.35 * np.sin(2 * ph) * np.exp(-t / (decay * 0.5))     # 2nd harmonic: audible on phones
    click = rng.standard_normal(N) * np.exp(-t / 0.006)
    click = np.convolve(click, [1, -0.95], 'same') * 0.25          # bright transient
    y = body + harm + click
    a = int(0.002 * SR); y[:a] *= np.linspace(0, 1, a)
    y[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    return y

def write(path, y):
    y = np.asarray(y, dtype=np.float64)
    y = y / (np.abs(y).max() + 1e-9) * 0.7
    ch = 1 if y.ndim == 1 else y.shape[1]
    pcm = (np.clip(y, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == '__main__':
    o = sys.argv[1]; os.makedirs(o, exist_ok=True)
    write(os.path.join(o, 'riser_short.wav'), riser(1.2, 300, 5000, 220, 880))
    write(os.path.join(o, 'riser_medium.wav'), riser(1.8, 250, 6000, 180, 1100))
    write(os.path.join(o, 'riser_long.wav'), riser(2.4, 200, 7000, 150, 1200))
    write(os.path.join(o, 'whoosh_soft.wav'), whoosh(0.7, 350, 2200, 0.45))
    write(os.path.join(o, 'whoosh_pan.wav'), whoosh(0.9, 300, 3000, 0.5, stereo_pan=True))
    write(os.path.join(o, 'hit_sub_low.wav'), sub_hit(0.9, 95, 55, 0.22))
    write(os.path.join(o, 'hit_sub_tight.wav'), sub_hit(0.6, 120, 72, 0.12))
    print('done')
