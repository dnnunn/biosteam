export default function RunPage({ params }: { params: { id: string } }) {
  return (
    <main style={{ padding: 24 }}>
      <h2>Run {params.id}</h2>
      <p>Results detail view — wire to /runs/{params.id}.</p>
    </main>
  );
}
