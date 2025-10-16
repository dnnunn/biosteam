"use client";
import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Icon } from '@/components/Icon';
import { getUnitIcon } from '@/components/unitIcons';
import { api } from '@/lib/api';
import { useGraphStore } from '@/state/graphStore';

export type UnitDef = {
  id: string;
  label: string;
  iconKey: string;
  category: 'Upstream' | 'DSP' | 'Utilities';
};

const UNITS: UnitDef[] = [
  { id: 'Seed1', label: 'Seed Stage 1', iconKey: 'Seed1', category: 'Upstream' },
  { id: 'Seed2', label: 'Seed Stage 2', iconKey: 'Seed2', category: 'Upstream' },
  { id: 'Seed3', label: 'Seed Stage 3', iconKey: 'Seed3', category: 'Upstream' },
  { id: 'Production', label: 'Production Fermenter', iconKey: 'ProductionFermenter', category: 'Upstream' },
  { id: 'CellSeparation', label: 'Cell Separation', iconKey: 'Diskstack', category: 'Upstream' },
  { id: 'Chitosan', label: 'Chitosan Flocculation', iconKey: 'Chitosan', category: 'Upstream' },
  { id: 'DSP01', label: 'SPTFF', iconKey: 'UF', category: 'DSP' },
  { id: 'DSP02', label: 'Chromatography', iconKey: 'Chromatography', category: 'DSP' },
  { id: 'DSP03', label: 'UF → DF → UF', iconKey: 'TFF', category: 'DSP' },
  { id: 'AEXMembrane', label: 'AEX Membrane (FT)', iconKey: 'AEXMembrane', category: 'DSP' },
  { id: 'DSP04', label: 'Sterile Filtration', iconKey: 'SterileFiltration', category: 'DSP' },
  { id: 'SprayDryer', label: 'Spray Dryer', iconKey: 'SprayDryer', category: 'DSP' },
  { id: 'MFPolish', label: 'MF Polishing', iconKey: 'MF Polishing', category: 'DSP' },
  { id: 'HoldingTank', label: 'Holding Tank', iconKey: 'HoldingTank', category: 'Utilities' },
  { id: 'MixTank', label: 'Mixing Tank', iconKey: 'MixTank', category: 'Utilities' },
  { id: 'Pump', label: 'Pump', iconKey: 'Pump', category: 'Utilities' },
];

