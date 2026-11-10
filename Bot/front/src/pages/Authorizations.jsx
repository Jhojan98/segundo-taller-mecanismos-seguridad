import { useState } from 'react';

import ErrorAlert from '../components/ErrorAlert';
import Spinner from '../components/Spinner';
import StatusBadge from '../components/StatusBadge';
import { api } from '../services/api';
import { useResource } from '../hooks/useResource';
import { formatDateTime, shortName } from '../utils/format';

/**
 * Gestión de autorizaciones: consulta, revocación, generación de invitaciones
 * y otorgamiento de consentimiento desde el panel web.
 */
export default function Authorizations() {
  const authorizations = useResource('/authorizations');
  const contacts = useResource('/users');
  const invitations = useResource('/invitations');

  const [actionError, setActionError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [createdCode, setCreatedCode] = useState(null);
  const [grantTarget, setGrantTarget] = useState('');

  async function runAction(action) {
    setBusy(true);
    setActionError(null);
    try {
      await action();
    } catch (error) {
      setActionError(error);
    } finally {
      setBusy(false);
    }
  }

  function handleRevoke(authorization) {
    const confirmed = window.confirm(
      `¿Revocar el acceso de ${shortName(authorization.usuario)} a tu ubicación?`,
    );
    if (!confirmed) return;
    runAction(async () => {
      await api.del(`/authorizations/${authorization.id}`);
      authorizations.reload();
      contacts.reload();
    });
  }

  function handleCreateInvitation() {
    runAction(async () => {
      const invitation = await api.post('/invitations');
      setCreatedCode(invitation.codigo);
      invitations.reload();
    });
  }

  function handleGrant(event) {
    event.preventDefault();
    if (!grantTarget) return;
    runAction(async () => {
      await api.post('/authorizations', { usuario_id: Number(grantTarget) });
      setGrantTarget('');
      authorizations.reload();
      contacts.reload();
    });
  }

  const loading = authorizations.loading || contacts.loading;

  return (
    <div className="stack">
      <ErrorAlert error={actionError} onRetry={null} />

      <section className="card">
        <div className="card__header">
          <div>
            <h2>Autorizaciones vigentes</h2>
            <p className="muted">
              Quién puede ver tu ubicación y de quién puedes ver tú. Solo el propietario puede
              revocar.
            </p>
          </div>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => authorizations.reload()}
            disabled={busy}
          >
            Actualizar
          </button>
        </div>

        {loading ? (
          <Spinner />
        ) : authorizations.error ? (
          <ErrorAlert error={authorizations.error} onRetry={authorizations.reload} />
        ) : authorizations.data?.length === 0 ? (
          <p className="muted">
            Aún no existen autorizaciones. Vincúlate con alguien desde el bot (<code>/vincular</code>)
            y otorga el consentimiento.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Mi rol</th>
                  <th>Estado</th>
                  <th>Autorizada el</th>
                  <th>Revocada el</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {authorizations.data.map((authorization) => (
                  <tr key={authorization.id}>
                    <td>
                      {shortName(authorization.usuario)}
                      {authorization.usuario.username && (
                        <small className="muted"> @{authorization.usuario.username}</small>
                      )}
                    </td>
                    <td>{authorization.rol === 'propietario' ? 'Propietario' : 'Autorizado'}</td>
                    <td>
                      <StatusBadge estado={authorization.estado} />
                    </td>
                    <td>{formatDateTime(authorization.fecha_autorizacion)}</td>
                    <td>{formatDateTime(authorization.fecha_revocacion)}</td>
                    <td>
                      {authorization.rol === 'propietario' &&
                        ['activa', 'pendiente'].includes(authorization.estado) && (
                          <button
                            type="button"
                            className="btn btn--danger btn--sm"
                            onClick={() => handleRevoke(authorization)}
                            disabled={busy}
                          >
                            Revocar
                          </button>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="grid-2">
        <section className="card">
          <div className="card__header">
            <div>
              <h2>Invitaciones de vinculación</h2>
              <p className="muted">Código de un solo uso con caducidad para enlazar cuentas.</p>
            </div>
            <button
              type="button"
              className="btn btn--primary"
              onClick={handleCreateInvitation}
              disabled={busy}
            >
              Generar código
            </button>
          </div>

          {createdCode && (
            <div className="code-box">
              <span className="code-box__label">Código generado (válido unos minutos)</span>
              <strong className="code-box__value">{createdCode}</strong>
              <p className="muted">
                La otra persona debe enviar <code>/vincular {createdCode}</code> al bot. Después
                deberás autorizarla desde «Compartir mi ubicación».
              </p>
            </div>
          )}

          {invitations.data?.length > 0 && (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Creada</th>
                    <th>Expira</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {invitations.data.slice(0, 5).map((invitation) => (
                    <tr key={invitation.id}>
                      <td className="mono">{invitation.codigo}</td>
                      <td>{formatDateTime(invitation.fecha_creacion)}</td>
                      <td>{formatDateTime(invitation.fecha_expiracion)}</td>
                      <td>{invitation.utilizado ? 'Utilizada' : 'Pendiente'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="card">
          <div className="card__header">
            <div>
              <h2>Compartir mi ubicación</h2>
              <p className="muted">
                Otorga tu consentimiento a un contacto vinculado (puedes revocarlo cuando quieras).
              </p>
            </div>
          </div>

          <form className="inline-form" onSubmit={handleGrant}>
            <label htmlFor="contacto-autorizar">Contacto</label>
            <select
              id="contacto-autorizar"
              value={grantTarget}
              onChange={(event) => setGrantTarget(event.target.value)}
            >
              <option value="">Selecciona un contacto…</option>
              {(contacts.data || [])
                .filter((contact) => !contact.puede_ver_mi_ubicacion)
                .map((contact) => (
                  <option key={contact.usuario.id} value={contact.usuario.id}>
                    {shortName(contact.usuario)}
                  </option>
                ))}
            </select>
            <button type="submit" className="btn btn--primary" disabled={busy || !grantTarget}>
              Autorizar
            </button>
          </form>

          <h3 className="card__subtitle">Mis contactos</h3>
          {contacts.loading ? (
            <Spinner label="Cargando contactos…" />
          ) : contacts.data?.length === 0 ? (
            <p className="muted">
              Sin contactos vinculados todavía. Genera una invitación con <code>/vincular</code> en
              el bot.
            </p>
          ) : (
            <ul className="contact-list">
              {contacts.data.map((contact) => (
                <li key={contact.usuario.id} className="contact-list__item">
                  <div>
                    <strong>{shortName(contact.usuario)}</strong>
                    <small className="muted">
                      {' '}
                      {contact.usuario.username ? `@${contact.usuario.username}` : ''}
                    </small>
                  </div>
                  <div className="contact-list__flags">
                    <span className={contact.puede_ver_mi_ubicacion ? 'flag flag--on' : 'flag'}>
                      {contact.puede_ver_mi_ubicacion ? 've mi ubicación' : 'sin mi ubicación'}
                    </span>
                    <span className={contact.puede_ver_su_ubicacion ? 'flag flag--on' : 'flag'}>
                      {contact.puede_ver_su_ubicacion ? 'veo la suya' : 'sin su ubicación'}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
