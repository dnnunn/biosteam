"use client";
import React, { useMemo, useState } from 'react';
import type { Edge, Node } from 'reactflow';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useGraphStore } from '@/state/graphStore';
import { FEForm, SeedForm, ProductionForm, CellSepForm, DSP01SPTFFForm, DSP02Form, DSP03UFDFUFForm, DSP04Form, SprayForm, MixTankForm, PumpForm, HoldingTankForm, AEXMembraneForm } from '@/components/UnitLibrary';

export function Inspector() {
  const { selectedNodes, nodes: nodesAll, edges: edgesAll, pendingAdd } = useGraphStore((s) => ({
    selectedNodes: s.selectedNodes,
    nodes: s.nodes,
    edges: s.edges,
    pendingAdd: s.pendingAdd,
  }));

  const topoIndex = computeTopoIndex(nodesAll, edgesAll);
  const selectedSorted = [...(selectedNodes || [])].sort((a, b) => compareByTopoAndPosition(a, b, topoIndex));
  const { data: buffers } = useQuery({ queryKey: ['buffers'], queryFn: () => api.listBuffers() });
  const bufferOptions = buffers || [];

  const showEmpty = (!pendingAdd && (!selectedNodes || selectedNodes.length === 0));

  const panels = selectedSorted.map((n) => (
    <details key={n.id} open style={{ marginBottom: 8 }}>
      <summary style={{ cursor: 'pointer' }}>{labelOf(n)}</summary>
      <NodePanel node={n} bufferOptions={bufferOptions} />
    </details>
  ));

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Inspector</h3>
      {pendingAdd && <AddPanel />}
      {showEmpty ? <p>Select a node, or click a palette item to configure and add.</p> : panels}
    </div>
  );
}

function labelOf(n: Node) {
  const lbl = (n.data as any)?.label;
  return typeof lbl === 'string' ? lbl : 'Unit';
}

function buildSeedCond(seed: any, vol?: number) {
  const inoc = typeof seed?.inoculum_fraction === 'number' ? (seed.inoculum_fraction * 100).toFixed(1) + '%' : '—';
  const vtxt = (typeof vol === 'number' && isFinite(vol)) ? `${vol.toFixed(2)} m³` : '—';
  const media = seed?.media_type;
  const carbon = seed?.carbon_source;
  const temp = typeof seed?.temperature_c === 'number' ? `${seed.temperature_c} °C` : undefined;
  const parts: string[] = [];
  if (media || carbon) parts.push(`Media: ${media ?? '—'}, Carbon: ${carbon ?? '—'}`);
  parts.push(`Inoc ${inoc}`);
  parts.push(`Vol ${vtxt}`);
  if (temp) parts.push(`Temp ${temp}`);
  return parts.join(' · ');
}

function compareByTopoAndPosition(a: Node, b: Node, topoIndex: Map<string, number>) {
  const ai = topoIndex.get(a.id);
  const bi = topoIndex.get(b.id);
  if (ai != null && bi != null && ai !== bi) return ai - bi;
  if (ai != null && bi == null) return -1;
  if (ai == null && bi != null) return 1;
  const ax = a.position?.x ?? 0;
  const bx = b.position?.x ?? 0;
  if (ax !== bx) return ax - bx;
  const ay = a.position?.y ?? 0;
  const by = b.position?.y ?? 0;
  if (ay !== by) return ay - by;
  return a.id.localeCompare(b.id);
}

function computeTopoIndex(nodes: Node[], edges: Edge[]) {
  const nodeIds = new Set(nodes.map((n) => n.id));
  const indeg = new Map<string, number>();
  const out = new Map<string, string[]>();
  for (const n of nodes) {
    indeg.set(n.id, 0);
    out.set(n.id, []);
  }
  for (const e of edges) {
    if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) continue;
    indeg.set(e.target, (indeg.get(e.target) || 0) + 1);
    out.get(e.source)!.push(e.target);
  }
  const q: string[] = nodes
    .filter((n) => (indeg.get(n.id) || 0) === 0)
    .sort((a, b) => (a.position?.x ?? 0) - (b.position?.x ?? 0))
    .map((n) => n.id);
  const order = new Map<string, number>();
  let i = 0;
  while (q.length) {
    const id = q.shift()!;
    if (order.has(id)) continue;
    order.set(id, i++);
    for (const t of out.get(id) || []) {
      indeg.set(t, (indeg.get(t) || 0) - 1);
      if ((indeg.get(t) || 0) === 0) q.push(t);
    }
  }
  return order;
}

