import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {EASE_IN_OUT, EASE_OUT, EASE_IN, clamp01, prog} from '../lib/anim';

export type Trans = 'cut' | 'circle' | 'square' | 'flash' | 'push' | 'slideUp' | 'zoomBlur';

/**
 * Wraps a full-screen scene (rendered inside a <Sequence>, so frame 0 = scene start) and applies the
 * entrance/exit transition against whatever is underneath (the A-roll).
 * durIn/durOut in frames. cx/cy = reveal origin.
 */
export const SceneWrap: React.FC<{
  len: number;
  tin?: Trans;
  tout?: Trans;
  durIn?: number;
  durOut?: number;
  cx?: number;
  cy?: number;
  children: React.ReactNode;
}> = ({len, tin = 'cut', tout = 'cut', durIn = 12, durOut = 10, cx = 540, cy = 960, children}) => {
  const f = useCurrentFrame();
  const pin = tin === 'cut' ? 1 : prog(f, 0, durIn, EASE_IN_OUT);
  const pout = tout === 'cut' ? 0 : prog(f, len - durOut, durOut, EASE_IN_OUT);
  let clip: string | undefined;
  let transform = '';
  let opacity = 1;
  let filter: string | undefined;

  // entrance
  if (pin < 1) {
    if (tin === 'circle') clip = 'circle(' + (pin * 2250).toFixed(1) + 'px at ' + cx + 'px ' + cy + 'px)';
    if (tin === 'square') {
      const hw = 30 + pin * 1100, hh = 30 + pin * 1600;
      clip = 'inset(' + Math.max(0, cy - hh) + 'px ' + Math.max(0, 1080 - cx - hw) + 'px ' + Math.max(0, 1920 - cy - hh) + 'px ' + Math.max(0, cx - hw) + 'px round ' + (60 * (1 - pin)).toFixed(1) + 'px)';
    }
    if (tin === 'push') transform += ' translateY(' + ((1 - EASE_OUT(clamp01(f / durIn))) * 1920).toFixed(1) + 'px)';
    if (tin === 'slideUp') {
      transform += ' translateY(' + ((1 - EASE_OUT(clamp01(f / durIn))) * 260).toFixed(1) + 'px)';
      opacity = clamp01(f / (durIn * 0.6));
    }
    if (tin === 'zoomBlur') {
      const e = EASE_OUT(clamp01(f / durIn));
      transform += ' scale(' + (1.25 - 0.25 * e).toFixed(4) + ')';
      opacity = clamp01(e * 1.4);
      filter = 'blur(' + ((1 - e) * 22).toFixed(2) + 'px)';
    }
  }
  // exit
  if (pout > 0) {
    if (tout === 'circle') clip = 'circle(' + ((1 - pout) * 2250).toFixed(1) + 'px at ' + cx + 'px ' + cy + 'px)';
    if (tout === 'square') {
      const q = 1 - pout;
      const hw = 30 + q * 1100, hh = 30 + q * 1600;
      clip = 'inset(' + Math.max(0, cy - hh) + 'px ' + Math.max(0, 1080 - cx - hw) + 'px ' + Math.max(0, 1920 - cy - hh) + 'px ' + Math.max(0, cx - hw) + 'px round ' + (60 * pout).toFixed(1) + 'px)';
    }
    if (tout === 'push') transform += ' translateY(' + (-EASE_IN(pout) * 1920).toFixed(1) + 'px)';
    if (tout === 'zoomBlur') {
      transform += ' scale(' + (1 + 0.3 * EASE_IN(pout)).toFixed(4) + ')';
      opacity = 1 - EASE_IN(pout);
      filter = 'blur(' + (EASE_IN(pout) * 24).toFixed(2) + 'px)';
    }
  }
  const flashIn = tin === 'flash' ? 1 - prog(f, 0, 7, EASE_OUT) : 0;
  const flashOut = tout === 'flash' ? prog(f, len - 3, 3, EASE_IN) : 0;
  return (
    <AbsoluteFill style={{clipPath: clip, transform: transform || undefined, opacity, filter}}>
      {children}
      {flashIn > 0 || flashOut > 0 ? <AbsoluteFill style={{background: '#fff', opacity: Math.max(flashIn, flashOut) * 0.85}} /> : null}
    </AbsoluteFill>
  );
};
