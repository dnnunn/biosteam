import { API_BASE } from '@/lib/config';

export const api = {
  async listBuffers() {
    const res = await fetch(`${API_BASE}/buffers`);
    if (!res.ok) throw new Error('Failed to fetch buffers');
    return res.json();
  },
  async bufferRecommendations(id: string) {
    const res = await fetch(`${API_BASE}/buffers/${encodeURIComponent(id)}/recommendations`);
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    return res.json();
  },
  async runFrontEnd(baseline_overrides: unknown) {
    const res = await fetch(`${API_BASE}/runs/front_end`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ baseline_overrides, mode: 'baseline' })
    });
    if (!res.ok) throw new Error('Run failed');
    return res.json();
  }
};

