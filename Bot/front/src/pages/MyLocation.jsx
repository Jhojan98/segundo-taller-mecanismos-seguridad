import { useMemo, useState } from 'react';

import ErrorAlert from '../components/ErrorAlert';
import LocationTable from '../components/LocationTable';
import MapView from '../components/MapView';
import Spinner from '../components/Spinner';
import StatCard from '../components/StatCard';
import { api } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useResource } from '../hooks/useResource';
import { formatAccuracy, formatDateShort, formatDateTime, formatCoord } from '../utils/format';

/**
 * Sección «Mi ubicación»: última posición propia, historial y control del
 * interruptor de compartición.
 */
export default function MyLocation() {
  const { user } = useAuth();
  const config = useResource('/config');
  const locations = useResource('/locations/me?limit=50');

  const [actionError, setActionError] = useState(null);
  const [busy, setBusy] = useState(false);

  const latest = locations.data?.[0] || null;

  const points = useMemo(
    () =>
      (locations.data || []).slice(0, 15).map((location) => ({
        id: `own-${location.id}`,
        lat: Number(location.latitud),
        lon: Number(location.longitud),
        color: '#16a34a',
        title: `Tú (${shortNameFallback(user)})`,
        fecha: formatDateShort(location.fecha_hora),
        extra: `Precisión: ${formatAccuracy(location.precision)}`,
      })),
    [locations.data, user],
  );

  const tableItems = useMemo(
    () => (locations.data || []).map((location) => ({ ...location, id: `loc-${location.id}` })),
    [locations.data],
  );

  async function toggleSharing() {
    if (!config.data) return;
    setBusy(true);
    setActionError(null);
    try {
      await api.put('/config', { compartir_ubicacion: !config.data.compartir_ubicacion });
      config.reload();
    } catch (error) {
      setActionError(error);
    } finally {
      setBusy(false);
    }
  }

  const sharing = config.data?.compartir_ubicacion;

  return (
    <div className="stack">
      <ErrorAlert error={actionError || config.error || locations.error} onRetry={null} />

      <section className="card card--highlight">
        <div className="card__header">
          <div>
            <h2>Estado de tu compartición</h2>
            <p className="muted">
              Mientras esté detenida, tus ubicaciones no se entregan a terceros aunque existan
              autorizaciones vigentes.
            </p>
          </div>
          <button
            type="button"
            className={`btn ${sharing ? 'btn--danger' : 'btn--primary'}`}
            onClick={toggleSharing}
            disabled={busy || !config.data}
          >
            {busy ? 'Aplicando…' : sharing ? 'Detener compartición' : 'Activar compartición'}
          </button>
        </div>

        <div className="status-line">
          <span className={`status-dot ${sharing ? 'status-dot--on' : 'status-dot--off'}`} />
          <strong>{sharing ? 'Compartición activa' : 'Compartición detenida'}</strong>
          <span className="muted">
            {config.data
              ? `Última actualización: ${formatDateTime(config.data.fecha_actualizacion)}`
              : 'Cargando configuración…'}
          </span>
        </div>
      </section>

      <section className="stats">
        <StatCard
          label="Última ubicación"
          value={latest ? formatDateShort(latest.fecha_hora) : 'Sin datos'}
          hint={latest ? 'Recibida desde Telegram' : 'Envía /compartir en el bot'}
          tone={latest ? 'green' : 'default'}
        />
        <StatCard
          label="Coordenadas"
          value={latest ? `${formatCoord(latest.latitud)}, ${formatCoord(latest.longitud)}` : '—'}
          hint="WGS84 (grados decimales)"
        />
        <StatCard
          label="Precisión"
          value={latest ? formatAccuracy(latest.precision) : '—'}
          hint="Informada por el dispositivo"
        />
        <StatCard
          label="Ubicaciones registradas"
          value={locations.data ? locations.data.length : '—'}
          hint="Historial visible en este panel"
        />
      </section>

      <section className="card">
        <div className="card__header">
          <div>
            <h2>Mapa de tu historial reciente</h2>
            <p className="muted">Últimas posiciones que has enviado desde Telegram.</p>
          </div>
        </div>
        {locations.loading ? (
          <Spinner />
        ) : (
          <MapView
            points={points}
            emptyTitle="Todavía no has compartido tu ubicación"
            emptyDescription="Abre el bot en Telegram, envía /compartir y pulsa el botón de ubicación. Solo se registra lo que tú envías."
            legend={
              <span className="legend__item">
                <i className="legend__dot legend__dot--green" /> Tus ubicaciones
              </span>
            }
          />
        )}
      </section>

      <section className="card">
        <div className="card__header">
          <div>
            <h2>Historial propio</h2>
            <p className="muted">Las fechas se muestran en la zona horaria de tu navegador.</p>
          </div>
        </div>
        {locations.loading ? (
          <Spinner />
        ) : (
          <LocationTable
            items={tableItems}
            emptyLabel="Sin ubicaciones registradas. Usa /compartir en el bot."
          />
        )}
      </section>
    </div>
  );
}

/** Nombre corto del usuario autenticado para los marcadores. */
function shortNameFallback(user) {
  if (!user) return 'tú';
  if (user.nombre) return user.nombre;
  if (user.username) return `@${user.username}`;
  return 'tú';
}
