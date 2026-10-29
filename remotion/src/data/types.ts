import React from 'react';
import {Trans} from '../components/SceneWrap';
export type FSDef = {
  id: string;
  from: number;
  to: number;
  Comp: React.FC;
  tin?: Trans;
  tout?: Trans;
  durIn?: number;
  durOut?: number;
  cx?: number;
  cy?: number;
  opaqueFrom?: number; // absolute frame from which the scene fully covers the A-roll
  opaqueUntil?: number; // absolute frame (exclusive) until which it fully covers
};
export type OSDef = {id: string; from: number; to: number; Comp: React.FC};
export type ShadeRange = {from: number; to: number; strength?: number};
