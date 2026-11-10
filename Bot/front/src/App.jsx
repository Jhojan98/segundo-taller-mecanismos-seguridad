import { Navigate, Route, BrowserRouter, Routes } from 'react-router-dom';

import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Spinner from './components/Spinner';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Authorizations from './pages/Authorizations';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Login from './pages/Login';
import MyLocation from './pages/MyLocation';

/** Ruta protegida: sin sesión válida redirige al inicio de sesión. */
function Protected({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="fullscreen">
        <Spinner label="Verificando sesión…" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

/** Estructura común: barra lateral + encabezado + contenido. */
function Shell({ title, subtitle, children }) {
  return (
    <div className="shell">
      <Sidebar />
      <div className="shell__main">
        <Header title={title} subtitle={subtitle} />
        <main className="content">{children}</main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/"
            element={
              <Protected>
                <Shell
                  title="Mapa de ubicaciones"
                  subtitle="Ubicaciones compartidas contigo y tu última posición"
                >
                  <Dashboard />
                </Shell>
              </Protected>
            }
          />

          <Route
            path="/mi-ubicacion"
            element={
              <Protected>
                <Shell title="Mi ubicación" subtitle="Historial propio y control de compartición">
                  <MyLocation />
                </Shell>
              </Protected>
            }
          />

          <Route
            path="/historial"
            element={
              <Protected>
                <Shell title="Historial" subtitle="Consulta autorizada de ubicaciones registradas">
                  <History />
                </Shell>
              </Protected>
            }
          />

          <Route
            path="/autorizaciones"
            element={
              <Protected>
                <Shell
                  title="Autorizaciones"
                  subtitle="Consentimientos, invitaciones y revocación de permisos"
                >
                  <Authorizations />
                </Shell>
              </Protected>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
