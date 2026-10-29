import {Easing, interpolate, spring} from 'remotion';

export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1); // fast then slow
export const EASE_IN_OUT = Easing.bezier(0.65, 0, 0.35, 1);
export const EASE_IN = Easing.bezier(0.7, 0, 0.84, 0);

export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** 0..1 progress from frame `start` over `dur` frames with ease. */
export const prog = (frame: number, start: number, dur: number, ease = EASE_OUT) =>
  interpolate(frame, [start, start + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

export const sp = (frame: number, fps: number, start: number, cfg = {stiffness: 220, damping: 18}) =>
  spring({frame: Math.max(0, frame - start), fps, config: cfg});

/** Word pop: rises from slightly below, fades in, de-blurs. Fast then slow. */
export const wordPop = (frame: number, start: number, dur = 9, rise = 22, blur = 8) => {
  const p = prog(frame, start, dur);
  return {
    opacity: clamp01(p * 1.6),
    transform: 'translateY(' + (1 - p) * rise + 'px)',
    filter: p >= 1 ? 'none' : 'blur(' + (1 - p) * blur + 'px)',
  };
};

/** Deterministic pseudo-random (no Math.random in renders). */
export const rand = (seed: number) => {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
