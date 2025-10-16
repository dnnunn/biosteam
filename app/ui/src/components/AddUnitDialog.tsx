"use client";
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useGraphStore } from '@/state/graphStore';
import type { UnitDef } from '@/components/UnitLibrary';
import { SeedForm, ProductionForm, CellSepForm, DSP01SPTFFForm, DSP02Form, DSP03UFDFUFForm, DSP04Form, SprayForm, HoldingTankForm, MixTankForm, AEXMembraneForm } from '@/components/UnitLibrary';

export function AddUnitDialog() {
  const pending = useGraphStore((s) => s.pendingAdd);
  const close = useGraphStore((s) => s.closeAddModal);
  const addNode = useGraphStore((s) => s.addNode);
  const setNodeData = useGraphStore((s) => s.setNodeData);
  // helper for seed condition text
  function buildSeedCond(seed: any, vol?: number) {
    const inoc = typeof seed?.inoculum_fraction === 'number' ? (seed.inoculum_fraction * 100).toFixed(1) + '%' : '—';
    const vtxt = (typeof vol === 'number' && isFinite(vol)) ? `${vol.toFixed(2)} m³` : '—';
    const media = seed?.media_type;
    const carbon = seed?.carbon_source;
    const parts: string[] = [];
    if (media || carbon) parts.push(`Media: ${media ?? '—'}, Carbon: ${carbon ?? '—'}`);
    parts.push(`Inoc ${inoc}`);
    parts.push(`Vol ${vtxt}`);
    const temp = typeof seed?.temperature_c === 'number' ? `${seed.temperature_c} °C` : undefined;
    if (temp) parts.push(`Temp ${temp}`);
    return parts.join(' · ');
  }
  const alignBelowCentered = useGraphStore((s) => s.alignBelowCentered);

  const { data: buffers } = useQuery({ queryKey: ['buffers'], queryFn: () => api.listBuffers() });
  const bufferOptions = buffers || [];

  if (!pending) return null;
  const unit: UnitDef = pending.unit as any;

  function handleClose(e?: React.MouseEvent) {
    e?.stopPropagation();
    close();
  }

  // Map unit id to specific parameter form
  let form: React.ReactNode = null;
  switch (unit.id) {
    case 'Seed1':
      form = (
        <SeedForm stage={1} submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('Seed Stage 1', { seed: { ...vals, stage: 1 }, iconKey: 'Seed1' }, pending.position);
          let vol: number | undefined = undefined;
          try {
            const { nodes } = useGraphStore.getState();
            const ferm = nodes.find(n => (n.data as any)?.fermentation);
            const workingV = (ferm?.data as any)?.fermentation?.working_volume_m3 as number | undefined;
            const s3 = nodes.find(n => (n.data as any)?.seed?.stage === 3);
            const s2 = nodes.find(n => (n.data as any)?.seed?.stage === 2);
            const s3frac = (s3?.data as any)?.seed?.inoculum_fraction as number | undefined;
            const s2frac = (s2?.data as any)?.seed?.inoculum_fraction as number | undefined;
            const v3 = (typeof workingV === 'number' && typeof s3frac === 'number') ? workingV * s3frac : undefined;
            const v2 = (typeof v3 === 'number' && typeof s2frac === 'number') ? v3 * s2frac : undefined;
            if (typeof v2 === 'number' && typeof vals.inoculum_fraction === 'number') vol = v2 * vals.inoculum_fraction;
          } catch {}
          setNodeData(id, { conditions: buildSeedCond({ ...vals }, vol) });
          close();
        }} />
      );
      break;
    case 'Seed2':
      form = (
        <SeedForm stage={2} submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('Seed Stage 2', { seed: { ...vals, stage: 2 }, iconKey: 'Seed2' }, pending.position);
          let vol: number | undefined = undefined;
          try {
            const { nodes } = useGraphStore.getState();
            const ferm = nodes.find(n => (n.data as any)?.fermentation);
            const workingV = (ferm?.data as any)?.fermentation?.working_volume_m3 as number | undefined;
            const s3 = nodes.find(n => (n.data as any)?.seed?.stage === 3);
            const s3frac = (s3?.data as any)?.seed?.inoculum_fraction as number | undefined;
            const v3 = (typeof workingV === 'number' && typeof s3frac === 'number') ? workingV * s3frac : undefined;
            if (typeof v3 === 'number' && typeof vals.inoculum_fraction === 'number') vol = v3 * vals.inoculum_fraction;
          } catch {}
          setNodeData(id, { conditions: buildSeedCond({ ...vals }, vol) });
          close();
        }} />
      );
      break;
    case 'Seed3':
      form = (
        <SeedForm stage={3} submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('Seed Stage 3', { seed: { ...vals, stage: 3 }, iconKey: 'Seed3' }, pending.position);
          let vol: number | undefined = undefined;
          try {
            const { nodes } = useGraphStore.getState();
            const ferm = nodes.find(n => (n.data as any)?.fermentation);
            const workingV = (ferm?.data as any)?.fermentation?.working_volume_m3 as number | undefined;
            if (typeof workingV === 'number' && typeof vals.inoculum_fraction === 'number') vol = workingV * vals.inoculum_fraction;
          } catch {}
          setNodeData(id, { conditions: buildSeedCond({ ...vals }, vol) });
          close();
        }} />
      );
      break;
    case 'Production':
      form = (
        <ProductionForm submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('Production', { fermentation: vals, iconKey: 'ProductionFermenter' }, pending.position);
          setNodeData(id, { conditions: `Media: ${vals.media_type}, Carbon: ${vals.carbon_source} · Size ${vals.fermenter_volume_m3} m³ · Working ${vals.working_volume_m3} m³ · Titre ${vals.product_titre_g_L} g/L · Temp ${vals.temperature_c} °C` });
          close();
        }} />
      );
      break;
    case 'CellSeparation':
      form = (
        <CellSepForm submitLabel="Add to graph" onAdd={(vals) => {
          const pos = pending.position;
          const id = addNode('Cell Separation', { cell_removal: vals, iconKey: 'Diskstack' }, pos);
          const odTxt = typeof (vals as any)?.od600_target === 'number' ? ` · OD ${(vals as any).od600_target}` : '';
          setNodeData(id, { conditions: `Route: ${vals.method}${vals.membranes_required ? ' · +Polish' : ''}${odTxt}` });
          if (vals.membranes_required) {
            const offsetPos = pos ? { x: pos.x + 180, y: pos.y } : undefined;
            const id2 = addNode('MF Polishing', { iconKey: 'MF Polishing' }, offsetPos);
            setNodeData(id2, { conditions: `Route: ${vals.method} · +Polish${odTxt}` });
            alignBelowCentered(id, id2, 24);
          }
          close();
        }} />
      );
      break;
    case 'DSP01':
      form = (
        <DSP01SPTFFForm submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('SPTFF', { concentration: { route: 'sptff', sptff: vals }, iconKey: 'UF' }, pending.position);
          setNodeData(id, { iconKey: 'UF', conditions: `CF ${vals.concentration_factor}× · ${vals.flux_lmh} LMH` });
          close();
        }} />
      );
      break;
    case 'DSP02':
      form = (
        <DSP02Form submitLabel="Add to graph" buffers={bufferOptions} onAdd={(vals) => {
          const id = addNode('Chromatography', { dsp02: vals, iconKey: 'Chromatography' }, pending.position);
          setNodeData(id, { conditions: `Load I=${vals.load_ionic_strength_mM} mM · Wash I=${vals.wash_ionic_strength_mM} · Elute I=${vals.elute_ionic_strength_mM}` });
          close();
        }} />
      );
      break;
    
    case 'DSP03':
      form = (
        <DSP03UFDFUFForm submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('UF → DF → UF', { dsp03_params: vals, iconKey: 'TFF' }, pending.position);
          setNodeData(id, { iconKey: 'TFF', conditions: `VRR ${vals.vr_preuf}× · ND ${vals.nd} · ${vals.flux_lmh} LMH` });
          close();
        }} />
      );
      break;
    case 'DSP04':
      form = (
        <DSP04Form submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('Sterile Filtration', { sterile: vals, iconKey: 'SterileFiltration' }, pending.position);
          setNodeData(id, { conditions: `${vals.filter_area_m2} m²` });
          close();
        }} />
      );
      break;
    case 'AEXMembrane':
      form = (() => {
        const { nodes, edges, selectedNodes } = useGraphStore.getState();
        const sptffs = nodes.filter(n => !!(n.data as any)?.concentration && ((n.data as any).concentration as any).route === 'sptff');
        const selIds = (selectedNodes || []).map(n => n.id);
        const fwd = new Map<string, string[]>();
        const rev = new Map<string, string[]>();
        nodes.forEach(n => { fwd.set(n.id, []); rev.set(n.id, []); });
        edges.forEach(e => { (fwd.get(e.source) || fwd.set(e.source, []).get(e.source)!, fwd.get(e.source)!.push(e.target)); (rev.get(e.target) || rev.set(e.target, []).get(e.target)!, rev.get(e.target)!.push(e.source)); });
        const bfs = (starts: string[], adj: Map<string, string[]>) => { const seen = new Set<string>(); const q = [...starts]; starts.forEach(id=>seen.add(id)); while(q.length){ const id=q.shift()!; for(const nb of (adj.get(id)||[])){ if(!seen.has(nb)){ seen.add(nb); q.push(nb);} } } return seen; };
        let initialPlacement: 'before_sptff'|'after_sptff'|'in_dsp04' = 'in_dsp04';
        let initialVm3: number | undefined = undefined;
        if (selIds.length && sptffs.length) {
          const upOfSel = bfs(selIds, rev);
          const downOfSel = bfs(selIds, fwd);
          for (const s of sptffs) {
            if (upOfSel.has(s.id)) {
              initialPlacement = 'after_sptff';
              const conc = (s.data as any)?.concentration?.sptff; const cf = conc?.concentration_factor as number|undefined;
              if (cf && cf > 0) {
                const upOfSP = bfs([s.id], rev);
                const cands = nodes.filter(n => upOfSP.has(n.id));
                const hold = cands.find(n => (n.data as any)?.holding_tank?.capacity_m3 != null);
                const vBase = hold ? (hold.data as any).holding_tank.capacity_m3 : ((cands.find(n => (n.data as any)?.fermentation?.working_volume_m3 != null)?.data as any)?.fermentation?.working_volume_m3 as number|undefined);
                if (typeof vBase === 'number') initialVm3 = vBase / cf;
              }
              break;
            } else if (downOfSel.has(s.id)) {
              initialPlacement = 'before_sptff';
            }
          }
          if (initialPlacement === 'in_dsp04' && sptffs.length) initialPlacement = 'after_sptff';
        }
        return (
          <AEXMembraneForm initial={{ placement: initialPlacement, assumed_feed_volume_m3: initialVm3 }} submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('AEX Membrane (FT)', { aex_membrane: vals, iconKey: 'AEXMembrane' }, pending.position);
            const placeTxt = vals.placement === 'in_dsp04' ? 'DSP04' : (vals.placement === 'after_sptff' ? 'Post‑SPTFF' : 'Pre‑SPTFF');
            setNodeData(id, { conditions: `${placeTxt} · t=${vals.t_window_h} h · MV ${vals.MV_per_min}/min` });
            close();
          }} />
        );
      })();
      break;
      break;
    case 'SprayDryer':
      form = (
        <SprayForm submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('Spray Dryer', { spray: vals, iconKey: 'SprayDryer' }, pending.position);
          setNodeData(id, { conditions: `Outlet ${vals.outlet_temp_c} °C` });
          close();
        }} />
      );
      break;
    case 'HoldingTank':
      form = (
        <HoldingTankForm submitLabel="Add to graph" onAdd={(vals) => {
          const id = addNode('Holding Tank', { iconKey: 'HoldingTank' }, pending.position);
          setNodeData(id, { label: vals.label || 'Holding Tank', holding_tank: vals, conditions: `Capacity ${vals.capacity_m3.toFixed(2)} m³` });
          close();
        }} />
      );
      break;
    case 'MixTank':
      form = (
        <MixTankForm submitLabel="Add to graph" onAdd={(vals) => {
          const ferm = useGraphStore.getState().nodes.find(n => (n.data as any)?.fermentation);
          const carb = (ferm?.data as any)?.fermentation?.carbon_source as string | undefined;
          const autoLabel = vals.label && vals.label.trim().length ? vals.label : (vals.mode === 'carbon' ? `${(carb || 'Carbon').replace(/^./, c=>c.toUpperCase())} Feed Tank` : 'Mixing Tank');
          const id = addNode('Mixing Tank', { iconKey: 'MixTank', mixing_tank: { ...vals, label: autoLabel } }, pending.position);
          setNodeData(id, { label: autoLabel, conditions: `Capacity ${vals.capacity_m3.toFixed(2)} m³ (${vals.mode})` });
          close();
        }} />
      );
      break;
    default:
      form = <div style={{ color: '#666' }}>No form available for {unit.label}.</div>;
  }

  return (
    <div
      role="dialog"
      aria-modal
      onClick={handleClose}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}
    >
      <div onClick={(e) => e.stopPropagation()} style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 8, width: 520, maxWidth: '95vw', padding: 16, boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>Add: {unit.label}</h3>
          <button onClick={handleClose} aria-label="Close">✕</button>
        </div>
        <div>{form}</div>
      </div>
    </div>
  );
}
