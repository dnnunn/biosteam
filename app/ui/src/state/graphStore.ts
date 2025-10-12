import { create } from 'zustand';
import { nanoid } from 'nanoid/non-secure';
import type { Edge, Node } from 'reactflow';

type GraphState = {
  nodes: Node[];
  edges: Edge[];
  selectedNode?: { node: Node };
  setNodes: (changes: any) => void;
  setEdges: (changes: any) => void;
  addNode: (label: string, initial?: Record<string, unknown>) => void;
  setNodeData: (id: string, data: Record<string, unknown>) => void;
  toOverrides: () => Record<string, unknown>;
};

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [
    { id: 'front_end', position: { x: 200, y: 120 }, data: { label: 'Front-End' }, type: 'default' }
  ],
  edges: [],
  setNodes: (changes) => set((state) => ({ nodes: applyChanges(state.nodes, changes) })),
  setEdges: (changes) => set((state) => ({ edges: applyChanges(state.edges, changes) })),
  addNode: (label, initial) => set((state) => ({
    nodes: state.nodes.concat({ id: nanoid(6), position: { x: 300, y: 200 }, data: { label, ...initial }, type: 'default' })
  })),
  setNodeData: (id, data) => set((state) => ({
    nodes: state.nodes.map(n => n.id === id ? { ...n, data: { ...(n.data || {}), ...data } } : n)
  })),
  toOverrides: () => {
    // Map a simple DSP03 macro node to baseline_overrides for /runs/front_end
    const dsp03Node = get().nodes.find(n => (n.data as any)?.dsp03 || (n.data as any)?.cost_buffer_id);
    const dsp03 = (dsp03Node?.data as any)?.dsp03 || {};
    const cost_buffer_id = (dsp03Node?.data as any)?.cost_buffer_id;
    const overrides: any = {};
    if (dsp03Node) {
      overrides.dsp03 = {
        buffers: {
          df: {
            use_planner: true,
            auto_plan: true,
            target_ionic_strength_mM: dsp03.target_ionic_strength_mM ?? 5.0,
            df_time_h_target: 10.0,
            headroom_fraction: 0.2,
            cost_from_registry: true,
            cost_buffer_id: cost_buffer_id ?? 'tris_hcl_pH7p5_50mM'
          }
        }
      };
    }
    return overrides;
  }
}));

function applyChanges<T extends { id: string }>(current: T[], changes: any): T[] {
  // Minimal no-op diff handler for placeholder; React Flow will pass arrays when directly using setNodes/setEdges with new values.
  if (Array.isArray(changes)) return changes as T[];
  return current;
}

