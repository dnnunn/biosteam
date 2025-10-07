const API = process.env.NEXT_PUBLIC_API ?? 'http://localhost:8000';

export async function listScenarios() {
  const res = await fetch(`${API}/scenarios`);
  if (!res.ok) throw new Error('failed to load scenarios');
  return res.json();
}

export async function createRun(payload: unknown) {
  const res = await fetch(`${API}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('failed to create run');
  return res.json();
}
