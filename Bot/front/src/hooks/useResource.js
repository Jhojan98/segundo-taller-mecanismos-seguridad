import { useCallback, useEffect, useState } from 'react';

import { api } from '../services/api';

/**
 * Hook genérico de consumo de la API.
 *
 * @param {string|null} path Ruta bajo `/api` (si es `null` no se consulta).
 * @returns {{data: any, loading: boolean, error: Error|null, reload: () => void}}
 */
export function useResource(path) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(path));
  const [error, setError] = useState(null);
  const [version, setVersion] = useState(0);

  const reload = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    let cancelled = false;

    if (!path) {
      setData(null);
      setLoading(false);
      setError(null);
      return undefined;
    }

    setLoading(true);
    setError(null);

    api
      .get(path)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [path, version]);

  return { data, loading, error, reload };
}
