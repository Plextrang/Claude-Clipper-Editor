# clip - the fast look

The clipper's own edit, rendered by the clipper (`clipper/edit.py`, OpenCV + ffmpeg), not by the Remotion engine.
About a minute per clip instead of the 10-20 minutes of `podcast` / `talking-head`.

- **Cut and reframe:** each moment cut on whole words, 9:16 around the speaker's face, per camera shot
  (slides and b-roll get a blurred-background "fit" layout).
- **Captions:** 1-3 words at a time, Montserrat ExtraBold uppercase, popping in as spoken; the spoken word and the
  moment's emphasis words light up in one accent colour (the creator's brand colour if known, else taken from the video,
  else short-form yellow). An `.srt` is written too.
- **Zooms:** a quick zoom-out to open, then wide / punched-in framing every few seconds on sentence ends, a slow push in
  between. Camera cuts and splices get a framing change.
- **Sound:** at most 2 subtle whooshes per clip (`assets/sfx/`), voice lightly compressed, mix at -14 LUFS. No music.

Say `edit this in clip style` (every moment found), or `edit clip 3 in clip style`. Tweaks the clipper understands:
"captions lower", "not all caps", "no sound effects", "use #00E5FF as the caption colour" (see
`.claude/skills/clip-video/references/editing.md`).

This folder holds no engine files on purpose: `use_style.py clip` refuses it, and the router sends `clip` to the clipper.
