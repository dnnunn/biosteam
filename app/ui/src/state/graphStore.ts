"use client";
import { create } from 'zustand';
import { nanoid } from 'nanoid/non-secure';
import type { Edge, Node, EdgeChange, NodeChange } from 'reactflow';
import { applyNodeChanges, applyEdgeChanges } from 'reactflow';

type GraphState = {
  nodes: Node[];
  edges: Edge[];
  selectedNodes: Node[];
  showMiniMap: boolean;
  rfKey: number; // force remount ReactFlow when needed
  history: { nodes: Node[]; edges: Edge[]; selectedIds: string[] }[];
  setNodes: (changes: NodeChange[] | Node[] | ((nodes: Node[]) => Node[])) => void;
  setEdges: (changes: EdgeChange[] | Edge[] | ((edges: Edge[]) => Edge[])) => void;
  addNode: (label: string, initial?: Record<string, unknown>, position?: { x: number; y: number }) => string;
  setSelectedNode: (node: Node | undefined) => void;
  setSelectedNodes: (nodes: Node[]) => void;
  setNodeData: (id: string, data: Record<string, unknown>) => void;
  toggleMiniMap: () => void;
  undo: () => void;
  reset: () => void;
  hardReset: () => void;
  toOverrides: () => Record<string, unknown>;
  // UI: pending add-unit modal state
  pendingAdd: { unit: { id: string; label: string; iconKey: string; category?: string }; position?: { x: number; y: number } } | null;
  openAddModal: (unit: { id: string; label: string; iconKey: string; category?: string }, position?: { x: number; y: number }) => void;
  closeAddModal: () => void;
  // Helpers
  alignBelowCentered: (parentId: string, childId: string, gap?: number, maxTries?: number) => void;
};

const STORE_KEY = 'designer_graph_v2';

function initialState(): Pick<GraphState, 'nodes' | 'edges' | 'selectedNodes' | 'showMiniMap' | 'history'> {
  try {
    if (typeof window !== 'undefined') {
      const raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as { nodes?: Node[]; edges?: Edge[]; selectedIds?: string[]; showMiniMap?: boolean };
        const selectedIds = new Set(parsed.selectedIds || []);
        const nodes = (parsed.nodes || []).map((n) => ({ ...n, selected: selectedIds.has(n.id) }));
        const selectedNodes = nodes.filter((n) => n.selected);
        return { nodes, edges: parsed.edges || [], selectedNodes, showMiniMap: !!parsed.showMiniMap, history: [] };
      }
    }
  } catch {}
  // Start with a blank canvas by default
  return { nodes: [], edges: [], selectedNodes: [], showMiniMap: false, history: [] };
}

function persistState(nodes: Node[], edges: Edge[], selectedNodes: Node[], showMiniMap: boolean) {
  try {
    if (typeof window === 'undefined') return;
    const selectedIds = (selectedNodes || []).map((n) => n.id);
    localStorage.setItem(STORE_KEY, JSON.stringify({ nodes, edges, selectedIds, showMiniMap }));
  } catch {}
}

