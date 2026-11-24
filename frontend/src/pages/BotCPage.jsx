import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import '../styles/BotCPage.css';

export default function BotCPage({ usuario }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const chaveSala = `mc656_botc_sessao_${usuario?.id || 'anon'}`;

  const sessaoSalva = (() => {
    const daUrl = searchParams.get('partida_id');
    if (daUrl) return { partidaId: daUrl, emPartida: true };
    try {
      return JSON.parse(localStorage.getItem(chaveSala)) || null;
    } catch {
      return null;
    }
  })();

  const [emPartida, setEmPartida] = useState(Boolean(sessaoSalva?.emPartida));
  const [partidaId, setPartidaId] = useState(sessaoSalva?.partidaId || 'principal');
  const [novaSenhaSala, setNovaSenhaSala] = useState('');
  const [semSalas, setSemSalas] = useState(false);
  const [requerSenha, setRequerSenha] = useState(false);
  const [senhaDigitadaSala, setSenhaDigitadaSala] = useState('');
  const [jogadorAlvoStatus, setJogadorAlvoStatus] = useState('');
  const [novoStatusEscolhido, setNovoStatusEscolhido] = useState('Vivo');
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

  // Ângulo cumulativo contínuo para o ponteiro nunca girar para trás ao cruzar o topo da roda
  const anguloAcumuladoRef = useRef(null);
  const maoOtimistaRef = useRef({ pendente: false, valor: false });

  const carregarRoda = useCallback(async () => {
    try {
      const url = `/botc/api/estado?partida_id=${encodeURIComponent(partidaId)}&apenas_lobby=${!emPartida}`;
      const res = await fetch(url, { credentials: 'include' });
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
        const meuStatusServidor = data.usuario_atual || {};
        if (maoOtimistaRef.current.pendente) {
          meuStatusServidor.mao_levantada = maoOtimistaRef.current.valor;
        }
        setSemSalas(false);
        setRequerSenha(false);
        setMeuStatus(meuStatusServidor);
        setJogadores(
          (data.jogadores || []).map((j) =>
            maoOtimistaRef.current.pendente && j.id === meuStatusServidor.id
          ? { ...j, mao_levantada: maoOtimistaRef.current.valor }
          : j
        )
        );        
        setGiro(data.giro || {});
        setPartidaAtualInfo(data.partida_atual || {});
        setPartidasDisponiveis(data.partidas_disponiveis || []);
        if (data.partida_atual?.id && data.partida_atual.id !== partidaId) {
          setPartidaId(data.partida_atual.id);
        }
        const lista = data.jogadores || [];
        setNomeadoSelecionado((prev) => {
          const aindaValido = lista.some((j) => j.id === prev && !j.ja_nomeado_hoje);
          if (aindaValido) return prev;
          const primeiroLivre = lista.find((j) => !j.ja_nomeado_hoje);
          return primeiroLivre?.id || lista[0]?.id || '';
        });
        setJogadorAlvoStatus((prev) => {
          const existe = lista.some((j) => j.id === prev);
          return existe ? prev : lista[0]?.id || '';
        });
      }
    } catch {
      // ignora oscilação temporária
    }
  }, [partidaId, emPartida]);

  useEffect(() => {
    carregarRoda();
    const intervaloMs = giro.ativo ? 500 : 2000;
    const poll = setInterval(carregarRoda, intervaloMs);
    return () => clearInterval(poll);
  }, [carregarRoda, giro.ativo]);

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

  useEffect(() => {
    const deveTravarNavegacao = emPartida && (giro.ativo || meuStatus.preso_como_storyteller);
    if (!deveTravarNavegacao) return undefined;

    window.history.pushState(null, '', window.location.href);
    const impedirBotaoVoltarBrowser = () => {
      window.history.pushState(null, '', window.location.href);
      setErro('🔒 Navegação bloqueada! Use o botão oficial de Sair/Encerrar quando a votação ou partida terminar.');
    };

    window.addEventListener('popstate', impedirBotaoVoltarBrowser);
    return () => window.removeEventListener('popstate', impedirBotaoVoltarBrowser);
  }, [emPartida, giro.ativo, meuStatus.preso_como_storyteller]);

  useEffect(() => {
    if (emPartida && partidaId && !semSalas) {
      localStorage.setItem(chaveSala, JSON.stringify({ partidaId, emPartida: true }));
    }
  }, [chaveSala, emPartida, partidaId, semSalas]);

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
    setErro('');
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
      setEmPartida(true);
    } else {
      const d = await res.json().catch(() => ({}));
      setErro(d.detail || 'Não é possível criar uma nova sala enquanto a partida atual não acabou.');
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

  const sairDaSalaAtual = async (irParaDashboard = false) => {
    if (giro.ativo) return;
    if (meuStatus.preso_como_storyteller) {
      setErro('⚠️ Como Storyteller de uma partida ativa, encerre a partida inteira ou exclua a sala antes de sair!');
      return;
    }

    const totalParticipantesNaSala = jogadores.length + (partidaAtualInfo.storyteller_id ? 1 : 0);
    if (totalParticipantesNaSala <= 1) {
      const confirmar = window.confirm(
        '⚠️ Tem certeza que deseja sair? Você é a única pessoa nesta sala — se sair ela será excluída e perdida.'
      );
      if (!confirmar) return;
    }

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
    localStorage.removeItem(chaveSala);
    if (irParaDashboard) {
      navigate('/dashboard');
    } else {
      setEmPartida(false);
    }
  };

  const trocarDeSala = async (novaPartidaId) => {
  if (novaPartidaId === partidaId) return;
  const form = new URLSearchParams({ partida_id: partidaId });
  await fetch('/botc/api/sair-sala', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  }).catch(() => {});
  setNomeadoSelecionado('');
  setJogadorAlvoStatus('');
  setErro('');
  setPartidaId(novaPartidaId);
};

  const excluirSalaAtual = async () => {
    if (giro.ativo) return;
    const confirmar = window.confirm(
      `🗑️ Tem certeza que deseja excluir a sala "${partidaAtualInfo.nome}"? A sala será excluída e perdida para todos.`
    );
    if (!confirmar) return;

    setErro('');
    const form = new URLSearchParams();
    form.append('partida_id', partidaId);
    const res = await fetch('/botc/api/excluir-sala', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (res.ok) {
      localStorage.removeItem(chaveSala);
      const d = await res.json();
      setPartidaId(d.partida_destino || '');
      setEmPartida(false);
    } else {
      const d = await res.json().catch(() => ({}));
      setErro(d.detail || 'Não foi possível excluir a sala.');
    }
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
      localStorage.removeItem(chaveSala);
      await carregarRoda();
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
  const estadoAnterior = Boolean(meuStatus.mao_levantada);
  const novoEstado = !estadoAnterior;
  const novaAcao = novoEstado ? 'levantar_mao' : 'abaixar_mao';

  // 1. Atualiza o botão e a bolinha na roda imediatamente (0ms)
  maoOtimistaRef.current = { pendente: true, valor: novoEstado };
  setMeuStatus((prev) => ({ ...prev, mao_levantada: novoEstado }));
  setJogadores((prev) =>
    prev.map((j) => (j.id === meuStatus.id ? { ...j, mao_levantada: novoEstado } : j))
  );

  try {
    const formData = new URLSearchParams();
    formData.append('acao', novaAcao);
    formData.append('partida_id', partidaId);

    const res = await fetch('/botc/votar', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: formData.toString(),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.erro || 'Não foi possível alterar a mão.');
    }
  } catch (err) {
    // 2. Reverte visualmente se o servidor bloqueou (ex: ponteiro já passou)
    setMeuStatus((prev) => ({ ...prev, mao_levantada: estadoAnterior }));
    setJogadores((prev) =>
      prev.map((j) => (j.id === meuStatus.id ? { ...j, mao_levantada: estadoAnterior } : j))
    );
    setErro(err.message || 'Erro de conexão ao alterar a mão.');
  } finally {
    maoOtimistaRef.current = { pendente: false, valor: novoEstado };
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
    await carregarRoda();
  };

  if (!emPartida) {
    return (
      <div className="botc-page">
        <div className="botc-header">
          <div className="botc-title">
            <h1>🩸 Blood on the Clocktower — Lobby de Partidas</h1>
            <p>Escolha uma sala existente para entrar na roda ou crie uma nova.</p>
          </div>
          <button type="button" className="btn-secondary" onClick={() => navigate('/dashboard')}>
            Voltar ao Menu Principal
          </button>
        </div>

        {erro && <div className="alert-banner alert-error">{erro}</div>}

        <div className="botc-layout">
          <div className="botc-panel-box">
            <h3>🎲 Salas Disponíveis ({partidasDisponiveis.length})</h3>
            {partidasDisponiveis.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
                Nenhuma partida ativa no momento. Crie uma nova sala ao lado!
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
                {partidasDisponiveis.map((p) => (
                  <div
                    key={p.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.9rem 1.1rem',
                      background: 'var(--surface)',
                      border: '1px solid rgba(255,255,255,0.12)',
                      borderRadius: '10px',
                    }}
                  >
                    <div>
                      <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                        {p.tem_senha ? '🔒 ' : '🎲 '}
                        {p.nome}
                      </strong>
                      <span style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        Storyteller: {p.storyteller_nome || 'Livre'}
                      </span>
                    </div>
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => {
                        setPartidaId(p.id);
                        setErro('');
                        setEmPartida(true);
                      }}
                    >
                      Entrar na Sala →
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="botc-panel-box">
            <h3>➕ Criar Nova Sala</h3>
            <form
              onSubmit={criarNovaPartida}
              style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', marginTop: '0.85rem' }}
            >
              <input
                type="text"
                className="form-control"
                placeholder="Nome da sala (ex: Mesa Noturna)"
                value={novoNomeSala}
                onChange={(e) => setNovoNomeSala(e.target.value)}
                required
              />
              <input
                type="password"
                className="form-control"
                placeholder="Senha opcional (em branco para pública)"
                value={novaSenhaSala}
                onChange={(e) => setNovaSenhaSala(e.target.value)}
              />
              <button type="submit" className="btn-primary">
                Criar e Entrar na Sala
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }
  
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
          {partidasDisponiveis.length > 0 && (
            <select
              aria-label="Selecionar Sala de Partida"
              className="form-control"
              disabled={giro.ativo || meuStatus.preso_como_storyteller}
              title={
                meuStatus.preso_como_storyteller
                  ? 'Encerre a partida ou exclua a sala atual antes de trocar de sala'
                  : 'Selecionar Sala'
              }
              value={partidaId}
              onChange={(e) => {
                trocarDeSala(e.target.value);
              }}
            >
              {partidasDisponiveis.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.tem_senha ? '🔒 ' : '🎲 '}
                  {p.nome} (Mestre: {p.storyteller_nome || 'Livre'})
                </option>
              ))}
            </select>
          )}

          {!semSalas && (
            <button
              type="button"
              className="btn-secondary"
              disabled={giro.ativo || meuStatus.preso_como_storyteller}
              onClick={() => sairDaSalaAtual(false)}
              title="Sair desta sala e voltar ao Lobby"
            >
              🚪 Sair da Sala
            </button>
          )}

          <button
            type="button"
            className="btn-secondary"
            disabled={giro.ativo || meuStatus.preso_como_storyteller}
            onClick={() => sairDaSalaAtual(true)}
          >
            {giro.ativo
              ? '🔒 Votação em Andamento'
              : meuStatus.preso_como_storyteller
              ? '🔒 Partida Ativa (Mestre)'
              : 'Voltar ao Menu Principal'}
          </button>
        </div>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {giro.mensagem_final && !giro.ativo && (
        <div className="alert-banner alert-success">✅ {giro.mensagem_final}</div>
      )}

      {semSalas ? (
        <div className="botc-panel-box" style={{ maxWidth: '480px', margin: '2rem auto', textAlign: 'center' }}>
          <h3>🎲 Nenhuma Sala Ativa no Momento</h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: '0.6rem 0 1.2rem' }}>
            Todas as salas foram encerradas ou excluídas. Crie uma nova sala abaixo para iniciar uma partida!
          </p>
          <form onSubmit={criarNovaPartida} style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Nome da nova sala (ex: Mesa Principal)"
              value={novoNomeSala}
              onChange={(e) => setNovoNomeSala(e.target.value)}
              required
            />
            <input
              type="password"
              className="form-control"
              placeholder="Senha opcional (em branco para pública)"
              value={novaSenhaSala}
              onChange={(e) => setNovaSenhaSala(e.target.value)}
            />
            <button type="submit" className="btn-primary">
              ➕ Criar Nova Sala
            </button>
          </form>
        </div>
      ) : requerSenha ? (
        <div className="botc-panel-box" style={{ maxWidth: '440px', margin: '2rem auto' }}>
          <h3>🔒 Sala Privada: {partidaAtualInfo.nome}</h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: '0.5rem 0 1rem' }}>
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
                <strong style={{ fontSize: '0.82rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  {partidaAtualInfo.storyteller_nome}
                </strong>
                <small style={{ color: 'var(--text-secondary)', fontSize: '0.65rem' }}>VOTOS NA FORCA</small>
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
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
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
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                  Como Storyteller titular desta partida, você conduz a execução no centro da roda e{' '}
                  <strong>não possui poder de voto</strong> nesta sala.
                </p>
              </div>
            )}

            {meuStatus.tem_escopo_storyteller && !partidaAtualInfo.storyteller_id && (
              <div className="botc-panel-box">
                <h3>🎩 Assumir Centro da Roda</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
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
                  <label htmlFor="select-nomeado" style={{ color: 'var(--text-primary)' }}>
                    Indicar Jogador Nomeado para a Forca
                  </label>
                  
                  <select
                    id="select-nomeado"
                    className="form-control"
                    value={jogadores.length === 0 ? '' : nomeadoSelecionado}
                    disabled={giro.ativo || jogadores.length === 0}
                    onChange={(e) => setNomeadoSelecionado(e.target.value)}
                  >
                    {jogadores.length === 0 ? (
                      <option value="">⏳ Aguardando jogadores entrarem na roda...</option>
                    ) : (
                      jogadores.map((j) => (
                      <option key={j.id} value={j.id} disabled={j.ja_nomeado_hoje}>
                        {j.nome} ({j.status}) {j.ja_nomeado_hoje ? '— [Já nomeado hoje]' : ''}
                      </option>
                    ))
                  )}
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
                  <hr style={{ borderColor: 'var(--shadow-card)', margin: '1.1rem 0' }} />

                  <form onSubmit={alterarStatusVidaJogador}>
                    <label 
                      htmlFor="select-status-jog" 
                      style={{ color: 'var(--text-primary)', fontSize: '0.88rem', fontWeight: 600 }}
                    >
                      Alterar Status de Vida / Voto Fantasma
                    </label>
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem', flexWrap: 'wrap' }}>

                      <select
                        id="select-status-jog"
                        className="form-control"
                        style={{ flex: 1 }}
                        value={jogadores.length === 0 ? '' : jogadorAlvoStatus}
                        disabled={jogadores.length === 0}
                        onChange={(e) => setJogadorAlvoStatus(e.target.value)}
                      >
                        {jogadores.length === 0 ? (
                          <option value="">⏳ Sem jogadores na roda</option>
                        ) : (
                          jogadores.map((j) => (
                          <option key={j.id} value={j.id}>
                            {j.nome} ({j.status})
                          </option>
                        ))
                      )}
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
                      
                      <button 
                        type="submit" 
                        className="btn-secondary" 
                        disabled={giro.ativo || jogadores.length === 0}
                      >
                        Aplicar Status
                      </button>
                    </div>
                  </form>

                  <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.8rem', flexWrap: 'wrap' }}>
                    {!partidaAtualInfo.encerrada && (
                      <button
                        type="button"
                        onClick={encerrarPartidaInteira}
                        disabled={giro.ativo}
                        className="btn-secondary"
                        style={{ flex: 1 }}
                      >
                        🏁 Encerrar Partida Inteira
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={excluirSalaAtual}
                      disabled={giro.ativo}
                      style={{
                        flex: 1,
                        backgroundColor: '#991b1b',
                        color: '#fff',
                        border: 'none',
                        padding: '0.65rem',
                        borderRadius: '8px',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      🗑️ Excluir Esta Sala
                    </button>
                  </div>
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
                  disabled={giro.ativo || meuStatus.preso_como_storyteller}
                  required
                />
                <input
                  type="password"
                  className="form-control"
                  placeholder="Senha opcional (deixe em branco para sala pública)"
                  value={novaSenhaSala}
                  onChange={(e) => setNovaSenhaSala(e.target.value)}
                  disabled={giro.ativo || meuStatus.preso_como_storyteller}
                />
                <button 
                  type="submit" 
                  className="btn-secondary" 
                  disabled={giro.ativo || meuStatus.preso_como_storyteller}
                >
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