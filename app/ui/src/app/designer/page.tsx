"use client";
import React from 'react';
import { GraphCanvas } from '@/components/GraphCanvas';
import { Palette } from '@/components/Palette';
import { Inspector } from '@/components/Inspector';
import { ResultsPanel } from '@/components/ResultsPanel';

export default function DesignerPage() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 360px', gridTemplateRows: '1fr 240px', height: '100vh' }}>
      <aside style={{ borderRight: '1px solid #eee', padding: 8 }}>
        <Palette />
      </aside>
      <section style={{ position: 'relative' }}>
        <GraphCanvas />
      </section>
      <aside style={{ borderLeft: '1px solid #eee', padding: 8 }}>
        <Inspector />
      </aside>
      <div style={{ gridColumn: '1 / span 3', borderTop: '1px solid #eee', padding: 8 }}>
        <ResultsPanel />
      </div>
    </div>
  );
}

