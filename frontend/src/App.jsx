import React, { useEffect, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import CadastroPage from './pages/CadastroPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';
import AustraliaPage from './pages/AustraliaPage';
import BotCPage from './pages/BotCPage';
import CACoPage from './pages/CACoPage';
import './styles/global.css';

export default function App() {
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);

  const carregarSessao = useCallback(async () => {
    try {
      const res = await fetch('/api/me');
      if (res.ok) {
        const data = await res.json();
        setUsuario(data);
      } else {
        setUsuario(null);
      }
    } catch {
      setUsuario(null);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregarSessao();
  }, [carregarSessao]);

  if (carregando) return null;

  return (
    <BrowserRouter>
      <Navbar usuario={usuario} onLogout={() => setUsuario(null)} />
      <main className="app-shell">
        <Routes>
          <Route path="/" element={<LoginPage onLoginSuccess={carregarSessao} />} />
          <Route path="/cadastro" element={<CadastroPage onAuthSuccess={carregarSessao} />} />
          <Route
            path="/dashboard"
            element={
              usuario ? <DashboardPage usuario={usuario} onScopeAdded={carregarSessao} /> : <Navigate to="/" />
            }
          />
          <Route
            path="/admin"
            element={usuario ? <AdminPage usuario={usuario} /> : <Navigate to="/" />}
          />
          <Route
            path="/caco/resultados"
            element={usuario ? <CACoPage usuario={usuario} /> : <Navigate to="/" />}
          />
          <Route
            path="/australia/votar"
            element={usuario ? <AustraliaPage /> : <Navigate to="/" />}
          />
          <Route
            path="/botc/partida"
            element={usuario ? <BotCPage usuario={usuario} /> : <Navigate to="/" />}
          />
          <Route
            path="/caco/assembleia"
            element={usuario ? <CACoPage usuario={usuario} /> : <Navigate to="/" />}
          />
        </Routes>
      </main>
    </BrowserRouter>
  );
}