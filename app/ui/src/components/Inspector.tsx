"use client";
import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useGraphStore } from '@/state/graphStore';

export function Inspector() {
  const selected = useGraphStore((s) => s.selectedNode);
  const setNodeData = useGraphStore((s) => s.setNodeData);
  const [bufferId, setBufferId] = useState<string | undefined>(undefined);
  const { data: recs } = useQuery({
    queryKey: ['buffer_rec', bufferId],
    queryFn: () => (bufferId ? api.bufferRecommendations(bufferId) : Promise.resolve(undefined)),
    enabled: !!bufferId,
  });

  const node = selected?.node;
  const dsp03Data = useMemo(() => (node?.data?.dsp03 ?? {}), [node]);

  if (!node) return <div><h3 style={{ marginTop: 0 }}>Inspector</h3><p>Select a node to edit parameters.</p></div>;

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Inspector</h3>
      <p style={{ margin: '8px 0' }}>Selected: <b>{node.type || node.data?.label || node.id}</b></p>

      <div style={{ borderTop: '1px solid #eee', paddingTop: 8 }}>
        <label>DSP03 Buffer ID</label>
        <input
          value={bufferId ?? dsp03Data.cost_buffer_id ?? ''}
          onChange={(e) => setBufferId(e.target.value)}
          placeholder="e.g. tris_hcl_pH7p5_50mM"
          style={{ width: '100%', padding: 6, marginTop: 4 }}
        />
        <button style={{ marginTop: 8 }} onClick={() => bufferId && setNodeData(node.id, { dsp03: { ...dsp03Data, cost_buffer_id: bufferId } })}>Apply Buffer</button>
      </div>

      <div style={{ borderTop: '1px solid #eee', paddingTop: 8, marginTop: 8 }}>
        <button disabled={!bufferId} onClick={() => bufferId && setNodeData(node.id, { dsp03: { ...dsp03Data, use_planner: true, auto_plan: true, target_ionic_strength_mM: recs?.recommended_target_ionic_strength_mM, cost_from_registry: true } })}>
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
    </div>
  );
}

