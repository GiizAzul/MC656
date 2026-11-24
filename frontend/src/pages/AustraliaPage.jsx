import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AustraliaPage.css';

export default function AustraliaPage() {
  const [modoVotacao, setModoVotacao] = useState('candidatos');
  const [podeVotar, setPodeVotar] = useState(true);
  const [partidosMap, setPartidosMap] = useState({});
  const [ordemPartidos, setOrdemPartidos] = useState([]);

  const [candidatos, setCandidatos] = useState([]);
  const [nomesFormatados, setNomesFormatados] = useState({});
  const [estadoEleicao, setEstadoEleicao] = useState('AGUARDANDO');
  const [isGestao, setIsGestao] = useState(false);
  const [jaVotou, setJaVotou] = useState(false);
  const [totalVotos, setTotalVotos] = useState(0);
  const [resultados, setResultados] = useState(null);

  const [draggedIdx, setDraggedIdx] = useState(null);
  const [dragOverIdx, setDragOverIdx] = useState(null);
  const [mensagemSucesso, setMensagemSucesso] = useState('');
  const [erro, setErro] = useState('');

  const carregarEstadoAustralia = useCallback(async () => {
    try {
      const res = await fetch('/australia/api/estado');
      if (res.ok) {
        const data = await res.json();
        setPartidosMap(data.partidos || {});
        const nomesPartidos = Object.keys(data.partidos || {});
        setPodeVotar(data.pode_votar !== undefined ? data.pode_votar : true);
        setOrdemPartidos((prev) => (prev.length === 0 ? nomesPartidos : prev));
        setCandidatos((prev) => (prev.length === 0 ? data.candidatos : prev));
        setNomesFormatados(data.nomes_formatados || {});
        setEstadoEleicao(data.estado_eleicao);
        setIsGestao(data.is_gestao);
        setJaVotou(data.ja_votou);
        setTotalVotos(data.total_votos);
        setResultados(data.resultados || null);
      }
    } catch {
      // ignora erro temporário
    }
  }, []);

  useEffect(() => {
    carregarEstadoAustralia();
  }, [carregarEstadoAustralia]);
  
  const submeterVotoPorPartidos = async (e) => {
    e.preventDefault();
    setErro('');
    setMensagemSucesso('');
    const res = await fetch('/australia/api/votar-partidos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ranking_partidos: ordemPartidos }),
    });
    const data = await res.json();
    if (res.ok) {
      setMensagemSucesso(`🎉 ${data.mensagem}`);
      await carregarEstadoAustralia();
    } else {
      setErro(data.erro || 'Não foi possível registrar o voto por partidos.');
    }
  };
  
  const controlarEleicaoAustralia = async (acao) => {
    setErro('');
    setMensagemSucesso('');
    const res = await fetch(`/australia/${acao}`, { method: 'POST' });
    const html = await res.text();

    if (html.includes('iniciada com sucesso')) {
      setMensagemSucesso('✅ Eleição Federal da Austrália iniciada com sucesso! Agora você já pode votar.');
    } else if (html.includes('Eleição encerrada')) {
      setMensagemSucesso('⏹ Eleição Federal da Austrália encerrada.');
    } else if (html.includes('alert-error')) {
      const m = html.match(/<div class="alert-error"[^>]*>([\s\S]*?)<\/div>/);
      setErro(m ? m[1].trim() : 'Operação não permitida no estado atual da eleição.');
    } else {
      setErro('Apenas usuários com escopo AUSTRALIA_GESTAO podem iniciar ou encerrar a eleição.');
    }
    await carregarEstadoAustralia();
  };

  const handleDragStart = (index) => setDraggedIdx(index);

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (index !== dragOverIdx) setDragOverIdx(index);
  };

  const listaAtiva = modoVotacao === 'partidos' ? ordemPartidos : candidatos;
  const setListaAtiva = modoVotacao === 'partidos' ? setOrdemPartidos : setCandidatos;

  const handleDrop = (indexDestino) => {
    if (draggedIdx === null || draggedIdx === indexDestino) {
      setDraggedIdx(null);
      setDragOverIdx(null);
      return;
    }
    const novaLista = [...listaAtiva];
    const [itemMovido] = novaLista.splice(draggedIdx, 1);
    novaLista.splice(indexDestino, 0, itemMovido);

    setListaAtiva(novaLista);
    setDraggedIdx(null);
    setDragOverIdx(null);
  };

  const moverItemLista = (index, direcao) => {
    const novoIndex = index + direcao;
    if (novoIndex < 0 || novoIndex >= listaAtiva.length) return;
    const novaLista = [...listaAtiva];
    const [item] = novaLista.splice(index, 1);
    novaLista.splice(novoIndex, 0, item);
    setListaAtiva(novaLista);
  };

  const submeterCedula = async (e) => {
    e.preventDefault();
    setErro('');
    setMensagemSucesso('');

    const formData = new URLSearchParams();
    candidatos.forEach((cand, idx) => {
      formData.append(`posicao_${cand}`, String(idx + 1));
    });

    const response = await fetch('/australia/votar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });

    const html = await response.text();
    if (html.toLowerCase().includes('voto registrado com sucesso')) {
      setMensagemSucesso('🎉 Voto preferencial registrado com sucesso na Eleição Federal!');
      await carregarEstadoAustralia();
    } else {
      const m = html.match(/<div class="alert-error"[^>]*>([\s\S]*?)<\/div>/);
      setErro(
        m
          ? m[1].trim()
          : `Não foi possível registrar o voto. Estado atual da eleição: ${estadoEleicao}.`
      );
    }
  };

  return (
    <div className="australia-container">
      <div className="australia-banner">
        <h1>🪃 Eleição Preferencial Australiana (IRV)</h1>
        <p>
          Status da Eleição: <strong>{estadoEleicao}</strong> | Cédulas computadas: <strong>{totalVotos}</strong>
        </p>
      </div>

      {estadoEleicao === 'ENCERRADA' && resultados && (
        <section className="australia-results" aria-live="polite">
          <h2>Resultado da eleição</h2>
          <p className="australia-winner">Vencedor: <strong>{nomesFormatados[resultados.vencedor] || resultados.vencedor || 'Sem vencedor'}</strong></p>
          <p className="australia-chart-caption">
            {resultados.rodadas.length === 1
              ? 'Gráfico de primeiras preferências'
              : 'Gráfico de preferências por rodada (com transferências)'}
          </p>
          {resultados.rodadas.map((rodada, indice) => (
            <div className="australia-round" key={indice}>
              <h3>{indice === 0 ? 'Contagem inicial' : `Rodada ${indice + 1}`} · {rodada.total} votos válidos</h3>
              {rodada.eliminado && (
                (() => {
                  const votosEliminado = rodada.contagem[rodada.eliminado];
                  const empatadosNaMenor = Object.values(rodada.contagem).filter((votos) => votos === votosEliminado).length > 1;
                  return (
                    <p className="australia-elimination">
                      <strong>{nomesFormatados[rodada.eliminado] || rodada.eliminado}</strong> foi eliminado por ter
                      {empatadosNaMenor ? ' empatado na menor votação' : ' a menor votação'}: {votosEliminado} {votosEliminado === 1 ? 'voto' : 'votos'}.
                    </p>
                  );
                })()
              )}
              <div className="australia-chart" role="img" aria-label={`Votos por candidato na rodada ${indice + 1}`}>
                {Object.entries(rodada.contagem).map(([id, votos]) => (
                  <div className="australia-chart-row" key={id}>
                    <span className="australia-chart-label">{nomesFormatados[id] || id}</span>
                    <div className="australia-chart-track" aria-hidden="true">
                      <div
                        className={`australia-chart-bar${id === resultados.vencedor ? ' is-winner' : ''}${id === rodada.eliminado ? ' is-eliminated' : ''}`}
                        style={{ width: `${rodada.total ? (votos / rodada.total) * 100 : 0}%` }}
                      />
                    </div>
                    <strong className="australia-chart-value">{votos}</strong>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      )}

      {isGestao && (
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn-primary"
            disabled={estadoEleicao === 'VOTACAO'}
            onClick={() => controlarEleicaoAustralia('iniciar')}
          >
            ▶ Iniciar Votação (Comissão Australiana)
          </button>
          <button
            type="button"
            className="btn-secondary"
            disabled={estadoEleicao !== 'VOTACAO'}
            onClick={() => controlarEleicaoAustralia('encerrar')}
          >
            ⏹ Encerrar Votação
          </button>
        </div>
      )}

      {Object.keys(partidosMap).length > 0 && (
        <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1rem' }}>
          <button
            type="button"
            className={modoVotacao === 'candidatos' ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setModoVotacao('candidatos')}
          >
            👤 Ranquear Candidatos
          </button>
          <button
            type="button"
            className={modoVotacao === 'partidos' ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setModoVotacao('partidos')}
          >
            🏛️ Ranquear Partidos
          </button>
        </div>
      )}

      <div className="australia-instructions">
        {modoVotacao === 'partidos' ? (
          <>
            <strong>Votação por Ranking de Partidos:</strong> Segure e arraste os <strong>partidos</strong> abaixo (ou use as setas
            ▲/▼) para definir sua ordem de preferência (de 1º ao {ordemPartidos.length}º lugar). O sistema expandirá automaticamente o seu voto para os candidatos filiados a cada partido.
          </>
        ) : (
          <>
            <strong>Votação Individual por Candidatos:</strong> Segure e arraste os <strong>candidatos</strong> abaixo (ou use as setas
            ▲/▼) para definir sua ordem de preferência (de 1º a {candidatos.length}º lugar).
          </>
        )}
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {mensagemSucesso && <div className="alert-banner alert-success">{mensagemSucesso}</div>}

      <form onSubmit={modoVotacao === 'partidos' ? submeterVotoPorPartidos : submeterCedula}>
        <ul className="dnd-list">
          {listaAtiva.map((itemNome, index) => {
            const isDragging = draggedIdx === index;
            const isDragOver = dragOverIdx === index;
            const isPartido = modoVotacao === 'partidos';
            const filiados = isPartido ? partidosMap[itemNome] || [] : [];

            return (
              <li
                key={itemNome}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDrop={() => handleDrop(index)}
                onDragEnd={() => {
                  setDraggedIdx(null);
                  setDragOverIdx(null);
                }}
                style={isPartido ? { borderLeft: '6px solid var(--caco-purple)' } : { borderLeft: '6px solid var(--aus-green)' }}
                className={`dnd-item ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''}`}
              >
                <div className="dnd-left">
                  <span
                    className="rank-badge"
                    style={isPartido ? { backgroundColor: 'var(--caco-purple)' } : { backgroundColor: 'var(--aus-green)' }}
                  >
                    {index + 1}º
                  </span>
                  <div className="candidate-info">
                    <span className="candidate-name">
                    {isPartido
                      ? `🏛️ ${itemNome}`
                      : `👤 ${nomesFormatados[itemNome] || itemNome}`}
                  </span>
                    <span className="candidate-hint">
                    {isPartido
                      ? `Candidatos da legenda: ${
                          filiados.map((c) => nomesFormatados[c] || c).join(', ') || 'Nenhum'
                        }`
                      : index === 0
                      ? '1ª Preferência Principal'
                      : `${index + 1}ª Preferência de Transferência`}
                  </span>
                  </div>
                </div>

                <div className="dnd-controls">
                  <button
                    type="button"
                    className="btn-move"
                    onClick={() => moverItemLista(index, -1)}
                    disabled={index === 0}
                    title="Subir posição"
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    className="btn-move"
                    onClick={() => moverItemLista(index, 1)}
                    disabled={index === listaAtiva.length - 1}
                    title="Descer posição"
                  >
                    ▼
                  </button>
                  <span className="drag-handle" title="Arraste para reordenar">
                    ⠿
                  </span>
                </div>
              </li>
            );
          })}
        </ul>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            type="submit"
            className="btn-primary"
            disabled={!podeVotar || jaVotou || estadoEleicao !== 'VOTACAO'}
          >
            {!podeVotar
              ? '🔒 Apenas Eleitores Podem Votar'
              : jaVotou
              ? '✓ Voto Já Registrado'
              : estadoEleicao !== 'VOTACAO'
              ? `Aguardando Abertura (${estadoEleicao})`
              : modoVotacao === 'partidos'
              ? 'Confirmar Voto por Partidos'
              : 'Confirmar Cédula Preferencial'}
          </button>
          <Link to="/dashboard" className="btn-secondary">
            Voltar ao Painel
          </Link>
        </div>
      </form>
    </div>
  );
}
