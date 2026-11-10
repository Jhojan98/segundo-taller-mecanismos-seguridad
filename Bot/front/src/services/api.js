/**
 * Cliente HTTP de la API REST.
 *
 * - `VITE_API_URL` vacío (producción con Nginx): las peticiones van a la misma
 *   origin y Nginx las proxea hacia el backend (`/api` → `backend:8000`).
 * - En desarrollo local se puede definir `VITE_API_URL=http://localhost:8000`.
 */
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

const TOKEN_KEY = 'access_token';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function authHeader(token) {
  if (token === null) return {}; // explícitamente sin autenticación (login)
  const current = token || localStorage.getItem(TOKEN_KEY);
  return current ? { Authorization: `Bearer ${current}` } : {};
}

async function request(path, { method = 'GET', body, token, headers = {} } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}/api${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...authHeader(token),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `No se pudo conectar con el backend${API_BASE ? ` (${API_BASE})` : ''}. ` +
        'Verifica que el servicio esté en ejecución.',
      0,
    );
  }

  if (response.status === 401) {
    // Sesión caducada o inválida: se limpia y se notifica a la aplicación
    localStorage.removeItem(TOKEN_KEY);
    window.dispatchEvent(new Event('auth:expired'));
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    /* respuesta sin cuerpo JSON */
  }

  if (!response.ok) {
    const detail =
      typeof payload?.detail === 'string'
        ? payload.detail
        : `El servidor respondió con error (${response.status}).`;
    throw new ApiError(detail, response.status);
  }
  return payload;
}

export const api = {
  get: (path, options = {}) => request(path, { ...options, method: 'GET' }),
  post: (path, body, options = {}) => request(path, { ...options, method: 'POST', body }),
  put: (path, body, options = {}) => request(path, { ...options, method: 'PUT', body }),
  del: (path, options = {}) => request(path, { ...options, method: 'DELETE' }),

  /** Canjea el código emitido por el bot (`/web`) y guarda el JWT. */
  async login(codigo) {
    const data = await request('/auth/token', {
      method: 'POST',
      body: { codigo },
      token: null,
    });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    return data;
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
  },

  hasSession() {
    return Boolean(localStorage.getItem(TOKEN_KEY));
  },
};
