export const meta = {
  name: 'short-form-scene-build',
  description: 'Build every motion-graphics scene of a short-form edit in parallel (implement + self-check), return event reports',
  whenToUse: 'Step 6 of the short-form-edit skill. args = {root: "<absolute project root>", style: "styles/<name> or clients/<client>/<style>", ids: ["FS1_...", "OS1_...", ...]}',
  phases: [{title: 'Build', detail: 'one agent per scene: implement, contact sheet, self-critique, fix (max 3 rounds)'}],
}

const REPORT = {
  type: 'object',
  properties: {
    id: {type: 'string'},
    summary: {type: 'string'},
    events: {
      type: 'array',
      items: {type: 'object', properties: {frame: {type: 'number'}, what: {type: 'string'}}, required: ['frame', 'what']},
    },
    opaqueFrom: {type: 'number'},
    opaqueUntil: {type: 'number'},
    knownIssues: {type: 'array', items: {type: 'string'}},
  },
  required: ['id', 'summary', 'events', 'opaqueFrom', 'opaqueUntil', 'knownIssues'],
}

const A = typeof args === 'string' ? JSON.parse(args) : args || {}
const root = A.root
const ids = Array.isArray(A.ids) ? A.ids : []
const style = (A.style || '').replace(/\\/g, '/').replace(/^\/+|\/+$/g, '')
if (!root || !ids.length || !style) throw new Error('args must be {root: "<absolute project root>", style: "styles/<name> or clients/<client>/<style>", ids: ["FS1_...", ...]}')
const S = `${root}/${style}`

const prompt = (id) => `You are a senior motion designer. Implement ONE scene of a short-form talking-head edit in Remotion: ${id}.
Project root: ${root}  (work ONLY inside it). Use the Bash tool; shells do not keep the working directory, so start EVERY command
with: cd "${root}/remotion" &&

READ (nothing else unless needed):
1. ${root}/work/plan/ENGINE.md - the contract. Follow its rules, Seams section and Self-check procedure (max 3 rounds) exactly.
2. Your section "## ${id}" in ${root}/work/plan/MASTER_PLAN.md - the spec (ABSOLUTE frames). If your FROM/TO touches another
   full-screen scene, read that scene's section too (hand-off rule in ENGINE.md).
3. The style guide (${S}/STYLE_GUIDE.md, or ${S}/style/STYLE_GUIDE.md) sections 1-2 (the client's look: it overrides ${root}/work/plan/CRAFT_DEFAULTS.md), and the board
   tiles / example scenes named in your spec's "refs" line (paths from the project root).
4. ${root}/remotion/public/brand/README.md - the REAL logo + UI glyph library and its rules.
CAMERA and SHADE in remotion/src/data/edit.ts are FINAL: at seams derive framing and band with camAt/bandAt, never type numbers.
HOUSE STANDARDS (CRAFT_DEFAULTS section 5; they override any colour the style guide names): (a) colours come from THIS video's
footage palette: import C/accentGlow/alpha from '../theme' (never '../data/style_theme'), every colour is a token or alpha()/mix()
of one, no hex or rgb literals except a brand's own colours and white/black; light scenes use PaperBG tone="palette".
(b) every brand/app/platform is the REAL logo (BrandLogo / Glyph brand from components/Brand.tsx) and every UI looks like the
real product with real glyphs (Glyph name); never draw a stand-in. Missing asset: python work/scripts/fetch_brand_assets.py
--si <slug> | --commons "<Commons file title>" <name>.svg | --ui <name> (run from the project root).

WRITE ONLY remotion/src/scenes/${id}.tsx and remotion/src/preview/${id}.entry.tsx. Your transitions live inside your scene.
Do NOT run integrate.py, finalize.sh or full renders, and do not touch other scenes (they are being written in parallel).

RETURN the report: summary (2-3 sentences); events = EVERY visible motion beat at the ABSOLUTE frame where it visibly lands or
peaks in your stills (entrances, pops, slams, drops, wipes, counters, cursor clicks, exits) - the sound designer syncs SFX to these;
opaqueFrom / opaqueUntil (-1 for on-screen overlays); knownIssues (empty if none).`

phase('Build')
const LIMIT = 5 // parallel scene agents (each renders stills with CONC=1): more saturates the CPU and causes render timeouts
const out = []
let next = 0
const worker = async () => {
  while (next < ids.length) {
    const k = next++
    out[k] = await agent(prompt(ids[k]), {label: `scene:${ids[k]}`, phase: 'Build', schema: REPORT})
  }
}
await Promise.all(Array.from({length: Math.min(LIMIT, ids.length)}, worker))
const missing = ids.filter((id, k) => !out[k])
if (missing.length) log(`no report for: ${missing.join(', ')} - check those scenes manually`)
return out.filter(Boolean)
