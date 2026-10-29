"""Contact sheet of a folder of stills.
usage: python work/scripts/sheet.py <folder of .png> <out.png> [columns=6]"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import sys, glob, os
from PIL import Image, ImageDraw
d = sys.argv[1]; out = sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
fs = sorted(glob.glob(os.path.join(d, '*.png')))
if not fs:
    sys.exit(f'no .png stills in {d}')
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
ims = [Image.open(f) for f in fs]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * (h + 22)), (20, 20, 20))
dr = ImageDraw.Draw(sheet)
for k, (f, im) in enumerate(zip(fs, ims)):
    x, y = (k % cols) * w, (k // cols) * (h + 22)
    sheet.paste(im, (x, y + 22)); dr.text((x + 6, y + 4), os.path.basename(f).split('_')[-1].replace('.png', ''), fill=(255, 220, 0))
sheet.save(out); print(sheet.size)
