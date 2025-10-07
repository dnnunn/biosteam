import { ReactNode } from 'react';

export default function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section style={{ border: '1px solid #d1d5db', borderRadius: 6, padding: 16, marginBottom: 16 }}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      {children}
    </section>
  );
}
