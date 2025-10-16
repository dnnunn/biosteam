"use client";
import * as React from 'react';
import ChromatographyIcon from '@/icons/chromatography.svg';
import TffIcon from '@/icons/tff.svg';
import UfIcon from '@/icons/uf.svg';
import TankIcon from '@/icons/tank.svg';
import MixTankIcon from '@/icons/mixing_tank.svg';
import PumpIcon from '@/icons/pump.svg';
import DffIcon from '@/icons/dff.svg';
import DiskstackIcon from '@/icons/diskstack.svg';
import FlocculationIcon from '@/icons/flocculation.svg';
import MfPolishingIcon from '@/icons/mf_polishing.svg';
import SprayDryerIcon from '@/icons/spraydryer.svg';
import SterileFiltrationIcon from '@/icons/sterile_filtration.svg';
import AexFilterIcon from '@/icons/aex_filter.svg';
import ProductionFermenterIcon from '@/icons/production_fermenter.svg';
import Seed1Icon from '@/icons/seed_fermenter_1.svg';
import Seed23Icon from '@/icons/seed_fermenter_2_3.svg';

export type UnitIconCmp = React.ComponentType<React.SVGProps<SVGSVGElement>>;

const FALLBACK_ICON: UnitIconCmp = TankIcon;

// Map common unit names/ids to icons. Extend as more SVGs arrive.
const ICONS_BY_KEY: Record<string, UnitIconCmp> = {
  // Front end / seed/fermenter placeholder
  front_end: ProductionFermenterIcon,
  'Front-End': ProductionFermenterIcon,
  ProductionFermenter: ProductionFermenterIcon,
  'Production Fermenter': ProductionFermenterIcon,
  Seed1: Seed1Icon,
  'Seed Fermenter 1': Seed1Icon,
  Seed23: Seed23Icon,
  'Seed Fermenter 2/3': Seed23Icon,
  // Map separate stages 2 and 3 to same icon for now
  Seed2: Seed23Icon,
  'Seed Stage 2': Seed23Icon,
  Seed3: Seed23Icon,
  'Seed Stage 3': Seed23Icon,
  // TFF/UF family
  DSP03: TffIcon,
  TFF: TffIcon,
  UF: UfIcon,
  // Chromatography
  Chromatography: ChromatographyIcon,
  DSP02: ChromatographyIcon,
  // Clarification / pre-treatment
  DFF: DffIcon,
  'DF/Mix': DffIcon,
  Diskstack: DiskstackIcon,
  'Cell Separation': DiskstackIcon,
  Flocculation: FlocculationIcon,
  Chitosan: FlocculationIcon,
  'Chitosan Flocculation': FlocculationIcon,
  'MF Polishing': MfPolishingIcon,
  MF_Polishing: MfPolishingIcon,
  // AEX membrane FT
  AEXMembrane: AexFilterIcon,
  'AEX Membrane (FT)': AexFilterIcon,
  // Sterile / terminal
  'Sterile Filtration': SterileFiltrationIcon,
  SterileFiltration: SterileFiltrationIcon,
  SprayDryer: SprayDryerIcon,
  'Spray Dryer': SprayDryerIcon,
  // Tanks / pumps
  HoldingTank: TankIcon,
  'Holding Tank': TankIcon,
  MixTank: MixTankIcon,
  'Mixing Tank': MixTankIcon,
  Pump: PumpIcon,
};

export function getUnitIcon(key?: string): UnitIconCmp {
  if (!key) return FALLBACK_ICON;
  if (ICONS_BY_KEY[key]) return ICONS_BY_KEY[key];
  // Try a normalized fallback: lowercase, strip spaces/underscores
  const norm = key.toLowerCase().replace(/\s+/g, '_');
  if (ICONS_BY_KEY[norm]) return ICONS_BY_KEY[norm];
  return FALLBACK_ICON;
}
