"""Frame strips around every transition of a rendered video, for glitch review.
usage: python strips.py <video.mp4> <outdir> [step] [--points=a,b,c]   (default points = every seam from video.json)"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json, subprocess
from PIL import Image, ImageDraw

_args = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(_args) < 2:
    sys.exit(__doc__)
video, outdir = _args[0], _args[1]
step = int(_args[2]) if len(_args) > 2 else 1
os.makedirs(outdir, exist_ok=True)
# every scene boundary / jump cut / camera cut in the edit (work/plan/video.json, written by integrate.py)
_V = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plan', 'video.json')))
POINTS, TOTAL = _V['points'], _V['total']
_pa = [a for a in sys.argv if a.startswith('--points=')]
if _pa:
    POINTS = [int(x) for x in _pa[0].split('=', 1)[1].split(',') if x]
W, H = 216, 384


need = sorted({n for pt in POINTS for n in range(pt - 5, pt + 6, step) if 0 <= n < TOTAL})
if not os.path.exists(os.path.join(outdir, f'_a{TOTAL - 1:04d}.jpg')):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vf', f'scale={W}:{H}', '-q:v', '3', '-start_number', '0',
                    os.path.join(outdir, '_a%04d.jpg')], check=True)


def frame(n):
    return Image.open(os.path.join(outdir, f'_a{n:04d}.jpg'))


for pt in POINTS:
    fr = [n for n in range(pt - 5, pt + 6, step) if 0 <= n < TOTAL]
    sheet = Image.new('RGB', (W * len(fr), H + 20), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(fr):
        sheet.paste(frame(n), (i * W, 20))
        d.text((i * W + 4, 4), str(n), fill=(255, 220, 0) if n != pt else (255, 80, 80))
    sheet.save(os.path.join(outdir, f'strip_{pt:04d}.png'))
print('done', len(POINTS))
