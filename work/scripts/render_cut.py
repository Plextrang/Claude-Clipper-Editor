"""Render the cut: frame-exact trims of the raw footage per edl.json -> remotion/public/aroll.mp4 (x264 CRF 15, GOP 15, no
B-frames for fast seeking) + work/audio/voice_cut_raw.wav (6/8 ms fades on every piece).
usage: python work/scripts/render_cut.py [path/to/raw.mp4]   (default: the single video in input/)"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, glob, json, subprocess
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

edl = json.load(open(os.path.join(ROOT,'transcript','edl.json')))['edl']
src = raw_footage(sys.argv[1] if len(sys.argv) > 1 else None)
pub = os.path.join(PROJ, 'remotion', 'public')
FPS = 30
# --- video: frame-exact trims, concatenated
vf = []; af = []
for i, c in enumerate(edl):
    a, b = c['src_in_f']/FPS, c['src_out_f']/FPS
    vf.append(f"[0:v]trim=start_frame={c['src_in_f']}:end_frame={c['src_out_f']},setpts=PTS-STARTPTS[v{i}]")
    d = b - a
    af.append(f"[0:a]atrim=start={a:.6f}:end={b:.6f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.006,afade=t=out:st={d-0.008:.6f}:d=0.008[a{i}]")
n = len(edl)
fc = ';'.join(vf + af) + ';' + ''.join(f'[v{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0[vout];' + ''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[aout]'
FILT = os.path.join(ROOT, 'plan', 'cut_filter.txt')  # per-video (git-ignored)
open(FILT,'w').write(fc)
cmd = ['ffmpeg','-y','-v','error','-i',src,'-filter_complex_script',FILT,
       '-map','[vout]','-c:v','libx264','-preset','slow','-crf','15','-pix_fmt','yuv420p','-r','30','-g','15','-bf','0',
       os.path.join(pub,'aroll.mp4'),
       '-map','[aout]','-c:a','pcm_s24le','-ar','48000', os.path.join(ROOT,'audio','voice_cut_raw.wav')]
subprocess.run(cmd, check=True)
# the picture must have exactly the EDL's frame count, or every later cut, caption and camera key is off by a frame
_tot = json.load(open(os.path.join(ROOT, 'transcript', 'edl.json')))['total_frames']
_r = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_packets',
                     '-of', 'csv=p=0', os.path.join(pub, 'aroll.mp4')], capture_output=True, text=True)
_n = int((_r.stdout.strip() or '0').split(',')[0])
if _n != _tot:
    sys.exit(f'CUT FRAME MISMATCH: aroll.mp4 has {_n} frames, edl.json says {_tot}. Check keep.json ranges at the very start/end of the recording, then re-run build_edl.py and render_cut.py.')
print(f'cut rendered ({_n} frames, matches the EDL)')
