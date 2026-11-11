import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/AustraliaPage.css';

export default function AustraliaPage({ candidatosIniciais = ['Ana', 'Beto', 'Caio'] }) {
  const [candidatos, setCandidatos] = useState(candidatosIniciais);
  const [draggedIdx, setDraggedIdx] = useState(null);
  const [dragOverIdx, setDragOverIdx] = useState(null);
  const [mensagemSucesso, setMensagemSucesso] = useState('');
  const [erro, setErro] = useState('');

  const handleDragStart = (index) => {
    setDraggedIdx(index);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (index !== dragOverIdx) {
      setDragOverIdx(index);
    }
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
      // Envia inteiros estritos 1..N conforme a ordem do Drag and Drop
      formData.append(`posicao_${cand}`, String(idx + 1));
    });

    const response = await fetch('/australia/votar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });

    const html = await response.text();
    if (html.toLowerCase().includes('voto registrado com sucesso')) {
      setMensagemSucesso('Voto preferencial registrado com sucesso na Eleição Federal!');
    } else if (html.includes('já registrou seu voto')) {
      setErro('Você já registrou seu voto nesta eleição.');
    } else {
      setErro('Não foi possível registrar o voto. Verifique se a eleição está aberta.');
    }
  };

  return (
    <div className="australia-container">
      <div className="australia-banner">
        <h1>🇦🇺 Eleição Preferencial Australiana (IRV)</h1>
        <p>Arraste e solte os candidatos para definir sua ordem de preferência (1º ao {candidatos.length}º).</p>
      </div>

      <div className="australia-instructions">
        <strong>Como votar:</strong> Segure e arraste qualquer candidato para reordenar sua cédula, ou utilize as setas
        laterais. A numeração de 1 a {candidatos.length} é atualizada automaticamente sem risco de empates ou valores inválidos.
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
          <button type="submit" className="btn-primary">
            Confirmar Cédula Preferencial
          </button>
          <Link to="/dashboard" className="btn-secondary">
            Voltar ao Painel
          </Link>
        </div>
      </form>
    </div>
  );
}