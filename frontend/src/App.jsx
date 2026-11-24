import React, { useEffect, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import CadastroPage from './pages/CadastroPage';
import DashboardPage from './pages/DashboardPage';
import AustraliaPage from './pages/AustraliaPage';
import BotCPage from './pages/BotCPage';
import CACoPage from './pages/CACoPage';
import AdminPage from './pages/AdminPage';
import './styles/global.css';

export function limparCacheLocalVotacao() {
  Object.keys(localStorage).forEach((chave) => {
    if (chave.startsWith('mc656_rascunho_') || chave.startsWith('mc656_botc_sessao_')) {
      localStorage.removeItem(chave);
    }
  });
}

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

function GerenciadorSessao({ usuario, setUsuario, carregarSessao, tema, alternarTema }) {
  const navigate = useNavigate();
  const location = useLocation();

  const verificarVotacaoAtiva = useCallback(async () => {
    try {
      const res = await fetch('/api/votacao-ativa', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        if (data.rota) {
          navigate(data.rota, { replace: true });
          return true;
        }
      }
    } catch {
      // ignora oscilação
    }
    return false;
  }, [navigate]);

  // Ao abrir o app em '/' ou '/dashboard' já autenticado, restaura na cédula ativa ou dashboard
  useEffect(() => {
    if (!usuario) return;
    const rotasEntrada = ['/', '/dashboard'];
    if (rotasEntrada.includes(location.pathname)) {
      verificarVotacaoAtiva().then((redirecionou) => {
        if (!redirecionou && location.pathname === '/') {
          navigate('/dashboard', { replace: true });
        }
      });
    }
  }, [usuario, location.pathname, verificarVotacaoAtiva, navigate]);

  const handleLogout = useCallback(async () => {
    try {
      await fetch('/logout', { method: 'POST', credentials: 'include' });
    } catch {
      // ignora falha de rede
    }
    limparCacheLocalVotacao();
    setUsuario(null);
    navigate('/', { replace: true });
  }, [setUsuario, navigate]);

  return (
    <>
      <Navbar
        usuario={usuario}
        onLogout={handleLogout}
        tema={tema}
        onToggleTema={alternarTema}
      />
      <main className="app-shell">
        <Routes>
          <Route
            path="/"
            element={
              usuario ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <LoginPage onLoginSuccess={carregarSessao} />
              )
            }
          />
          <Route
            path="/cadastro"
            element={
              usuario ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <CadastroPage onAuthSuccess={carregarSessao} />
              )
            }
          />
          <Route
            path="/dashboard"
            element={
              usuario ? (
                <DashboardPage usuario={usuario} onScopeAdded={carregarSessao} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/australia/votar"
            element={
              <RotaEscopo usuario={usuario} escopoNecessario="AUSTRALIA">
                <AustraliaPage usuario={usuario} />
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
    </>
  );
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
      const res = await fetch('/api/me', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setUsuario(data);
        return data;
      }
      limparCacheLocalVotacao();
      setUsuario(null);
      return null;
    } catch {
      setUsuario(null);
      return null;
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregarSessao();
  }, [carregarSessao]);

  if (carregando) {
    return (
      <div className="app-shell" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        Restaurando sessão...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <GerenciadorSessao
        usuario={usuario}
        setUsuario={setUsuario}
        carregarSessao={carregarSessao}
        tema={tema}
        alternarTema={alternarTema}
      />
    </BrowserRouter>
  );
}