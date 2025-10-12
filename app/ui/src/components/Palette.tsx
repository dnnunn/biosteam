"use client";
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useGraphStore } from '@/state/graphStore';

export function Palette() {
  const { data } = useQuery({ queryKey: ['buffers'], queryFn: () => api.listBuffers() });
  const addNode = useGraphStore((s) => s.addNode);

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Palette</h3>
      <p style={{ color: '#666' }}>Buffers (click to add DSP03 macro):</p>
      <div style={{ maxHeight: 320, overflow: 'auto' }}>
        {(data || []).map((b) => (
          <div key={b.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 4px', borderBottom: '1px solid #eee', cursor: 'pointer' }}
            onClick={() => addNode('DSP03', { cost_buffer_id: b.id })}
            title={`pH ${b.pH}${b.estimated_cost_usd_per_m3 ? ` · ~$${b.estimated_cost_usd_per_m3.toFixed(2)}/m³` : ''}`}>
            <span>{b.name}</span>
            <span style={{ color: '#999' }}>{b.pH ? `pH ${b.pH}` : ''}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

