# Changelog

## v2.0.0 - 2026-10-29: Claude Clipper Editor, edit ANY video

Claude Clipper Editor is v2 of [Claude Short Form Editor](https://github.com/Plextrang/Claude-Short-Form-Editor) (v1 stays
there unchanged). It merges [Claude Video Clipper](https://github.com/Plextrang/Claude-Video-Clipper) into the editing engine: one folder,
one prompt (`edit this: <link or file>`) turns any video, long or short, into finished vertical reels.

### New compared with v1 (the client-style engine)
- **One entry point:** the `edit-any-video` skill + `work/scripts/eav.py`. Detects a link or a file and long (> ~90 s) vs
  short; long videos are downloaded, transcribed, the best 3-8 moments picked, cut and reframed to 9:16, then the best 3
  are edited (`edit the rest`, `edit all of them`, `edit clip 5 in talking-head`, `edit this in clip style`).
- **Resume:** `work/run_state.json` records every step and clip; `continue` restarts an interrupted clip from a clean
  engine and goes on with the rest. The engine is archived between clips exactly like `new_video.py` does by hand.
- **Deliverables per video:** `deliverables/<video>/NN - <clip title> [style].mp4`, one extras folder per clip,
  `clips.md` (every moment found, what was edited, how to get the rest) and `REPORT.md` (step timings, things to check).
- **`styles/`**, a one-level style path next to `clients/<client>/<style>/` (which keeps working unchanged):
  `use_style.py podcast` selects `styles/podcast/`; styles keep `STYLE_GUIDE.md` and `theme.ts` at their root (or in
  `style/`); their sound pack defaults to the shared `assets/sfx/pack/`.
- **Three ready-made styles:** `podcast` (new), `talking-head` (new), `clip` (the clipper's look), plus `styles/_template`
  (the former `clients/_template`, adapted) for building your own.
- **Reel kit** (new engine feature, used by `podcast` and `talking-head`): `remotion/src/components/Reel.tsx` (karaoke /
  pop captions, hook headline, name tags, number / keyword / logo / list / quote cards, full-screen text slams, progress
  bar), `work/scripts/reel_build.py` (one small `reel.json` plan → scenes, camera, band, flashes, sound design),
  `work/scripts/face_track.py` (camera shots + face per shot → a speaker-aware camera; contact sheet of shots),
  `work/scripts/keep_all.py`, `work/scripts/music_fit.py`. A kit edit needs no scene workflow and no sub-agents: 10-20 min
  per clip in our tests instead of ~3 hours, and far less usage.
- **Full-screen inserts instead of UI cards** (after the first review): real B-roll stills or clips, a moving wall of
  pictures ("tons of references"), a big real logo, a big counting number. `work/scripts/broll_fetch.py` finds and saves
  freely licensed B-roll (Wikimedia Commons without a key; Pexels / Unsplash files found with the Claude in Chrome
  extension) and records every credit. The podcast hook headline lost its box; it stands out with a heavy outline.
- **Clean cuts between takes:** `build_edl.py` trims every kept sentence to its first and last word and drops word-less
  micro-pieces, so no frame of the speaker looking down at notes between takes survives; full-screen moments start
  exactly on the jump cut and are already covering the frame on their first frame.
- **Talking-head camera = slow spanning zooms** (`camera.mode: smooth`): no punch-ins, the camera holds still before every
  animation. The music never stops under full-screen moments, and talking-head music is upbeat by default.
- **Music level measured per track:** `music_fit.py` measures the exact stretch used (EBU R128) and sets it to the style's
  level (podcast -24 LUFS, talking-head -18), so every track sits the same distance under the voice.
- **Re-edits and several videos:** `eav.py queue --redo` re-edits a clip as `... v2.mp4` (the old one stays); starting
  another video parks the current run in `work/runs/` and starting it again brings it back; a new request is served
  before clips left pending by an older one ("continue" picks those up).
- **Music fallback chain:** Epidemic Sound connector → your track in `input/music/` → bundled CC0 / public-domain tracks
  (two moods per premium style, `assets/music/`, licences in `MUSIC_LICENSES.md`).
- **Bundled CC0 sound pack** (`assets/sfx/pack/`: whooshes, pops, UI clicks, risers, hits), licences recorded.
- **One-command setup:** `python install.py` installs ffmpeg and Node.js when missing (winget / Homebrew / apt), a private
  `.venv` with every Python package, the Whisper models (small.en, medium.en, tiny) and the engine's Node packages.
  Engine scripts re-run themselves inside `.venv` (`work/scripts/venv_boot.py`), so `python work/scripts/x.py` keeps working.
- `build_edl.py`: `MAX_PAUSE` env / style `maxPause` (podcast clips keep pauses up to 0.7 s: fewer jump cuts).
- `new_video.py`: archives only the engine's own files in `deliverables/`, never a router video folder; `--quiet`;
  tolerates a missing `active_style.json`.
- `source_pages.py`, `palette.py`, `use_style.py --list`, the scene workflow and ONBOARDING know both style layouts.

### New compared with Claude Video Clipper
- Its moments can now be edited in the premium engine styles; the clipper's own edit is the `clip` style.
- Setup no longer asks you to install FFmpeg / Node by hand: `install.py` does it (`clip-video` skill step 0 updated).
- Whisper models are shared with the engine (`work/hf_cache/`), downloaded once at setup.
- Its optional Remotion caption renderer moved to `clipper/remotion/` (`python install.py --clipper-remotion`).

### Engine changes from the local working copy that were not on GitHub
- None. The local engine (HEAD `c69c9d6`, 2026-10-13) was compared file by file with the public repository: all 83
  tracked files are identical (one differed only by Windows line endings). Everything above is new in v2.

## v1 - 2026-10-13
Client-based short-form editing engine (`clients/<client>/<style>/`), footage palette, real brand assets.