function AddPanel() {
  const { pendingAdd, closeAddModal, addNode, setNodeData, alignBelowCentered } = useGraphStore((s) => ({
    pendingAdd: s.pendingAdd,
    closeAddModal: s.closeAddModal,
    addNode: s.addNode,
    setNodeData: s.setNodeData,
    alignBelowCentered: s.alignBelowCentered,
  }));
  const { data: buffers } = useQuery({ queryKey: ['buffers'], queryFn: () => api.listBuffers() });
  const bufferOptions = buffers || [];
  if (!pendingAdd) return null;
  const unit = pendingAdd.unit as any;
  const pos = pendingAdd.position;
  const onClose = () => closeAddModal();

  switch (unit.id) {
    case 'Seed1':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <SeedForm stage={1} submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Seed Stage 1', { seed: { ...vals, stage: 1 }, iconKey: 'Seed1' }, pos);
            // compute seed volume if possible
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
            setNodeData(id, { conditions: buildSeedCond(vals, vol) });
            onClose();
          }} />
        </div>
      );
    case 'Seed2':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <SeedForm stage={2} submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Seed Stage 2', { seed: { ...vals, stage: 2 }, iconKey: 'Seed2' }, pos);
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
            setNodeData(id, { conditions: buildSeedCond(vals, vol) });
            onClose();
          }} />
        </div>
      );
    case 'Seed3':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <SeedForm stage={3} submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Seed Stage 3', { seed: { ...vals, stage: 3 }, iconKey: 'Seed3' }, pos);
            let vol: number | undefined = undefined;
            try {
              const { nodes } = useGraphStore.getState();
              const ferm = nodes.find(n => (n.data as any)?.fermentation);
              const workingV = (ferm?.data as any)?.fermentation?.working_volume_m3 as number | undefined;
              if (typeof workingV === 'number' && typeof vals.inoculum_fraction === 'number') vol = workingV * vals.inoculum_fraction;
            } catch {}
            setNodeData(id, { conditions: buildSeedCond(vals, vol) });
            onClose();
          }} />
        </div>
      );
    case 'Production':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <ProductionForm submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Production', { fermentation: vals, iconKey: 'ProductionFermenter' }, pos);
            setNodeData(id, { conditions: `Media: ${vals.media_type}, Carbon: ${vals.carbon_source} · Size ${vals.fermenter_volume_m3} m³ · Working ${vals.working_volume_m3} m³ · Titre ${vals.product_titre_g_L} g/L · Temp ${vals.temperature_c} °C` });
            // Try to update seed nodes' condition strings with computed volumes
            try {
              const { nodes } = useGraphStore.getState();
              const workingV = vals.working_volume_m3;
              const seeds = nodes.filter(n => (n.data as any)?.seed);
              const seed3 = seeds.find(n => (n.data as any).seed?.stage === 3);
              const seed2 = seeds.find(n => (n.data as any).seed?.stage === 2);
              const seed1 = seeds.find(n => (n.data as any).seed?.stage === 1);
              const frac3 = (seed3?.data as any)?.seed?.inoculum_fraction as number | undefined;
              const frac2 = (seed2?.data as any)?.seed?.inoculum_fraction as number | undefined;
              const frac1 = (seed1?.data as any)?.seed?.inoculum_fraction as number | undefined;
              const v3 = (typeof workingV === 'number' && typeof frac3 === 'number') ? workingV * frac3 : undefined;
              const v2 = (typeof v3 === 'number' && typeof frac2 === 'number') ? v3 * frac2 : undefined;
              const v1 = (typeof v2 === 'number' && typeof frac1 === 'number') ? v2 * frac1 : undefined;
              if (seed3) setNodeData(seed3.id, { ...((seed3.data as any) || {}), conditions: buildSeedCond((seed3.data as any).seed, v3) });
              if (seed2) setNodeData(seed2.id, { ...((seed2.data as any) || {}), conditions: buildSeedCond((seed2.data as any).seed, v2) });
              if (seed1) setNodeData(seed1.id, { ...((seed1.data as any) || {}), conditions: buildSeedCond((seed1.data as any).seed, v1) });
            } catch {}
            onClose();
          }} />
        </div>
      );
    case 'CellSeparation':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <CellSepForm submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Cell Separation', { cell_removal: vals, iconKey: 'Diskstack' }, pos);
            const odTxt = typeof (vals as any)?.od600_target === 'number' ? ` · OD ${(vals as any).od600_target}` : '';
            setNodeData(id, { conditions: `Route: ${vals.method}${vals.membranes_required ? ' · +Polish' : ''}${odTxt}` });
            if (vals.membranes_required) {
              const offsetPos = pos ? { x: pos.x, y: pos.y + 120 } : undefined;
              const id2 = addNode('MF Polishing', { iconKey: 'MF Polishing' }, offsetPos);
              setNodeData(id2, { conditions: `Route: ${vals.method} · +Polish${odTxt}` });
              alignBelowCentered(id, id2, 24);
            }
            onClose();
          }} />
        </div>
      );
    case 'DSP01':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <DSP01SPTFFForm submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('SPTFF', { concentration: { route: 'sptff', sptff: vals }, iconKey: 'UF' }, pos);
            setNodeData(id, { iconKey: 'UF', conditions: `CF ${vals.concentration_factor}× · ${vals.flux_lmh} LMH` });
            onClose();
          }} />
        </div>
      );
    
    case 'DSP02':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <DSP02Form submitLabel="Add to graph" buffers={bufferOptions} onAdd={(vals) => {
            const id = addNode('Chromatography', { dsp02: vals, iconKey: 'Chromatography' }, pos);
            setNodeData(id, { conditions: `Load I=${vals.load_ionic_strength_mM} mM · Wash I=${vals.wash_ionic_strength_mM} · Elute I=${vals.elute_ionic_strength_mM}` });
            onClose();
          }} />
        </div>
      );
    case 'DSP03':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <DSP03UFDFUFForm submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('UF → DF → UF', { dsp03_params: vals, iconKey: 'TFF' }, pos);
            setNodeData(id, { iconKey: 'TFF', conditions: `VRR ${vals.vr_preuf}× · ND ${vals.nd} · ${vals.flux_lmh} LMH` });
            onClose();
          }} />
        </div>
      );
    case 'DSP04':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <DSP04Form submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Sterile Filtration', { sterile: vals, iconKey: 'SterileFiltration' }, pos);
            setNodeData(id, { conditions: `${vals.filter_area_m2} m²` });
            onClose();
          }} />
        </div>
      );
    case 'AEXMembrane':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          {(() => {
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
                const id = addNode('AEX Membrane (FT)', { aex_membrane: vals, iconKey: 'AEXMembrane' }, pos);
                const placeTxt = vals.placement === 'in_dsp04' ? 'DSP04' : (vals.placement === 'after_sptff' ? 'Post‑SPTFF' : 'Pre‑SPTFF');
                setNodeData(id, { conditions: `${placeTxt} · t=${vals.t_window_h} h · MV ${vals.MV_per_min}/min` });
                onClose();
              }} />
            );
          })()}
        </div>
      );
    case 'SprayDryer':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <SprayForm submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Spray Dryer', { spray: vals, iconKey: 'SprayDryer' }, pos);
            setNodeData(id, { conditions: `Outlet ${vals.outlet_temp_c} °C` });
            onClose();
          }} />
        </div>
      );
    case 'MFPolish':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <button onClick={() => { const id = addNode('MF Polishing', { iconKey: 'MF Polishing' }, pos); setNodeData(id, {}); onClose(); }}>Add to graph</button>
        </div>
      );
    case 'Chitosan':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <button onClick={() => { const id = addNode('Chitosan Flocculation', { iconKey: 'Chitosan' }, pos); setNodeData(id, {}); onClose(); }}>Add to graph</button>
        </div>
      );
    case 'HoldingTank':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <HoldingTankForm submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Holding Tank', { iconKey: 'HoldingTank' }, pos);
            setNodeData(id, { label: vals.label || 'Holding Tank', holding_tank: vals, conditions: `Capacity ${vals.capacity_m3.toFixed(2)} m³` });
            onClose();
          }} />
        </div>
      );
    case 'MixTank':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <MixTankForm submitLabel="Add to graph" onAdd={(vals) => {
            const autoLabel = vals.label && vals.label.trim().length ? vals.label : (vals.mode === 'carbon' ? (() => {
              const ferm = useGraphStore.getState().nodes.find(n => (n.data as any)?.fermentation);
              const carb = (ferm?.data as any)?.fermentation?.carbon_source as string | undefined;
              return `${(carb || 'Carbon').replace(/^./, c=>c.toUpperCase())} Feed Tank`;
            })() : 'Mixing Tank');
            const id = addNode('Mixing Tank', { iconKey: 'MixTank', mixing_tank: { ...vals, label: autoLabel } }, pos);
            setNodeData(id, { label: autoLabel, conditions: `Capacity ${vals.capacity_m3.toFixed(2)} m³ (${vals.mode})` });
            onClose();
          }} />
        </div>
      );
    case 'Pump':
      return (
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ margin: 0 }}>Add: {unit.label}</h4>
          <PumpForm submitLabel="Add to graph" onAdd={(vals) => {
            const id = addNode('Pump', { iconKey: 'Pump', pump: vals }, pos);
            setNodeData(id, { conditions: `${vals.flow_m3_h} m³/h · ${vals.head_m} m · ${vals.power_kW.toFixed(2)} kW` });
            onClose();
          }} />
        </div>
      );
    default:
      return null;
  }
}

