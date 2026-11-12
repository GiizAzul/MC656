import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/BotCPage.css';

export default function BotCPage() {
  const navigate = useNavigate();
  const [novaSenhaSala, setNovaSenhaSala] = useState('');
  const [semSalas, setSemSalas] = useState(false);
  const [requerSenha, setRequerSenha] = useState(false);
  const [senhaDigitadaSala, setSenhaDigitadaSala] = useState('');
  const [jogadorAlvoStatus, setJogadorAlvoStatus] = useState('');
  const [novoStatusEscolhido, setNovoStatusEscolhido] = useState('Vivo');
  const [partidaId, setPartidaId] = useState('principal');
  const [partidasDisponiveis, setPartidasDisponiveis] = useState([]);
  const [partidaAtualInfo, setPartidaAtualInfo] = useState({
    id: 'principal',
    nome: 'Partida Principal',
    storyteller_id: null,
    storyteller_nome: 'Aguardando Storyteller',
  });
  const [novoNomeSala, setNovoNomeSala] = useState('');

  const [jogadores, setJogadores] = useState([]);
  const [meuStatus, setMeuStatus] = useState({
    pode_votar: true,
    mao_levantada: false,
    trancado: false,
    status: 'vivo',
    is_storyteller_desta_partida: false,
    tem_escopo_storyteller: false,
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

  // Ângulo cumulativo contínuo para o ponteiro NUNCA girar para trás ao cruzar o topo da roda
  const anguloAcumuladoRef = useRef(null);

  const carregarRoda = useCallback(async () => {
    try {
      const res = await fetch(`/botc/api/estado?partida_id=${encodeURIComponent(partidaId)}`);
      if (res.status === 403) {
        const data = await res.json();
        setRequerSenha(true);
        setPartidaAtualInfo(data.partida_atual || {});
        setPartidasDisponiveis(data.partidas_disponiveis || []);
        return;
      }
      if (res.ok) {
        const data = await res.json();
        if (data.sem_salas) {
          setSemSalas(true);
          setPartidasDisponiveis([]);
          setMeuStatus(data.usuario_atual || {});
          return;
        }
        setSemSalas(false);
        setRequerSenha(false);
        setJogadores(data.jogadores || []);
        setMeuStatus(data.usuario_atual || {});
        setGiro(data.giro || {});
        setPartidaAtualInfo(data.partida_atual || {});
        setPartidasDisponiveis(data.partidas_disponiveis || []);
        if (data.partida_atual?.id && data.partida_atual.id !== partidaId) {
          setPartidaId(data.partida_atual.id);
        }
        setNomeadoSelecionado((prev) => prev || data.giro?.nomeado_id || data.jogadores?.[0]?.id || '');
        setJogadorAlvoStatus((prev) => prev || data.jogadores?.[0]?.id || '');
      }
    } catch {
      // ignora oscilação temporária
    }
  }, [partidaId]);

  useEffect(() => {
    carregarRoda();
    const poll = setInterval(carregarRoda, 400);
    return () => clearInterval(poll);
  }, [carregarRoda]);

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

  // Calcula o ângulo sempre avançando em sentido horário (delta >= 0)
  const idxPonteiro = jogadores.findIndex((j) => j.id === giro.id_ponteiro_atual);
  let anguloPonteiro = null;
  if (giro.ativo && idxPonteiro >= 0 && jogadores.length > 0) {
    const anguloAlvoBase = (idxPonteiro * 360) / jogadores.length - 90;
    if (anguloAcumuladoRef.current === null) {
      anguloAcumuladoRef.current = anguloAlvoBase;
    } else {
      const atualMod = ((anguloAcumuladoRef.current % 360) + 360) % 360;
      const alvoMod = ((anguloAlvoBase % 360) + 360) % 360;
      let delta = alvoMod - atualMod;
      if (delta < -0.01) {
        delta += 360; // força a continuar girando para a frente (sentido horário)
      }
      anguloAcumuladoRef.current += delta;
    }
    anguloPonteiro = anguloAcumuladoRef.current;
  } else {
    anguloAcumuladoRef.current = null;
  }

  const assumirCentroDaRoda = async () => {
    setErro('');
    const form = new URLSearchParams();
    form.append('partida_id', partidaId);
    const res = await fetch('/botc/api/assumir-storyteller', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      setErro(d.detail || 'Não foi possível assumir como Storyteller.');
    } else {
      await carregarRoda();
    }
  };

  const criarNovaPartida = async (e) => {
    e.preventDefault();
    if (!novoNomeSala.trim()) return;
    const form = new URLSearchParams();
    form.append('nome_sala', novoNomeSala);
    form.append('senha_sala', novaSenhaSala);

    const res = await fetch('/botc/api/criar-partida', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (res.ok) {
      const d = await res.json();
      setNovoNomeSala('');
      setNovaSenhaSala('');
      setNomeadoSelecionado('');
      setPartidaId(d.partida_id);
    }
  };

  const entrarComSenha = async (e) => {
    e.preventDefault();
    setErro('');
    const form = new URLSearchParams();
    form.append('partida_id', partidaId);
    form.append('senha_sala', senhaDigitadaSala);
    const res = await fetch('/botc/api/entrar-sala', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (!res.ok) {
      setErro('Senha incorreta para esta sala!');
    } else {
      setSenhaDigitadaSala('');
      setRequerSenha(false);
      await carregarRoda();
    }
  };

  const sairDaSalaAtual = async () => {
    if (giro.ativo) return;
    setErro('');
    const form = new URLSearchParams();
    form.append('partida_id', partidaId);
    const res = await fetch('/botc/api/sair-sala', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      setErro(d.detail || 'Não foi possível sair da sala.');
      return;
    }
    navigate('/dashboard');
  };

  const encerrarPartidaInteira = async () => {
    setErro('');
    const form = new URLSearchParams();
    form.append('partida_id', partidaId);
    const res = await fetch('/botc/api/encerrar-partida', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (res.ok) {
      await carregarRoda();
    }
  };

  const excluirSalaAtual = async () => {
    if (giro.ativo) return;
    setErro('');
    const form = new URLSearchParams();
    form.append('partida_id', partidaId);
    const res = await fetch('/botc/api/excluir-sala', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (res.ok) {
      const d = await res.json();
      setPartidaId(d.partida_destino || '');
      await carregarRoda();
    } else {
      const d = await res.json().catch(() => ({}));
      setErro(d.detail || 'Não foi possível excluir a sala.');
    }
  };

  const alterarStatusVidaJogador = async (e) => {
    e.preventDefault();
    if (!jogadorAlvoStatus) return;
    setErro('');
    const form = new URLSearchParams();
    form.append('id_jogador', jogadorAlvoStatus);
    form.append('novo_status', novoStatusEscolhido);
    form.append('partida_id', partidaId);

    const res = await fetch('/botc/status-jogador', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (!res.ok) {
      setErro('Erro ao atualizar status do jogador.');
    } else {
      await carregarRoda();
    }
  };
  const iniciarGiroStoryteller = async () => {
    if (!nomeadoSelecionado) return;
    setErro('');
    setVeredito('');

    const form = new URLSearchParams();
    form.append('nomeado_id', nomeadoSelecionado);
    form.append('partida_id', partidaId);

    const res = await fetch('/botc/api/iniciar-giro', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });

    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      setErro(d.detail || 'Apenas o Storyteller titular desta partida pode iniciar o ponteiro.');
    } else {
      await carregarRoda();
    }
  };

  const alternarMinhaMao = async () => {
    if (meuStatus.is_storyteller_desta_partida) {
      setErro('O Storyteller fica no centro da roda e não vota na partida que conduz!');
      return;
    }
    if (meuStatus.trancado) {
      setErro('🔒 O ponteiro já passou por você! Seu voto foi computado e sua mão está travada.');
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
    formData.append('partida_id', partidaId);

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
    const form = new URLSearchParams();
    form.append('partida_id', partidaId);
    const res = await fetch('/botc/apurar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    const html = await res.text();
    const match = html.match(/O jogador executado foi:[^<]+|Ninguém foi executado[^<]+/);
    setVeredito(match ? match[0] : 'Apuração concluída.');
    await carregarRoda();
  };

  return (
    <div className="botc-page">
      <div className="botc-header">
        <div className="botc-title">
          <h1>🩸 {partidaAtualInfo.nome}</h1>
          <p>
            Seu papel nesta sala: <strong>{meuStatus.status?.toUpperCase()}</strong> |{' '}
            {giro.nomeado_nome
              ? `Nomeado na Forca: 🎯 ${giro.nomeado_nome}`
              : 'Aguardando o Storyteller nomear um jogador'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            aria-label="Selecionar Sala de Partida"
            className="form-control"
            disabled={giro.ativo}
            value={partidaId}
            onChange={(e) => {
              setNomeadoSelecionado('');
              setErro('');
              setPartidaId(e.target.value);
            }}
          >
            {partidasDisponiveis.map((p) => (
              <option key={p.id} value={p.id}>
                {p.tem_senha ? '🔒 ' : '🎲 '}
                {p.nome} (Mestre: {p.storyteller_nome || 'Livre'})
              </option>
            ))}
          </select>

          {partidaId !== 'principal' && (
            <button
              type="button"
              className="btn-secondary"
              disabled={giro.ativo}
              onClick={sairDaSalaAtual}
              title="Sair desta sala (se todos saírem, a sala é excluída automaticamente)"
            >
              🚪 Sair da Sala
            </button>
          )}
        </div>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {giro.mensagem_final && !giro.ativo && (
        <div className="alert-banner alert-success">✅ {giro.mensagem_final}</div>
      )}
      {veredito && <div className="alert-banner alert-success">⚖️ {veredito}</div>}

      {requerSenha ? (
        <div className="botc-panel-box" style={{ maxWidth: '440px', margin: '2rem auto' }}>
          <h3>🔒 Sala Privada: {partidaAtualInfo.nome}</h3>
          <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: '0.5rem 0 1rem' }}>
            Digite a senha definida pelo criador para entrar nesta roda:
          </p>
          <form onSubmit={entrarComSenha} style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="password"
              className="form-control"
              placeholder="Senha da sala"
              value={senhaDigitadaSala}
              onChange={(e) => setSenhaDigitadaSala(e.target.value)}
              required
            />
            <button type="submit" className="btn-primary">
              Entrar
            </button>
          </form>
        </div>
      ) : (
        <div className="botc-layout">
          {/* RODA CIRCULAR COM O STORYTELLER NO CENTRO E JOGADORES NAS BOLAS AO REDOR */}
          <div className="wheel-wrapper">
            <div className="town-wheel">
              {anguloPonteiro !== null && (
                <div
                  className="wheel-pointer-arm"
                  style={{ transform: `rotate(${anguloPonteiro}deg)` }}
                />
              )}

              {/* CENTRO DA RODA: STORYTELLER + CONTADOR */}
              <div className="wheel-center">
                <span style={{ fontSize: '0.72rem', color: '#fbbf24', fontWeight: 700 }}>
                  🎩 STORYTELLER
                </span>
                <strong style={{ fontSize: '0.82rem', color: '#f8fafc', marginBottom: '0.2rem' }}>
                  {partidaAtualInfo.storyteller_nome}
                </strong>
                <small style={{ color: '#94a3b8', fontSize: '0.65rem' }}>VOTOS NA FORCA</small>
                <strong style={{ fontSize: '1.65rem', color: '#f87171', lineHeight: 1.1 }}>
                  {giro.votos_computados || 0}
                </strong>
              </div>

              {jogadores.map((jog, index) => {
                const total = jogadores.length || 1;
                const angleRad = ((index * 360) / total - 90) * (Math.PI / 180);
                const radius = 190;
                const x = 240 + radius * Math.cos(angleRad);
                const y = 240 + radius * Math.sin(angleRad);

                const isNomeado = jog.id === giro.nomeado_id;
                const isPonteiroAqui = giro.ativo && jog.id === giro.id_ponteiro_atual;
                const estaVivo = jog.status?.toLowerCase() === 'vivo';
                const temGhostVote = !estaVivo && jog.pode_votar;

                return (
                  <div
                    key={jog.id}
                    style={{ left: `${x}px`, top: `${y}px` }}
                    className={`seat-node ${!estaVivo ? 'dead-player' : ''} ${
                      isNomeado ? 'nominated' : ''
                    } ${isPonteiroAqui ? 'pointer-active' : ''} ${jog.trancado ? 'locked' : ''} ${
                      jog.mao_levantada ? 'hand-up' : ''
                    }`}
                  >
                    {temGhostVote && (
                      <span className="ghost-vote-indicator" title="Morto com Voto Fantasma disponível!">
                        👻
                      </span>
                    )}
                    <span className="seat-name" title={jog.nome}>
                      {isNomeado ? '🎯' : ''} {jog.nome}
                    </span>
                    <span className="seat-hand">
                      {jog.mao_levantada ? '✋' : '👇'}
                      {jog.trancado ? '🔒' : ''}
                    </span>
                    <span className="seat-badge">
                      {jog.trancado
                        ? 'Trancado'
                        : estaVivo
                        ? 'Vivo'
                        : temGhostVote
                        ? 'Fantasma'
                        : 'Morto'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* COLUNA LATERAL DE CONTROLES */}
          <div className="controls-column">
            {!meuStatus.is_storyteller_desta_partida ? (
              <div className="botc-panel-box">
                <h3>Seu Assento de Jogador ({meuStatus.nome})</h3>
                <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginTop: '0.3rem' }}>
                  {meuStatus.trancado
                    ? '🔒 O ponteiro já passou pela sua bola! Seu voto foi computado e sua mão está travada.'
                    : 'Enquanto o ponteiro não passar por você, alterne sua mão livremente:'}
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
            ) : (
              <div className="botc-panel-box">
                <h3>🎩 Você está no Centro da Roda (Storyteller)</h3>
                <p style={{ fontSize: '0.88rem', color: '#cbd5e1', marginTop: '0.35rem' }}>
                  Como Storyteller titular desta partida, você conduz a execução no centro da roda e{' '}
                  <strong>não possui poder de voto</strong> nesta sala.
                </p>
              </div>
            )}

            {meuStatus.tem_escopo_storyteller && !partidaAtualInfo.storyteller_id && (
              <div className="botc-panel-box">
                <h3>🎩 Assumir Centro da Roda</h3>
                <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '0.75rem' }}>
                  Esta partida ainda não possui Storyteller. Deseja assumir o centro da roda (máx. 1 por partida)?
                </p>
                <button type="button" className="btn-primary" onClick={assumirCentroDaRoda}>
                  Assumir como Único Storyteller desta Partida
                </button>
              </div>
            )}

            {meuStatus.is_storyteller_desta_partida && (
              <div className="botc-panel-box">
                <h3>📜 Grimório do Storyteller (Condução da Roda)</h3>
                <div className="form-group" style={{ marginTop: '0.85rem' }}>
                  <label htmlFor="select-nomeado" style={{ color: '#e2e8f0' }}>
                    Indicar Jogador Nomeado para a Forca
                  </label>
                  <select
                    id="select-nomeado"
                    className="form-control"
                    value={nomeadoSelecionado}
                    disabled={giro.ativo}
                    onChange={(e) => setNomeadoSelecionado(e.target.value)}
                  >
                    {jogadores.map((j) => (
                      <option key={j.id} value={j.id} disabled={j.ja_nomeado_hoje}>
                        {j.nome} ({j.status}) {j.ja_nomeado_hoje ? '— [Já nomeado hoje]' : ''}
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
                  <hr style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '1.1rem 0' }} />

                <form onSubmit={alterarStatusVidaJogador}>
                  <label htmlFor="select-status-jog" style={{ color: '#e2e8f0', fontSize: '0.88rem', fontWeight: 600 }}>
                    Alterar Status de Vida / Voto Fantasma
                  </label>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem', flexWrap: 'wrap' }}>
                    <select
                      id="select-status-jog"
                      className="form-control"
                      style={{ flex: 1 }}
                      value={jogadorAlvoStatus}
                      onChange={(e) => setJogadorAlvoStatus(e.target.value)}
                    >
                      {jogadores.map((j) => (
                        <option key={j.id} value={j.id}>
                          {j.nome} ({j.status})
                        </option>
                      ))}
                    </select>
                    <select
                      aria-label="Novo Status de Vida"
                      className="form-control"
                      style={{ flex: 1 }}
                      value={novoStatusEscolhido}
                      onChange={(e) => setNovoStatusEscolhido(e.target.value)}
                    >
                      <option value="Vivo">Vivo</option>
                      <option value="Morto (Com Voto)">Morto (Com Voto Fantasma 👻)</option>
                      <option value="Morto (Sem Voto)">Morto (Sem Voto Fantasma)</option>
                    </select>
                    
                    <button type="submit" className="btn-secondary" disabled={giro.ativo}>
                      Aplicar Status
                    </button>
                  </div>
                </form>

              {partidaId !== 'principal' && (
                <button
                  type="button"
                  onClick={excluirSalaAtual}
                  disabled={giro.ativo}
                  style={{
                    marginTop: '1rem',
                    width: '100%',
                    backgroundColor: '#991b1b',
                    color: '#fff',
                    border: 'none',
                    padding: '0.65rem',
                    borderRadius: '8px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  🗑️ Excluir Esta Sala (Mestre)
                </button>
              )}
                </div>
              </div>
            )}
            <div className="botc-panel-box">
              <h3>➕ Criar Nova Sala / Partida Separada</h3>
              <form
                onSubmit={criarNovaPartida}
                style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem', marginTop: '0.75rem' }}
              >
                <input
                  type="text"
                  className="form-control"
                  placeholder="Nome da nova sala (ex: Mesa dos Amigos)"
                  value={novoNomeSala}
                  onChange={(e) => setNovoNomeSala(e.target.value)}
                  disabled={giro.ativo}
                  required
                />
                <input
                  type="password"
                  className="form-control"
                  placeholder="Senha opcional (deixe em branco para sala pública)"
                  value={novaSenhaSala}
                  onChange={(e) => setNovaSenhaSala(e.target.value)}
                  disabled={giro.ativo}
                />
                <button type="submit" className="btn-secondary" disabled={giro.ativo}>
                  Criar Sala Limpa
                </button>
              </form>
            </div>
          </div>
        </div>
        )}
    </div>
  );
}