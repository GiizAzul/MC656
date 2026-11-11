import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CACoPage.css';

export default function AdminPage() {
  const [msg, setMsg] = useState('');

  const disparar = async (url, texto) => {
    await fetch(url, { method: 'POST' });
    setMsg(texto);
  };

  return (
    <div className="caco-container">
      <div className="caco-header">
        <h1>⚙️ Painel Central de Gestão e Administração</h1>
        <p>Controle o ciclo de vida das eleições ativas nos três domínios.</p>
      </div>

      {msg && <div className="alert-banner alert-success">{msg}</div>}

      <div className="caco-card">
        <h3>🇦🇺 Comissão Eleitoral Australiana</h3>
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
          <button type="button" className="btn-primary" onClick={() => disparar('/australia/iniciar', 'Eleição da Austrália iniciada!')}>
            ▶ Iniciar Eleição Austrália
          </button>
          <button type="button" className="btn-secondary" onClick={() => disparar('/australia/encerrar', 'Eleição da Austrália encerrada!')}>
            ⏹ Encerrar Eleição Austrália
          </button>
        </div>
      </div>

      <div className="caco-card">
        <h3>🏛️ Gestão da Assembleia CACo</h3>
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
          <button type="button" className="btn-primary" onClick={() => disparar('/caco/iniciar', 'Votação do CACo iniciada!')}>
            ▶ Iniciar Assembleia CACo
          </button>
          <button type="button" className="btn-secondary" onClick={() => disparar('/caco/encerrar', 'Votação do CACo encerrada!')}>
            ⏹ Encerrar Assembleia CACo
          </button>
        </div>
      </div>

      <Link to="/dashboard" className="btn-secondary">
        Voltar ao Dashboard
      </Link>
    </div>
  );
}