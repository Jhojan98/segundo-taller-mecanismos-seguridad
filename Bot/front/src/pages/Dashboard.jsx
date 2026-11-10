import { useMemo } from 'react';

import ErrorAlert from '../components/ErrorAlert';
import LocationTable from '../components/LocationTable';
import MapView from '../components/MapView';
import Spinner from '../components/Spinner';
import StatCard from '../components/StatCard';
import { useAuth } from '../hooks/useAuth';
import { useResource } from '../hooks/useResource';
import { formatDateShort, shortName } from '../utils/format';

/**
 * Panel principal: mapa con las últimas ubicaciones compartidas con el usuario
 * autenticado y su propia última ubicación.
 */
export default function Dashboard() {
  const { user } = useAuth();
  const shared = useResource('/locations/shared');
  const mine = useResource('/locations/me?limit=1');
  const contacts = useResource('/users');
  const config = useResource('/config');

  const loading = shared.loading || mine.loading;
  const error = shared.error || mine.error;

  const { points, tableItems } = useMemo(() => {
    const mappedPoints = [];
    const rows = [];

    const own = mine.data?.[0];
    if (own) {
      mappedPoints.push({
        id: `me-${own.id}`,
        lat: Number(own.latitud),
        lon: Number(own.longitud),
        color: '#16a34a',
        title: `Tú (${shortName(user)})`,
        fecha: formatDateShort(own.fecha_hora),
        extra: 'Tu última ubicación compartida',
      });
      rows.push({
        id: `me-${own.id}`,
        label: `${shortName(user)} (tú)`,
        latitud: own.latitud,
        longitud: own.longitud,
        precision: own.precision,
        fecha_hora: own.fecha_hora,
      });
    }

    (shared.data || []).forEach(({ usuario, ubicacion }) => {
      mappedPoints.push({
        id: `shared-${usuario.id}`,
        lat: Number(ubicacion.latitud),
        lon: Number(ubicacion.longitud),
        color: '#2563eb',
        title: shortName(usuario),
        fecha: formatDateShort(ubicacion.fecha_hora),
        extra: 'Ubicación autorizada',
      });
      rows.push({
        id: `shared-${ubicacion.id}`,
        label: shortName(usuario),
        latitud: ubicacion.latitud,
        longitud: ubicacion.longitud,
        precision: ubicacion.precision,
        fecha_hora: ubicacion.fecha_hora,
      });
    });

    return { points: mappedPoints, tableItems: rows };
  }, [mine.data, shared.data, user]);

  return (
    <div className="stack">
      <ErrorAlert error={error} onRetry={() => { shared.reload(); mine.reload(); }} />

      <section className="stats">
        <StatCard
          label="Compartidas conmigo"
          value={shared.data ? shared.data.length : '—'}
          hint="Usuarios que me autorizaron"
          tone="blue"
        />
        <StatCard
          label="Mi última ubicación"
          value={mine.data?.[0] ? formatDateShort(mine.data[0].fecha_hora) : 'Sin datos'}
          hint={mine.data?.[0] ? 'Recibida desde Telegram' : 'Usa /compartir en el bot'}
          tone={mine.data?.[0] ? 'green' : 'default'}
        />
        <StatCard
          label="Contactos vinculados"
          value={contacts.data ? contacts.data.length : '—'}
          hint="Relaciones mediante invitación"
        />
        <StatCard
          label="Compartición"
          value={config.data?.compartir_ubicacion ? 'Activa' : 'Detenida'}
          hint="Tu interruptor de privacidad"
          tone={config.data?.compartir_ubicacion ? 'green' : 'amber'}
        />
      </section>

      <section className="card">
        <div className="card__header">
          <div>
            <h2>Mapa de ubicaciones autorizadas</h2>
            <p className="muted">
              Se muestran únicamente ubicaciones con consentimiento vigente y compartición activada.
            </p>
          </div>
        </div>

        {loading ? (
          <Spinner />
        ) : (
          <MapView
            points={points}
            emptyTitle="Sin ubicaciones para mostrar"
            emptyDescription={
              'Aún no hay ubicaciones compartidas contigo. Envía la tuya con /compartir en el bot ' +
              'y solicita a tus contactos que te autoricen para ver las suyas.'
            }
            legend={
              <>
                <span className="legend__item">
                  <i className="legend__dot legend__dot--green" /> Tu ubicación
                </span>
                <span className="legend__item">
                  <i className="legend__dot legend__dot--blue" /> Ubicaciones autorizadas
                </span>
              </>
            }
          />
        )}
      </section>

      <section className="card">
        <div className="card__header">
          <div>
            <h2>Ubicaciones recientes</h2>
            <p className="muted">Fecha y hora de la última posición recibida de cada usuario.</p>
          </div>
        </div>
        {loading ? (
          <Spinner />
        ) : (
          <LocationTable
            items={tableItems}
            showOwner
            emptyLabel="No hay ubicaciones disponibles todavía."
          />
        )}
      </section>
    </div>
  );
}
