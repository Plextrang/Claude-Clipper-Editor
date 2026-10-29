import {CamKey, BandRange} from '../components/ARoll';
import {CapGroup, CapWord} from '../components/Captions';
import WORDS from './words.json';

type W = {w: string; s: number; e: number; f: number; i: number};
const words = WORDS as unknown as W[];

/* CAMERA - talking-head framing. Key = state AT frame f; origin (x,y) stays fixed on screen. Face centre in source ~(540,560).
 * ease: cut (instant, hides a jump cut) | snap (fast ease-out over dur) | smooth | accel | linear (slow push from previous key).
 * Every jump cut gets a cut key (punch-in/out) unless a full-screen scene covers it. Full example: clients/<client>/<style>/examples/<video>/edit.ts (if the style has one). */
export const CAMERA: CamKey[] = [{f: 0, s: 1.0, x: 540, y: 600, ease: 'cut'}];

/* Source jump cuts on the output timeline (EDL piece boundaries) - captions never hold across these. */
export const JUMP_CUTS: number[] = [];

/* CAPTIONS - cap(from, to, firstWordIndex, lastWordIndex, layout, {accent, bold, y, accentSize}); stack2 groups take {...cap(), split}. */
export const cap = (
  from: number,
  to: number,
  i0: number,
  i1: number,
  layout: CapGroup['layout'],
  o: {accent?: number[]; bold?: number[]; y?: number; accentSize?: number} = {},
): CapGroup => {
  const ws: CapWord[] = [];
  for (let i = i0; i <= i1; i++) {
    const w = words[i];
    ws.push({t: w.w, f: Math.max(from, w.f), accent: o.accent?.includes(i), bold: o.bold?.includes(i)});
  }
  return {from, to, words: ws, layout, y: o.y, accentSize: o.accentSize};
};
export const CAPTIONS: CapGroup[] = [];

/* SHADE - blurred + darkened lower band (+ logo veil) behind captions and on-screen cards. {from,to,strength?,top?,blur?,dark?} */
export const SHADE: BandRange[] = [];

/* Static brand logo on the set (source px of its centre, 1080x1920), softened behind captions - or null. */
export const LOGO = null as {x: number; y: number} | null;

/* White camera-flash cuts straddling a scene boundary. */
export const FLASHES: {peak: number; up: number; down: number; max: number}[] = [];
