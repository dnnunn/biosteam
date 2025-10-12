"use client";
import React, { useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useGraphStore } from '@/state/graphStore';

export function ResultsPanel() {
  const overrides = useGraphStore((s) => s.toOverrides());
  const { data, mutate, isPending } = useMutation({
    mutationFn: () => api.runFrontEnd(overrides),
  });

  const onRun = useCallback(() => mutate(), [mutate]);

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={onRun} disabled={isPending}>{isPending ? 'Running…' : 'Run'}</button>
        <small style={{ color: '#666' }}>Sends overrides to /runs/front_end; shows TEA results.</small>
      </div>
      {data && (
        <div style={{ marginTop: 8 }}>
          <div style={{ display: 'flex', gap: 24 }}>
            <div>Cost/kg: <b>{fmt(data.cost_per_kg_usd)}</b></div>
            <div>Materials/batch: <b>{fmt(data.materials_cost_per_batch_usd)}</b></div>
            <div>Materials/kg: <b>{fmt(data.materials_cost_per_kg_usd)}</b></div>
          </div>
          <div style={{ marginTop: 8 }}>
            <details>
              <summary>Material cost breakdown</summary>
              <ul>
                {Object.entries(data.material_cost_breakdown || {}).map(([k, v]) => (
                  <li key={k}>{k}: {fmt(v as number)}</li>
                ))}
              </ul>
            </details>
          </div>
          <div style={{ marginTop: 8 }}>
            <details>
              <summary>DSP03 notes</summary>
              <ul>
                {(data.dsp03_notes || []).map((n: string, i: number) => (<li key={i}>{n}</li>))}
              </ul>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}

function fmt(x?: number | null) {
  if (x == null) return '—';
  return `$${Number(x).toFixed(2)}`;
}

