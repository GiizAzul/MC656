import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AustraliaPage.css';

export default function AustraliaPage({ usuario }) {
  const chaveRascunho = `mc656_rascunho_australia_${usuario?.id || 'anon'}`;

  const [modoVotacao, setModoVotacao] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(chaveRascunho))?.modoVotacao || 'candidatos';
    } catch {
      return 'candidatos';
    }
  });
  const [podeVotar, setPodeVotar] = useState(true);
  const [partidosMap, setPartidosMap] = useState({});
  const [ordemPartidos, setOrdemPartidos] = useState([]);

  const [candidatos, setCandidatos] = useState([]);
  const [nomesFormatados, setNomesFormatados] = useState({});
  const [estadoEleicao, setEstadoEleicao] = useState('AGUARDANDO');
  const [isGestao, setIsGestao] = useState(false);
  const [jaVotou, setJaVotou] = useState(false);
  const [totalVotos, setTotalVotos] = useState(0);

  const [draggedIdx, setDraggedIdx] = useState(null);
  const [dragOffsetY, setDragOffsetY] = useState(0);
  const dragStartYRef = React.useRef(0);
  const [mensagemSucesso, setMensagemSucesso] = useState('');
  const [erro, setErro] = useState('');

  const carregarEstadoAustralia = useCallback(async () => {
    try {
      const res = await fetch('/australia/api/estado', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setPartidosMap(data.partidos || {});
        const nomesPartidos = Object.keys(data.partidos || {});
        setPodeVotar(data.pode_votar !== undefined ? data.pode_votar : true);
        setNomesFormatados(data.nomes_formatados || {});
        setEstadoEleicao(data.estado_eleicao);
        setIsGestao(data.is_gestao);
        setJaVotou(data.ja_votou);
        setTotalVotos(data.total_votos);

        let rascunho = null;
        try {
          rascunho = JSON.parse(localStorage.getItem(chaveRascunho));
        } catch {
          rascunho = null;
        }

        if (data.ja_votou) {
          localStorage.removeItem(chaveRascunho);
        }

        setOrdemPartidos((prev) => {
          if (prev.length > 0) return prev;
          if (!data.ja_votou && rascunho?.ordemPartidos?.length === nomesPartidos.length) {
            return rascunho.ordemPartidos;
          }
          return nomesPartidos;
        });

        setCandidatos((prev) => {
          if (prev.length > 0) return prev;
          if (!data.ja_votou && rascunho?.candidatos?.length === data.candidatos.length) {
            return rascunho.candidatos;
          }
          return data.candidatos;
        });
      }
    } catch {
      // ignora erro temporário
    }
  }, [chaveRascunho]);

  useEffect(() => {
    if (!jaVotou && estadoEleicao === 'VOTACAO' && (candidatos.length > 0 || ordemPartidos.length > 0)) {
      localStorage.setItem(
        chaveRascunho,
        JSON.stringify({ modoVotacao, candidatos, ordemPartidos })
      );
    }
  }, [chaveRascunho, modoVotacao, candidatos, ordemPartidos, jaVotou, estadoEleicao]);

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
      localStorage.removeItem(chaveRascunho)
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

  const listaAtiva = modoVotacao === 'partidos' ? ordemPartidos : candidatos;
  const setListaAtiva = modoVotacao === 'partidos' ? setOrdemPartidos : setCandidatos;

  const handlePointerDown = (e, index) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    setDraggedIdx(index);
    setDragOffsetY(0);
    dragStartYRef.current = e.clientY;
  };

  const handlePointerMove = (e) => {
    if (draggedIdx === null) return;
    const deltaY = e.clientY - dragStartYRef.current;
    setDragOffsetY(deltaY);

    // Descobre qual card está sob o dedo/mouse e reordena em tempo real
    const el = document.elementFromPoint(e.clientX, e.clientY);
    const li = el?.closest('li[data-dnd-index]');
    if (li) {
      const targetIdx = Number(li.getAttribute('data-dnd-index'));
      if (!Number.isNaN(targetIdx) && targetIdx !== draggedIdx) {
        const novaLista = [...listaAtiva];
        const [movido] = novaLista.splice(draggedIdx, 1);
        novaLista.splice(targetIdx, 0, movido);
        setListaAtiva(novaLista);
        setDraggedIdx(targetIdx);
        dragStartYRef.current = e.clientY;
        setDragOffsetY(0);
      }
    }
  };

  const handlePointerUp = () => {
    setDraggedIdx(null);
    setDragOffsetY(0);
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
      localStorage.removeItem(chaveRascunho)
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
            const isPartido = modoVotacao === 'partidos';
            const filiados = isPartido ? partidosMap[itemNome] || [] : [];

            return (
              <li
                key={itemNome}
                data-dnd-index={index}
                style={{
                  borderLeft: isPartido ? '6px solid var(--caco-purple)' : '6px solid var(--aus-green)',
                  transform: isDragging ? `translateY(${dragOffsetY}px) scale(1.02)` : undefined,
                  zIndex: isDragging ? 50 : 1,
                  position: 'relative',
                  boxShadow: isDragging ? '0 12px 24px rgba(0, 0, 0, 0.35)' : undefined,
                  transition: isDragging ? 'none' : 'transform 0.15s ease',
                }}
                className={`dnd-item ${isDragging ? 'dragging' : ''}`}
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
                  <span
                    className="drag-handle"
                    title="Segure e arraste para reordenar"
                    onPointerDown={(e) => handlePointerDown(e, index)}
                    onPointerMove={handlePointerMove}
                    onPointerUp={handlePointerUp}
                    onPointerCancel={handlePointerUp}
                  >
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
