---
name: edit-any-video
description: The one entry point of this repo. Turns ANY video - a YouTube/web link or a local file, long or short - into finished vertical reels (1080x1920) in a style. Long videos (over ~90 s) - download, word-level transcript, Claude picks the best hook-to-payoff moments, cuts and reframes them to 9:16, then edits the best 3 in the podcast style (or every moment in the fast clip style) one at a time; short recordings become one reel in the talking-head style. Use whenever the user says "edit this", "edit this: <link or file>", "edit the rest", "edit all of them", "edit clip 5 in talking-head", "edit this in clip style", "continue", or pastes a video link or file and wants reels, shorts, TikToks or clips.
---

# Edit any video (router)

One verb, one knob. The verb is "edit"; the knob is the **style**:
- `podcast` (default for long videos): premium engine edit for clipped podcasts and interviews. 10-20 min per clip.
- `talking-head` (default for short recordings): premium engine edit for one person to camera. 15-25 min per reel.
- `clip`: the clipper's fast look (cut, reframe, word-by-word captions, zooms, a whoosh). About a minute per clip.
- any other folder in `styles/` (the user's own), or `<client>/<style>` in `clients/`.

The mechanical steps are `python work/scripts/eav.py <command>` (state in `work/run_state.json`). The judgment steps
reuse the two skills of this repo without duplicating them: **picking moments = the `clip-video` skill's rules**
(`.claude/skills/clip-video/references/picking-moments.md`), **editing one clip = the `short-form-edit` skill**.

## 0. Operating rules
- The user is usually away (an edit of 3 clips takes hours). Don't ask questions; make the calls yourself, report at the end.
- Work in the foreground of this session, one clip at a time. Never start `claude -p` or other headless sessions, never
  run two engine edits at once (the engine has one workspace: `input/`, `remotion/`, `work/`).
- Run long commands (fetch, render) in the background with a timeout you watch, and tell the user roughly how long.
- First run on this machine: if `.venv/` or `remotion/node_modules/` is missing, run `python install.py` first. It installs
  ffmpeg and Node.js if they are missing (winget / brew / apt), the Python packages, the Whisper models and the engine.
  If it says a tool was installed but isn't visible yet, tell the user to restart Claude Code and say "continue".
- Never commit or upload anything. Remind the user once to only post videos they own or may use.
- Music: never use the user's Epidemic Sound connector if they said not to; otherwise the engine's step 4 order applies
  (Epidemic connector → `input/music/` → bundled CC0 tracks via `music_fit.py`).

## 1. Understand the request
| The user says | You run |
|---|---|
| `edit this: <url or file>` | `eav.py start "<url or file>"` then follow the hints it prints (sections 2-4) |
| `edit this: <...> in talking-head style` / `in clip style` | `eav.py start "<...>" --style <style>` |
| `edit this in clip style` (same video as the current run) | `eav.py start "<same source>" --style clip` (the project, download and transcript are reused), then `eav.py queue --style clip` |
| `edit the rest` / `edit all of them` | `eav.py queue --rest` (every moment not yet done in the premium style used last, default podcast) / `eav.py queue --count all --style <style>`, then the loop |
| `edit clip 5 in talking-head` | `eav.py queue --clips 5 --style talking-head`, then the loop |
| `continue` (or a new session after an interruption) | `eav.py status`, then `eav.py next --continue` and the loop (an interrupted clip restarts cleanly) |
| `re-edit clip 2 in podcast` / `redo this one` / a revision round | `eav.py queue --clips 2 --style podcast --redo` (a short video: start it again, then `eav.py queue --redo`; a second style in the same request: add `--also` to the second queue command), then the loop. The new reel is saved as `... v2.mp4`; the earlier version stays |
| `just give me the cuts` / `don't edit` | sections 2-3 only: the raw 9:16 cuts are in `output/<project>/clips/` |

`eav.py start` decides long or short: a local file of 90 s or less is short (one reel). A link is fetched first; a link
to a short video is also handled as one reel.

## 2. Long videos: transcript (eav.py fetch)
`python work/scripts/eav.py fetch` downloads the audio and transcribes it with word timestamps (about 1/5 of the video's
length on a laptop CPU: ~20 min for a 1h40 podcast; run it in the background). If YouTube asks for a sign-in check, add
`--cookies-from-browser chrome` (or edge / firefox) - ask which browser only if the user is around; otherwise try chrome.

## 3. Long videos: pick the moments (your judgment), then cut
1. Read `.claude/skills/clip-video/references/picking-moments.md`, then the WHOLE
   `output/<project>/transcript/transcript.txt`. Pick the best **3-8** self-contained moments (hook → payoff, 25-60 s,
   15-90 s hard limits), ranked by score. Get exact word times with `python run.py find <project> "<phrase>"`.
2. Write `output/<project>/clips.json` in the format given there (title, hook, ranges, score, emphasis, caption, why).
3. `python work/scripts/eav.py cut`: it checks every boundary first; fix any warning with `run.py find` and run it again
   (or `--force` when a cut is intentional). It then downloads the video (max 1080p) and writes raw reframed 9:16 cuts,
   no captions, to `output/<project>/clips/` (the input of every style).
4. Show the user a short table (#, title, length, hook line, score) and keep going.

## 4. Queue and loop
1. `python work/scripts/eav.py queue` (default: the best 3 in `podcast` for long videos; one reel in `talking-head` for
   short ones; `--style clip` queues every moment). It writes `deliverables/<video>/clips.md`.
2. Loop until it prints ALL QUEUED CLIPS DONE or REQUEST DONE (the latter means older clips are still queued: mention
   them and stop; only "continue" edits those):
   - `python work/scripts/eav.py next` (`--continue` when the user said "continue"). For `clip`-style items it renders them all right away (clipper, minutes) and copies
     them to `deliverables/<video>/`. For an engine style it archives anything left in the engine, conforms the clip to
     `input/` (1080x1920, 30 fps), selects the style and writes `work/plan/clip_brief.md`; then:
   - **edit it with the `short-form-edit` skill** (`.claude/skills/short-form-edit/SKILL.md`) in that style. Step 0 parts
     2-4 are already done (engine archived, input ready, style selected): start at step 0 part 1 (setup check), then
     step 1. Kit styles (`podcast`, `talking-head`) follow the skill's section 4. Read `work/plan/clip_brief.md` first: it
     has the clip's title, hook, emphasis words and the video's metadata (names for vocabulary.txt and name tags).
     Deliver as the skill's step 9 says (`deliverables/FINAL - <clip title>.mp4`, extras), then:
   - `python work/scripts/eav.py done`: moves the reel to `deliverables/<video>/NN - <clip title> [style].mp4` and its
     extras (stems, captions.srt, EDIT_NOTES.md, phone copy) into the subfolder `NN - <clip title> [style]/`, archives the
     engine, updates `clips.md` and `REPORT.md`, prints the next step.
   - A clip that can't be finished after one honest fix pass: `eav.py fail "<reason>"`, then go on.
3. Between clips, post a one-line progress note (clip N of M done, minutes it took).

## 5. Deliver
When the loop ends, report: the folder `deliverables/<video>/`, each reel (style, length), how long each took, the music
credits, what `REPORT.md` says to check, and how to get the rest (`clips.md`: "edit the rest", "edit clip N in <style>",
"edit all of them in clip style"). If SendUserFile exists, send the first reel's phone copy (status proactive).
