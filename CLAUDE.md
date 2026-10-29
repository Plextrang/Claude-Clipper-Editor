# Claude Clipper Editor

This repo turns ANY video (a YouTube/web link or a local file, long or short) into finished 1080x1920 reels, autonomously.

- **Whenever the user asks to edit something** ("edit this: <link or file>", "edit the rest", "edit all of them",
  "edit clip 5 in talking-head", "edit this in clip style", "continue"), or pastes a video link or file, use the
  `edit-any-video` skill (`.claude/skills/edit-any-video/SKILL.md`) and follow it. It routes to the two other skills:
  `clip-video` (finding and cutting the moments of a long video) and `short-form-edit` (editing one clip in a style).
- Use `short-form-edit` directly only when the user asks for the engine itself: a video they put in `input/` themselves
  ("run the edit for acme/talking-head"), onboarding a new style, or redoing one stage of an edit.
- Styles live in `styles/<name>/` (`podcast`, `talking-head`, `clip`, the user's own; how to build one:
  `styles/_template/README.md`). Agencies can also keep client styles in `clients/<client>/<style>/` (git-ignored).
- First run on a new machine: `python install.py` (installs ffmpeg/Node if missing, .venv, Whisper models, the engine).
- The user is usually away during an edit: do not ask questions. Make and approve your own decisions, then report.
- Results go to `deliverables/<video title>/`. Footage, transcripts, renders and run state are git-ignored.
- Work only inside this folder (first-run installs and Remotion temp cleanup excepted). Never commit or upload anything.
- Never copy client material (anything in `clients/`) into tracked files.
- House standards on every engine edit: animation colours come from the video's own footage (`work/scripts/palette.py`)
  unless the style says `Palette: fixed`, and every brand, app or UI on screen is the real logo / real interface
  (`remotion/public/brand`, `Brand.tsx`), never a drawn stand-in.
