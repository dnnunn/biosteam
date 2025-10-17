"use client";
import React from 'react';
import { GraphCanvas } from '@/components/GraphCanvas';
import { UnitLibrary } from '@/components/UnitLibrary';
import { Inspector } from '@/components/Inspector';
import { ResultsPanel } from '@/components/ResultsPanel';

export default function DesignerPage() {
  const [expanded, setExpanded] = React.useState(false);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 360px', gridTemplateRows: `1fr ${expanded ? '240px' : '40px'}`, height: '100vh' }}>
      <aside style={{ borderRight: '1px solid #eee', padding: 8 }}>
        <UnitLibrary />
      </aside>
      <section style={{ position: 'relative' }}>
        <GraphCanvas />
      </section>
      <aside style={{ borderLeft: '1px solid #eee', padding: 8 }}>
        <Inspector />
      </aside>
      <div style={{ gridColumn: '1 / span 3', borderTop: '1px solid #eee', padding: 8 }}>
        <ResultsPanel expanded={expanded} onExpand={setExpanded} />
      </div>
    </div>
  );
}
