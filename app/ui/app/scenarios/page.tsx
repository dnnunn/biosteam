'use client';
import { useState } from 'react';

export default function Scenarios() {
  const [yamlText, setYamlText] = useState(`name: OPN_demo\nversion: '0.1'\nunits: []\nstreams: []\nassumptions: {}\nuncertainty: {}`);
  const [result, setResult] = useState<any>(null);

  const run = async () => {
    const scenario = yamlToJson(yamlText);
    const r = await fetch('http://localhost:8000/runs', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, analyses: ['deterministic'] })
    }).then(r => r.json());
    setResult(r);
  };

  return (
    <main style={{ padding: 24 }}>
      <h2>Scenario runner</h2>
      <textarea style={{ width: '100%', height: 240 }} value={yamlText} onChange={e=>setYamlText(e.target.value)} />
      <div style={{ marginTop: 8 }}>
        <button onClick={run}>Run</button>
      </div>
      {result && (
        <pre style={{marginTop:16, background:'#f6f6f6', padding:12}}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </main>
  );
}

function yamlToJson(text: string) {
  // extremely naive; replace later with proper yaml in server-side; here we expect JSON-compatible string
  try { return JSON.parse(text); } catch {
    // fallback dummy
    return { name: 'OPN_demo', version: '0.1', units: [], streams: [], assumptions: {}, uncertainty: {} };
  }
}
