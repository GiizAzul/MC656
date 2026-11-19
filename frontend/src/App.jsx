import React, { useEffect, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import CadastroPage from './pages/CadastroPage';
import DashboardPage from './pages/DashboardPage';
import AustraliaPage from './pages/AustraliaPage';
import BotCPage from './pages/BotCPage';
import CACoPage from './pages/CACoPage';
import AdminPage from './pages/AdminPage';
import './styles/global.css';

function RotaEscopo({ usuario, escopoNecessario, children }) {
  if (!usuario) return <Navigate to="/" replace />;
  const escopos = usuario.escopo || '';
  const autorizado = Array.isArray(escopoNecessario)
    ? escopoNecessario.some((e) => escopos.includes(e))
    : escopos.includes(escopoNecessario);

  if (!autorizado) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

export default function App() {
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [tema, setTema] = useState(() => localStorage.getItem('mc656_tema') || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', tema);
    localStorage.setItem('mc656_tema', tema);
  }, [tema]);

  const alternarTema = () => {
    setTema((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

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

  const limparSessaoLocal = useCallback(() => {
    setUsuario(null);
  }, []);

  useEffect(() => {
    carregarSessao();
  }, [carregarSessao]);

  if (carregando) return null;

  return (
    <BrowserRouter>
      <Navbar
        usuario={usuario}
        onLogout={() => setUsuario(null)}
        tema={tema}
        onToggleTema={alternarTema}
      />
      <main className="app-shell">
        <Routes>
          <Route
            path="/"
            element={<LoginPage onLoginSuccess={carregarSessao} onLogout={limparSessaoLocal} />}
          />
          <Route
            path="/cadastro"
            element={<CadastroPage onAuthSuccess={carregarSessao} onLogout={limparSessaoLocal} />}
          />
          <Route
            path="/dashboard"
            element={
              usuario ? <DashboardPage usuario={usuario} onScopeAdded={carregarSessao} /> : <Navigate to="/" replace />
            }
          />
          <Route
            path="/australia/votar"
            element={
              <RotaEscopo usuario={usuario} escopoNecessario="AUSTRALIA">
                <AustraliaPage />
              </RotaEscopo>
            }
          />
          <Route
            path="/botc/partida"
            element={
              <RotaEscopo usuario={usuario} escopoNecessario="BOTC">
                <BotCPage usuario={usuario} />
              </RotaEscopo>
            }
          />
          <Route
            path="/caco/assembleia"
            element={
              <RotaEscopo usuario={usuario} escopoNecessario="CACO">
                <CACoPage usuario={usuario} />
              </RotaEscopo>
            }
          />
          <Route
            path="/caco/resultados"
            element={
              <RotaEscopo usuario={usuario} escopoNecessario="CACO">
                <CACoPage usuario={usuario} />
              </RotaEscopo>
            }
          />
          <Route
            path="/admin"
            element={
              <RotaEscopo usuario={usuario} escopoNecessario={['GESTAO', 'STORYTELLER']}>
                <AdminPage usuario={usuario} />
              </RotaEscopo>
            }
          />
        </Routes>
      </main>
    </BrowserRouter>
  );
}