export function UnitLibrary() {
  const { data: buffers } = useQuery({ queryKey: ['buffers'], queryFn: () => api.listBuffers() });
  void buffers; // keep fetch warm for Inspector
  const openAddModal = useGraphStore((s) => s.openAddModal);

  const upstreamUnits = useMemo(() => UNITS.filter(u => u.category === 'Upstream'), []);
  const dspUnits = useMemo(() => UNITS.filter(u => u.category === 'DSP'), []);
  const utilUnits = useMemo(() => UNITS.filter(u => u.category === 'Utilities'), []);

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Palette</h3>
      <p style={{ color: '#666', marginTop: 0 }}>Unit Operations (click or drag to Inspector)</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, marginBottom: 12 }}>
        {upstreamUnits.map((u) => (
          <UnitCard key={u.id} unit={u} onOpen={() => openAddModal(u)} />
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
        {dspUnits.map((u) => (
          <UnitCard key={u.id} unit={u} onOpen={() => openAddModal(u)} />
        ))}
      </div>
      {utilUnits.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <p style={{ color: '#666', marginTop: 12 }}>Utilities</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {utilUnits.map((u) => (
              <UnitCard key={u.id} unit={u} onOpen={() => openAddModal(u)} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function UnitCard({ unit, onOpen }: { unit: UnitDef; onOpen: () => void }) {
  const IconCmp = getUnitIcon(unit.iconKey);
  return (
    <button
      onClick={onOpen}
      onDoubleClick={onOpen}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('application/x-biosteam-unit', JSON.stringify(unit));
        // Helpful hint for the drop effect
        e.dataTransfer.effectAllowed = 'copyMove';
      }}
      style={{ display: 'flex', gap: 8, alignItems: 'center', padding: 8, border: '1px solid #ddd', borderRadius: 8, background: '#fff', cursor: 'grab' }}
    >
      <Icon component={IconCmp} size={20} />
      <span style={{ textAlign: 'left' }}>{unit.label}</span>
    </button>
  );
}

function LabeledRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, alignItems: 'center', margin: '8px 0' }}>
      <label style={{ color: '#555' }}>{label}</label>
      <div>{children}</div>
    </div>
  );
}

export function FEForm({ onAdd, initial, submitLabel }: { onAdd: (vals: { media_type: string; carbon_source: string }) => void; initial?: { media_type?: string; carbon_source?: string }; submitLabel?: string }) {
  const [media, setMedia] = useState(initial?.media_type ?? 'defined');
  const [carbon, setCarbon] = useState(initial?.carbon_source ?? 'glucose');
  return (
    <div>
      <LabeledRow label="Media">
        <select value={media} onChange={(e) => setMedia(e.target.value)}>
          <option value="rich">Rich</option>
          <option value="defined">Defined</option>
          <option value="custom">Custom</option>
        </select>
      </LabeledRow>
      <LabeledRow label="Carbon Source">
        <select value={carbon} onChange={(e) => setCarbon(e.target.value)}>
          <option value="glucose">Glucose</option>
          <option value="sucrose">Sucrose</option>
          <option value="glycerol">Glycerol</option>
        </select>
      </LabeledRow>
      <button onClick={() => onAdd({ media_type: media, carbon_source: carbon })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function SeedForm({ onAdd, initial, submitLabel, stage }: {
  onAdd: (vals: { media_type: string; carbon_source: string; inoculum_fraction: number; temperature_c: number; duration_h?: number }) => void;
  initial?: { media_type?: string; carbon_source?: string; inoculum_fraction?: number; temperature_c?: number; duration_h?: number; stage?: number };
  submitLabel?: string;
  stage?: 1 | 2 | 3;
}) {
  const nodes = useGraphStore(s => s.nodes);
  const [media, setMedia] = useState(initial?.media_type ?? 'defined');
  const [carbon, setCarbon] = useState(initial?.carbon_source ?? 'glucose');
  const [inoc, setInoc] = useState<number>(initial?.inoculum_fraction ?? 0.05);
  const [tempC, setTempC] = useState<number>(initial?.temperature_c ?? 30);
  const [durationH, setDurationH] = useState<number | ''>((initial?.duration_h as any) ?? ('' as any));
  const st = (stage ?? (initial?.stage as any)) as 1 | 2 | 3 | undefined;
  // Compute live volume preview using existing nodes
  const workingV = (() => {
    const prod = nodes.find(n => (n.data as any)?.fermentation);
    return (prod?.data as any)?.fermentation?.working_volume_m3 as number | undefined;
  })();
  const s3frac = (() => {
    const s3 = nodes.find(n => (n.data as any)?.seed?.stage === 3);
    return (s3?.data as any)?.seed?.inoculum_fraction as number | undefined;
  })();
  const s2frac = (() => {
    const s2 = nodes.find(n => (n.data as any)?.seed?.stage === 2);
    return (s2?.data as any)?.seed?.inoculum_fraction as number | undefined;
  })();
  const previewVol = React.useMemo(() => {
    try {
      if (st === 3 && typeof workingV === 'number') return typeof inoc === 'number' ? workingV * inoc : undefined;
      if (st === 2) {
        const v3 = (typeof workingV === 'number' && typeof s3frac === 'number') ? workingV * s3frac : undefined;
        return (typeof v3 === 'number' && typeof inoc === 'number') ? v3 * inoc : undefined;
      }
      if (st === 1) {
        const v3 = (typeof workingV === 'number' && typeof s3frac === 'number') ? workingV * s3frac : undefined;
        const v2 = (typeof v3 === 'number' && typeof s2frac === 'number') ? v3 * s2frac : undefined;
        return (typeof v2 === 'number' && typeof inoc === 'number') ? v2 * inoc : undefined;
      }
    } catch {}
    return undefined;
  }, [st, workingV, s3frac, s2frac, inoc]);
  return (
    <div>
      <LabeledRow label="Media">
        <select value={media} onChange={(e) => setMedia(e.target.value)}>
          <option value="rich">Rich</option>
          <option value="defined">Defined</option>
          <option value="custom">Custom</option>
        </select>
      </LabeledRow>
      <LabeledRow label="Carbon Source">
        <select value={carbon} onChange={(e) => setCarbon(e.target.value)}>
          <option value="glucose">Glucose</option>
          <option value="sucrose">Sucrose</option>
          <option value="glycerol">Glycerol</option>
        </select>
      </LabeledRow>
      <LabeledRow label="Inoculum (fraction)">
        <input type="number" min={0} max={1} step={0.005} value={inoc} onChange={(e) => setInoc(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Temperature (°C)">
        <input type="number" min={0} step={0.5} value={tempC} onChange={(e) => setTempC(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label={`Duration (h)`}>
        <input type="number" min={0} step={0.25} value={durationH as any} onChange={(e) => setDurationH(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#555', margin: '6px 0' }}>Computed volume: {typeof previewVol === 'number' && isFinite(previewVol) ? `${previewVol.toFixed(2)} m³` : '—'}</div>
      <button onClick={() => onAdd({ media_type: media, carbon_source: carbon, inoculum_fraction: inoc, temperature_c: tempC, duration_h: (typeof durationH === 'number' ? durationH : undefined) })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function ProductionForm({ onAdd, initial, submitLabel }: {
  onAdd: (vals: { media_type: string; carbon_source: string; fermenter_volume_m3: number; working_volume_m3: number; product_titre_g_L: number; temperature_c: number; fermentation_time_h?: number; feed_glucose_concentration_g_L?: number; total_glucose_feed_kg?: number }) => void;
  initial?: { media_type?: string; carbon_source?: string; fermenter_volume_m3?: number; working_volume_m3?: number; product_titre_g_L?: number; temperature_c?: number; fermentation_time_h?: number; feed_glucose_concentration_g_L?: number; total_glucose_feed_kg?: number };
  submitLabel?: string;
}) {
  const [media, setMedia] = useState(initial?.media_type ?? 'defined');
  const [carbon, setCarbon] = useState(initial?.carbon_source ?? 'glucose');
  const [size, setSize] = useState<number>(initial?.fermenter_volume_m3 ?? 100);
  const [work, setWork] = useState<number>(initial?.working_volume_m3 ?? 80);
  const [titre, setTitre] = useState<number>(initial?.product_titre_g_L ?? 10);
  const [tempC, setTempC] = useState<number>(initial?.temperature_c ?? 30);
  const [fermTimeH, setFermTimeH] = useState<number | ''>((initial?.fermentation_time_h as any) ?? ('' as any));
  const [feedConc, setFeedConc] = useState<number | ''>((initial?.feed_glucose_concentration_g_L as any) ?? ('' as any));
  const [totalFeed, setTotalFeed] = useState<number | ''>((initial?.total_glucose_feed_kg as any) ?? ('' as any));
  return (
    <div>
      <LabeledRow label="Media">
        <select value={media} onChange={(e) => setMedia(e.target.value)}>
          <option value="rich">Rich</option>
          <option value="defined">Defined</option>
          <option value="custom">Custom</option>
        </select>
      </LabeledRow>
      <LabeledRow label="Carbon Source">
        <select value={carbon} onChange={(e) => setCarbon(e.target.value)}>
          <option value="glucose">Glucose</option>
          <option value="sucrose">Sucrose</option>
          <option value="glycerol">Glycerol</option>
        </select>
      </LabeledRow>
      <LabeledRow label="Fermenter Size (m³)">
        <input type="number" min={0} step={0.1} value={size} onChange={(e) => setSize(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Working Volume (m³)">
        <input type="number" min={0} step={0.1} value={work} onChange={(e) => setWork(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Product titre (g/L)">
        <input type="number" min={0} step={0.1} value={titre} onChange={(e) => setTitre(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Temperature (°C)">
        <input type="number" min={0} step={0.5} value={tempC} onChange={(e) => setTempC(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Fermentation time (h)">
        <input type="number" min={0} step={0.5} value={fermTimeH as any} onChange={(e) => setFermTimeH(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
      </LabeledRow>
      <details style={{ marginTop: 8 }}>
        <summary style={{ cursor: 'pointer', color: '#444' }}>Advanced (feed)</summary>
        <div style={{ marginTop: 8 }}>
          <LabeledRow label="Feed glucose (g/L)">
            <input type="number" min={0} step={1} value={feedConc as any} onChange={(e) => setFeedConc(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
          </LabeledRow>
          <LabeledRow label="Total feed (kg)">
            <input type="number" min={0} step={0.1} value={totalFeed as any} onChange={(e) => setTotalFeed(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
          </LabeledRow>
          <div style={{ color: '#666', fontSize: 12 }}>Defines carbon tank suggestion in Mixing Tank form.</div>
        </div>
      </details>
      <button onClick={() => onAdd({ media_type: media, carbon_source: carbon, fermenter_volume_m3: size, working_volume_m3: work, product_titre_g_L: titre, temperature_c: tempC, fermentation_time_h: typeof fermTimeH === 'number' ? fermTimeH : undefined, feed_glucose_concentration_g_L: typeof feedConc === 'number' ? feedConc : undefined, total_glucose_feed_kg: typeof totalFeed === 'number' ? totalFeed : undefined })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function CellSepForm({ onAdd, initial, submitLabel }: { onAdd: (vals: { method: string; membranes_required?: boolean; solids_vv?: number; post_turbidity_spec?: number; od600_target?: number; od_to_dcw_g_per_l_per_od?: number; dcw_concentration_g_per_l?: number }) => void; initial?: { method?: string; membranes_required?: boolean; solids_vv?: number; post_turbidity_spec?: number; od600_target?: number; od_to_dcw_g_per_l_per_od?: number; dcw_concentration_g_per_l?: number }; submitLabel?: string }) {
  const [route, setRoute] = useState('disc_stack');
  const [polish, setPolish] = useState<boolean>(!!initial?.membranes_required);
  const [od600, setOD] = useState<number | ''>(((initial as any)?.od600_target as any) ?? ('' as any));
  const [od2dcw, setOD2DCW] = useState<number>((initial as any)?.od_to_dcw_g_per_l_per_od ?? 0.4);
  const dcwConc = typeof od600 === 'number' && isFinite(od600) ? od600 * (od2dcw || 0) : undefined;
  const solids = typeof dcwConc === 'number' ? (dcwConc / 750.0) : undefined; // approx: 60 g/L -> 0.08 v/v
  const [turb, setTurb] = useState<number>(initial?.post_turbidity_spec ?? 50);
  return (
    <div>
      <LabeledRow label="Route">
        <select value={route} onChange={(e) => setRoute(e.target.value)} disabled>
          <option value="disc_stack">Disc Stack</option>
        </select>
      </LabeledRow>
      <LabeledRow label="+ Polishing?">
        <input type="checkbox" checked={polish} onChange={(e) => setPolish(e.target.checked)} />
      </LabeledRow>
      <LabeledRow label="OD600">
        <input type="number" min={0} step={0.5} value={od600 as any} onChange={(e) => setOD(e.target.value === '' ? '' as any : parseFloat(e.target.value))} placeholder="e.g., 150" />
      </LabeledRow>
      <LabeledRow label="OD→DCW (g/L/OD)">
        <input type="number" min={0} step={0.01} value={od2dcw} onChange={(e) => setOD2DCW(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#555', margin: '6px 0' }}>
        {typeof dcwConc === 'number' && isFinite(dcwConc) ? `≈ DCW ${dcwConc.toFixed(1)} g/L · Solids ${((solids || 0)*100).toFixed(1)}% v/v` : 'Enter OD600 to estimate DCW and solids'}
      </div>
      <details style={{ marginTop: 8 }}>
        <summary style={{ cursor: 'pointer', color: '#444' }}>Advanced</summary>
        <div style={{ marginTop: 8 }}>
          <LabeledRow label="Turbidity spec (NTU)">
            <input type="number" min={0} step={1} value={turb} onChange={(e) => setTurb(parseFloat(e.target.value))} placeholder="NTU" />
          </LabeledRow>
          <div style={{ color: '#666', fontSize: 12 }}>Default 50 NTU; lower targets may require extra polishing.</div>
        </div>
      </details>
      <button onClick={() => onAdd({
        method: route,
        membranes_required: polish,
        solids_vv: typeof solids === 'number' ? solids : undefined,
        post_turbidity_spec: turb,
        od600_target: typeof od600 === 'number' ? od600 : undefined,
        od_to_dcw_g_per_l_per_od: od2dcw || undefined,
        dcw_concentration_g_per_l: typeof dcwConc === 'number' ? dcwConc : undefined,
      })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function DSP01SPTFFForm({ onAdd, initial, submitLabel }: { onAdd: (vals: { concentration_factor: number; flux_lmh: number; product_recovery_fraction?: number; membrane_area_m2?: number; membrane_cost_per_m2?: number; membrane_life_batches?: number }) => void; initial?: { concentration_factor?: number; flux_lmh?: number; product_recovery_fraction?: number; membrane_area_m2?: number; membrane_cost_per_m2?: number; membrane_life_batches?: number }; submitLabel?: string }) {
  const [cf, setCf] = useState<number>(initial?.concentration_factor ?? 3.0);
  const [flux, setFlux] = useState<number>(initial?.flux_lmh ?? 80);
  const [rec, setRec] = useState<number>(initial?.product_recovery_fraction ?? 0.985);
  const [area, setArea] = useState<number | ''>((initial?.membrane_area_m2 as any) ?? ('' as any));
  const [mcost, setMCost] = useState<number | ''>((initial?.membrane_cost_per_m2 as any) ?? ('' as any));
  const [life, setLife] = useState<number | ''>((initial?.membrane_life_batches as any) ?? ('' as any));
  return (
    <div>
      <LabeledRow label="CF (total)">
        <input type="number" min={1} max={6} step={0.1} value={cf} onChange={(e) => setCf(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 3.0×</div>
      <LabeledRow label="Flux (LMH)">
        <input type="number" min={0} step={1} value={flux} onChange={(e) => setFlux(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 80 LMH</div>
      <LabeledRow label="Recovery">
        <input type="number" min={0.95} max={1} step={0.001} value={rec} onChange={(e) => setRec(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 0.985</div>
      <details>
        <summary>Advanced</summary>
        <LabeledRow label="Membrane area (m²)">
          <input type="number" min={0} step={1} value={area as any} onChange={(e) => setArea(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <LabeledRow label="Membrane cost ($/m²)">
          <input type="number" min={0} step={1} value={mcost as any} onChange={(e) => setMCost(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <LabeledRow label="Membrane life (batches)">
          <input type="number" min={1} step={1} value={life as any} onChange={(e) => setLife(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
      </details>
      <button onClick={() => onAdd({ concentration_factor: cf, flux_lmh: flux, product_recovery_fraction: rec, membrane_area_m2: typeof area === 'number' ? area : undefined, membrane_cost_per_m2: typeof mcost === 'number' ? mcost : undefined, membrane_life_batches: typeof life === 'number' ? life : undefined })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function UFForm({ onAdd, initial, submitLabel }: {
  onAdd: (vals: { volume_reduction_ratio: number; product_recovery_fraction?: number; flux_lmh?: number; tmp_bar?: number }) => void;
  initial?: { volume_reduction_ratio?: number; product_recovery_fraction?: number; flux_lmh?: number; tmp_bar?: number };
  submitLabel?: string;
}) {
  const [vrr, setVrr] = useState<number>(initial?.volume_reduction_ratio ?? 4.0);
  const [rec, setRec] = useState<number>(initial?.product_recovery_fraction ?? 0.985);
  const [flux, setFlux] = useState<number>(initial?.flux_lmh ?? 80);
  const [tmp, setTmp] = useState<number>(initial?.tmp_bar ?? 1.2);
  return (
    <div>
      <LabeledRow label="VRR">
        <input type="number" min={1} step={0.1} value={vrr} onChange={(e) => setVrr(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Recovery">
        <input type="number" min={0} max={1} step={0.001} value={rec} onChange={(e) => setRec(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Flux (LMH)">
        <input type="number" min={0} step={1} value={flux} onChange={(e) => setFlux(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="TMP (bar)">
        <input type="number" min={0} step={0.05} value={tmp} onChange={(e) => setTmp(parseFloat(e.target.value))} />
      </LabeledRow>
      <button onClick={() => onAdd({ volume_reduction_ratio: vrr, product_recovery_fraction: rec, flux_lmh: flux, tmp_bar: tmp })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function DSP02Form({ buffers, onAdd, initial, submitLabel }: { buffers: any[]; onAdd: (vals: {
  load_buffer_id?: string; load_ionic_strength_mM: number; wash_ionic_strength_mM: number; elute_ionic_strength_mM: number; wash_volumes: number; elute_volumes: number;
}) => void; initial?: { load_buffer_id?: string; load_ionic_strength_mM?: number; wash_ionic_strength_mM?: number; elute_ionic_strength_mM?: number; wash_volumes?: number; elute_volumes?: number }; submitLabel?: string }) {
  const [loadBuf, setLoadBuf] = useState<string | undefined>(initial?.load_buffer_id ?? buffers?.[0]?.id);
  const [loadI, setLoadI] = useState(initial?.load_ionic_strength_mM ?? 5);
  const [washI, setWashI] = useState(initial?.wash_ionic_strength_mM ?? 50);
  const [eluteI, setEluteI] = useState(initial?.elute_ionic_strength_mM ?? 500);
  const [washV, setWashV] = useState(initial?.wash_volumes ?? 5);
  const [eluteV, setEluteV] = useState(initial?.elute_volumes ?? 3);
  return (
    <div>
      <LabeledRow label="Load Buffer">
        <select value={loadBuf} onChange={(e) => setLoadBuf(e.target.value)}>
          <option value="">—</option>
          {buffers.map((b) => (
            <option key={b.id} value={b.id}>{b.name || b.id}</option>
          ))}
        </select>
      </LabeledRow>
      <LabeledRow label="Load I (mM)">
        <input type="number" min={0} value={loadI} onChange={(e) => setLoadI(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Wash I (mM)">
        <input type="number" min={0} value={washI} onChange={(e) => setWashI(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Elute I (mM)">
        <input type="number" min={0} value={eluteI} onChange={(e) => setEluteI(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Wash Volumes">
        <input type="number" min={0} value={washV} onChange={(e) => setWashV(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Elute Volumes">
        <input type="number" min={0} value={eluteV} onChange={(e) => setEluteV(parseFloat(e.target.value))} />
      </LabeledRow>
      <button onClick={() => onAdd({ load_buffer_id: loadBuf, load_ionic_strength_mM: loadI, wash_ionic_strength_mM: washI, elute_ionic_strength_mM: eluteI, wash_volumes: washV, elute_volumes: eluteV })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function DSP03UFDFUFForm({ onAdd, initial, submitLabel }: { onAdd: (vals: { vr_preuf: number; nd: number; flux_lmh: number; tmp_bar_cap: number; df_time_h: number; area_headroom_fraction?: number; sieving_uf?: number; sieving_df?: number; adsorption_loss_per_100_m2?: number; mwco_kda?: number; cfv_ms?: number; final_spray_solids_wt_pct?: number }) => void; initial?: Partial<{ vr_preuf: number; nd: number; flux_lmh: number; tmp_bar_cap: number; df_time_h: number; area_headroom_fraction: number; sieving_uf: number; sieving_df: number; adsorption_loss_per_100_m2: number; mwco_kda: number; cfv_ms: number; final_spray_solids_wt_pct: number }>; submitLabel?: string }) {
  const [vr, setVr] = useState<number>(initial?.vr_preuf ?? 3.0);
  const [nd, setNd] = useState<number>(initial?.nd ?? 5.0);
  const [flux, setFlux] = useState<number>(initial?.flux_lmh ?? 85.0);
  const [tmp, setTmp] = useState<number>(initial?.tmp_bar_cap ?? 1.5);
  const [tDF, setTDF] = useState<number>(initial?.df_time_h ?? 10.0);
  const [head, setHead] = useState<number | ''>((initial?.area_headroom_fraction as any) ?? ('' as any));
  const [suf, setSUF] = useState<number | ''>((initial?.sieving_uf as any) ?? ('' as any));
  const [sdf, setSDF] = useState<number | ''>((initial?.sieving_df as any) ?? ('' as any));
  const [ads, setAds] = useState<number | ''>((initial?.adsorption_loss_per_100_m2 as any) ?? ('' as any));
  const [mwco, setMwco] = useState<number | ''>((initial?.mwco_kda as any) ?? ('' as any));
  const [cfv, setCfv] = useState<number | ''>((initial?.cfv_ms as any) ?? ('' as any));
  const [spray, setSpray] = useState<number | ''>((initial?.final_spray_solids_wt_pct as any) ?? ('' as any));
  return (
    <div>
      <LabeledRow label="Pre-UF VRR (×)">
        <input type="number" min={1} step={0.1} value={vr} onChange={(e) => setVr(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 3.0×</div>
      <LabeledRow label="DF ND (diavolumes)">
        <input type="number" min={0} step={0.1} value={nd} onChange={(e) => setNd(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 5.0</div>
      <LabeledRow label="Flux (LMH)">
        <input type="number" min={0} step={1} value={flux} onChange={(e) => setFlux(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 85 LMH</div>
      <LabeledRow label="TMP cap (bar)">
        <input type="number" min={0} step={0.05} value={tmp} onChange={(e) => setTmp(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 1.5 bar</div>
      <LabeledRow label="DF time target (h)">
        <input type="number" min={0} step={0.25} value={tDF} onChange={(e) => setTDF(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 10 h</div>
      <details>
        <summary>Advanced</summary>
        <LabeledRow label="Headroom (frac)">
          <input type="number" min={0} max={1} step={0.01} value={head as any} onChange={(e) => setHead(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 0.2</div>
        <LabeledRow label="Sieving UF">
          <input type="number" min={0} max={1} step={0.001} value={suf as any} onChange={(e) => setSUF(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 0.01</div>
        <LabeledRow label="Sieving DF">
          <input type="number" min={0} max={1} step={0.001} value={sdf as any} onChange={(e) => setSDF(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 0.007</div>
        <LabeledRow label="Adsorption loss/100 m²">
          <input type="number" min={0} step={0.001} value={ads as any} onChange={(e) => setAds(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 0.002</div>
        <LabeledRow label="MWCO (kDa)">
          <input type="number" min={1} step={1} value={mwco as any} onChange={(e) => setMwco(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 30 kDa</div>
        <LabeledRow label="CFV (m/s)">
          <input type="number" min={0} step={0.1} value={cfv as any} onChange={(e) => setCfv(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 2.0 m/s</div>
        <LabeledRow label="Spray solids (wt%)">
          <input type="number" min={0} step={0.1} value={spray as any} onChange={(e) => setSpray(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color: '#777', fontStyle: 'italic', margin: '-6px 0 6px 120px' }}>Baseline: 12%</div>
      </details>
      <button onClick={() => onAdd({ vr_preuf: vr, nd, flux_lmh: flux, tmp_bar_cap: tmp, df_time_h: tDF, area_headroom_fraction: typeof head === 'number' ? head : undefined, sieving_uf: typeof suf === 'number' ? suf : undefined, sieving_df: typeof sdf === 'number' ? sdf : undefined, adsorption_loss_per_100_m2: typeof ads === 'number' ? ads : undefined, mwco_kda: typeof mwco === 'number' ? mwco : undefined, cfv_ms: typeof cfv === 'number' ? cfv : undefined, final_spray_solids_wt_pct: typeof spray === 'number' ? spray : undefined })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function AEXMembraneForm({ onAdd, initial, submitLabel, contextNodeId }: {
  onAdd: (vals: {
    placement: 'before_sptff' | 'after_sptff' | 'in_dsp04';
    q_DNA_mg_per_mL: number; q_HCP_mg_per_mL: number; utilization: number; salt_derate_HCP: number;
    MV_per_min: number; deltaP_cap_bar: number;
    membrane_volume_per_module_L: number; max_flow_per_module_Lph: number; module_cost_usd: number; hold_up_L_per_module: number;
    product_adsorption_loss_frac: number; t_window_h: number;
    buffer_fee_usd_per_m3?: number; labor_h_per_batch?: number; labor_rate_usd_per_h?: number; waste_fee_usd_per_tonne?: number;
    dna_in_mg_per_l?: number; hcp_in_g_per_l?: number;
    pre_load_salt_mM?: number; assumed_feed_volume_m3?: number;
  }) => void;
  initial?: Partial<{
    placement: 'before_sptff' | 'after_sptff' | 'in_dsp04';
    q_DNA_mg_per_mL: number; q_HCP_mg_per_mL: number; utilization: number; salt_derate_HCP: number;
    MV_per_min: number; deltaP_cap_bar: number;
    membrane_volume_per_module_L: number; max_flow_per_module_Lph: number; module_cost_usd: number; hold_up_L_per_module: number;
    product_adsorption_loss_frac: number; t_window_h: number;
    buffer_fee_usd_per_m3: number; labor_h_per_batch: number; labor_rate_usd_per_h: number; waste_fee_usd_per_tonne: number;
    dna_in_mg_per_l: number; hcp_in_g_per_l: number;
    pre_load_salt_mM: number; assumed_feed_volume_m3: number;
  }>; submitLabel?: string; contextNodeId?: string;
}) {
  const nodes = useGraphStore(s => s.nodes);
  const edges = useGraphStore(s => s.edges);
  const [placement, setPlacement] = useState<'before_sptff' | 'after_sptff' | 'in_dsp04'>(initial?.placement ?? 'after_sptff');
  const [placementTouched, setPlacementTouched] = useState(false);
  const [qDNA, setQDNA] = useState<number>(initial?.q_DNA_mg_per_mL ?? 10);
  const [qHCP, setQHCP] = useState<number>(initial?.q_HCP_mg_per_mL ?? 2);
  const [util, setUtil] = useState<number>(initial?.utilization ?? 0.70);
  const [derate, setDerate] = useState<number>(initial?.salt_derate_HCP ?? 0.5);
  const [mvpm, setMV] = useState<number>(initial?.MV_per_min ?? 10);
  const [dp, setDP] = useState<number>(initial?.deltaP_cap_bar ?? 2.0);
  const [mvPerMod, setMVPerMod] = useState<number>(initial?.membrane_volume_per_module_L ?? 0.5);
  const [maxFlow, setMaxFlow] = useState<number>(initial?.max_flow_per_module_Lph ?? 600);
  const [modCost, setModCost] = useState<number>(initial?.module_cost_usd ?? 1500);
  const [holdup, setHoldup] = useState<number>(initial?.hold_up_L_per_module ?? 1.0);
  const [adsFrac, setAdsFrac] = useState<number>(initial?.product_adsorption_loss_frac ?? 0.005);
  const [tH, setTH] = useState<number>(initial?.t_window_h ?? 8);
  const [bufFee, setBufFee] = useState<number | ''>((initial?.buffer_fee_usd_per_m3 as any) ?? ('' as any));
  const [laborH, setLaborH] = useState<number | ''>((initial?.labor_h_per_batch as any) ?? (6 as any));
  const [rate, setRate] = useState<number | ''>((initial?.labor_rate_usd_per_h as any) ?? (80 as any));
  const [waste, setWaste] = useState<number | ''>((initial?.waste_fee_usd_per_tonne as any) ?? (220 as any));
  const [dnaIn, setDNAIn] = useState<number | ''>((initial?.dna_in_mg_per_l as any) ?? ('' as any));
  const [hcpIn, setHCPIn] = useState<number | ''>((initial?.hcp_in_g_per_l as any) ?? ('' as any));
  const [saltmM, setSaltmM] = useState<number | ''>((initial?.pre_load_salt_mM as any) ?? ('' as any));
  const [condmScm, setCondmScm] = useState<number | ''>('' as any);
  const [feedVm3, setFeedVm3] = useState<number | ''>((initial?.assumed_feed_volume_m3 as any) ?? ('' as any));

  // Topology helpers
  function buildAdj() {
    const fwd = new Map<string, string[]>();
    const rev = new Map<string, string[]>();
    nodes.forEach(n => { fwd.set(n.id, []); rev.set(n.id, []); });
    edges.forEach(e => {
      (fwd.get(e.source) || fwd.set(e.source, []).get(e.source)!, fwd.get(e.source)!.push(e.target));
      (rev.get(e.target) || rev.set(e.target, []).get(e.target)!, rev.get(e.target)!.push(e.source));
    });
    return { fwd, rev };
  }
  function bfs(startIds: string[], adj: Map<string, string[]>) {
    const seen = new Set<string>();
    const q = [...startIds];
    startIds.forEach(id => seen.add(id));
    while (q.length) {
      const id = q.shift()!;
      for (const nb of (adj.get(id) || [])) {
        if (!seen.has(nb)) { seen.add(nb); q.push(nb); }
      }
    }
    return seen;
  }
  function isSPTFF(n: any) {
    return !!(n?.data as any)?.concentration && ((n.data as any).concentration as any).route === 'sptff';
  }
  const topoSuggestion = React.useMemo(() => {
    if (!contextNodeId) return { place: undefined as ('before_sptff'|'after_sptff'|'in_dsp04'|undefined), cf: undefined as number|undefined, vBase: undefined as number|undefined };
    const { fwd, rev } = buildAdj();
    const up = bfs([contextNodeId], rev);
    const down = bfs([contextNodeId], fwd);
    const sptffs = nodes.filter(isSPTFF);
    let place: 'before_sptff'|'after_sptff'|'in_dsp04'|undefined;
    let cf: number|undefined;
    let vBase: number|undefined;
    for (const s of sptffs) {
      if (up.has(s.id)) {
        place = 'after_sptff';
        const conc = (s.data as any)?.concentration?.sptff;
        if (conc && typeof conc.concentration_factor === 'number') cf = conc.concentration_factor;
        const upOfSP = bfs([s.id], rev);
        const cands = nodes.filter(n => upOfSP.has(n.id));
        const hold = cands.find(n => (n.data as any)?.holding_tank?.capacity_m3 != null);
        if (hold) vBase = (hold.data as any).holding_tank.capacity_m3;
        else {
          const prod = cands.find(n => (n.data as any)?.fermentation?.working_volume_m3 != null);
          if (prod) vBase = (prod.data as any).fermentation.working_volume_m3;
        }
        break;
      } else if (down.has(s.id)) {
        place = 'before_sptff';
      }
    }
    if (!place) place = 'in_dsp04';
    return { place, cf, vBase };
  }, [contextNodeId, nodes, edges]);

  React.useEffect(() => {
    if (!placementTouched && topoSuggestion.place && initial?.placement == null) {
      setPlacement(topoSuggestion.place);
    }
  }, [topoSuggestion.place, placementTouched, initial?.placement]);

  // Conductivity ↔ salt mapping (simple): mM ≈ 10 × mS/cm
  React.useEffect(() => {
    if (typeof condmScm === 'number' && (saltmM === '' || typeof saltmM !== 'number')) {
      setSaltmM(condmScm * 10);
    }
  }, [condmScm]);
  return (
    <div>
      <LabeledRow label="Placement">
        <select value={placement} onChange={(e)=>{ setPlacement(e.target.value as any); setPlacementTouched(true); }}>
          <option value="before_sptff">Before SPTFF</option>
          <option value="after_sptff">After SPTFF</option>
          <option value="in_dsp04">DSP04 (Polish)</option>
        </select>
      </LabeledRow>
      <div style={{ color:'#666', fontSize: 12, margin: '4px 0 8px 120px' }}>Flow‑through; sizing primarily from volume/time. Salt before load affects HCP trimming.</div>
      <LabeledRow label="Conductivity (mS/cm)">
        <input type="number" min={0} step={0.5} value={condmScm as any} onChange={(e)=>setCondmScm(e.target.value===''?'' as any:parseFloat(e.target.value))} placeholder="e.g., 25" />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Approx: mM ≈ 10 × mS/cm → {typeof condmScm==='number' ? `${(condmScm*10).toFixed(0)} mM` : '—'}</div>
      <LabeledRow label="Salt before load (mM)">
        <input type="number" min={0} step={5} value={saltmM as any} onChange={(e)=>setSaltmM(e.target.value===''?'' as any:parseFloat(e.target.value))} placeholder="e.g., 250" />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Typical: 200–300 mM (baseline 250 mM)</div>
      <LabeledRow label="DNA_in (mg/L)">
        <input type="number" min={0} step={0.01} value={dnaIn as any} onChange={(e)=>setDNAIn(e.target.value===''?'' as any:parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="HCP_in (g/L)">
        <input type="number" min={0} step={0.001} value={hcpIn as any} onChange={(e)=>setHCPIn(e.target.value===''?'' as any:parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="q_DNA (mg/mL)">
        <input type="number" min={0} step={0.1} value={qDNA} onChange={(e)=>setQDNA(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 10 mg/mL</div>
      <LabeledRow label="q_HCP (mg/mL)">
        <input type="number" min={0} step={0.1} value={qHCP} onChange={(e)=>setQHCP(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 2 mg/mL</div>
      <LabeledRow label="Utilization">
        <input type="number" min={0} max={1} step={0.01} value={util} onChange={(e)=>setUtil(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 0.70</div>
      <LabeledRow label="Salt derate (HCP)">
        <input type="number" min={0} max={1} step={0.01} value={derate} onChange={(e)=>setDerate(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 0.5</div>
      <LabeledRow label="MV/min">
        <input type="number" min={0} step={0.5} value={mvpm} onChange={(e)=>setMV(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 10</div>
      <LabeledRow label="ΔP cap (bar)">
        <input type="number" min={0} step={0.1} value={dp} onChange={(e)=>setDP(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 2.0</div>
      <details>
        <summary>Packaging & econ</summary>
        <LabeledRow label="MV per module (L)">
          <input type="number" min={0} step={0.1} value={mvPerMod} onChange={(e)=>setMVPerMod(parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 0.5 L</div>
        <LabeledRow label="Max flow/module (L/h)">
          <input type="number" min={0} step={10} value={maxFlow} onChange={(e)=>setMaxFlow(parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 600 L/h</div>
        <LabeledRow label="Module cost (USD)">
          <input type="number" min={0} step={10} value={modCost} onChange={(e)=>setModCost(parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 1500</div>
        <LabeledRow label="Hold-up per module (L)">
          <input type="number" min={0} step={0.1} value={holdup} onChange={(e)=>setHoldup(parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 1.0 L</div>
        <LabeledRow label="Adsorption loss (frac)">
          <input type="number" min={0} max={1} step={0.001} value={adsFrac} onChange={(e)=>setAdsFrac(parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 0.005</div>
        <LabeledRow label="Takt window (h)">
          <input type="number" min={0} step={0.25} value={tH} onChange={(e)=>setTH(parseFloat(e.target.value))} />
        </LabeledRow>
        <div style={{ color:'#777', fontStyle:'italic', margin:'-6px 0 6px 120px' }}>Baseline: 8 h</div>
        <LabeledRow label="Buffer fee ($/m³)">
          <input type="number" min={0} step={1} value={bufFee as any} onChange={(e)=>setBufFee(e.target.value===''?'' as any:parseFloat(e.target.value))} />
        </LabeledRow>
        <LabeledRow label="Labor (h/batch)">
          <input type="number" min={0} step={0.5} value={laborH as any} onChange={(e)=>setLaborH(e.target.value===''?'' as any:parseFloat(e.target.value))} />
        </LabeledRow>
        <LabeledRow label="Labor rate ($/h)">
          <input type="number" min={0} step={1} value={rate as any} onChange={(e)=>setRate(e.target.value===''?'' as any:parseFloat(e.target.value))} />
        </LabeledRow>
        <LabeledRow label="Waste fee ($/t)">
          <input type="number" min={0} step={1} value={waste as any} onChange={(e)=>setWaste(e.target.value===''?'' as any:parseFloat(e.target.value))} />
        </LabeledRow>
      </details>
      <details style={{ marginTop: 8 }}>
        <summary>Preview (volume‑driven sizing)</summary>
        <div style={{ marginTop: 8 }}>
          <LabeledRow label="Assumed feed (m³)">
            <input type="number" min={0} step={0.1} value={feedVm3 as any} onChange={(e)=>setFeedVm3(e.target.value===''?'' as any:parseFloat(e.target.value))} placeholder="e.g., 15" />
          </LabeledRow>
          <div style={{ color:'#666', fontSize: 12, margin:'-6px 0 8px 120px' }}>
            {topoSuggestion.cf && topoSuggestion.vBase ? (
              <>Topology: base volume {topoSuggestion.vBase.toFixed(2)} m³, CF {topoSuggestion.cf} → post‑SPTFF ≈ {(topoSuggestion.vBase / topoSuggestion.cf).toFixed(2)} m³</>
            ) : (
              <>Use post‑SPTFF volume when placed after SPTFF.</>
            )}
          </div>
          {(() => {
            const autoVm3 = (typeof feedVm3 === 'number') ? feedVm3 : (topoSuggestion.cf && topoSuggestion.vBase ? (topoSuggestion.vBase / topoSuggestion.cf) : undefined);
            const VfL = typeof autoVm3 === 'number' ? autoVm3 * 1000 : undefined;
            const DNA = typeof dnaIn === 'number' ? dnaIn : undefined;
            const HCP = typeof hcpIn === 'number' ? hcpIn : undefined;
            let VcapL: number | undefined;
            if (typeof VfL === 'number' && isFinite(VfL) && typeof qDNA === 'number' && qDNA>0 && typeof util==='number' && util>0) {
              const dnaTermL = DNA != null ? (VfL * DNA) / (qDNA * 1000 /* mL/L */ * util) : 0; // L
              const hcpTermL = (HCP != null && typeof qHCP==='number' && qHCP>0) ? (VfL * (HCP*1000) * derate) / (qHCP * 1000 * util) : 0; // L
              VcapL = dnaTermL + hcpTermL;
            }
            const VflowL = (typeof VfL === 'number' && typeof mvpm==='number' && mvpm>0 && typeof tH==='number' && tH>0)
              ? (VfL / (mvpm * 60 * tH))
              : undefined;
            const VmemL = (VcapL!=null && VflowL!=null) ? Math.max(VcapL, VflowL) : (VcapL ?? VflowL);
            const modules = (typeof VmemL === 'number' && typeof mvPerMod==='number' && mvPerMod>0) ? Math.ceil(VmemL / mvPerMod) : undefined;
            const flowCapOK = (typeof VfL==='number' && typeof tH==='number' && typeof maxFlow==='number' && typeof modules==='number')
              ? (VfL / tH) <= (modules * maxFlow)
              : undefined;
            return (
              <div style={{ marginTop: 4, color:'#333' }}>
                <div>Vcap: <b>{VcapL!=null? VcapL.toFixed(2): '—'} L</b> · Vflow: <b>{VflowL!=null? VflowL.toFixed(2): '—'} L</b> → Vmem: <b>{VmemL!=null? VmemL.toFixed(2): '—'} L</b></div>
                <div>Modules: <b>{modules!=null? modules: '—'}</b> {flowCapOK!=null? (flowCapOK? '· Flow OK':'· Flow > cap'): ''}</div>
                <div style={{ color:'#777', fontStyle:'italic' }}>Sizing tends to be flow‑limited; salt before load influences HCP capture via derate.</div>
              </div>
            );
          })()}
        </div>
      </details>
      <button onClick={() => onAdd({ placement, q_DNA_mg_per_mL: qDNA, q_HCP_mg_per_mL: qHCP, utilization: util, salt_derate_HCP: derate, MV_per_min: mvpm, deltaP_cap_bar: dp, membrane_volume_per_module_L: mvPerMod, max_flow_per_module_Lph: maxFlow, module_cost_usd: modCost, hold_up_L_per_module: holdup, product_adsorption_loss_frac: adsFrac, t_window_h: tH, buffer_fee_usd_per_m3: typeof bufFee==='number'?bufFee:undefined, labor_h_per_batch: typeof laborH==='number'?laborH:undefined, labor_rate_usd_per_h: typeof rate==='number'?rate:undefined, waste_fee_usd_per_tonne: typeof waste==='number'?waste:undefined, dna_in_mg_per_l: typeof dnaIn==='number'?dnaIn:undefined, hcp_in_g_per_l: typeof hcpIn==='number'?hcpIn:undefined, pre_load_salt_mM: typeof saltmM==='number'?saltmM:undefined, assumed_feed_volume_m3: typeof feedVm3==='number'?feedVm3: (topoSuggestion.cf && topoSuggestion.vBase ? (topoSuggestion.vBase / topoSuggestion.cf) : undefined), pre_load_conductivity_mScm: typeof condmScm==='number'?condmScm:undefined })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function DSP04Form({ onAdd, initial, submitLabel }: { onAdd: (vals: { filter_area_m2: number }) => void; initial?: { filter_area_m2?: number }; submitLabel?: string }) {
  const [area, setArea] = useState(initial?.filter_area_m2 ?? 1.5);
  return (
    <div>
      <LabeledRow label="Filter Area (m²)">
        <input type="number" min={0} value={area} onChange={(e) => setArea(parseFloat(e.target.value))} />
      </LabeledRow>
      <button onClick={() => onAdd({ filter_area_m2: area })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function SprayForm({ onAdd, initial, submitLabel }: { onAdd: (vals: { outlet_temp_c: number }) => void; initial?: { outlet_temp_c?: number }; submitLabel?: string }) {
  const [outlet, setOutlet] = useState(initial?.outlet_temp_c ?? 80);
  return (
    <div>
      <LabeledRow label="Outlet Temp (°C)">
        <input type="number" min={0} value={outlet} onChange={(e) => setOutlet(parseFloat(e.target.value))} />
      </LabeledRow>
      <button onClick={() => onAdd({ outlet_temp_c: outlet })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}

export function MixTankForm({ onAdd, initial, submitLabel, contextNodeId }: {
  onAdd: (vals: { label?: string; mode: 'hold' | 'buffer' | 'carbon'; flow_m3_h?: number; hold_time_h?: number; batch_volume_m3?: number; headroom_fraction?: number; capacity_m3: number }) => void;
  initial?: { label?: string; mode?: 'hold' | 'buffer' | 'carbon'; flow_m3_h?: number; hold_time_h?: number; batch_volume_m3?: number; headroom_fraction?: number; capacity_m3?: number };
  submitLabel?: string;
  contextNodeId?: string;
}) {
  const nodes = useGraphStore(s => s.nodes);
  const edges = useGraphStore(s => s.edges);
  const [mode, setMode] = useState<'hold' | 'buffer' | 'carbon'>(initial?.mode ?? 'hold');
  const [flow, setFlow] = useState<number | ''>((initial?.flow_m3_h as any) ?? ('' as any));
  const [holdH, setHoldH] = useState<number | ''>((initial?.hold_time_h as any) ?? ('' as any));
  const [batchV, setBatchV] = useState<number | ''>((initial?.batch_volume_m3 as any) ?? ('' as any));
  const [headroom, setHeadroom] = useState<number>(initial?.headroom_fraction ?? 0.2);
  const [label, setLabel] = useState<string>(initial?.label ?? 'Mixing Tank');
  // Suggest carbon tank batch volume from production feed params when available
  const prod = nodes.find(n => (n.data as any)?.fermentation);
  const fe: any = (prod?.data as any)?.fermentation || {};
  const workingV = fe.working_volume_m3 as number | undefined;
  const FEED_KG_PER_M3_DEFAULT = 125; // from baseline: ~8750 kg per 70 m3
  const feedConc = (fe.feed_glucose_concentration_g_L as number | undefined)
    ?? (fe.feed_carbon_concentration_g_per_l as number | undefined)
    ?? 500; // g/L default per module defaults
  const totalFeedKg = (fe.total_glucose_feed_kg as number | undefined)
    ?? (typeof workingV === 'number' ? workingV * FEED_KG_PER_M3_DEFAULT : undefined);
  // Placeholder; computed after seed contributions are evaluated
  let suggestedCarbonBatchV: number | undefined = undefined;

  // Topology-aware: if context node id provided, only suggest for carbon when connected to Production; ignore if only connected to rich seeds
  const topo = React.useMemo(() => {
    const result = { toProduction: true, hasRichSeed: false, reach: undefined as undefined | Set<string> };
    if (!contextNodeId) return result;
    const adj = new Map<string, string[]>();
    for (const e of edges) {
      const arr = adj.get(e.source) || [];
      arr.push(e.target);
      adj.set(e.source, arr);
    }
    const seen = new Set<string>();
    const stack = [contextNodeId];
    let toProduction = false;
    let hasRichSeed = false;
    while (stack.length) {
      const id = stack.pop()!;
      if (seen.has(id)) continue;
      seen.add(id);
      const node = nodes.find(n => n.id === id);
      const data: any = node?.data;
      if (data?.fermentation) toProduction = true;
      if (data?.seed && data.seed.media_type === 'rich') hasRichSeed = true;
      for (const nb of (adj.get(id) || [])) stack.push(nb);
    }
    result.toProduction = toProduction;
    result.hasRichSeed = hasRichSeed;
    result.reach = seen;
    return result;
  }, [contextNodeId, edges, nodes]);
  // Seed contributions to carbon sizing: use production feed rate (g/L/h) × seed volume × seed time
  const seed2Node = React.useMemo(() => {
    const list = nodes.filter(n => (n.data as any)?.seed?.stage === 2);
    if (!list.length) return undefined;
    if (topo.reach) return list.find(n => topo.reach!.has(n.id)) || list[0];
    return list[0];
  }, [nodes, topo.reach]);
  const seed3Node = React.useMemo(() => {
    const list = nodes.filter(n => (n.data as any)?.seed?.stage === 3);
    if (!list.length) return undefined;
    if (topo.reach) return list.find(n => topo.reach!.has(n.id)) || list[0];
    return list[0];
  }, [nodes, topo.reach]);

  const seed2Inoc = (seed2Node as any)?.data?.seed?.inoculum_fraction as number | undefined;
  const seed3Inoc = (seed3Node as any)?.data?.seed?.inoculum_fraction as number | undefined;
  const seed2Media = (seed2Node as any)?.data?.seed?.media_type as string | undefined;
  const seed3Media = (seed3Node as any)?.data?.seed?.media_type as string | undefined;
  const prodTimeH = (fe.fermentation_time_h as number | undefined) ?? 48;
  const FEED_RATE_DEFAULT_G_L_H = 1.0;
  const feedRate_g_L_h = (() => {
    if (typeof totalFeedKg === 'number' && typeof workingV === 'number' && workingV > 0 && prodTimeH > 0) {
      return totalFeedKg / (workingV * prodTimeH); // kg/m3/h == g/L/h
    }
    return FEED_RATE_DEFAULT_G_L_H;
  })();
  const SEED2_TIME_H = ((seed2Node as any)?.data?.seed?.duration_h as number | undefined) ?? 4.0;
  const SEED3_TIME_H = ((seed3Node as any)?.data?.seed?.duration_h as number | undefined) ?? 4.0;
  const v3_m3 = (typeof workingV === 'number' && typeof seed3Inoc === 'number') ? workingV * seed3Inoc : undefined;
  const v2_m3 = (typeof v3_m3 === 'number' && typeof seed2Inoc === 'number') ? v3_m3 * seed2Inoc : undefined;
  const seed3FeedKg = (seed3Media !== 'rich' && typeof v3_m3 === 'number') ? (feedRate_g_L_h * v3_m3 * SEED3_TIME_H) : 0;
  const seed2FeedKg = (seed2Media !== 'rich' && typeof v2_m3 === 'number') ? (feedRate_g_L_h * v2_m3 * SEED2_TIME_H) : 0;
  const totalFeedKgAll = (typeof totalFeedKg === 'number' ? totalFeedKg : 0) + seed2FeedKg + seed3FeedKg;
  if (typeof feedConc === 'number' && feedConc > 0) {
    suggestedCarbonBatchV = totalFeedKgAll / feedConc;
  }

  const capacity_m3 = React.useMemo(() => {
    if (mode === 'hold') {
      const q = typeof flow === 'number' ? flow : NaN;
      const t = typeof holdH === 'number' ? holdH : NaN;
      if (isFinite(q) && isFinite(t)) return q * t;
      return NaN;
    } else {
      const allowSuggest = mode === 'carbon' && (topo.toProduction || !contextNodeId);
      const effectiveBatchV = (allowSuggest && (batchV === '' || batchV == null) && typeof suggestedCarbonBatchV === 'number') ? suggestedCarbonBatchV : batchV;
      const v = typeof effectiveBatchV === 'number' ? effectiveBatchV : NaN;
      if (isFinite(v)) return v * (1 + (headroom ?? 0));
      return NaN;
    }
  }, [mode, flow, holdH, batchV, headroom, suggestedCarbonBatchV, topo]);

  // Auto-fill batch volume for carbon mode if empty and suggestion available
  React.useEffect(() => {
    const allowSuggest = mode === 'carbon' && (topo.toProduction || !contextNodeId);
    if (allowSuggest && (batchV === '' || batchV == null) && typeof suggestedCarbonBatchV === 'number') {
      setBatchV(suggestedCarbonBatchV);
    }
  }, [mode, topo, contextNodeId, suggestedCarbonBatchV, batchV]);

  // Auto-name carbon tank from Production carbon source if label is default/empty
  React.useEffect(() => {
    if (mode !== 'carbon') return;
    const carbon = (fe.carbon_source as string | undefined) || 'Carbon';
    const auto = `${carbon.charAt(0).toUpperCase() + carbon.slice(1)} Feed Tank`;
    if (!label || label === 'Mixing Tank') setLabel(auto);
  }, [mode, fe?.carbon_source]);
  return (
    <div>
      <LabeledRow label="Label">
        <input type="text" value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g., Glucose Feed Tank" />
      </LabeledRow>
      <LabeledRow label="Mode">
        <select value={mode} onChange={(e) => setMode(e.target.value as any)}>
          <option value="hold">Hold-up (flow × time)</option>
          <option value="buffer">Buffer storage</option>
          <option value="carbon">Carbon source storage</option>
        </select>
      </LabeledRow>
      {mode === 'hold' ? (
        <>
          <LabeledRow label="Flow (m³/h)">
            <input type="number" min={0} step={0.01} value={flow as any} onChange={(e) => setFlow(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
          </LabeledRow>
          <LabeledRow label="Hold Time (h)">
            <input type="number" min={0} step={0.05} value={holdH as any} onChange={(e) => setHoldH(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
          </LabeledRow>
        </>
      ) : (
        <>
          <LabeledRow label="Batch Volume (m³)">
            <input type="number" min={0} step={0.01} value={batchV as any} onChange={(e) => setBatchV(e.target.value === '' ? '' as any : parseFloat(e.target.value))} />
          </LabeledRow>
          <LabeledRow label="Headroom (frac)">
            <input type="number" min={0} max={1} step={0.01} value={headroom} onChange={(e) => setHeadroom(parseFloat(e.target.value))} />
          </LabeledRow>
          {mode === 'carbon' && (
            <div style={{ color: '#444', margin: '6px 0' }}>
              {topo.hasRichSeed && !topo.toProduction ? (
                <div>Connected to rich Seed; excluding from carbon sizing.</div>
              ) : null}
              {(topo.toProduction || !contextNodeId) ? (
                <>
                  <div style={{ marginBottom: 2 }}>Feed rate ≈ {feedRate_g_L_h.toFixed(2)} g/L/h</div>
                  <div style={{ fontSize: 12, color: '#666' }}>
                    Seed3: V={isFinite(v3_m3 || NaN) ? `${(v3_m3 as number).toFixed(2)} m³` : '—'} × t={SEED3_TIME_H} h → {seed3FeedKg.toFixed(0)} kg
                  </div>
                  <div style={{ fontSize: 12, color: '#666' }}>
                    Seed2: V={isFinite(v2_m3 || NaN) ? `${(v2_m3 as number).toFixed(2)} m³` : '—'} × t={SEED2_TIME_H} h → {seed2FeedKg.toFixed(0)} kg
                  </div>
                  <div style={{ marginTop: 2 }}>
                    Suggested volume: <b>{typeof suggestedCarbonBatchV === 'number' ? `${suggestedCarbonBatchV.toFixed(2)} m³` : '—'}</b>
                    {` (Production ${(typeof totalFeedKg==='number'? totalFeedKg:0).toFixed(0)} kg + Seeds ${(seed2FeedKg + seed3FeedKg).toFixed(0)} kg) ÷ conc ${feedConc} g/L`}
                    {(fe.total_glucose_feed_kg==null || fe.feed_glucose_concentration_g_L==null) ? <span style={{ color: '#999' }}> · defaults applied</span> : null}
                  </div>
                </>
              ) : (
                <div>Connect this tank to Production to enable carbon sizing. Otherwise, set Batch Volume manually.</div>
              )}
            </div>
          )}
        </>
      )}
      <div style={{ color: '#555', margin: '6px 0' }}>Computed capacity: {isFinite(capacity_m3) ? `${capacity_m3.toFixed(2)} m³` : '—'}</div>
      <button onClick={() => onAdd({ label, mode, flow_m3_h: typeof flow === 'number' ? flow : undefined, hold_time_h: typeof holdH === 'number' ? holdH : undefined, batch_volume_m3: typeof batchV === 'number' ? batchV : (mode === 'carbon' && typeof suggestedCarbonBatchV === 'number' ? suggestedCarbonBatchV : undefined), headroom_fraction: headroom, capacity_m3: Number.isFinite(capacity_m3) ? capacity_m3 : 0 })}>
        {submitLabel ?? 'Add to graph'}
      </button>
    </div>
  );
}

export function HoldingTankForm({ onAdd, initial, submitLabel }: {
  onAdd: (vals: { label?: string; based_on_production?: boolean; headroom_fraction?: number; capacity_m3: number }) => void;
  initial?: { label?: string; based_on_production?: boolean; headroom_fraction?: number; capacity_m3?: number };
  submitLabel?: string;
}) {
  const nodes = useGraphStore(s => s.nodes);
  const prod = nodes.find(n => (n.data as any)?.fermentation);
  const workingV = (prod?.data as any)?.fermentation?.working_volume_m3 as number | undefined;
  const [label, setLabel] = useState<string>(initial?.label ?? 'Holding Tank');
  const [basedOnProduction, setBasedOnProduction] = useState<boolean>(initial?.based_on_production ?? true);
  const [headroom, setHeadroom] = useState<number>(initial?.headroom_fraction ?? 0.1);
  const capacity_m3 = React.useMemo(() => {
    if (basedOnProduction && typeof workingV === 'number') {
      return workingV * (1 + (headroom ?? 0));
    }
    return (initial?.capacity_m3 as number | undefined) ?? NaN;
  }, [basedOnProduction, headroom, workingV, initial]);
  return (
    <div>
      <LabeledRow label="Label">
        <input type="text" value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g., Harvest Holding Tank" />
      </LabeledRow>
      <LabeledRow label="Based on Production?">
        <input type="checkbox" checked={basedOnProduction} onChange={(e) => setBasedOnProduction(e.target.checked)} />
      </LabeledRow>
      <LabeledRow label="Headroom (frac)">
        <input type="number" min={0} max={1} step={0.01} value={headroom} onChange={(e) => setHeadroom(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#555', margin: '6px 0' }}>Computed capacity: {isFinite(capacity_m3) ? `${capacity_m3.toFixed(2)} m³` : '—'}</div>
      <button onClick={() => onAdd({ label, based_on_production: basedOnProduction, headroom_fraction: headroom, capacity_m3: Number.isFinite(capacity_m3) ? capacity_m3 : (workingV || 0) })}>
        {submitLabel ?? 'Add to graph'}
      </button>
    </div>
  );
}

export function PumpForm({ onAdd, initial, submitLabel }: {
  onAdd: (vals: { flow_m3_h: number; head_m: number; efficiency: number; power_kW: number }) => void;
  initial?: { flow_m3_h?: number; head_m?: number; efficiency?: number; power_kW?: number };
  submitLabel?: string;
}) {
  const [flow, setFlow] = useState<number>(initial?.flow_m3_h ?? 10);
  const [head, setHead] = useState<number>(initial?.head_m ?? 30);
  const [eff, setEff] = useState<number>(initial?.efficiency ?? 0.7);
  const power_kW = React.useMemo(() => {
    const Q = (flow ?? 0) / 3600; // m³/s
    const H = head ?? 0; // m
    const eta = Math.max(0.05, Math.min(eff || 0.7, 0.95));
    // P(kW) = rho*g*Q*H / (1000) / eta, with rho=1000 kg/m³, g=9.81 m/s²
    return (1000 * 9.81 * Q * H) / 1000 / eta;
  }, [flow, head, eff]);
  return (
    <div>
      <LabeledRow label="Flow (m³/h)">
        <input type="number" min={0} step={0.1} value={flow} onChange={(e) => setFlow(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Head (m)">
        <input type="number" min={0} step={0.5} value={head} onChange={(e) => setHead(parseFloat(e.target.value))} />
      </LabeledRow>
      <LabeledRow label="Efficiency (0-1)">
        <input type="number" min={0.05} max={0.95} step={0.01} value={eff} onChange={(e) => setEff(parseFloat(e.target.value))} />
      </LabeledRow>
      <div style={{ color: '#555', margin: '6px 0' }}>Estimated power: {power_kW.toFixed(2)} kW</div>
      <button onClick={() => onAdd({ flow_m3_h: flow, head_m: head, efficiency: eff, power_kW })}>{submitLabel ?? 'Add to graph'}</button>
    </div>
  );
}
