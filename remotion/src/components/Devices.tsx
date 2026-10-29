import React from 'react';
import {C, SANS} from '../theme';

/** Dark glass UI card for on-screen (over talking head) animations. */
export const GlassCard: React.FC<{w: number; h: number; x?: number; y?: number; radius?: number; glow?: number; children?: React.ReactNode; style?: React.CSSProperties}> = ({
  w,
  h,
  x,
  y,
  radius = 38,
  glow = 0,
  children,
  style,
}) => (
  <div
    style={{
      position: x !== undefined ? 'absolute' : 'relative',
      left: x,
      top: y,
      width: w,
      height: h,
      borderRadius: radius,
      background: 'linear-gradient(160deg, rgba(38,44,54,0.84) 0%, rgba(16,19,25,0.90) 100%)',
      border: '1.5px solid rgba(255,255,255,0.10)',
      boxShadow:
        '0 40px 90px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.14)' + (glow > 0 ? ', 0 0 ' + 60 * glow + 'px rgba(' + C.accentRgb + ',' + 0.28 * glow + ')' : ''),
      overflow: 'hidden',
      ...style,
    }}
  >
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(120% 60% at 20% 0%, rgba(255,255,255,0.08), transparent 60%)', pointerEvents: 'none'}} />
    {children}
  </div>
);

/** Minimal modern phone. Content fills the screen area. */
export const Phone: React.FC<{w: number; x?: number; y?: number; children?: React.ReactNode; tilt?: number; shadow?: boolean}> = ({w, x, y, children, tilt = 0, shadow = true}) => {
  const h = w * 2.06;
  const r = w * 0.16;
  const b = w * 0.035;
  return (
    <div
      style={{
        position: x !== undefined ? 'absolute' : 'relative',
        left: x,
        top: y,
        width: w,
        height: h,
        borderRadius: r,
        background: 'linear-gradient(145deg, #2b2b2e 0%, #0d0d0f 60%, #1c1c1f 100%)',
        boxShadow: shadow ? '0 50px 90px rgba(0,0,0,0.30), 0 18px 30px rgba(0,0,0,0.18), inset 0 0 0 1.5px rgba(255,255,255,0.10)' : undefined,
        transform: tilt ? 'rotate(' + tilt + 'deg)' : undefined,
      }}
    >
      <div style={{position: 'absolute', inset: b, borderRadius: r - b, overflow: 'hidden', background: '#000'}}>
        {children}
        <div style={{position: 'absolute', top: w * 0.035, left: '50%', width: w * 0.3, height: w * 0.085, transform: 'translateX(-50%)', borderRadius: 999, background: '#000'}} />
        <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(120deg, rgba(255,255,255,0.10) 0%, transparent 30%)', pointerEvents: 'none'}} />
      </div>
    </div>
  );
};

/** Small UI label row used inside glass cards. */
export const UIRow: React.FC<{label: string; value?: string; active?: boolean; p?: number}> = ({label, value, active, p = 1}) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '18px 24px',
      borderRadius: 18,
      background: active ? 'rgba(' + C.accentRgb + ',0.14)' : 'rgba(255,255,255,0.04)',
      border: '1.5px solid ' + (active ? 'rgba(' + C.accentRgb + ',0.55)' : 'rgba(255,255,255,0.06)'),
      fontFamily: SANS,
      color: C.white,
      opacity: p,
    }}
  >
    <span style={{fontSize: 30, fontWeight: 600, letterSpacing: '-0.01em'}}>{label}</span>
    {value ? <span style={{fontSize: 26, fontWeight: 700, color: active ? C.accent : 'rgba(255,255,255,0.55)'}}>{value}</span> : null}
  </div>
);
