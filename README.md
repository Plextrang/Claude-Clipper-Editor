# Claude Clipper Editor ✂️🎬

**Paste any video, get finished vertical reels.** A YouTube link or a file on your computer, a 2-hour podcast or a
40-second selfie video: Claude Code finds the best moments, cuts them to 9:16 around the speaker and edits them into
premium reels with captions, motion graphics, music and sound design. One folder, one prompt.

Claude Clipper Editor is a separate, standalone tool. It combines a few pieces of
[Claude Video Clipper](https://github.com/Plextrang/Claude-Video-Clipper) (finding, cutting and reframing the best
moments) with a few pieces of [Claude Short Form Editor](https://github.com/Plextrang/Claude-Short-Form-Editor) (the
editing engine). Both of those stay as they are and keep working on their own.

> **Needs a paid Claude plan.** Runs inside [Claude Code](https://claude.com/claude-code) (desktop app or CLI). The fast
> `clip` style works on Pro. The premium styles (`podcast`, `talking-head`) are long, autonomous sessions (~10-20 min and
> a large share of a Pro plan's 5-hour limit per reel), so for several reels a night a **Max plan** is the comfortable choice.
> If you hit your limit mid-run, just say `continue` later: it resumes at the next unfinished clip.

## Set up (once)
1. Install [Claude Code](https://claude.com/claude-code) and [Python 3.10+](https://www.python.org/downloads/)
   (Windows: tick "Add Python to PATH").
2. Download this repo (Code → Download ZIP, or `git clone https://github.com/Plextrang/Claude-Clipper-Editor.git`).
3. Open the folder in Claude Code. Use **High** effort and a permission mode that won't stop for approvals while you're
   away. Keep ~30 GB free disk space.

That's it. On the first edit Claude runs `python install.py` itself: it installs ffmpeg and Node.js if you don't have
them (winget / Homebrew / apt), a private Python environment, the Whisper speech models (~2 GB) and the video engine.

## Use it
Say one of these:

> **edit this: https://www.youtube.com/watch?v=...**

| You say | You get |
|---|---|
| `edit this: <YouTube link or long video file>` | all the best moments found and listed; **the best 3 edited** in the `podcast` style |
| `edit the rest` / `edit all of them` | the remaining moments, one after another |
| `edit this in clip style` | every moment in the fast `clip` look (minutes each) |
| `edit this: C:\videos\raw.mp4` (a short recording, under ~90 s) | one reel in the `talking-head` style |
| `edit clip 5 in talking-head` | one moment, any style |
| `continue` | picks up an interrupted run at the next unfinished clip |

Results land in `deliverables/<video title>/`:
```
01 - <clip title> [podcast].mp4      the reels
01 - <clip title> [podcast]/         per clip: captions.srt, audio stems, phone copy, EDIT_NOTES.md
clips.md                             every moment found (timestamps, hook line, length), what was edited, how to get the rest
REPORT.md                            what ran, how long each step took, anything to check
```

## The styles (`styles/`)
| Style | Look | Time per clip* |
|---|---|---|
| `clip` | cut + 9:16 reframe, word-by-word captions, zooms, a whoosh. No music. | **~1 min** |
| `podcast` | bold hook headline, karaoke captions, speaker-aware camera, name tags when two people talk, full-screen real B-roll on the key lines, quiet music bed, sound design | **~10-20 min** |
| `talking-head` | hook headline, clean captions with one accent word, slow spanning zooms, full-screen B-roll / image walls / logo and number animations, a full-screen text slam, colours from your footage, upbeat music, sound design | **~10-20 min** |

\*Measured on a mid-range Windows laptop (CPU only), see "Real timings" below; slower machines or extra fix passes can
double it. A default run on a long podcast (find the moments + 3 `podcast` reels) took **about 75 minutes**, and
`edit the rest` adds ~10-20 min per moment: start big runs before bed.

**Music:** `podcast` and `talking-head` always get a music bed: (1) if your [Epidemic Sound](https://www.epidemicsound.com)
account is connected in Claude (Settings → Connectors), Claude picks a track and fits it to the clip; (2) otherwise a track
you drop into `input/music/` is used as is; (3) otherwise a bundled royalty-free track (CC0 / public domain, see
`assets/music/MUSIC_LICENSES.md`). `clip` has no music.

**B-roll:** the premium styles cut to real, freely licensed photos and clips on the lines that deserve a visual.
Claude finds them on Wikimedia Commons by itself, and on Pexels too when the Claude in Chrome
extension is connected; every file's licence and author go into the reel's `EDIT_NOTES.md`. Nothing is stored in the repo.

**Your own style:** copy `styles/_template/` to `styles/my-style/`, drop reference frames or a PDF of edits you like into
`source/`, and say "set up the style styles/my-style". Then `edit this: <link> in my-style style`. Details in
`styles/_template/README.md`. (Agencies: `clients/<client>/<style>/` works too and never enters git.)

## Real timings
Measured 2026-10-28/29 on a Windows 11 laptop (12-thread CPU, no GPU used), from a fresh clone:

| Step | Time |
|---|---|
| First-run setup (`python install.py`) | 51 min, of which 44 min was the 2 GB Whisper download on a slow (~1 MB/s) connection; Python packages 5 min, engine 1 min. Expect ~10-15 min on a fast connection. |
| 1h43m podcast: audio download + word-level transcription | 14 min |
| Claude picks the moments (8 found) | 3 min |
| Cutting + 9:16 reframing of all 8 (includes the 870 MB video download) | 19 min |
| One `podcast` reel (52-67 s) | 10, 13 and 15 min; with real B-roll fetched per line: 13 and 17 min |
| One `talking-head` reel (22-28 s, from 33-47 s raw recordings, with B-roll) | 9, 10 and 12 min (first versions 14-24 min) |
| One `clip` reel (52-73 s) | ~55 s (all 8 in 7.5 min) |

Usage: a premium reel is one long autonomous session (roughly 200k tokens of model work per reel in our tests). On Pro
you can hit the 5-hour limit after a reel or two; say `continue` when it resets.

## What's inside
| Path | What |
|---|---|
| `.claude/skills/edit-any-video/` | the router: "edit this", styles, queue, resume |
| `.claude/skills/clip-video/` | finding and cutting the moments (from Claude Video Clipper) |
| `.claude/skills/short-form-edit/` | the editing engine's pipeline (one clip, one style) |
| `styles/` | `clip`, `podcast`, `talking-head`, `_template` |
| `clipper/`, `run.py` | download, transcription, moment finder, cutter, face reframe, the clip-style renderer |
| `remotion/`, `work/scripts/` | the video engine (Remotion) and its pipeline scripts; `work/scripts/eav.py` = the router's state machine |
| `assets/` | fonts (OFL), face model (MIT), sound effects, bundled music (CC0 / PD) |
| `input/`, `output/`, `deliverables/`, `archive/` | your footage, clipper projects, results, finished clips' working files (all git-ignored) |

## Notes
- **Clip responsibly:** only clip and post videos you own or have permission to use.
- **Privacy:** footage, transcripts, renders and run state never leave your computer and are git-ignored.
- **Disk:** each premium reel keeps its working files in `archive/` (~1-2 GB). Delete old ones when you're happy.
- **YouTube says "confirm you're not a bot":** say "use my chrome cookies" (or edge / firefox).
- **Licences:** code MIT (`LICENSE`). Montserrat + Inter: SIL Open Font License (`assets/fonts/`). YuNet face model: MIT.
  Bundled music and sounds: see `assets/music/MUSIC_LICENSES.md` and `assets/sfx/`. [Remotion](https://www.remotion.dev/license)
  is free for individuals and small teams; larger companies need a company licence. Brand logos are downloaded on your
  machine (simple-icons CC0, Material Symbols Apache-2.0, Wikimedia Commons) and are trademarks of their owners.
