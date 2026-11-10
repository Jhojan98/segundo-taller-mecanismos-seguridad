import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { api } from '../services/api';

const AuthContext = createContext(null);

/**
 * Proveedor de sesión.
 *
 * La identidad NO la elige el frontend: se deriva del JWT emitido por el
 * backend tras canjear el código de un solo uso generado en Telegram (`/web`).
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function restore() {
      if (!api.hasSession()) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.get('/users/me');
        if (!cancelled) setUser(me);
      } catch {
        // Token inválido o caducado: api.js ya limpió el almacenamiento
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restore();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener('auth:expired', onExpired);
    return () => window.removeEventListener('auth:expired', onExpired);
  }, []);

  const login = useCallback(async (codigo) => {
    await api.login(codigo);
    const me = await api.get('/users/me');
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    api.logout();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth debe usarse dentro de <AuthProvider>');
  return context;
}
