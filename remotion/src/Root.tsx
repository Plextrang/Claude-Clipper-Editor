import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {TOTAL_FRAMES} from './data/scenes';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Main" component={Main} durationInFrames={Math.max(1, TOTAL_FRAMES)} fps={30} width={1080} height={1920} />
  </>
);
