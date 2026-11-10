/** Mensaje de estado vacío (sin datos ficticios). */
export default function EmptyState({ icon = '🗺️', title, description, action }) {
  return (
    <div className="empty">
      <span className="empty__icon" aria-hidden="true">
        {icon}
      </span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}
