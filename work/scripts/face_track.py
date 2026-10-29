"""Find the camera shots of the cut and the speaker's face in each one (reel kit, step 2 of the kit path).
usage: python work/scripts/face_track.py          (after render_cut.py + integrate.py: reads remotion/public/aroll.mp4)
writes work/plan/faces.json:
  {"shots": [{"i", "from", "to", "face": {"x", "y", "h"} | null, "look": "A"|"B"|...}], "jumpCuts": [...],
   "people": <how many different people the shots look like>}
  x/y = face centre in output px (1080x1920), h = face height px. `look` groups shots that look alike (same person / same
  camera); it is only a hint: confirm it on the contact sheet.
and work/frames/shots.png: one numbered thumbnail per shot (read it to see who is on camera in each shot).
reel_build.py uses the faces for a speaker-aware camera (zoom origin on the face of whoever is on screen)."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, re, json, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)
AROLL = os.path.join(PROJ, 'remotion', 'public', 'aroll.mp4')
MODEL = os.path.join(PROJ, 'assets', 'models', 'face_detection_yunet_2023mar.onnx')
FPS = 30

import cv2  # noqa: E402

if not os.path.exists(AROLL):
    sys.exit('no remotion/public/aroll.mp4 yet - run render_cut.py first')
cap = cv2.VideoCapture(AROLL)
N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# --- camera shots (scene changes) on the cut. 0.14: podcast angles on the same set differ only a little (0.32 missed them)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', AROLL, '-vf', "scale=270:-2,select='gt(scene,0.14)',showinfo", '-an', '-f', 'null', '-'],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
cuts = sorted({int(round(float(t) * FPS)) for t in re.findall(r'pts_time:([0-9.]+)', r.stderr)})
bounds = [0]
for c in cuts:
    if c - bounds[-1] >= 12 and N - c >= 12:
        bounds.append(c)
bounds.append(N)

vid = os.path.join(ROOT, 'plan', 'video.json')
jumps = json.load(open(vid)).get('jumpCuts', []) if os.path.exists(vid) else []

det = cv2.FaceDetectorYN.create(MODEL, '', (360, 640), 0.6, 0.3, 5000)


def faces_at(f):
    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, img = cap.read()
    if not ok:
        return None, None
    small = cv2.resize(img, (360, 640))
    _, fs = det.detect(small)
    best = None
    if fs is not None and len(fs):
        x, y, w, h = max(fs, key=lambda b: b[2] * b[3])[:4]
        if h >= 14:
            best = ((x + w / 2) * 3, (y + h / 2) * 3, h * 3)
    return best, img


shots, thumbs, sigs = [], [], []
for i, (a, b) in enumerate(zip(bounds[:-1], bounds[1:])):
    pts, mid_img = [], None
    for k in range(5):
        fr = int(a + (b - a) * (k + 0.5) / 5)
        face, img = faces_at(fr)
        if k == 2:
            mid_img = img
        if face:
            pts.append(face)
    face = None
    if len(pts) >= 2:
        m = np.median(np.array(pts), axis=0)
        face = {'x': int(m[0]), 'y': int(m[1]), 'h': int(m[2])}
    # appearance signature: HSV histogram of the face + upper body region
    sig = None
    if mid_img is not None:
        cx, cy, fh = (face['x'], face['y'], face['h']) if face else (540, 760, 300)
        x0, x1 = max(0, cx - fh), min(1080, cx + fh)
        y0, y1 = max(0, cy - fh // 2), min(1920, cy + int(fh * 2.2))
        roi = cv2.cvtColor(mid_img[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
        if roi.size:
            sig = cv2.normalize(cv2.calcHist([roi], [0, 1], None, [18, 8], [0, 180, 0, 256]), None).flatten()
        thumbs.append(cv2.resize(mid_img, (216, 384)))
    else:
        thumbs.append(np.zeros((384, 216, 3), np.uint8))
    sigs.append(sig)
    shots.append({'i': i, 'from': a, 'to': b, 'face': face})

# group shots that look alike (Bhattacharyya distance on the histograms)
groups = []
for i, s in enumerate(sigs):
    lab = None
    for g, rep in enumerate(groups):
        if s is not None and rep is not None and cv2.compareHist(s, rep, cv2.HISTCMP_BHATTACHARYYA) < 0.42:
            lab = g
            break
    if lab is None:
        groups.append(s)
        lab = len(groups) - 1
    shots[i]['look'] = 'ABCDEFGH'[min(lab, 7)]
# a "person" = a look group holding at least ~15% of the screen time (stray b-roll / wide shots do not count)
time_by = {}
for s in shots:
    time_by[s['look']] = time_by.get(s['look'], 0) + (s['to'] - s['from'])
people = sum(1 for v in time_by.values() if v >= 0.15 * N)

json.dump({'frames': N, 'shots': shots, 'jumpCuts': jumps, 'people': people}, open(os.path.join(ROOT, 'plan', 'faces.json'), 'w'), indent=1)

# contact sheet
cols = min(6, max(1, len(thumbs)))
rows = (len(thumbs) + cols - 1) // cols
sheet = np.full((rows * 420, cols * 226, 3), 24, np.uint8)
for i, t in enumerate(thumbs):
    r_, c_ = divmod(i, cols)
    sheet[r_ * 420 + 30:r_ * 420 + 414, c_ * 226 + 5:c_ * 226 + 221] = t
    s = shots[i]
    lab = f"#{i} {s['look']} {s['from'] / FPS:.1f}-{s['to'] / FPS:.1f}s"
    cv2.putText(sheet, lab, (c_ * 226 + 6, r_ * 420 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    if s['face']:
        fx, fy = int(c_ * 226 + 5 + s['face']['x'] / 5), int(r_ * 420 + 30 + s['face']['y'] / 5)
        cv2.circle(sheet, (fx, fy), 5, (0, 220, 255), -1)
os.makedirs(os.path.join(ROOT, 'frames'), exist_ok=True)
cv2.imwrite(os.path.join(ROOT, 'frames', 'shots.png'), sheet)

for s in shots:
    f = s['face']
    print(f"shot #{s['i']} look {s['look']}  {s['from']}-{s['to']}  " + (f"face ({f['x']},{f['y']}) h{f['h']}" if f else 'no face'))
print(f'{len(shots)} shot(s), {len(jumps)} jump cut(s), looks like {people} person(s) on camera -> work/plan/faces.json, work/frames/shots.png')
