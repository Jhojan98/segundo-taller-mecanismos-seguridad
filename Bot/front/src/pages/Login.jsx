import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import Spinner from '../components/Spinner';
import { useAuth } from '../hooks/useAuth';

/**
 * Página de inicio de sesión.
 *
 * La identidad proviene de un código de un solo uso generado en Telegram con
 * `/web`: el backend lo canjea por un JWT y el panel no permite autenticarse
 * de ninguna otra manera.
 */
export default function Login() {
  const { user, loading, login } = useAuth();
  const [codigo, setCodigo] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="fullscreen">
        <Spinner label="Verificando sesión…" />
      </div>
    );
  }

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    const value = codigo.trim();
    if (!value) {
      setError('Introduce el código generado con /web en el bot de Telegram.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await login(value);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login">
      <div className="login__card">
        <div className="login__brand">
          <span aria-hidden="true">📍</span>
          <div>
            <h1>Ubicación Compartida</h1>
            <small>Panel de visualización autorizada</small>
          </div>
        </div>

        <form className="login__form" onSubmit={handleSubmit}>
          <label htmlFor="codigo">Código de acceso</label>
          <input
            id="codigo"
            name="codigo"
            type="text"
            inputMode="text"
            autoComplete="one-time-code"
            placeholder="P. ej. K7M2P9QD"
            value={codigo}
            onChange={(event) => setCodigo(event.target.value)}
            maxLength={64}
            disabled={submitting}
          />

          {error && (
            <div className="alert alert--error" role="alert">
              <p>{error}</p>
            </div>
          )}

          <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
            {submitting ? 'Validando…' : 'Ingresar al panel'}
          </button>
        </form>

        <div className="login__steps">
          <h2>¿Cómo obtengo el código?</h2>
          <ol>
            <li>
              Abre el bot en Telegram y envía <code>/start</code> si es tu primera vez.
            </li>
            <li>
              Escribe <code>/web</code>: el bot te entregará un código de un solo uso.
            </li>
            <li>Pégalo aquí antes de que caduque (caduca en pocos minutos).</li>
          </ol>
          <p className="muted">
            El código demuestra que controlas esa cuenta de Telegram. No hay
            contraseñas ni registros por correo: la identidad del panel es tu
            identidad en Telegram.
          </p>
        </div>
      </div>
    </div>
  );
}
