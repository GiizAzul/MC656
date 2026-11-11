import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/BotCPage.css';

export default function BotCPage({ usuario }) {
  const [maoLevantada, setMaoLevantada] = useState(false);
  const [totalMaos, setTotalMaos] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [erro, setErro] = useState('');

  // Cronômetro regressivo de votação (padrão: 60 segundos)
  const [segundosRestantes, setSegundosRestantes] = useState(60);
  const [cronometroAtivo, setCronometroAtivo] = useState(false);

  // Campos exclusivos do Storyteller
  const [nomeado, setNomeado] = useState('');
  const [numVotos, setNumVotos] = useState(0);
  const [veredito, setVeredito] = useState('');

  const isStoryteller = usuario?.escopo?.includes('STORYTELLER');

  useEffect(() => {
    if (!cronometroAtivo) return undefined;
    if (segundosRestantes <= 0) {
      setCronometroAtivo(false);
      setFeedback('⏱️ Tempo de votação encerrado! As mãos foram congeladas para contagem.');
      return undefined;
    }
    const timer = setInterval(() => {
      setSegundosRestantes((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [cronometroAtivo, segundosRestantes]);

  const formatarTempo = (seg) => {
    const m = String(Math.floor(seg / 60)).padStart(2, '0');
    const s = String(seg % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  const alternarMao = async () => {
    if (segundosRestantes <= 0) {
      setErro('O cronômetro zerou! Aguarde o Storyteller reiniciar a contagem.');
      return;
    }
    setErro('');
    const novaAcao = !maoLevantada ? 'levantar_mao' : 'abaixar_mao';

    const formData = new URLSearchParams();
    formData.append('acao', novaAcao);

    const response = await fetch('/botc/votar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: formData.toString(),
    });

    if (response.ok) {
      const data = await response.json();
      setMaoLevantada(data.mao_levantada);
      setTotalMaos(data.total_maos);
      setFeedback(
        data.mao_levantada
          ? '✋ Sua mão está LEVANTADA! (Clique novamente se quiser abaixar antes do tempo acabar)'
          : '👇 Sua mão está ABAIXADA.'
      );
    }
  };

  const registrarNaForca = async (e) => {
    e.preventDefault();
    const formData = new URLSearchParams();
    formData.append('nomeado', nomeado);
    formData.append('num_votos', String(numVotos));

    const res = await fetch('/botc/registrar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });
    if (res.ok) {
      setFeedback(`Registrados ${numVotos} votos para ${nomeado} na forca.`);
    }
  };

  const apurarForca = async () => {
    const res = await fetch('/botc/apurar', { method: 'POST' });
    const html = await res.text();
    const match = html.match(/O jogador executado foi:[^<]+|Ninguém foi executado[^<]+/);
    setVeredito(match ? match[0] : 'Apuração concluída.');
  };

  return (
    <div className="botc-page">
      <div className="botc-header">
        <div className="botc-title">
          <h1>🩸 Blood on the Clocktower — Praça da Cidade</h1>
          <p>Levante ou abaixe sua mão livremente enquanto o cronômetro estiver rodando.</p>
        </div>

        <div className="timer-box">
          <div>
            <small style={{ display: 'block', color: '#cbd5e1' }}>CRONÔMETRO DA FORCA</small>
            <span className="timer-display">{formatarTempo(segundosRestantes)}</span>
          </div>
          <div className="timer-controls">
            <button type="button" className="btn-timer" onClick={() => setCronometroAtivo(!cronometroAtivo)}>
              {cronometroAtivo ? '⏸ Pausar' : '▶ Iniciar'}
            </button>
            <button
              type="button"
              className="btn-timer"
              onClick={() => {
                setCronometroAtivo(false);
                setSegundosRestantes(30);
                setFeedback('');
              }}
            >
              ↺ 30s
            </button>
            <button
              type="button"
              className="btn-timer"
              onClick={() => {
                setCronometroAtivo(false);
                setSegundosRestantes(60);
                setFeedback('');
              }}
            >
              ↺ 60s
            </button>
          </div>
        </div>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {feedback && <div className="alert-banner alert-success">{feedback}</div>}
      {veredito && <div className="alert-banner alert-success">⚖️ {veredito}</div>}

      <div className="botc-grid">
        <div className="town-square-card">
          <h2>Sua Ação na Roda</h2>
          <div className="hand-toggle-area">
            <button
              type="button"
              onClick={alternarMao}
              className={`btn-hand-toggle ${maoLevantada ? 'raised' : 'lowered'}`}
            >
              {maoLevantada ? '✋ MÃO LEVANTADA (Clique para Abaixar)' : '👇 MÃO ABAIXADA (Clique para Levantar)'}
            </button>
            <p style={{ marginTop: '1rem', color: '#cbd5e1', fontSize: '0.9rem' }}>
              Mãos levantadas na cidade neste instante: <strong>{totalMaos}</strong>
            </p>
          </div>

          <Link to="/dashboard" className="btn-secondary">
            Voltar ao Painel
          </Link>
        </div>

        {isStoryteller && (
          <div className="storyteller-card">
            <h2>📜 Grimório do Storyteller</h2>
            <form onSubmit={registrarNaForca} style={{ marginTop: '1rem' }}>
              <div className="form-group">
                <label htmlFor="botc-nomeado" style={{ color: '#e2e8f0' }}>
                  Jogador Nomeado na Forca
                </label>
                <input
                  id="botc-nomeado"
                  type="text"
                  className="form-control"
                  value={nomeado}
                  onChange={(e) => setNomeado(e.target.value)}
                  placeholder="Ex: Leo"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="botc-votos" style={{ color: '#e2e8f0' }}>
                  Quantidade de Votos Computados
                </label>
                <input
                  id="botc-votos"
                  type="number"
                  min="0"
                  step="1"
                  className="form-control"
                  value={numVotos}
                  onChange={(e) => setNumVotos(Math.max(0, parseInt(e.target.value || '0', 10)))}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className="btn-primary">
                  Registrar Votos
                </button>
                <button type="button" onClick={apurarForca} className="btn-secondary">
                  Apurar Execução
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}