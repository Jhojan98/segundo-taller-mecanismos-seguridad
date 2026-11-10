/** Utilidades de formato (fechas, coordenadas y nombres). */

export function formatDateTime(iso) {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
}

export function formatDateShort(iso) {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' });
}

export function formatCoord(value, digits = 5) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(digits);
}

export function shortName(user) {
  if (!user) return 'Usuario';
  if (user.nombre) return user.nombre;
  if (user.username) return `@${user.username}`;
  return `Usuario ${user.telegram_id ?? ''}`.trim();
}

export function formatAccuracy(value) {
  if (value === null || value === undefined) return 'no informada';
  return `${Number(value).toFixed(1)} m`;
}
