"""Delete Remotion's leftover temp copies (every render/still bundle copies the project's public/ folder to the OS temp dir;
left alone they fill the disk - ~85 GB on the first project). Only touches folders Remotion itself names
remotion-v*-assets* and remotion-webpack-bundle-*.  usage: python work/scripts/clean_temp.py"""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, glob, shutil, tempfile

tmp = tempfile.gettempdir()
gone = 0
for p in glob.glob(os.path.join(tmp, 'remotion-v*-assets*')) + glob.glob(os.path.join(tmp, 'remotion-webpack-bundle-*')):
    shutil.rmtree(p, ignore_errors=True)
    gone += not os.path.exists(p)
print(f'removed {gone} Remotion temp folders from {tmp}')
