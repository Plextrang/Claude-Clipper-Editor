"""Per-section QA contact sheets (every Nth frame) from a rendered video.
usage: python qa_sheets.py <video.mp4> <outdir> [every=3]"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json, subprocess
from PIL import Image, ImageDraw

_V = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plan', 'video.json')))
TOTAL = _V['total']

video, outdir = sys.argv[1], sys.argv[2]
every = int(sys.argv[3]) if len(sys.argv) > 3 else 3
W, H = 216, 384
frames_dir = os.path.join(outdir, 'frames')
os.makedirs(frames_dir, exist_ok=True)
if not os.path.exists(os.path.join(frames_dir, f'f{TOTAL - 1:04d}.jpg')):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vf', f'scale={W}:{H}', '-q:v', '3', '-start_number', '0',
                    os.path.join(frames_dir, 'f%04d.jpg')], check=True)

SECTIONS = {f'S{i + 1}': (max(0, i * TOTAL // 6 - 10), min(TOTAL, (i + 1) * TOTAL // 6 + 10)) for i in range(6)}
COLS, ROWS = 10, 4
for name, (a, b) in SECTIONS.items():
    fr = list(range(a, b, every))
    for p in range(0, len(fr), COLS * ROWS):
        chunk = fr[p:p + COLS * ROWS]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new('RGB', (COLS * W, rows * (H + 18)), (14, 14, 14))
        d = ImageDraw.Draw(sheet)
        for i, n in enumerate(chunk):
            x, y = (i % COLS) * W, (i // COLS) * (H + 18)
            sheet.paste(Image.open(os.path.join(frames_dir, f'f{n:04d}.jpg')), (x, y + 18))
            d.text((x + 4, y + 3), str(n), fill=(255, 220, 0))
        sheet.save(os.path.join(outdir, f'{name}_p{p // (COLS * ROWS)}.png'))
print('done')
