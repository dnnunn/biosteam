import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: 24 }}>
      <h1>BDSTEAM</h1>
      <p>Prototype UI — run scenarios and view results.</p>
      <ul>
        <li><Link href="/scenarios">Scenarios</Link></li>
      </ul>
    </main>
  );
}
