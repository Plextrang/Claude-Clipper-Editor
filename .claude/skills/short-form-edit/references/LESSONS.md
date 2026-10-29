# Where the first project's tokens went (measured), and what this skill cuts

Measured from the session transcripts: 1 main agent (394 turns) + 158 sub-agents in 8 workflows, over 3 daily sessions,
about 6.3 h of active work. "Units" weight tokens by API price ratios (input 1, cache write 1.25, cache read 0.1, output 5);
plan usage limits track roughly the same thing.

| Block | Agents | Units | Share | Verdict for next time |
|---|---|---|---|---|
| Scene build: implement → separate reviewer → fixer, 13 scenes (19 impl, 25 review, 18 fix) | 62 | 66.0M | 46% | **Keep the build, cut the reviewers.** Implementers self-check with one contact sheet per round. Reviews were 24M of this; most findings were systemic (backdrop-filter, fonts, seams) and are now rules in ENGINE.md. |
| QA round 1 + round 2: 7 reviewers each + 49 skeptic verifiers | 64 | 33.7M | 24% | **Cut.** Real defects were almost all at seams; the main agent reviewing strips with the checklist finds them. The verifiers mostly re-confirmed near-duplicates. |
| Main agent (orchestration, engine, cut, audio, fixes, 160 images read) | 1 | 25.2M | 18% | Lean it out. 187M cache-read tokens = a huge context re-read every turn. Fewer, batched turns; sheets instead of single stills. |
| Plan panel: 4 planners + 3 judges + synthesis | 9 | 9.5M | 7% | **Cut.** One planner (main agent) with the style guide + an earlier plan as template. |
| Fix dispatches after QA (3 workflows) | 23 | 9.0M | 6% | Cut to direct edits or one agent with a precise list. |
| **Total** | 159 | **~143M** | | Target next time: <= 60M (a third to a half) and ~3 h. The main agent now also plans, reviews and fixes, so it will grow; everything else shrinks. |

Reviewing and verifying alone (review + verify classes) was 41% of everything.

## One-time costs that are now solved (don't pay them again)
- Whisper install on Windows: xet download stall, PyAV numpy workaround, models cached in `work/hf_cache`.
- `backdrop-filter` kaleidoscope: discovered after renders; required patching every card. Now banned in ENGINE.md.
- Disk full (~85 GB of Remotion temp copies) → crash, recovery and re-cut. Now: clean temp after each render.
- Render timeouts from CPU saturation (parallel agents + renders). Now: never full-render while agents render stills, 5 agents max.
- Workflow plumbing errors: CRLF scripts, args passed as a string, workflow scripts can't read files.
- Hard-coded per-video numbers in scripts. Now: everything derives from `edl.json` and `video.json`.
- Mix: bass-heavy music chosen for headphones vanished on phones. Fixed with the mobile mix; pick phone-friendly tracks.
- Renders: 6 full renders (draft1, candidate1, final, final2, final3, final4). 2 are enough with strips QA + still checks.

## Solved inside the scripts (no action needed, kept for debugging)
- Whisper on Windows: audio passed as a numpy array (PyAV bug); `HF_HUB_DISABLE_XET=1` (downloads stall); packages in
  `work/pylibs` (`pip --target`), models in `work/hf_cache`.
- `finalize.sh`: never pipe Python into `head` under `pipefail` (broken pipe kills the run); logs go to `work/*.log`.
- Mix: voice anchored at -16 LUFS; master gain from the un-boosted balance (voice locked); music +6 dB + presence shelf, SFX +4 dB
  capped 1 dB under the voice; 4x-oversampled limiter keeps true peak <= -1 (a plain soft clip overshot 3 dB between samples).
- Audit after packaging (3 read-only agents) caught: ENGINE.md claiming the integrator adds transitions; seams being built before
  CAMERA/SHADE were final; strips skipping the frame before each cut; unbounded self-check loops. All fixed in the skill.

## What actually made the edit great (keep doing these)
- The engine: an explicit-geometry camera, a real blurred band instead of backdrop-filter, the caption engine (reserved
  layout, hard exits at cuts, hold-until-next-pop), and scenes owning their own transitions.
- Per-scene craft from a very specific spec (exact sizes, colours, positions, frame-keyed choreography, emotional job).
- Seam discipline: camera match + band hand-off on every reveal.
- Sound cues aligned to reported event frames; sample-accurate placement by peak.
- A strips-based QA pass at every seam.

## Client feedback after the 15-video batch (Oct 2026): two new house standards
The client approved the batch, then asked for (1) REAL icons, logos and UIs instead of the stand-ins we drew, and (2) animation
colours matched to the footage instead of the same orange every time. A v2 of "Doubling Down on YouTube" (lavender shirt,
lavender room, peach lamp; real YouTube / Premiere Pro / CapCut assets and a real YouTube comment sheet) was called
"literally perfect, even much better". Built into the engine: `palette.py` + `src/data/palette.ts` (merged in `theme.ts`),
`fetch_brand_assets.py` + `Brand.tsx` + `PaperBG tone="palette"`, and rules in ENGINE.md, CRAFT_DEFAULTS §5 and the skill.
Lessons from that run:
- Scenes that import colours from `../data/style_theme` silently bypass the palette: always import from `../theme`.
- Hard-coded rgba() shadows/glows are where stock colours hide; build them from tokens with `alpha()`.
- `capcut_icon.svg` is the complete app icon: an agent boxed it inside a second tile. Read the brand README notes.
- CSS-mask glyphs are not awaited by the renderer; `Glyph` inlines the SVG path behind delayRender instead.
- Cost of the v2 rebuild (plan revision + 7 scenes + finish): ~1.5M subagent tokens, ~29 min.
- Batch prep: raws at other sizes/frame rates must be conformed to 1080x1920 / 30 fps CFR before the cut (render_cut trims by
  30 fps frame index); build_edl's energy refinement does nothing on noisy rooms (floor above ~-40 dB): check edl.json.
