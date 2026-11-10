import { formatAccuracy, formatCoord, formatDateTime } from '../utils/format';

/**
 * Tabla de ubicaciones.
 * `items`: [{ id, label?, latitud, longitud, precision, fecha_hora }]
 */
export default function LocationTable({
  items = [],
  showOwner = false,
  emptyLabel = 'Sin ubicaciones registradas.',
}) {
  if (!items.length) {
    return <p className="muted">{emptyLabel}</p>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {showOwner && <th>Usuario</th>}
            <th>Latitud</th>
            <th>Longitud</th>
            <th>Precisión</th>
            <th>Fecha y hora</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              {showOwner && <td>{item.label}</td>}
              <td className="mono">{formatCoord(item.latitud)}</td>
              <td className="mono">{formatCoord(item.longitud)}</td>
              <td>{formatAccuracy(item.precision)}</td>
              <td>{formatDateTime(item.fecha_hora)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
