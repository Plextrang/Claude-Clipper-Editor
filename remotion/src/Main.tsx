import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from 'remotion';
import {ARoll, BlurBand, LogoVeil, bandAt} from './components/ARoll';
import {Captions, LowerShade} from './components/Captions';
import {SceneWrap} from './components/SceneWrap';
import {CAMERA, CAPTIONS, FLASHES, JUMP_CUTS, LOGO, SHADE} from './data/edit';
import {FULLSCREEN, ONSCREEN} from './data/scenes';
import {EASE_IN, EASE_OUT, clamp01} from './lib/anim';

// A-roll decoding is skipped while a full-screen scene fully covers the frame.
const coveredByFullscreen = (f: number) => FULLSCREEN.some((s) => f >= (s.opaqueFrom ?? s.from) && f < (s.opaqueUntil ?? s.to));

const Shade: React.FC = () => {
  const f = useCurrentFrame();
  const b = bandAt(SHADE, f);
  if (!b) return null;
  return <LowerShade strength={b.a} top={b.r.top ?? 840} dark={b.r.dark ?? 1} />;
};

const Flash: React.FC = () => {
  const f = useCurrentFrame();
  let o = 0;
  for (const fl of FLASHES) {
    if (f >= fl.peak - fl.up && f <= fl.peak) o = Math.max(o, EASE_IN(clamp01((f - (fl.peak - fl.up)) / fl.up)) * fl.max);
    if (f > fl.peak && f <= fl.peak + fl.down) o = Math.max(o, (1 - EASE_OUT(clamp01((f - fl.peak) / fl.down))) * fl.max);
  }
  if (o <= 0.001) return null;
  return <AbsoluteFill style={{background: '#FFFFFF', opacity: o}} />;
};

export const Main: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    <ARoll keys={CAMERA} hidden={coveredByFullscreen} />
    <BlurBand keys={CAMERA} ranges={SHADE} />
    <LogoVeil logo={LOGO} keys={CAMERA} ranges={SHADE} hidden={coveredByFullscreen} />
    <Shade />
    {ONSCREEN.map((o) => (
      <Sequence key={o.id} from={o.from} durationInFrames={o.to - o.from} name={o.id}>
        <o.Comp />
      </Sequence>
    ))}
    {FULLSCREEN.map((s) => (
      <Sequence key={s.id} from={s.from} durationInFrames={s.to - s.from} name={s.id}>
        <SceneWrap len={s.to - s.from} tin={s.tin} tout={s.tout} durIn={s.durIn} durOut={s.durOut} cx={s.cx} cy={s.cy}>
          <s.Comp />
        </SceneWrap>
      </Sequence>
    ))}
    <Captions groups={CAPTIONS} cutFrames={[...FULLSCREEN.map((x) => x.from), ...JUMP_CUTS]} />
    <Flash />
  </AbsoluteFill>
);
