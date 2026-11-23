import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CACoPage.css';

export default function AdminPage({ usuario }) {
  const [msg, setMsg] = useState('');
  const [erro, setErro] = useState('');

  const escopos = usuario?.escopo || '';
  const isAusGestao = escopos.includes('AUSTRALIA_GESTAO');
  const isCacoGestao = escopos.includes('CACO_GESTAO');
  const isStoryteller = escopos.includes('BOTC_STORYTELLER');

  const disparar = async (url, textoSucesso) => {
    setMsg('');
    setErro('');
    const res = await fetch(url, { method: 'POST', redirect: 'manual' });
    if (res.status === 302 || res.type === 'opaqueredirect') {
      setErro('Você não possui permissão de gestão para realizar esta ação.');
      return;
    }
    const html = await res.text();
    if (html.includes('alert-error')) {
      const m = html.match(/<div class="alert-error"[^>]*>([\s\S]*?)<\/div>/);
      setErro(m ? m[1].trim() : 'Não foi possível alterar o estado da votação.');
    } else {
      setMsg(textoSucesso);
    }
  };

  return (
    <div className="caco-container">
      <div className="caco-header">
        <h1>⚙️ Painel Central de Gestão e Administração</h1>
        <p>Controle o ciclo de vida das eleições referentes aos seus escopos de gestão.</p>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {msg && <div className="alert-banner alert-success">{msg}</div>}

      {isAusGestao && (
        <div className="caco-card">
          <h3>🪃 Comissão Eleitoral Australiana</h3>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={() => disparar('/australia/iniciar', 'Eleição da Austrália iniciada!')}
            >
              ▶ Iniciar Eleição Austrália
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => disparar('/australia/encerrar', 'Eleição da Austrália encerrada!')}
            >
              ⏹ Encerrar Eleição Austrália
            </button>
          </div>
        </div>
      )}

      {isCacoGestao && (
        <div className="caco-card">
          <h3>🐸 Gestão de Assembleias e Pautas do CACo</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Crie novas assembleias, cadastre pautas, controle a votação única ativa e conduza a fila de falas.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            <Link to="/caco/assembleia" className="btn-primary">
              🏛️ Gerenciar Assembleias e Pautas do CACo
            </Link>
          </div>
        </div>
      )}

      {isStoryteller && (
        <div className="caco-card">
          <h3>🩸 Condução de Partidas de Blood on the Clocktower</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Acesse o lobby para criar salas privadas, assumir o centro da roda e conduzir partidas.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            <Link to="/botc/partida" className="btn-primary">
              🎲 Abrir Lobby de Partidas BoTC
            </Link>
          </div>
        </div>
      )}

      <Link to="/dashboard" className="btn-secondary">
        Voltar ao Dashboard
      </Link>
    </div>
  );
}