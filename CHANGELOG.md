# Changelog

## v1.0.0 - 2026-10-29: first release

Claude Clipper Editor is a separate, standalone tool: one folder, one prompt (`edit this: <link or file>`) turns any
video, long or short, into finished vertical reels.

### What's in it
- **One entry point:** the `edit-any-video` skill + `work/scripts/eav.py`. Detects a link or a file and long (> ~90 s) vs
  short; long videos are downloaded, transcribed, the best 3-8 moments picked, cut and reframed to 9:16, then the best 3
  are edited (`edit the rest`, `edit all of them`, `edit clip 5 in talking-head`, `edit this in clip style`).
- **Resume and re-edits:** `work/run_state.json` records every step and clip; `continue` restarts an interrupted clip
  cleanly and goes on with the rest. `eav.py queue --redo` re-edits a clip as `... v2.mp4` (the earlier one stays).
  Starting another video parks the current run in `work/runs/`; starting it again brings it back.
- **Deliverables per video:** `deliverables/<video>/NN - <clip title> [style].mp4`, one extras folder per clip,
  `clips.md` (every moment found, what was edited, how to get the rest) and `REPORT.md` (step timings, things to check).
- **Three ready-made styles** in `styles/`: `podcast`, `talking-head`, `clip` (the fast look), plus `styles/_template`
  for building your own. Agencies can also keep client styles in `clients/<client>/<style>/` (git-ignored).
- **Reel kit** (used by `podcast` and `talking-head`): `remotion/src/components/Reel.tsx` (karaoke / pop captions, hook
  headline, name tags, full-screen inserts, text slams, progress bar) and `work/scripts/reel_build.py` (one small
  `reel.json` plan → scenes, camera, captions, sound design). About 10-20 min per reel.
- **Full-screen inserts, no UI cards:** real B-roll stills or clips, a moving wall of pictures, a big real logo, a big
  counting number. `work/scripts/broll_fetch.py` finds and saves freely licensed B-roll (Wikimedia Commons without a key;
  Pexels / Unsplash files found with the Claude in Chrome extension) and records every credit.
- **Clean cuts between takes:** every kept sentence is trimmed to its words and word-less micro-pieces are dropped, so no
  frame of the speaker looking at notes survives; full-screen moments start exactly on the cut.
- **Camera:** speaker-aware framing for podcasts (`face_track.py`); slow spanning zooms for talking-head.
- **Music:** Epidemic Sound connector → your track in `input/music/` → bundled CC0 / public-domain tracks. Every track is
  measured and set to the style's level (`music_fit.py`), and the bed never stops under full-screen moments.
- **Bundled CC0 sound pack** (`assets/sfx/pack/`: whooshes, pops, UI clicks, risers, hits), licences recorded.
- **One-command setup:** `python install.py` installs ffmpeg and Node.js when missing (winget / Homebrew / apt), a private
  `.venv` with every Python package, the Whisper models and the video engine's packages.

### Where it comes from
- Finding, cutting and reframing the moments, and the `clip` style, come from
  [Claude Video Clipper](https://github.com/Plextrang/Claude-Video-Clipper).
- The editing engine (Remotion scenes, captions, cut, mix) comes from
  [Claude Short Form Editor](https://github.com/Plextrang/Claude-Short-Form-Editor).
- New here: the router, the `podcast` and `talking-head` styles, the reel kit, B-roll inserts and the one-command setup.
- Both of those repositories stay as they are and keep working on their own.
