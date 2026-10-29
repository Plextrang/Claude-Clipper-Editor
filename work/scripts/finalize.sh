#!/usr/bin/env bash
# Full rebuild: sync client style -> integrate scenes -> typecheck -> render video -> build cues -> mix -> mux -> loudness check -> QA strips.
# usage: bash work/scripts/finalize.sh <tag>      (outputs remotion/out/<tag>_video.mp4 and remotion/out/<tag>.mp4)
#        SKIP_RENDER=draft1 bash work/scripts/finalize.sh draft2   -> sound-only change: reuse draft1's video, redo cues/mix/mux
#        SCALE=0.5 bash work/scripts/finalize.sh draft1   -> half-resolution QA draft (faster; never deliver it). Full render ~5 min on an idle machine.
set -euo pipefail
TAG="${1:-final}"
SCALE="${SCALE:-1}"
PROJ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJ"
python work/scripts/use_style.py  # re-sync the active client style's theme
PYTHONIOENCODING=utf-8 python work/scripts/integrate.py > work/integrate.log; head -1 work/integrate.log
cd remotion
npx tsc --noEmit -p .
if [ -n "${SKIP_RENDER:-}" ]; then cp "out/${SKIP_RENDER}_video.mp4" "out/${TAG}_video.mp4"; else
PORT="${REMOTION_PORT:-$(python -c "import socket;s=socket.socket();s.bind(('127.0.0.1',0));print(s.getsockname()[1])")}"  # a free port of our own
npx remotion render Main "out/${TAG}_video.mp4" --port="$PORT" --muted --codec=h264 --crf=16 --x264-preset=slow --concurrency=8 \
  --scale="$SCALE" --timeout=240000 --image-format=jpeg --jpeg-quality=95 --log=error
fi
cd "$PROJ"
PYTHONIOENCODING=utf-8 python work/scripts/build_cues.py > work/build_cues.log; head -1 work/build_cues.log
python work/scripts/mix.py 2>&1 | grep -E "limiter|pre-norm|hot spots"
ffmpeg -v error -y -i "remotion/out/${TAG}_video.mp4" -i remotion/public/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k \
  -ar 48000 -shortest -movflags +faststart "remotion/out/${TAG}.mp4"
ffprobe -v error -show_entries stream=codec_name,width,height,nb_frames,duration -of compact "remotion/out/${TAG}.mp4"
ffmpeg -v info -i "remotion/out/${TAG}.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):"
rm -rf "remotion/out/strips_${TAG}"
python work/scripts/strips.py "remotion/out/${TAG}_video.mp4" "remotion/out/strips_${TAG}" 1
echo "FINALIZE OK: remotion/out/${TAG}.mp4"
