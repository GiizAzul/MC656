import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import '../styles/BotCPage.css';

export default function BotCPage({ usuario }) {
  const [jogadores, setJogadores] = useState([]);
  const [meuStatus, setMeuStatus] = useState({
    pode_votar: true,
    mao_levantada: false,
    status: 'VIVO',
    is_storyteller: false,
  });

  // Estado da Apuração com Ponteiro na Roda
  const [nomeadoId, setNomeadoId] = useState('');
  const [apuracaoEmAndamento, setApuracaoEmAndamento] = useState(false);
  const [ordemGiro, setOrdemGiro] = useState([]); // índices dos jogadores na ordem horária a partir da direita do nomeado
  const [passoAtualGiro, setPassoAtualGiro] = useState(-1);
  const [jogadoresTrancados, setJogadoresTrancados] = useState({}); // { id_jogador: boolean (mão no momento do ponteiro) }
  const [votosComputadosGiro, setVotosComputadosGiro] = useState(0);

  const [feedback, setFeedback] = useState('');
  const [erro, setErro] = useState('');
  const [veredito, setVeredito] = useState('');

  const carregarRoda = useCallback(async () => {
    try {
      const res = await fetch('/botc/api/estado');
      if (res.ok) {
        const data = await res.json();
        setJogadores(data.jogadores || []);
        setMeuStatus(data.usuario_atual || {});
        if (!nomeadoId && data.jogadores?.length > 0) {
          setNomeadoId(data.jogadores[0].id);
        }
      }
    } catch {
      // ignora falha de rede temporária
    }
  }, [nomeadoId]);

  useEffect(() => {
    carregarRoda();
    const poll = setInterval(carregarRoda, 1500);
    return () => clearInterval(poll);
  }, [carregarRoda]);

  // Verifica se o jogador logado já teve a mão trancada pelo ponteiro
  const meuIdNaRoda = meuStatus.id;
  const minhaMaoTrancada = Boolean(
    apuracaoEmAndamento &&
      meuIdNaRoda &&
      Object.prototype.hasOwnProperty.call(jogadoresTrancados, meuIdNaRoda)
  );

  // Avanço automático do ponteiro a cada 2.5 segundos durante a apuração
  useEffect(() => {
    if (!apuracaoEmAndamento || passoAtualGiro < 0) return undefined;

    if (passoAtualGiro >= ordemGiro.length) {
      // Terminou de girar toda a roda! Registra automaticamente no backend
      setApuracaoEmAndamento(false);
      const jogadorNomeadoObj = jogadores.find((j) => j.id === nomeadoId);
      const nomeRegistrar = jogadorNomeadoObj ? jogadorNomeadoObj.nome : nomeadoId;

      const form = new URLSearchParams();
      form.append('nomeado', nomeRegistrar);
      form.append('num_votos', String(votosComputadosGiro));
      fetch('/botc/registrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      });

      setFeedback(
        `✅ Giro concluído! ${votosComputadosGiro} voto(s) computado(s) oficialmente para ${nomeRegistrar}.`
      );
      return undefined;
    }

    const timer = setTimeout(() => {
      const idxJogadorAtual = ordemGiro[passoAtualGiro];
      const jog = jogadores[idxJogadorAtual];
      if (jog) {
        const maoNoMomento = Boolean(jog.mao_levantada);
        const peso = maoNoMomento ? jog.peso || 1 : 0;

        setJogadoresTrancados((prev) => ({
          ...prev,
          [jog.id]: maoNoMomento,
        }));
        if (maoNoMomento) {
          setVotosComputadosGiro((prev) => prev + peso);
        }
      }
      setPassoAtualGiro((prev) => prev + 1);
    }, 2400);

    return () => clearTimeout(timer);
  }, [apuracaoEmAndamento, passoAtualGiro, ordemGiro, jogadores, nomeadoId, votosComputadosGiro]);

  const iniciarGiroApuracao = () => {
    if (jogadores.length === 0) return;
    const idxNomeado = jogadores.findIndex((j) => j.id === nomeadoId);
    const baseIdx = idxNomeado >= 0 ? idxNomeado : 0;

    // Começa pelo jogador imediatamente à direita (próximo índice no sentido horário) e termina no nomeado
    const sequencia = [];
    for (let i = 1; i <= jogadores.length; i += 1) {
      sequencia.push((baseIdx + i) % jogadores.length);
    }

    setJogadoresTrancados({});
    setVotosComputadosGiro(0);
    setOrdemGiro(sequencia);
    setPassoAtualGiro(0);
    setApuracaoEmAndamento(true);
    setVeredito('');
    setErro('');
    setFeedback(
      '🔄 Ponteiro iniciado pelo jogador à direita do nomeado! Mãos permanecem livres até o ponteiro passar.'
    );
  };

  const alternarMinhaMao = async () => {
    if (minhaMaoTrancada) {
      setErro('🔒 O ponteiro já passou por você! Seu voto já foi computado e sua mão não pode mais ser alterada.');
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

    if (res.ok) {
      await carregarRoda();
    }
  };

  const apurarExecucaoDia = async () => {
    const res = await fetch('/botc/apurar', { method: 'POST' });
    const html = await res.text();
    const match = html.match(/O jogador executado foi:[^<]+|Ninguém foi executado[^<]+/);
    setVeredito(match ? match[0] : 'Apuração concluída.');
  };

  // Cálculo do ângulo do ponteiro central
  const idxPonteiroAtivo =
    apuracaoEmAndamento && passoAtualGiro >= 0 && passoAtualGiro < ordemGiro.length
      ? ordemGiro[passoAtualGiro]
      : null;

  const anguloPonteiro =
    idxPonteiroAtivo !== null && jogadores.length > 0
      ? (idxPonteiroAtivo * 360) / jogadores.length - 90
      : -90;

  return (
    <div className="botc-page">
      <div className="botc-header">
        <div className="botc-title">
          <h1>🩸 Blood on the Clocktower — Roda da Cidade</h1>
          <p>
            Seu status: <strong>{meuStatus.status}</strong> | Mãos livres até o ponteiro da forca passar pelo seu
            assento.
          </p>
        </div>
        <Link to="/dashboard" className="btn-secondary">
          Voltar ao Painel
        </Link>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {feedback && <div className="alert-banner alert-success">{feedback}</div>}
      {veredito && <div className="alert-banner alert-success">⚖️ {veredito}</div>}

      <div className="botc-layout">
        {/* RODA VISUAL DE JOGADORES */}
        <div className="wheel-wrapper">
          <div className="town-wheel">
            {idxPonteiroAtivo !== null && (
              <div
                className="wheel-pointer-arm"
                style={{ transform: `rotate(${anguloPonteiro}deg)` }}
              />
            )}

            <div className="wheel-center">
              <small style={{ color: '#94a3b8' }}>VOTOS NA CONTAGEM</small>
              <strong style={{ fontSize: '1.9rem', color: '#f87171' }}>{votosComputadosGiro}</strong>
              <span style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                {apuracaoEmAndamento ? '🔄 Apurando...' : 'Aguardando giro'}
              </span>
            </div>

            {jogadores.map((jog, index) => {
              const total = jogadores.length || 1;
              const angleRad = ((index * 360) / total - 90) * (Math.PI / 180);
              const radius = 165;
              const x = 210 + radius * Math.cos(angleRad);
              const y = 210 + radius * Math.sin(angleRad);

              const jaTrancado = Object.prototype.hasOwnProperty.call(jogadoresTrancados, jog.id);
              const maoExibida = jaTrancado ? jogadoresTrancados[jog.id] : jog.mao_levantada;
              const isNomeado = jog.id === nomeadoId;
              const isPonteiroAqui = idxPonteiroAtivo === index;

              return (
                <div
                  key={jog.id}
                  style={{ left: `${x}px`, top: `${y}px` }}
                  className={`seat-node ${isNomeado ? 'nominated' : ''} ${
                    isPonteiroAqui ? 'pointer-active' : ''
                  } ${jaTrancado ? 'locked' : ''} ${maoExibida ? 'hand-up' : ''}`}
                >
                  <span className="seat-name" title={jog.nome}>
                    {isNomeado ? '🎯 ' : ''}
                    {jog.nome}
                  </span>
                  <span className="seat-hand">
                    {maoExibida ? '✋' : '👇'} {jaTrancado ? '🔒' : ''}
                  </span>
                  <span className="seat-badge">
                    {jaTrancado ? 'Computado' : jog.status === 'vivo' ? 'Vivo' : 'Morto'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* COLUNA DE CONTROLES DO JOGADOR E DO STORYTELLER */}
        <div className="controls-column">
          <div className="botc-panel-box">
            <h3>Seu Controle de Mão</h3>
            <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginTop: '0.3rem' }}>
              {minhaMaoTrancada
                ? '🔒 O ponteiro já passou pelo seu lugar nesta rodada. Sua mão está travada.'
                : 'Enquanto o ponteiro não passar por você, alterne sua mão livremente:'}
            </p>

            <button
              type="button"
              onClick={alternarMinhaMao}
              disabled={minhaMaoTrancada || !meuStatus.pode_votar}
              className={`btn-hand-toggle ${meuStatus.mao_levantada ? 'raised' : 'lowered'}`}
            >
              {minhaMaoTrancada
                ? `🔒 VOTO COMPUTADO (${jogadoresTrancados[meuIdNaRoda] ? 'MÃO LEVANTADA' : 'MÃO ABAIXADA'})`
                : meuStatus.mao_levantada
                ? '✋ MÃO LEVANTADA (Clique para Abaixar)'
                : '👇 MÃO ABAIXADA (Clique para Levantar)'}
            </button>
          </div>

          {(meuStatus.is_storyteller || true) && (
            <div className="botc-panel-box">
              <h3>📜 Controles de Contagem (Storyteller)</h3>
              <div className="form-group" style={{ marginTop: '0.85rem' }}>
                <label htmlFor="select-nomeado" style={{ color: '#e2e8f0' }}>
                  Jogador Nomeado para a Forca
                </label>
                <select
                  id="select-nomeado"
                  className="form-control"
                  value={nomeadoId}
                  disabled={apuracaoEmAndamento}
                  onChange={(e) => setNomeadoId(e.target.value)}
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
                  disabled={apuracaoEmAndamento}
                  onClick={iniciarGiroApuracao}
                >
                  {apuracaoEmAndamento
                    ? '🔄 Girando Ponteiro na Roda...'
                    : '▶ Iniciar Apuração (Ponteiro à Direita do Nomeado)'}
                </button>

                {meuStatus.is_storyteller && (
                  <button type="button" className="btn-secondary" onClick={apurarExecucaoDia}>
                    ⚖️ Encerrar Dia e Apurar Executado na Forca
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}