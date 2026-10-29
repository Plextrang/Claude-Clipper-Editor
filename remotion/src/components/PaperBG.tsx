import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {C} from '../theme';
import {mix, rgbOf} from '../lib/color';

/**
 * Light paper background: white/greyish gradient + thin light grid + casted-shadow overlay + grain.
 * tone: 'white' (cool-neutral) | 'warm' (yellowish-white variant) | 'palette' (tinted to this video's footage palette:
 *   C.paper base, ink-tinted grid/shadows/vignette; use it when work/plan/palette.json is set).
 */
export const PaperBG: React.FC<{
  tone?: 'white' | 'warm' | 'palette';
  grid?: boolean;
  gridSize?: number;
  shadow?: boolean;
  shadowAngle?: number;
  drift?: number; // px of slow shadow drift over the scene
  localFrame?: number;
}> = ({tone = 'white', grid = true, gridSize = 90, shadow = true, shadowAngle = -32, drift = 40, localFrame}) => {
  const gf = useCurrentFrame();
  const f = localFrame ?? gf;
  const pal = tone === 'palette';
  const ink = pal ? rgbOf(C.ink).join(',') : '30,30,30';
  const shade = pal ? rgbOf(C.ink).join(',') : '40,36,30';
  const base =
    tone === 'palette'
      ? 'radial-gradient(120% 90% at 30% 18%, ' + mix(C.paper, '#FFFFFF', 0.45) + ' 0%, ' + C.paper + ' 55%, ' + mix(C.paper, C.accentDeep, 0.1) + ' 100%)'
      : tone === 'warm'
      ? 'radial-gradient(120% 90% at 30% 20%, #FBF8F1 0%, #F1ECE1 55%, #E4DED1 100%)'
      : 'radial-gradient(120% 90% at 30% 18%, #FAFAF8 0%, #EFEEEB 55%, #E1E0DC 100%)';
  const d = (f / 30) * (drift / 4);
  return (
    <AbsoluteFill style={{background: base, overflow: 'hidden'}}>
      {grid ? (
        <AbsoluteFill
          style={{
            backgroundImage:
              'linear-gradient(to right, rgba(' + ink + ',0.055) 1px, transparent 1px), linear-gradient(to bottom, rgba(' + ink + ',0.055) 1px, transparent 1px)',
            backgroundSize: gridSize + 'px ' + gridSize + 'px',
            backgroundPosition: '-1px -1px',
            maskImage: 'radial-gradient(90% 75% at 50% 45%, black 40%, transparent 100%)',
            WebkitMaskImage: 'radial-gradient(90% 75% at 50% 45%, black 40%, transparent 100%)',
          }}
        />
      ) : null}
      {shadow ? (
        // Casted window-light shadow: soft diagonal mullion bars + a leafy blob, heavily blurred, very light.
        <AbsoluteFill style={{transform: 'translate(' + d + 'px,' + d * 0.4 + 'px) rotate(' + shadowAngle + 'deg) scale(1.6)', opacity: 0.9}}>
          <div style={{position: 'absolute', left: '8%', top: '-20%', width: 120, height: '150%', background: 'rgba(' + shade + ',0.10)', filter: 'blur(38px)'}} />
          <div style={{position: 'absolute', left: '34%', top: '-20%', width: 64, height: '150%', background: 'rgba(' + shade + ',0.08)', filter: 'blur(30px)'}} />
          <div style={{position: 'absolute', left: '72%', top: '-20%', width: 180, height: '150%', background: 'rgba(' + shade + ',0.09)', filter: 'blur(46px)'}} />
          <div style={{position: 'absolute', left: '-10%', top: '62%', width: '130%', height: 60, background: 'rgba(' + shade + ',0.07)', filter: 'blur(34px)'}} />
        </AbsoluteFill>
      ) : null}
      {/* Grain */}
      <AbsoluteFill style={{opacity: 0.22, mixBlendMode: 'multiply'}}>
        <svg width="100%" height="100%">
          <filter id={'grain' + (Math.floor(f / 2) % 6)}>
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={Math.floor(f / 2) % 6} stitchTiles="stitch" />
            <feColorMatrix type="matrix" values="0 0 0 0 0.45  0 0 0 0 0.43  0 0 0 0 0.40  0 0 0 0.55 0" />
          </filter>
          <rect width="100%" height="100%" filter={'url(#grain' + (Math.floor(f / 2) % 6) + ')'} />
        </svg>
      </AbsoluteFill>
      {/* Vignette */}
      <AbsoluteFill style={{background: 'radial-gradient(110% 80% at 50% 45%, transparent 55%, rgba(' + (pal ? shade : '60,55,45') + ',0.16) 100%)'}} />
    </AbsoluteFill>
  );
};
