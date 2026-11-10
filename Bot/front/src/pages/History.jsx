import { useEffect, useMemo, useState } from 'react';

import ErrorAlert from '../components/ErrorAlert';
import LocationTable from '../components/LocationTable';
import Spinner from '../components/Spinner';
import { useAuth } from '../hooks/useAuth';
import { useResource } from '../hooks/useResource';
import { shortName } from '../utils/format';

/**
 * Historial de ubicaciones: del propio usuario o de cualquier contacto que lo
 * haya autorizado (el backend valida el permiso en cada petición).
 */
export default function History() {
  const { user } = useAuth();
  const contacts = useResource('/users');
  const [selected, setSelected] = useState('');

  const options = useMemo(() => {
    const list = [{ id: user.id, label: `${shortName(user)} (tú)` }];
    (contacts.data || []).forEach((contact) => {
      list.push({ id: contact.usuario.id, label: shortName(contact.usuario) });
    });
    return list;
  }, [contacts.data, user]);

  useEffect(() => {
    if (!selected && options.length > 0) {
      setSelected(String(options[0].id));
    }
  }, [options, selected]);

  const history = useResource(selected ? `/locations/history/${selected}?limit=100` : null);

  const items = useMemo(
    () => (history.data || []).map((location) => ({ ...location, id: `loc-${location.id}` })),
    [history.data],
  );

  return (
    <div className="stack">
      <section className="card">
        <div className="card__header">
          <div>
            <h2>Historial de ubicaciones</h2>
            <p className="muted">
              Se consulta el historial propio o el de los usuarios que te autorizaron.
            </p>
          </div>
          <div className="card__actions">
            <label htmlFor="usuario-historial">Usuario</label>
            <select
              id="usuario-historial"
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
              disabled={options.length <= 1}
            >
              {options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <ErrorAlert error={history.error || contacts.error} onRetry={history.reload} />

        {history.loading ? (
          <Spinner label="Cargando historial…" />
        ) : (
          <LocationTable
            items={items}
            emptyLabel={
              history.error
                ? 'No fue posible consultar el historial.'
                : 'Este usuario aún no ha compartido ubicaciones o no autoriza la consulta.'
            }
          />
        )}
      </section>
    </div>
  );
}
