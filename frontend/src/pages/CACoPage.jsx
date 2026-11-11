import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CACoPage.css';

export default function CACoPage({ usuario }) {
  const [opcao, setOpcao] = useState('APROVAR');
  const [feedback, setFeedback] = useState('');
  const [erro, setErro] = useState('');
  const isGestao = usuario?.escopo?.includes('GESTAO');

  const enviarVoto = async (e) => {
    e.preventDefault();
    setErro('');
    setFeedback('');

    const formData = new URLSearchParams();
    formData.append('opcao', opcao);

    const res = await fetch('/caco/votar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });
    const html = await res.text();
    if (html.includes('VOTO NEGADO')) {
      setErro('VOTO NEGADO: Você já registrou seu voto nesta pauta.');
    } else if (html.includes('contabilizado')) {
      setFeedback(`Seu voto na assembleia foi contabilizado como: ${opcao}`);
    } else {
      setErro('A votação ainda não foi iniciada pela Gestão ou já foi encerrada.');
    }
  };

  const acaoGestao = async (rota, msg) => {
    await fetch(rota, { method: 'POST' });
    setFeedback(msg);
    setErro('');
  };

  return (
    <div className="caco-container">
      <div className="caco-header">
        <h1>🏛️ Assembleia Geral do CACo</h1>
        <p>Votação estudantil secreta e auditada por quórum estatutário.</p>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {feedback && <div className="alert-banner alert-success">{feedback}</div>}

      <div className="caco-card">
        <h2>Cédula de Deliberação</h2>
        <form onSubmit={enviarVoto}>
          <div className="vote-options-grid">
            {['APROVAR', 'REJEITAR', 'ABSTER'].map((item) => (
              <button
                type="button"
                key={item}
                onClick={() => setOpcao(item)}
                className={`vote-option-btn ${opcao === item ? 'selected' : ''}`}
              >
                {item}
              </button>
            ))}
          </div>
          <button type="submit" className="btn-primary">
            Confirmar Voto Anônimo
          </button>
        </form>
      </div>

      {isGestao && (
        <div className="caco-card">
          <h3>Controles da Gestão CACo</h3>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={() => acaoGestao('/caco/iniciar', 'Votação da Assembleia iniciada com sucesso!')}
            >
              Iniciar Votação
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => acaoGestao('/caco/encerrar', 'Votação da Assembleia encerrada.')}
            >
              Encerrar Votação
            </button>
            <a href="/caco/resultados" className="btn-secondary">
              Ver Barras de Resultados
            </a>
          </div>
        </div>
      )}

      <Link to="/dashboard" className="btn-secondary">
        Voltar ao Painel
      </Link>
    </div>
  );
}