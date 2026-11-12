import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CACoPage.css';

export default function AdminPage({ usuario }) {
  const [msg, setMsg] = useState('');
  const [erro, setErro] = useState('');

  const escopos = usuario?.escopo || '';
  const isAusGestao = escopos.includes('AUSTRALIA_GESTAO');
  const isCacoGestao = escopos.includes('CACO_GESTAO');

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
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
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
          <h3>🏛️ Gestão da Assembleia CACo</h3>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={() => disparar('/caco/iniciar', 'Votação do CACo iniciada!')}
            >
              ▶ Iniciar Assembleia CACo
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => disparar('/caco/encerrar', 'Votação do CACo encerrada!')}
            >
              ⏹ Encerrar Assembleia CACo
            </button>
          </div>
        </div>
      )}

      <Link to="/dashboard" className="btn-secondary">
        Voltar ao Dashboard
      </Link>
    </div>
  );
}