function NodePanel({ node, bufferOptions }: { node: Node; bufferOptions: any[] }) {
  const setNodeData = useGraphStore((s) => s.setNodeData);
  const data: any = node.data || {};
  const kind = classify(node);
  switch (kind) {
    case 'seed':
      return (
        <SeedForm stage={data.seed?.stage as any}
          initial={data.seed}
          submitLabel="Apply"
          onAdd={(vals) => {
            // Compute derived volume when possible
            let vol: number | undefined = undefined;
            try {
              const st = (data.seed?.stage ?? undefined) as number | undefined;
              const { nodes } = useGraphStore.getState();
              const ferm = nodes.find(n => (n.data as any)?.fermentation);
              const workingV = (ferm?.data as any)?.fermentation?.working_volume_m3 as number | undefined;
              if (st === 3 && typeof workingV === 'number' && typeof vals.inoculum_fraction === 'number') {
                vol = workingV * vals.inoculum_fraction;
              } else if (st === 2) {
                const s3 = nodes.find(n => (n.data as any)?.seed?.stage === 3);
                const s3frac = (s3?.data as any)?.seed?.inoculum_fraction as number | undefined;
                const v3 = (typeof workingV === 'number' && typeof s3frac === 'number') ? workingV * s3frac : undefined;
                if (typeof v3 === 'number' && typeof vals.inoculum_fraction === 'number') vol = v3 * vals.inoculum_fraction;
              } else if (st === 1) {
                const s3 = nodes.find(n => (n.data as any)?.seed?.stage === 3);
                const s2 = nodes.find(n => (n.data as any)?.seed?.stage === 2);
                const s3frac = (s3?.data as any)?.seed?.inoculum_fraction as number | undefined;
                const s2frac = (s2?.data as any)?.seed?.inoculum_fraction as number | undefined;
                const v3 = (typeof workingV === 'number' && typeof s3frac === 'number') ? workingV * s3frac : undefined;
                const v2 = (typeof v3 === 'number' && typeof s2frac === 'number') ? v3 * s2frac : undefined;
                if (typeof v2 === 'number' && typeof vals.inoculum_fraction === 'number') vol = v2 * vals.inoculum_fraction;
              }
            } catch {}
            setNodeData(node.id, { seed: { ...vals, stage: (data.seed?.stage ?? undefined) }, conditions: buildSeedCond({ ...vals }, vol) });
          }}
        />
      );
    case 'production':
      return (
        <ProductionForm
          initial={data.fermentation}
          submitLabel="Apply"
          onAdd={(vals) => {
            setNodeData(node.id, { fermentation: vals, conditions: `Media: ${vals.media_type}, Carbon: ${vals.carbon_source} · Size ${vals.fermenter_volume_m3} m³ · Working ${vals.working_volume_m3} m³ · Titre ${vals.product_titre_g_L} g/L · Temp ${vals.temperature_c} °C` });
            // Update seed nodes if present
            try {
              const { nodes } = useGraphStore.getState();
              const workingV = vals.working_volume_m3;
              const seeds = nodes.filter(n => (n.data as any)?.seed);
              const seed3 = seeds.find(n => (n.data as any).seed?.stage === 3);
              const seed2 = seeds.find(n => (n.data as any).seed?.stage === 2);
              const seed1 = seeds.find(n => (n.data as any).seed?.stage === 1);
              const frac3 = (seed3?.data as any)?.seed?.inoculum_fraction as number | undefined;
              const frac2 = (seed2?.data as any)?.seed?.inoculum_fraction as number | undefined;
              const frac1 = (seed1?.data as any)?.seed?.inoculum_fraction as number | undefined;
              const v3 = (typeof workingV === 'number' && typeof frac3 === 'number') ? workingV * frac3 : undefined;
              const v2 = (typeof v3 === 'number' && typeof frac2 === 'number') ? v3 * frac2 : undefined;
              const v1 = (typeof v2 === 'number' && typeof frac1 === 'number') ? v2 * frac1 : undefined;
              if (seed3) setNodeData(seed3.id, { ...((seed3.data as any) || {}), conditions: buildSeedCond((seed3.data as any).seed, v3) });
              if (seed2) setNodeData(seed2.id, { ...((seed2.data as any) || {}), conditions: buildSeedCond((seed2.data as any).seed, v2) });
              if (seed1) setNodeData(seed1.id, { ...((seed1.data as any) || {}), conditions: buildSeedCond((seed1.data as any).seed, v1) });
            } catch {}
          }}
        />
      );
    case 'cell':
      return (
        <CellSepForm
          initial={data.cell_removal}
          submitLabel="Apply"
          onAdd={(vals) => setNodeData(node.id, { cell_removal: vals, conditions: `Route: ${vals.method}${vals.membranes_required ? ' · +Polish' : ''}` })}
        />
      );
    case 'dsp01':
      return (
        <DSP01SPTFFForm
          initial={(data.concentration as any)?.sptff}
          submitLabel="Apply"
          onAdd={(vals) => setNodeData(node.id, { concentration: { route: 'sptff', sptff: vals }, conditions: `CF ${vals.concentration_factor}× · ${vals.flux_lmh} LMH` })}
        />
      );
    case 'dsp_conc':
      return (
        <div style={{ color: '#666' }}>No editable parameters for this unit.</div>
      );
    case 'dsp02':
      return (
        <DSP02Form
          buffers={bufferOptions}
          initial={data.dsp02}
          submitLabel="Apply"
          onAdd={(vals) => setNodeData(node.id, { dsp02: vals, conditions: `Load I=${vals.load_ionic_strength_mM} mM · Wash I=${vals.wash_ionic_strength_mM} · Elute I=${vals.elute_ionic_strength_mM}` })}
        />
      );
    case 'dsp03':
      return (
        <DSP03UFDFUFForm
          initial={(data as any).dsp03_params}
          submitLabel="Apply"
          onAdd={(vals) => setNodeData(node.id, { dsp03_params: vals, conditions: `VRR ${vals.vr_preuf}× · ND ${vals.nd} · ${vals.flux_lmh} LMH` })}
        />
      );
    case 'dsp04':
      return (
        <DSP04Form
          initial={data.sterile}
          submitLabel="Apply"
          onAdd={(vals) => setNodeData(node.id, { sterile: vals, conditions: `${vals.filter_area_m2} m²` })}
        />
      );
    case 'aex_mem':
      return (
        <AEXMembraneForm
          contextNodeId={node.id}
          initial={data.aex_membrane}
          submitLabel="Apply"
          onAdd={(vals) => {
            const placeTxt = vals.placement === 'in_dsp04' ? 'DSP04' : (vals.placement === 'after_sptff' ? 'Post‑SPTFF' : 'Pre‑SPTFF');
            setNodeData(node.id, { aex_membrane: vals, conditions: `${placeTxt} · t=${vals.t_window_h} h · MV ${vals.MV_per_min}/min` });
          }}
        />
      );
    case 'spray':
      return (
        <SprayForm
          initial={data.spray}
          submitLabel="Apply"
          onAdd={(vals) => setNodeData(node.id, { spray: vals, conditions: `Outlet ${vals.outlet_temp_c} °C` })}
        />
      );
    case 'mix':
      return (
        <MixTankForm
          contextNodeId={node.id}
          initial={data.mixing_tank}
          submitLabel="Apply"
          onAdd={(vals) => {
            const autoLabel = vals.label && vals.label.trim().length ? vals.label : (vals.mode === 'carbon' ? (() => {
              const ferm = useGraphStore.getState().nodes.find(n => (n.data as any)?.fermentation);
              const carb = (ferm?.data as any)?.fermentation?.carbon_source as string | undefined;
              return `${(carb || 'Carbon').replace(/^./, c=>c.toUpperCase())} Feed Tank`;
            })() : 'Mixing Tank');
            setNodeData(node.id, { mixing_tank: { ...vals, label: autoLabel }, conditions: `Capacity ${vals.capacity_m3.toFixed(2)} m³ (${vals.mode})`, label: autoLabel });
          }}
        />
      );
    case 'pump':
      return (
        <PumpForm
          initial={data.pump}
          submitLabel="Apply"
          onAdd={(vals) => setNodeData(node.id, { pump: vals, conditions: `${vals.flow_m3_h} m³/h · ${vals.head_m} m · ${vals.power_kW.toFixed(2)} kW` })}
        />
      );
    default:
      return <div style={{ color: '#666' }}>No editable parameters for this unit.</div>;
  }
}

