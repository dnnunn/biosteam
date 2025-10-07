export default function Button({ label, onClick }: { label: string; onClick?: () => void }) {
  return (
    <button
      style={{
        padding: '8px 16px',
        background: '#1f2937',
        color: '#fff',
        border: 'none',
        borderRadius: 4,
        cursor: 'pointer',
      }}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
