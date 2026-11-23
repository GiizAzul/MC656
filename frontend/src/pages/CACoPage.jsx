import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CACoPage.css';

export default function CACoPage({ usuario }) {
  const [assembleiaId, setAssembleiaId] = useState('principal');
  const [assembleiasDisponiveis, setAssembleiasDisponiveis] = useState([]);
  const [assembleiaAtual, setAssembleiaAtual] = useState({});
  const [pautas, setPautas] = useState([]);
  const [pautaAtivaId, setPautaAtivaId] = useState(null);  
  const [opcao, setOpcao] = useState('APROVAR');
  const [resultados, setResultados] = useState(null);
  const isGestao = usuario?.escopo?.includes('CACO_GESTAO');
  
  // Form Nova Assembleia
  const [novaAsmTitulo, setNovaAsmTitulo] = useState('');
  const [novaAsmDesc, setNovaAsmDesc] = useState('');
  const [novaAsmLocal, setNovaAsmLocal] = useState('');
  const [novaAsmData, setNovaAsmData] = useState('');
  const [novaAsmHora, setNovaAsmHora] = useState('');
  
  // Form Nova Pauta
  const [novaPautaTitulo, setNovaPautaTitulo] = useState('');
  const [novaPautaDesc, setNovaPautaDesc] = useState('');
  
  // Falas
  const [tipoFala, setTipoFala] = useState('Fala Ordinária');
  
  const [msg, setMsg] = useState('');
  const [erro, setErro] = useState('');

  const carregarEstado = useCallback(async () => {
    try {
      const res = await fetch(`/caco/api/estado?assembleia_id=${encodeURIComponent(assembleiaId)}`);
      if (res.ok) {
        const data = await res.json();
        setAssembleiaAtual(data.assembleia_atual || {});
        setAssembleiasDisponiveis(data.assembleias_disponiveis || []);
        setPautas(data.pautas || []);
        setPautaAtivaId(data.pauta_ativa_id);
        if (data.assembleia_atual?.id && data.assembleia_atual.id !== assembleiaId) {
          setAssembleiaId(data.assembleia_atual.id);
        }
      }
    } catch {
      // ignora falha momentânea
    }
  }, [assembleiaId]);

  useEffect(() => {
    carregarEstado();
    const poll = setInterval(carregarEstado, 1500);
    return () => clearInterval(poll);
  }, [carregarEstado]);

  const criarAssembleia = async (e) => {
    e.preventDefault();
    setErro('');
    setMsg('');
    const form = new URLSearchParams({
      titulo: novaAsmTitulo,
      descricao: novaAsmDesc,
      local: novaAsmLocal,
      data: novaAsmData,
      horario: novaAsmHora,
    });

    const res = await fetch('/caco/api/assembleias', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    const d = await res.json();
    if (!res.ok) {
      setErro(d.detail || 'Erro ao criar assembleia.');
    } else {
      setMsg('✅ Nova assembleia criada com sucesso!');
      setNovaAsmTitulo('');
      setNovaAsmDesc('');
      setNovaAsmLocal('');
      setNovaAsmData('');
      setNovaAsmHora('');
      setAssembleiaId(d.assembleia_id);
    }
  };

  const criarPauta = async (e) => {
    e.preventDefault();
    setErro('');
    setMsg('');
    const form = new URLSearchParams({
      titulo: novaPautaTitulo,
      descricao: novaPautaDesc,
    });

    const res = await fetch(`/caco/api/assembleias/${assembleiaId}/pautas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    const d = await res.json();
    if (!res.ok) {
      setErro(d.detail || 'Erro ao criar pauta.');
    } else {
      setMsg('📌 Pauta adicionada à fila da assembleia!');
      setNovaPautaTitulo('');
      setNovaPautaDesc('');
      await carregarEstado();
    }
  };

  const acaoPauta = async (pautaId, acao) => {
    setErro('');
    setMsg('');
    const res = await fetch(`/caco/api/assembleias/${assembleiaId}/pautas/${pautaId}/${acao}`, {
      method: 'POST',
    });
    const d = await res.json();
    if (!res.ok) {
      setErro(d.detail || `Não foi possível ${acao} a pauta.`);
    } else {
      setMsg(acao === 'iniciar' ? '▶ Pauta aberta para votação!' : '⏹ Pauta encerrada e apurada!');
      await carregarEstado();
    }
  };

  const enviarVoto = async (e, pautaId) => {
    e.preventDefault();
    setErro('');
    setMsg('');
    const form = new URLSearchParams({ opcao });
    const res = await fetch(`/caco/api/assembleias/${assembleiaId}/pautas/${pautaId}/votar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    const d = await res.json();
    if (!res.ok) {
      setErro(d.detail || 'Não foi possível registrar seu voto.');
    } else {
      setMsg(`🗳️ ${d.mensagem}`);
      await carregarEstado();
    }
  };

  const inscreverFala = async (pautaId) => {
    setErro('');
    setMsg('');
    const form = new URLSearchParams({ 
      tipo_fala: tipoFala 
    });
    const res = await fetch(`/caco/api/assembleias/${assembleiaId}/pautas/${pautaId}/falas/inscrever`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    const d = await res.json();
    if (!res.ok) {
      setErro(d.detail || 'Não foi possível entrar na fila de falas.');
    } else {
      setMsg('🎙️ Você entrou na fila de falas!');
      await carregarEstado();
    }
  };

  const proximoOrador = async (pautaId) => {
    const res = await fetch(`/caco/api/assembleias/${assembleiaId}/pautas/${pautaId}/falas/proximo`, {
      method: 'POST',
    });
    if (res.ok) await carregarEstado();
  };
  
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

  const pct = (val, tot) => (tot > 0 ? Math.round((val / tot) * 100) : 0);
  const pautaEmVotacao = pautas.find((p) => p.id === pautaAtivaId);

  return (
    <div className="caco-container">
      <div className="caco-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1>🐸 {assembleiaAtual.titulo || 'Assembleia Geral do CACo'}</h1>
            <p>{assembleiaAtual.descricao}</p>
            <p style={{ fontSize: '0.88rem', marginTop: '0.35rem', opacity: 0.9 }}>
              📍 {assembleiaAtual.local} | 📅 {assembleiaAtual.data} às {assembleiaAtual.horario}
            </p>
          </div>
          <div style={{ width: '100%', maxWidth: '100%', minWidth: 0 }}>            
            <select
              aria-label="Selecionar Assembleia"
              className="form-control"
              value={assembleiaId}
              onChange={(e) => {
                setErro('');
                setMsg('');
                setAssembleiaId(e.target.value);
              }}
            >
              {assembleiasDisponiveis.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.encerrada ? '🔒 ' : '🐸 '}
                  {a.titulo} ({a.data} {a.horario})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {msg && <div className="alert-banner alert-success">{msg}</div>}

      {pautaEmVotacao ? (
        <div className="caco-card" style={{ borderLeft: '5px solid var(--aus-green)'}}>
          <h2>🟢 Em Votação: {pautaEmVotacao.titulo}</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>{pautaEmVotacao.descricao}</p>
          <form onSubmit={(e) => enviarVoto(e, pautaEmVotacao.id)}>
            <div className="vote-options-grid">
              {['APROVAR', 'REJEITAR', 'ABSTER'].map((item) => (
                <button
                  type="button"
                  key={item}
                  disabled={pautaEmVotacao.ja_votou}
                  onClick={() => setOpcao(item)}
                  className={`vote-option-btn ${opcao === item ? 'selected' : ''}`}
                >
                  {item}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button type="submit" className="btn-primary" disabled={pautaEmVotacao.ja_votou}>
                {pautaEmVotacao.ja_votou ? '✓ Voto Já Registrado' : 'Confirmar Voto Anônimo'}
              </button>
              {isGestao && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => acaoPauta(pautaEmVotacao.id, 'encerrar')}
                >
                  ⏹ Encerrar Votação desta Pauta
                </button>
              )}
            </div>
          </form>
        </div>
      ) : (
        <div className="caco-card">
          <h3>⏸️ Nenhuma pauta em votação no momento</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
            Aguarde a Gestão abrir uma pauta da ordem do dia abaixo.
          </p>
        </div>
      )}

      <div className="caco-card">
        <h3>📋 Pautas desta Assembleia ({pautas.length})</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
          {pautas.map((p) => {
            const aprovar = p.contadores?.APROVAR || 0;
            const rejeitar = p.contadores?.REJEITAR || 0;
            const abster = p.contadores?.ABSTER || 0;
            return (
              <div key={p.id} className="caco-pauta-item">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div>
                    <strong>{p.titulo}</strong>{' '}
                    <span style={{ fontSize: '0.8rem', opacity: 0.85 }}>[{p.estado}]</span>
                    <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>{p.descricao}</p>
                  </div>
                  {isGestao && p.estado === 'AGUARDANDO' && !p.ja_iniciada && !assembleiaAtual.encerrada && (
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={Boolean(pautaAtivaId)}
                      onClick={() => acaoPauta(p.id, 'iniciar')}
                    >
                      ▶ Iniciar Votação
                    </button>
                  )}
                </div>

                {(p.estado === 'ENCERRADO' || (isGestao && p.estado === 'VOTACAO')) && (
                  <div style={{ marginTop: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <strong>Resultado: {p.resultado} (Total: {p.total_votos} votos)</strong>
                    <div>
                      <small>Aprovar: {aprovar} ({pct(aprovar, p.total_votos)}%)</small>
                      <div className="progress-bar-track">
                        <div className="progress-bar-fill" style={{ width: `${pct(aprovar, p.total_votos)}%` }} />
                      </div>
                    </div>
                    <div>
                      <small>Rejeitar: {rejeitar} ({pct(rejeitar, p.total_votos)}%)</small>
                      <div className="progress-bar-track">
                        <div className="progress-bar-fill" style={{ width: `${pct(rejeitar, p.total_votos)}%` }} />
                      </div>
                    </div>
                    <div>
                      <small>Abster: {abster} ({pct(abster, p.total_votos)}%)</small>
                      <div className="progress-bar-track">
                        <div className="progress-bar-fill" style={{ width: `${pct(abster, p.total_votos)}%` }} />
                      </div>
                    </div>
                  </div>
                )}

                <div style={{ marginTop: '0.85rem', paddingTop: '0.7rem', borderTop: '1px dashed var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.85rem' }}>
                    🎙️ <strong>Com a palavra:</strong> {p.orador_atual ? `${p.orador_atual.nome} (${p.orador_atual.tipo})` : 'Ninguém'} |{' '}
                    <strong>Fila:</strong> {p.fila_falas.length}
                  </span>
                  <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {p.estado !== 'ENCERRADO' && !assembleiaAtual.encerrada && (
                      <>
                        <select
                          aria-label="Tipo de Fala"
                          className="form-control"
                          style={{ padding: '0.3rem 0.5rem', fontSize: '0.82rem' }}
                          value={tipoFala}
                          onChange={(e) => setTipoFala(e.target.value)}
                        >
                          <option value="Fala Ordinária">Fala Ordinária</option>
                          <option value="Questão de Ordem">Questão de Ordem</option>
                          <option value="Esclarecimento">Esclarecimento</option>
                        </select>
                        <button type="button" className="btn-secondary" style={{ padding: '0.3rem 0.65rem', fontSize: '0.82rem' }} onClick={() => inscreverFala(p.id)}>
                          ✋ Pedir Fala
                        </button>
                      </>
                    )}
                    {isGestao && (p.fila_falas.length > 0 || p.orador_atual) && (
                      <button type="button" className="btn-primary" style={{ padding: '0.3rem 0.65rem', fontSize: '0.82rem' }} onClick={() => proximoOrador(p.id)}>
                        ⏭ Próximo Orador
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <Link to="/dashboard" className="btn-secondary">
        Voltar ao Painel
      </Link>
    </div>
  );
}