function classify(node: Node): 'seed' | 'production' | 'cell' | 'dsp01' | 'dsp02' | 'dsp03' | 'dsp04' | 'dsp_conc' | 'aex_mem' | 'spray' | 'mix' | 'pump' | 'generic' {
  const d: any = node.data || {};
  if (d.seed) return 'seed';
  if (d.fermentation) return 'production';
  if (d.cell_removal) return 'cell';
  if ((d.concentration && ((d.concentration as any).route === 'sptff' || (d as any).concentration?.sptff)) || d.dsp01) return 'dsp01';
  if (d.dsp02) return 'dsp02';
  if (d.dsp03_params) return 'dsp03';
  if (d.sterile) return 'dsp04';
  if (d.aex_membrane) return 'aex_mem';
  if (d.concentration) return 'dsp_conc';
  if (d.spray) return 'spray';
  if (d.mixing_tank) return 'mix';
  if (d.pump) return 'pump';
  return 'generic';
}

function DSP03Panel({ node }: { node: Node }) {
  const setNodeData = useGraphStore((s) => s.setNodeData);
  const dsp03Data = useMemo(() => ((node.data as any)?.dsp03 ?? {}), [node]);
  const topLevelBuffer = (node.data as any)?.cost_buffer_id as string | undefined;
  const [bufferId, setBufferId] = useState<string | undefined>(topLevelBuffer ?? (dsp03Data?.cost_buffer_id as string | undefined));
  const effectiveId = bufferId ?? topLevelBuffer ?? (dsp03Data?.cost_buffer_id as string | undefined);
  const { data: recs } = useQuery({
    queryKey: ['buffer_rec', effectiveId],
    queryFn: () => (effectiveId ? api.bufferRecommendations(effectiveId) : Promise.resolve(undefined)),
    enabled: !!effectiveId,
  });

  return (
    <div>
      <label>DSP03 Buffer ID</label>
      <input
        value={bufferId ?? ''}
        onChange={(e) => setBufferId(e.target.value)}
        placeholder="e.g. tris_hcl_pH7p5_50mM"
        style={{ width: '100%', padding: 6, marginTop: 4 }}
      />
      <button
        style={{ marginTop: 8 }}
        onClick={() => {
          if (!bufferId) return;
          setNodeData(node.id, { label: `DSP03 · ${bufferId}`, underline_label: false, dsp03: { ...dsp03Data, cost_buffer_id: bufferId } });
        }}
      >
        Apply Buffer
      </button>

      <div style={{ borderTop: '1px solid #eee', paddingTop: 8, marginTop: 8 }}>
        <button
          disabled={!effectiveId}
          onClick={() => effectiveId && setNodeData(node.id, {
            underline_label: true,
            label: `DSP03 · ${effectiveId}`,
            dsp03: {
              ...dsp03Data,
              use_planner: true,
              auto_plan: true,
              target_ionic_strength_mM: recs?.recommended_target_ionic_strength_mM,
              df_time_h_target: recs?.recommended_df_time_h,
              headroom_fraction: recs?.recommended_headroom_fraction,
              cost_from_registry: true,
              cost_buffer_id: effectiveId,
            }
          })}
        >
          Apply Recommendations
        </button>
        {recs && (
          <ul style={{ color: '#666' }}>
            <li>Target I: {recs.recommended_target_ionic_strength_mM}</li>
            <li>Target κ: {recs.recommended_target_conductivity_mScm} mS/cm</li>
            <li>DF time: {recs.recommended_df_time_h} h, headroom: {recs.recommended_headroom_fraction}</li>
          </ul>
        )}
      </div>

      <div style={{ borderTop: '1px solid #eee', paddingTop: 8, marginTop: 8 }}>
        <details>
          <summary>Current overrides</summary>
          <pre style={{ background:'#f7f7f7', padding:8, overflow:'auto' }}>
{JSON.stringify(dsp03Data, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  );
}
