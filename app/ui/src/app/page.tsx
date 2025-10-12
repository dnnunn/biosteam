import Link from 'next/link';

export default function HomePage() {
  return (
    <main style={{ padding: 24 }}>
      <h1 style={{ margin: 0 }}>BioSTEAM Designer</h1>
      <p style={{ color: '#666' }}>Design and run the front-end process with block-based controls.</p>
      <ul>
        <li>
          <Link href="/designer">Open Designer</Link>
        </li>
      </ul>
    </main>
  );
}

