/** Alerta de error (conexión con el backend, permisos, etc.). */
export default function ErrorAlert({ error, onRetry }) {
  if (!error) return null;
  return (
    <div className="alert alert--error" role="alert">
      <div className="alert__body">
        <strong>No se pudo cargar la información</strong>
        <p>{error.message}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn btn--ghost" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}
