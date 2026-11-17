import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CACoPage.css';

export default function CACoPage({ usuario }) {
  const [opcao, setOpcao] = useState('APROVAR');
  const [feedback, setFeedback] = useState('');
  const [erro, setErro] = useState('');
  const [resultados, setResultados] = useState(null);
  const isGestao = usuario?.escopo?.includes('GESTAO');

  const carregarResultados = async () => {
    const res = await fetch('/caco/resultados', { headers: { Accept: 'application/html' } });
    const html = await res.text();
    const extrair = (label) => {
      const regex = new RegExp(`${label}[\\s\\S]*?(\\d+)\\s*votos`, 'i');
      const m = html.match(regex);
      return m ? parseInt(m[1], 10) : 0;
    };
    const aprovar = extrair('Aprovar');
    const rejeitar = extrair('Rejeitar');
    const abster = extrair('Absten');
    const total = aprovar + rejeitar + abster;
    setResultados({ aprovar, rejeitar, abster, total });
  };

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
    } else if (html.includes('contabilizado') || html.includes('Voto:')) {
      setFeedback(`Seu voto na assembleia foi contabilizado com sucesso: ${opcao}`);
      await carregarResultados();
    } else {
      setErro('A votação ainda não foi iniciada pela Gestão ou já foi encerrada.');
    }
  };

  const acaoGestao = async (rota, msg) => {
    await fetch(rota, { method: 'POST' });
    setFeedback(msg);
    setErro('');
    await carregarResultados();
  };

  const pct = (val, tot) => (tot > 0 ? Math.round((val / tot) * 100) : 0);

  return (
    <div className="caco-container">
      <div className="caco-header">
        <h1>🏛️ Assembleia Geral do CACo</h1>
        <p>Pauta: Aprovação do novo estatuto de representação discente.</p>
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
          <h3>⚙️ Controles da Gestão CACo</h3>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={() => acaoGestao('/caco/iniciar', 'Votação da Assembleia iniciada com sucesso!')}
            >
              ▶ Iniciar Votação
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => acaoGestao('/caco/encerrar', 'Votação da Assembleia encerrada.')}
            >
              ⏹ Encerrar Votação
            </button>
            <button type="button" className="btn-secondary" onClick={carregarResultados}>
              📊 Exibir / Atualizar Resultados
            </button>
          </div>
        </div>
      )}

      {resultados && (
        <div className="caco-card">
          <h3>📊 Resultados Parciais / Finais (Total: {resultados.total} votos)</h3>
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
            <div>
              <strong>A Favor (Aprovar): {resultados.aprovar} voto(s) ({pct(resultados.aprovar, resultados.total)}%)</strong>
              <div className="progress-bar-track">
                <div className="progress-bar-fill" style={{ width: `${pct(resultados.aprovar, resultados.total)}%` }} />
              </div>
            </div>
            <div>
              <strong>Contra (Rejeitar): {resultados.rejeitar} voto(s) ({pct(resultados.rejeitar, resultados.total)}%)</strong>
              <div className="progress-bar-track">
                <div className="progress-bar-fill" style={{ width: `${pct(resultados.rejeitar, resultados.total)}%` }} />
              </div>
            </div>
            <div>
              <strong>Abstenções: {resultados.abster} voto(s) ({pct(resultados.abster, resultados.total)}%)</strong>
              <div className="progress-bar-track">
                <div className="progress-bar-fill" style={{ width: `${pct(resultados.abster, resultados.total)}%` }} />
              </div>
            </div>
          </div>
        </div>
      )}

      <Link to="/dashboard" className="btn-secondary">
        Voltar ao Painel
      </Link>
    </div>
  );
}