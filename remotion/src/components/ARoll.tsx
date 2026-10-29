import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame} from 'remotion';
import {EASE_IN, EASE_IN_OUT, EASE_OUT, clamp01} from '../lib/anim';

/**
 * Camera key = state AT frame f. Transition INTO a key from the previous state:
 *  cut    -> instant at f (masks jump cuts as a punch-in/out)
 *  smooth -> eased over the `dur` frames ending at f
 *  snap   -> fast ease-out (punch) over `dur` frames ending at f
 *  linear -> continuous drift from the previous key's frame to f (slow push)
 */
export type CamKey = {f: number; s: number; x: number; y: number; ease: 'cut' | 'smooth' | 'snap' | 'accel' | 'linear'; dur?: number};

export const camAt = (keys: CamKey[], t: number) => {
  let pi = 0;
  for (let i = 0; i < keys.length; i++) if (keys[i].f <= t) pi = i;
  const p = keys[pi];
  const n = keys[pi + 1];
  if (!n || t < p.f) return {s: p.s, x: p.x, y: p.y, v: 0};
  let k = 0;
  if (n.ease === 'linear') k = (t - p.f) / (n.f - p.f);
  else if (n.ease === 'smooth' || n.ease === 'snap' || n.ease === 'accel') {
    const d = n.dur ?? 12;
    const r = clamp01((t - (n.f - d)) / d);
    k = n.ease === 'smooth' ? EASE_IN_OUT(r) : n.ease === 'snap' ? EASE_OUT(r) : EASE_IN(r);
  }
  const lerp = (a: number, b: number) => a + (b - a) * k;
  return {s: lerp(p.s, n.s), x: lerp(p.x, n.x), y: lerp(p.y, n.y), v: Math.abs(n.s - p.s) * (k > 0 && k < 1 ? 1 : 0)};
};

export const ARoll: React.FC<{keys: CamKey[]; hidden?: (f: number) => boolean}> = ({keys, hidden}) => {
  const f = useCurrentFrame();
  const c = camAt(keys, f);
  // velocity-based micro motion blur on fast camera moves
  const c2 = camAt(keys, f - 1);
  const vel = Math.abs(c.s - c2.s) * 1000;
  const blur = vel > 10 ? Math.min(1.2, (vel - 10) * 0.06) : 0; // gentle: avoids sharp-blur-sharp flicker after cuts
  if (hidden && hidden(f)) return null;
  const w = 1080 * c.s;
  const h = 1920 * c.s;
  const left = c.x - c.x * c.s;
  const top = c.y - c.y * c.s;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#0b2433'}}>
      <div
        style={{
          position: 'absolute',
          left,
          top,
          width: w,
          height: h,
          filter: blur > 0.05 ? 'blur(' + blur.toFixed(2) + 'px)' : undefined,
        }}
      >
        <OffthreadVideo src={staticFile('aroll.mp4')} muted style={{width: '100%', height: '100%', display: 'block'}} />
      </div>
    </AbsoluteFill>
  );
};

/**
 * Real blurred copy of the talking head (same camera geometry), masked to the lower part of the frame.
 * Replaces CSS backdrop-filter, which is broken over video in our renderer.
 */
export type BandRange = {from: number; to: number; strength?: number; top?: number; blur?: number; dark?: number};
// default caption band: starts at y=840 (fully on by ~1140, where the mic-arm logo sits) with a 13px blur
export const BAND_TOP = 840;
export const BAND_BLUR = 13;
export const bandAt = (ranges: BandRange[], f: number) => {
  // Hard on/off at scene cuts; smooth 8-frame interpolation only between ADJACENT bands (e.g. caption band -> card band).
  const i = ranges.findIndex((r) => f >= r.from && f < r.to);
  if (i < 0) return null;
  const r = ranges[i];
  const prev = i > 0 && ranges[i - 1].to === r.from ? ranges[i - 1] : null;
  const k = prev ? EASE_IN_OUT(clamp01((f - r.from + 1) / 8)) : 1;
  const mix = (x: number, y: number) => (prev ? x + (y - x) * k : y);
  const P = prev ?? r;
  return {
    a: mix(P.strength ?? 1, r.strength ?? 1),
    r: {...r, top: mix(P.top ?? BAND_TOP, r.top ?? BAND_TOP), blur: mix(P.blur ?? BAND_BLUR, r.blur ?? BAND_BLUR), dark: mix(P.dark ?? 1, r.dark ?? 1)},
  };
};
export const BlurBand: React.FC<{keys: CamKey[]; ranges: BandRange[]}> = ({keys, ranges}) => {
  const f = useCurrentFrame();
  const b = bandAt(ranges, f);
  if (!b) return null;
  const top = b.r.top ?? BAND_TOP;
  const blur = b.r.blur ?? BAND_BLUR;
  const c = camAt(keys, f);
  const w = 1080 * c.s;
  const h = 1920 * c.s;
  const mask = 'linear-gradient(to bottom, transparent ' + top + 'px, black ' + (top + 300) + 'px, black 100%)';
  return (
    <AbsoluteFill style={{opacity: b.a, maskImage: mask, WebkitMaskImage: mask, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: c.x - c.x * c.s, top: c.y - c.y * c.s, width: w, height: h, filter: 'blur(' + blur + 'px)'}}>
        <OffthreadVideo src={staticFile('aroll.mp4')} muted style={{width: '100%', height: '100%', display: 'block'}} />
      </div>
    </AbsoluteFill>
  );
};

/**
 * A static brand logo on the set (LOGO in data/edit.ts, source px). Whenever the lower band is on,
 * cover it with a small feathered, heavily blurred + slightly dimmed patch that follows the camera geometry,
 * so it never reads next to the caption accents. Only a small clipped box is blurred (cheap to render).
 */
export const LogoVeil: React.FC<{logo: {x: number; y: number} | null; keys: CamKey[]; ranges: BandRange[]; hidden?: (f: number) => boolean}> = ({logo, keys, ranges, hidden}) => {
  const f = useCurrentFrame();
  const b = bandAt(ranges, f);
  if (!logo || !b || (hidden && hidden(f))) return null;
  const c = camAt(keys, f);
  const X = c.x + (logo.x - c.x) * c.s; // screen = origin + (src - origin) * s (same mapping as ARoll)
  const Y = c.y + (logo.y - c.y) * c.s;
  const R = 170 * c.s;
  const B = R + 80; // half-size of the blurred box: keeps the blur's transparent edge outside the mask
  const mask = 'radial-gradient(circle ' + R.toFixed(1) + 'px at ' + B.toFixed(1) + 'px ' + B.toFixed(1) + 'px, black 60%, transparent 100%)';
  return (
    <AbsoluteFill style={{opacity: b.a, pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: X - B,
          top: Y - B,
          width: 2 * B,
          height: 2 * B,
          overflow: 'hidden',
          filter: 'blur(' + (26 * c.s).toFixed(1) + 'px) brightness(0.82)',
          maskImage: mask,
          WebkitMaskImage: mask,
        }}
      >
        <div style={{position: 'absolute', left: c.x - c.x * c.s - (X - B), top: c.y - c.y * c.s - (Y - B), width: 1080 * c.s, height: 1920 * c.s}}>
          <OffthreadVideo src={staticFile('aroll.mp4')} muted style={{width: '100%', height: '100%', display: 'block'}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
