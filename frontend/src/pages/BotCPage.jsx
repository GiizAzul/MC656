import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/BotCPage.css';

export default function BotCPage() {
  const navigate = useNavigate();
  const [jogadores, setJogadores] = useState([]);
  const [meuStatus, setMeuStatus] = useState({
    pode_votar: true,
    mao_levantada: false,
    trancado: false,
    status: 'vivo',
    is_storyteller: false,
  });
  const [giro, setGiro] = useState({
    ativo: false,
    nomeado_id: null,
    nomeado_nome: null,
    id_ponteiro_atual: null,
    votos_computados: 0,
    mensagem_final: '',
  });

  const [nomeadoSelecionado, setNomeadoSelecionado] = useState('');
  const [erro, setErro] = useState('');
  const [veredito, setVeredito] = useState('');

  const carregarRoda = useCallback(async () => {
    try {
      const res = await fetch('/botc/api/estado');
      if (res.ok) {
        const data = await res.json();
        setJogadores(data.jogadores || []);
        setMeuStatus(data.usuario_atual || {});
        setGiro(data.giro || {});
        setNomeadoSelecionado((prev) => prev || data.giro?.nomeado_id || data.jogadores?.[0]?.id || '');
      }
    } catch {
      // ignora erro de rede temporário
    }
  }, []);

  // Polling rápido (400ms) para todos verem o ponteiro e as mãos em tempo real
  useEffect(() => {
    carregarRoda();
    const poll = setInterval(carregarRoda, 400);
    return () => clearInterval(poll);
  }, [carregarRoda]);

  // Bloqueia fechamento/recarregamento da aba enquanto a votação está ocorrendo
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (giro.ativo) {
        e.preventDefault();
        e.returnValue = 'Uma votação está em andamento na roda!';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [giro.ativo]);

  const iniciarGiroStoryteller = async () => {
    if (!nomeadoSelecionado) return;
    setErro('');
    setVeredito('');

    const form = new URLSearchParams();
    form.append('nomeado_id', nomeadoSelecionado);

    const res = await fetch('/botc/api/iniciar-giro', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });

    if (!res.ok) {
      setErro('Apenas o Storyteller pode iniciar o giro do ponteiro.');
    } else {
      await carregarRoda();
    }
  };

  const alternarMinhaMao = async () => {
    if (meuStatus.trancado) {
      setErro('🔒 O ponteiro já passou por você! Seu voto foi computado e sua mão não pode mais ser alterada.');
      return;
    }
    if (!meuStatus.pode_votar) {
      setErro('Você está morto e já utilizou seu voto fantasma.');
      return;
    }

    setErro('');
    const novaAcao = !meuStatus.mao_levantada ? 'levantar_mao' : 'abaixar_mao';
    const formData = new URLSearchParams();
    formData.append('acao', novaAcao);

    const res = await fetch('/botc/votar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: formData.toString(),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setErro(data.erro || 'Não foi possível alterar a mão.');
    } else {
      await carregarRoda();
    }
  };

  const apurarExecucaoDia = async () => {
    const res = await fetch('/botc/apurar', { method: 'POST' });
    const html = await res.text();
    const match = html.match(/O jogador executado foi:[^<]+|Ninguém foi executado[^<]+/);
    setVeredito(match ? match[0] : 'Apuração concluída.');
  };

  const idxPonteiro = jogadores.findIndex((j) => j.id === giro.id_ponteiro_atual);
  const anguloPonteiro =
    giro.ativo && idxPonteiro >= 0 && jogadores.length > 0
      ? (idxPonteiro * 360) / jogadores.length - 90
      : null;

  return (
    <div className="botc-page">
      <div className="botc-header">
        <div className="botc-title">
          <h1>🩸 Blood on the Clocktower — Roda da Cidade</h1>
          <p>
            Seu status: <strong>{meuStatus.status?.toUpperCase()}</strong> |{' '}
            {giro.nomeado_nome
              ? `Nomeado na Forca: 🎯 ${giro.nomeado_nome}`
              : 'Aguardando o Storyteller nomear um jogador'}
          </p>
        </div>

        <button
          type="button"
          className="btn-secondary"
          disabled={giro.ativo}
          title={giro.ativo ? 'Aguarde o término da contagem na roda para sair' : 'Voltar ao Painel'}
          onClick={() => {
            if (giro.ativo) {
              setErro('⚠️ Você não pode sair da partida enquanto o ponteiro de votação está girando!');
              return;
            }
            navigate('/dashboard');
          }}
        >
          {giro.ativo ? '🔒 Votação em Andamento' : 'Voltar ao Painel'}
        </button>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {giro.mensagem_final && !giro.ativo && (
        <div className="alert-banner alert-success">✅ {giro.mensagem_final}</div>
      )}
      {veredito && <div className="alert-banner alert-success">⚖️ {veredito}</div>}

      <div className="botc-layout">
        {/* RODA CIRCULAR DE BOLAS */}
        <div className="wheel-wrapper">
          <div className="town-wheel">
            {anguloPonteiro !== null && (
              <div
                className="wheel-pointer-arm"
                style={{ transform: `rotate(${anguloPonteiro}deg)` }}
              />
            )}

            <div className="wheel-center">
              <small style={{ color: '#94a3b8', fontSize: '0.7rem' }}>VOTOS COMPUTADOS</small>
              <strong style={{ fontSize: '2rem', color: '#f87171' }}>{giro.votos_computados || 0}</strong>
              <span style={{ fontSize: '0.74rem', color: '#cbd5e1' }}>
                {giro.ativo ? '🔄 Ponteiro girando...' : 'Roda livre'}
              </span>
            </div>

            {jogadores.map((jog, index) => {
              const total = jogadores.length || 1;
              const angleRad = ((index * 360) / total - 90) * (Math.PI / 180);
              const radius = 190;
              const x = 240 + radius * Math.cos(angleRad);
              const y = 240 + radius * Math.sin(angleRad);

              const isNomeado = jog.id === giro.nomeado_id;
              const isPonteiroAqui = giro.ativo && jog.id === giro.id_ponteiro_atual;

              return (
                <div
                  key={jog.id}
                  style={{ left: `${x}px`, top: `${y}px` }}
                  className={`seat-node ${isNomeado ? 'nominated' : ''} ${
                    isPonteiroAqui ? 'pointer-active' : ''
                  } ${jog.trancado ? 'locked' : ''} ${jog.mao_levantada ? 'hand-up' : ''}`}
                >
                  <span className="seat-name" title={jog.nome}>
                    {isNomeado ? '🎯' : ''} {jog.nome}
                  </span>
                  <span className="seat-hand">
                    {jog.mao_levantada ? '✋' : '👇'}
                    {jog.trancado ? '🔒' : ''}
                  </span>
                  <span className="seat-badge">
                    {jog.trancado ? 'Trancado' : jog.status === 'vivo' ? 'Vivo' : 'Morto'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* COLUNA LATERAL: JOGADOR + GRIMÓRIO EXCLUSIVO DO STORYTELLER */}
        <div className="controls-column">
          <div className="botc-panel-box">
            <h3>Seu Controle de Mão ({meuStatus.nome})</h3>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginTop: '0.3rem' }}>
              {meuStatus.trancado
                ? '🔒 O ponteiro já passou por você nesta nomeação! Seu voto foi computado e sua mão está travada.'
                : 'Enquanto o ponteiro não passar pela sua bola na roda, você pode levantar ou abaixar a mão livremente:'}
            </p>

            <button
              type="button"
              onClick={alternarMinhaMao}
              disabled={meuStatus.trancado || !meuStatus.pode_votar}
              className={`btn-hand-toggle ${meuStatus.mao_levantada ? 'raised' : 'lowered'}`}
            >
              {meuStatus.trancado
                ? `🔒 VOTO TRANCADO (${meuStatus.mao_levantada ? 'MÃO LEVANTADA' : 'MÃO ABAIXADA'})`
                : meuStatus.mao_levantada
                ? '✋ MÃO LEVANTADA (Clique para Abaixar)'
                : '👇 MÃO ABAIXADA (Clique para Levantar)'}
            </button>
          </div>

          {meuStatus.is_storyteller ? (
            <div className="botc-panel-box">
              <h3>📜 Grimório do Storyteller (Exclusivo Mestre)</h3>
              <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                Indique o jogador nomeado e inicie o ponteiro (começa à direita do nomeado e avança de 1 em 1).
              </p>

              <div className="form-group" style={{ marginTop: '0.85rem' }}>
                <label htmlFor="select-nomeado" style={{ color: '#e2e8f0' }}>
                  Jogador Nomeado para a Forca
                </label>
                <select
                  id="select-nomeado"
                  className="form-control"
                  value={nomeadoSelecionado}
                  disabled={giro.ativo}
                  onChange={(e) => setNomeadoSelecionado(e.target.value)}
                >
                  {jogadores.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.nome} ({j.status})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  className="btn-primary"
                  disabled={giro.ativo}
                  onClick={iniciarGiroStoryteller}
                >
                  {giro.ativo
                    ? '🔄 Girando Ponteiro Oficial...'
                    : '▶ Indicar Nomeado e Iniciar Giro do Ponteiro'}
                </button>

                <button
                  type="button"
                  className="btn-secondary"
                  disabled={giro.ativo}
                  onClick={apurarExecucaoDia}
                >
                  ⚖️ Encerrar Dia e Apurar Executado na Forca
                </button>
              </div>
            </div>
          ) : (
            <div className="botc-panel-box">
              <h3>👁️ Acompanhamento da Cidade</h3>
              <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginTop: '0.35rem' }}>
                Apenas o <strong>Storyteller</strong> pode nomear jogadores e iniciar o giro do ponteiro. Fique atento
                à posição do ponteiro dourado na roda!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}