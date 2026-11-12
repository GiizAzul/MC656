import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AustraliaPage.css';

export default function AustraliaPage() {
  const [candidatos, setCandidatos] = useState([]);
  const [estadoEleicao, setEstadoEleicao] = useState('AGUARDANDO');
  const [isGestao, setIsGestao] = useState(false);
  const [jaVotou, setJaVotou] = useState(false);
  const [totalVotos, setTotalVotos] = useState(0);

  const [draggedIdx, setDraggedIdx] = useState(null);
  const [dragOverIdx, setDragOverIdx] = useState(null);
  const [mensagemSucesso, setMensagemSucesso] = useState('');
  const [erro, setErro] = useState('');

  const carregarEstadoAustralia = useCallback(async () => {
    try {
      const res = await fetch('/australia/api/estado');
      if (res.ok) {
        const data = await res.json();
        setCandidatos((prev) => (prev.length === 0 ? data.candidatos : prev));
        setEstadoEleicao(data.estado_eleicao);
        setIsGestao(data.is_gestao);
        setJaVotou(data.ja_votou);
        setTotalVotos(data.total_votos);
      }
    } catch {
      // ignora erro temporário
    }
  }, []);

  useEffect(() => {
    carregarEstadoAustralia();
  }, [carregarEstadoAustralia]);

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

  const handleDrop = (indexDestino) => {
    if (draggedIdx === null || draggedIdx === indexDestino) {
      setDraggedIdx(null);
      setDragOverIdx(null);
      return;
    }
    const novaLista = [...candidatos];
    const [itemMovido] = novaLista.splice(draggedIdx, 1);
    novaLista.splice(indexDestino, 0, itemMovido);

    setCandidatos(novaLista);
    setDraggedIdx(null);
    setDragOverIdx(null);
  };

  const moverCandidato = (index, direcao) => {
    const novoIndex = index + direcao;
    if (novoIndex < 0 || novoIndex >= candidatos.length) return;
    const novaLista = [...candidatos];
    const [item] = novaLista.splice(index, 1);
    novaLista.splice(novoIndex, 0, item);
    setCandidatos(novaLista);
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

      <div className="australia-instructions">
        <strong>Como votar:</strong> Segure e arraste os candidatos abaixo (ou use as setas ▲/▼) para definir sua ordem
        de preferência de 1º a {candidatos.length}º lugar.
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {mensagemSucesso && <div className="alert-banner alert-success">{mensagemSucesso}</div>}

      <form onSubmit={submeterCedula}>
        <ul className="dnd-list">
          {candidatos.map((candidato, index) => {
            const isDragging = draggedIdx === index;
            const isDragOver = dragOverIdx === index;
            return (
              <li
                key={candidato}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDrop={() => handleDrop(index)}
                onDragEnd={() => {
                  setDraggedIdx(null);
                  setDragOverIdx(null);
                }}
                className={`dnd-item ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''}`}
              >
                <div className="dnd-left">
                  <span className="rank-badge">{index + 1}º</span>
                  <div className="candidate-info">
                    <span className="candidate-name">{candidato}</span>
                    <span className="candidate-hint">
                      {index === 0 ? '1ª Preferência Principal' : `${index + 1}ª Preferência de Transferência`}
                    </span>
                  </div>
                </div>

                <div className="dnd-controls">
                  <button
                    type="button"
                    className="btn-move"
                    onClick={() => moverCandidato(index, -1)}
                    disabled={index === 0}
                    title="Subir posição"
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    className="btn-move"
                    onClick={() => moverCandidato(index, 1)}
                    disabled={index === candidatos.length - 1}
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

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            type="submit"
            className="btn-primary"
            disabled={jaVotou || estadoEleicao !== 'VOTACAO'}
          >
            {jaVotou
              ? '✓ Voto Já Registrado'
              : estadoEleicao !== 'VOTACAO'
              ? `Aguardando Abertura (${estadoEleicao})`
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