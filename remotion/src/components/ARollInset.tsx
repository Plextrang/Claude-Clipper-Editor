import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile} from 'remotion';

/**
 * The speaker's live A-roll rendered inside any container (phone screen, polaroid, circle, card).
 * Must be told the ABSOLUTE frame where the enclosing <Sequence> starts (`seqFrom`) so the picture stays
 * lip-synced with the voice. `scale` zooms about (fx, fy) in source pixels (face ~ 540,560).
 * The container decides size; the video is drawn as a 1080x1920 plane fitted to `fit` and then zoomed.
 */
export const ARollInset: React.FC<{
  seqFrom: number;
  scale?: number;
  fx?: number;
  fy?: number;
  width: number; // container width in px
  height: number; // container height in px
  filter?: string;
}> = ({seqFrom, scale = 1, fx = 540, fy = 560, width, height, filter}) => {
  // cover-fit the 1080x1920 source into the container
  const k = Math.max(width / 1080, height / 1920) * scale;
  const vw = 1080 * k;
  const vh = 1920 * k;
  // keep the focus point centred in the container
  let left = width / 2 - fx * k;
  let top = height / 2 - fy * k;
  left = Math.min(0, Math.max(width - vw, left));
  top = Math.min(0, Math.max(height - vh, top));
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <div style={{position: 'absolute', left, top, width: vw, height: vh, filter}}>
        <OffthreadVideo src={staticFile('aroll.mp4')} trimBefore={seqFrom} muted style={{width: '100%', height: '100%'}} />
      </div>
    </AbsoluteFill>
  );
};
