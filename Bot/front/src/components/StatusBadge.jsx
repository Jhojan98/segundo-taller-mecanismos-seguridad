/** Insignia de estado de autorización. */
const TONES = {
  activa: 'badge--green',
  pendiente: 'badge--amber',
  revocada: 'badge--gray',
  rechazada: 'badge--red',
};

export default function StatusBadge({ estado }) {
  const tone = TONES[estado] || 'badge--gray';
  return <span className={`badge ${tone}`}>{estado}</span>;
}