export const useGraphStore = create<GraphState>((set, get) => ({
  ...initialState(),
  rfKey: 0,
  pendingAdd: null,
  openAddModal: (unit, position) => set(() => ({ pendingAdd: { unit, position } })),
  closeAddModal: () => set(() => ({ pendingAdd: null })),
  alignBelowCentered: (parentId, childId, gap = 24, maxTries = 10) => {
    let tries = 0;
    const attempt = () => {
      tries += 1;
      const { nodes } = get();
      const parent = nodes.find((n) => n.id === parentId);
      const child = nodes.find((n) => n.id === childId);
      if (!parent || !child) return; // nothing to do
      const pw = (parent as any).width as number | undefined;
      const ph = (parent as any).height as number | undefined;
      const cw = (child as any).width as number | undefined;
      // Wait until React Flow measures node dimensions
      if (!pw || !ph || !cw) {
        if (tries < maxTries) {
          setTimeout(attempt, 50);
        }
        return;
      }
      const targetX = (parent.position?.x ?? 0) + (pw - cw) / 2;
      const targetY = (parent.position?.y ?? 0) + ph + gap;
      get().setNodes((curr) => curr.map((n) => (n.id === childId ? ({ ...n, position: { x: targetX, y: targetY } }) : n)) as any);
    };
    // kick off alignment once, then it will retry briefly until sizes exist
    setTimeout(attempt, 0);
  },
  setNodes: (changes) =>
    set((state) => {
      const prev = snapshot(state);
      const nodes = (() => {
        if (typeof changes === 'function') return (changes as (nodes: Node[]) => Node[])(state.nodes);
        if (Array.isArray(changes) && changes.length > 0) {
          const first: any = (changes as any[])[0];
          // Detect React Flow NodeChange[] vs Node[]
          // NodeChange.type is like 'position' | 'select' | 'dimensions' | ...; Node.type is our node type, e.g., 'unit'.
          const looksLikeNodeChange = typeof first?.type === 'string' && first.type !== 'unit';
          if (looksLikeNodeChange) {
            return applyNodeChanges(changes as NodeChange[], state.nodes) as unknown as Node[];
          }
        }
        return changes as Node[];
      })();
      const history = clampHistory(state.history.concat(prev));
      persistState(nodes, state.edges, state.selectedNodes, state.showMiniMap);
      return { nodes, history };
    }),
  setEdges: (changes) =>
    set((state) => {
      const prev = snapshot(state);
      const edges =
        typeof changes === 'function'
          ? (changes as (edges: Edge[]) => Edge[])(state.edges)
          : (Array.isArray(changes) && changes.length > 0 && !('source' in (changes as any)[0] && 'target' in (changes as any)[0])
              ? (applyEdgeChanges(changes as EdgeChange[], state.edges) as unknown as Edge[])
              : (changes as Edge[]));
      const history = clampHistory(state.history.concat(prev));
      persistState(state.nodes, edges, state.selectedNodes, state.showMiniMap);
      return { edges, history };
    }),
  addNode: (label, initial, position) => {
    const id = nanoid(6);
    const node: Node = { id, position: position ?? { x: 300, y: 200 }, data: { label, iconKey: label, ...initial }, type: 'unit' } as unknown as Node;
    set((state) => {
      const prev = snapshot(state);
      const nodes = state.nodes.concat(node);
      const selectedNodes = [node];
      const history = clampHistory(state.history.concat(prev));
      persistState(nodes, state.edges, selectedNodes, state.showMiniMap);
      return { nodes, selectedNodes, history };
    });
    return id;
  },
  setSelectedNode: (node) => set((state) => {
    const selectedNodes = node ? [node] : [];
    persistState(state.nodes, state.edges, selectedNodes, state.showMiniMap);
    return { selectedNodes };
  }),
  setSelectedNodes: (nodesSel) => set((state) => {
    const selectedNodes = nodesSel || [];
    persistState(state.nodes, state.edges, selectedNodes, state.showMiniMap);
    return { selectedNodes };
  }),
  setNodeData: (id, data) => set((state) => {
    const prev = snapshot(state);
    const nodes = state.nodes.map(n => n.id === id ? { ...n, data: { ...(n.data || {}), ...data } } : n);
    const history = clampHistory(state.history.concat(prev));
    persistState(nodes, state.edges, state.selectedNodes, state.showMiniMap);
    return { nodes, history };
  }),
  toggleMiniMap: () => set((state) => {
    const showMiniMap = !state.showMiniMap;
    persistState(state.nodes, state.edges, state.selectedNodes, showMiniMap);
    return { showMiniMap };
  }),
  undo: () => set((state) => {
    const last = state.history[state.history.length - 1];
    if (!last) return {};
    const history = state.history.slice(0, -1);
    const selectedIds = new Set(last.selectedIds || []);
    const nodes = (last.nodes || []).map((n) => ({ ...n, selected: selectedIds.has(n.id) }));
    const selectedNodes = nodes.filter((n) => n.selected);
    persistState(nodes, last.edges || [], selectedNodes, state.showMiniMap);
    // bump rfKey to guarantee ReactFlow remount in tricky cases
    return { nodes, edges: last.edges || [], selectedNodes, history, rfKey: state.rfKey + 1 };
  }),
  reset: () => set((state) => {
    persistState([], [], [], false);
    // bump rfKey to guarantee ReactFlow remount
    return { nodes: [], edges: [], selectedNodes: [], history: [], showMiniMap: false, rfKey: state.rfKey + 1 };
  }),
  hardReset: () => set((state) => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('designer_graph_v1');
        localStorage.removeItem('designer_graph_v2');
      }
    } catch {}
    return { nodes: [], edges: [], selectedNodes: [], history: [], showMiniMap: false, rfKey: state.rfKey + 1 };
  }),
  toOverrides: () => {
    const nodes = get().nodes;
    const overrides: any = {};

    // Seed and fermentation: take latest matching node(s)
    const seedNode = [...nodes].reverse().find(n => (n.data as any)?.seed);
    const fermNode = [...nodes].reverse().find(n => (n.data as any)?.fermentation || n.id === 'front_end');
    if (seedNode && (seedNode.data as any).seed) {
      const seed = (seedNode.data as any).seed || {};
      overrides.seed = { feed: { media_type: seed.media_type, carbon_source: seed.carbon_source } };
    }
    if (fermNode) {
      const fe = (fermNode.data as any).fermentation || (fermNode.data as any).fe || {};
      if (fe && (fe.media_type || fe.carbon_source)) {
        overrides.fermentation = Object.assign({}, overrides.fermentation || {}, { feed: { media_type: fe.media_type, carbon_source: fe.carbon_source } });
      }
      if (typeof fe.fermenter_volume_m3 === 'number' || typeof fe.working_volume_m3 === 'number') {
        overrides.fermentation = Object.assign({}, overrides.fermentation || {}, {
          vessel: {
            total_volume_m3: fe.fermenter_volume_m3,
            working_volume_m3: fe.working_volume_m3,
          },
        });
      }
      if (typeof fe.product_titre_g_L === 'number') {
        overrides.fermentation = Object.assign({}, overrides.fermentation || {}, {
          product_titre_g_L: fe.product_titre_g_L,
        });
      }
      if (typeof fe.temperature_c === 'number') {
        overrides.fermentation = Object.assign({}, overrides.fermentation || {}, {
          temperature_c: fe.temperature_c,
        });
      }
      if (typeof fe.fermentation_time_h === 'number') {
        const existing = (overrides.fermentation as any)?.derived || {};
        overrides.fermentation = Object.assign({}, overrides.fermentation || {}, {
          derived: Object.assign({}, existing, { fermentation_time_h: fe.fermentation_time_h })
        });
      }
      // Optional feed parameters for carbon storage sizing
      const derivedPatch: any = {};
      if (typeof fe.feed_glucose_concentration_g_L === 'number') derivedPatch.feed_carbon_concentration_g_per_l = fe.feed_glucose_concentration_g_L;
      if (typeof fe.total_glucose_feed_kg === 'number') derivedPatch.total_glucose_feed_kg = fe.total_glucose_feed_kg;
      if (Object.keys(derivedPatch).length) {
        const existing = (overrides.fermentation as any)?.derived || {};
        overrides.fermentation = Object.assign({}, overrides.fermentation || {}, { derived: Object.assign({}, existing, derivedPatch) });
      }
    }

    // Cell removal configuration (disc stack, polish, etc.)
    const cellNode = [...nodes].reverse().find(n => (n.data as any)?.cell_removal);
    if (cellNode) {
      const cr = (cellNode.data as any).cell_removal || {};
      const cfg: any = { method: cr.method };
      // Optional helpers to influence auto route
      const feed: any = {};
      if (typeof cr.solids_vv === 'number') feed.solids_vv = cr.solids_vv;
      if (typeof cr.volume_m3 === 'number') feed.volume_m3 = cr.volume_m3;
      if (Object.keys(feed).length) cfg.feed = feed;
      if (cr.membranes_required) cfg.membranes_required = true;
      if (typeof cr.post_turbidity_spec === 'number') cfg.post_turbidity_spec = cr.post_turbidity_spec;
      overrides.cell_removal = cfg;

      // If OD600/DCW entered here, propagate to fermentation derived and estimate solids_vv when missing.
      const od = (cr as any).od600_target as number | undefined;
      const od2dcw = (cr as any).od_to_dcw_g_per_l_per_od as number | undefined;
      const dcwConc = (cr as any).dcw_concentration_g_per_l as number | undefined;
      if (od || dcwConc) {
        const derived: any = {};
        if (typeof od === 'number') derived.od600_target = od;
        if (typeof od2dcw === 'number') derived.od_to_dcw_g_per_l_per_od = od2dcw;
        if (typeof dcwConc === 'number') derived.dcw_concentration_g_per_l = dcwConc;
        overrides.fermentation = Object.assign({}, overrides.fermentation || {}, { derived: Object.assign({}, (overrides.fermentation as any)?.derived || {}, derived) });
        // Backfill solids_vv if not explicitly set: solids_vv ≈ dcw / 750 g/L
        const dcw = (typeof dcwConc === 'number') ? dcwConc : (typeof od === 'number' && typeof od2dcw === 'number') ? od * od2dcw : undefined;
        if (dcw && feed && typeof feed.solids_vv !== 'number') {
          const svv = dcw / 750.0;
          cfg.feed = Object.assign({}, cfg.feed || {}, { solids_vv: svv });
        }
      }
    }

    // DSP01: pre-capture conditioning; push ionic strength to capture feed conductivity
    const dsp01Node = nodes.find(n => (n.data as any)?.dsp01);
    let preLoadIonic: number | undefined = undefined;
    if (dsp01Node) {
      const dsp01 = (dsp01Node.data as any).dsp01 || {};
      if (typeof dsp01.ionic_strength_mM === 'number') preLoadIonic = dsp01.ionic_strength_mM;
      // Also allow setting concentration route explicitly
      overrides.concentration = overrides.concentration || { method: 'uf_df' };
    }

    // DSP02: capture configuration (AEX defaults; chitosan not yet exposed in UI)
    const dsp02Node = nodes.find(n => (n.data as any)?.dsp02);
    if (dsp02Node) {
      const d2 = (dsp02Node.data as any).dsp02 || {};
      overrides.capture = overrides.capture || {};
      overrides.capture.method = overrides.capture.method || 'aex';
      if (preLoadIonic !== undefined) {
        overrides.capture.feed = Object.assign({}, overrides.capture.feed || {}, { conductivity_mM: preLoadIonic });
      }
      overrides.capture.aex = Object.assign({}, overrides.capture.aex || {}, {
        // Map UI fields to AEX specs
        cond_bind_mM_max: d2.load_ionic_strength_mM ?? preLoadIonic,
        wash1_bv: d2.wash_volumes,
        wash2_bv: undefined,
        elution_bv: d2.elute_volumes,
        elute_salt_mM: d2.elute_ionic_strength_mM,
      });
    } else if (preLoadIonic !== undefined) {
      // If no explicit DSP02 node, still let capture feed use the DSP01 target
      overrides.capture = overrides.capture || {};
      overrides.capture.feed = Object.assign({}, overrides.capture.feed || {}, { conductivity_mM: preLoadIonic });
    }

    // Concentration (DSP01) step — prefer SPTFF when set; else UF/DF params
    const concNode = nodes.find(n => (n.data as any)?.concentration);
    if (concNode) {
      const conc = (concNode.data as any).concentration || {};
      const route = (conc as any).route as string | undefined;
      if (route === 'sptff' && (conc as any).sptff) {
        overrides.concentration = {
          route: 'sptff',
          sptff: { ...(conc as any).sptff },
        } as any;
      } else {
        overrides.concentration = Object.assign({}, overrides.concentration || {}, {
          method: 'uf_df',
          uf_concentration: Object.assign({}, (overrides.concentration as any)?.uf_concentration || {}, {
            volume_reduction_ratio: (conc as any).volume_reduction_ratio,
            product_recovery_fraction: (conc as any).product_recovery_fraction,
            flux_lmh: (conc as any).flux_lmh,
            tmp_bar: (conc as any).tmp_bar,
          }),
        });
      }
    }

    // DSP03: post-capture TFF planning with buffer registry id and targets
    const dsp03Node = nodes.find(n => (n.data as any)?.dsp03_params);
    if (dsp03Node) {
      const params = ((dsp03Node.data as any).dsp03_params) || {};
      overrides.dsp03 = { parameters: { ...params } } as any;
    }

    // Optional AEX membrane polish (flow-through) — capture params for future use.
    const aexMemNode = nodes.find(n => (n.data as any)?.aex_membrane);
    if (aexMemNode) {
      const aex: any = (aexMemNode.data as any).aex_membrane || {};
      overrides.dsp04 = overrides.dsp04 || {} as any;
      (overrides.dsp04 as any).membrane_aex = {
        placement: aex.placement || 'after_sptff',
        parameters: {
          q_DNA_mg_per_mL: aex.q_DNA_mg_per_mL,
          q_HCP_mg_per_mL: aex.q_HCP_mg_per_mL,
          utilization: aex.utilization,
          salt_derate_HCP: aex.salt_derate_HCP,
          pre_load_salt_mM: aex.pre_load_salt_mM,
          pre_load_conductivity_mScm: aex.pre_load_conductivity_mScm,
          MV_per_min: aex.MV_per_min,
          deltaP_cap_bar: aex.deltaP_cap_bar,
          membrane_volume_per_module_L: aex.membrane_volume_per_module_L,
          max_flow_per_module_Lph: aex.max_flow_per_module_Lph,
          module_cost_usd: aex.module_cost_usd,
          hold_up_L_per_module: aex.hold_up_L_per_module,
          product_adsorption_loss_frac: aex.product_adsorption_loss_frac,
          t_window_h: aex.t_window_h,
          buffer_fee_usd_per_m3: aex.buffer_fee_usd_per_m3,
          labor_h_per_batch: aex.labor_h_per_batch,
          labor_rate_usd_per_h: aex.labor_rate_usd_per_h,
          waste_fee_usd_per_tonne: aex.waste_fee_usd_per_tonne,
          dna_in_mg_per_l: aex.dna_in_mg_per_l,
          hcp_in_g_per_l: aex.hcp_in_g_per_l,
          assumed_feed_volume_m3: aex.assumed_feed_volume_m3,
        }
      };
    }

    // Seed stages: collect inoculum params and compute volumes if possible
    const seedNodes = nodes.filter(n => (n.data as any)?.seed);
    if (seedNodes.length) {
      const workingV = ((fermNode?.data as any)?.fermentation || {})?.working_volume_m3 as number | undefined;
      const stages = seedNodes
        .map(n => ({
          stage: (n.data as any).seed?.stage as number | undefined,
          inoculum_fraction: (n.data as any).seed?.inoculum_fraction as number | undefined,
          temperature_c: (n.data as any).seed?.temperature_c as number | undefined,
        }))
        .filter(s => s.stage === 1 || s.stage === 2 || s.stage === 3)
        .sort((a, b) => (a.stage! - b.stage!));
      // Compute chain volumes if working volume and inocula available
      let v3: number | undefined = undefined;
      let v2: number | undefined = undefined;
      let v1: number | undefined = undefined;
      const s3 = stages.find(s => s.stage === 3);
      const s2 = stages.find(s => s.stage === 2);
      const s1 = stages.find(s => s.stage === 1);
      if (workingV && s3?.inoculum_fraction != null) v3 = workingV * s3.inoculum_fraction;
      if (v3 && s2?.inoculum_fraction != null) v2 = v3 * s2.inoculum_fraction;
      if (v2 && s1?.inoculum_fraction != null) v1 = v2 * s1.inoculum_fraction;
      overrides.seed = Object.assign({}, overrides.seed || {}, {
        stages: [
          s1 ? {
            stage: 1,
            inoculum_fraction: s1.inoculum_fraction,
            temperature_c: s1.temperature_c,
            duration_h: (nodes.find(n=> (n.data as any)?.seed?.stage === 1)?.data as any)?.seed?.duration_h,
            computed_volume_m3: v1
          } : undefined,
          s2 ? {
            stage: 2,
            inoculum_fraction: s2.inoculum_fraction,
            temperature_c: s2.temperature_c,
            duration_h: (nodes.find(n=> (n.data as any)?.seed?.stage === 2)?.data as any)?.seed?.duration_h,
            computed_volume_m3: v2
          } : undefined,
          s3 ? {
            stage: 3,
            inoculum_fraction: s3.inoculum_fraction,
            temperature_c: s3.temperature_c,
            duration_h: (nodes.find(n=> (n.data as any)?.seed?.stage === 3)?.data as any)?.seed?.duration_h,
            computed_volume_m3: v3
          } : undefined,
        ].filter(Boolean)
      });
    }

    // Utilities: holding & mixing tanks and pumps (allow multiple)
    const holdingTanks = nodes.filter(n => (n.data as any)?.holding_tank).map(n => (n.data as any).holding_tank);
    const mixingTanks = nodes.filter(n => (n.data as any)?.mixing_tank).map(n => (n.data as any).mixing_tank);
    const pumps = nodes.filter(n => (n.data as any)?.pump).map(n => (n.data as any).pump);
    if (holdingTanks.length || mixingTanks.length || pumps.length) {
      overrides.utilities = overrides.utilities || {};
      if (holdingTanks.length) overrides.utilities.holding_tanks = holdingTanks;
      if (mixingTanks.length) overrides.utilities.mixing_tanks = mixingTanks;
      if (pumps.length) overrides.utilities.pumps = pumps;
    }

    return overrides;
  }
}));

function snapshot(state: GraphState) {
  return {
    nodes: JSON.parse(JSON.stringify(state.nodes)),
    edges: JSON.parse(JSON.stringify(state.edges)),
    selectedIds: (state.selectedNodes || []).map((n) => n.id),
  };
}

function clampHistory(h: GraphState['history']) {
  const MAX = 20;
  if (h.length <= MAX) return h;
  return h.slice(h.length - MAX);
}
