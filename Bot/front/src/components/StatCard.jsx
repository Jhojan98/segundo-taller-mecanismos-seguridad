/** Tarjeta indicadora (KPI) del panel. */
export default function StatCard({ label, value, hint, tone = 'default' }) {
  return (
    <article className={`stat stat--${tone}`}>
      <span className="stat__label">{label}</span>
      <strong className="stat__value">{value}</strong>
      {hint && <span className="stat__hint">{hint}</span>}
    </article>
  );
}
