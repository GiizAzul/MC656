import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/DashboardPage.css';

export default function DashboardPage({ usuario, onScopeAdded }) {
  const [novoTipo, setNovoTipo] = useState('BOTC_JOGADOR');
  const [raExtra, setRaExtra] = useState('');
  const [mensagem, setMensagem] = useState('');
  const [erro, setErro] = useState('');

  const escopoStr = usuario?.escopo || '';
  const temAustralia = escopoStr.includes('AUSTRALIA');
  const temCACo = escopoStr.includes('CACO');
  const temBotC = escopoStr.includes('BOTC');
  const isAdmin = escopoStr.includes('GESTAO') || escopoStr.includes('STORYTELLER');

  const vincularNovoEscopo = async (e) => {
    e.preventDefault();
    setErro('');
    setMensagem('');

    const formData = new URLSearchParams();
    formData.append('tipo_conta', novoTipo);
    if (novoTipo === 'CACO_ESTUDANTE') {
      formData.append('ra', raExtra);
    }

    const res = await fetch('/adicionar-escopo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });

    if (res.ok || res.status === 302) {
      setMensagem('Novo escopo habilitado na sua conta com sucesso!');
      if (onScopeAdded) await onScopeAdded();
    } else {
      setErro('Não foi possível vincular o escopo. Verifique o RA.');
    }
  };

  return (
    <div>
      <div className="dashboard-header">
        <h1>Bem-vindo, {usuario?.nome_real}!</h1>
        <p>Selecione uma pauta ativa do seu escopo ou habilite sua participação em outro contexto eleitoral.</p>
      </div>

      {erro && <div className="alert-banner alert-error">{erro}</div>}
      {mensagem && <div className="alert-banner alert-success">{mensagem}</div>}

      <div className="cards-grid">
        {temAustralia && (
          <div className="context-card aus">
            <div>
              <h2>🪃 Eleição Federal 2026</h2>
              <p>Votação preferencial australiana com ranqueamento.</p>
            </div>
            <Link to="/australia/votar" className="btn-primary">
              Acessar Cédula Australiana
            </Link>
          </div>
        )}

        {temCACo && (
          <div className="context-card caco">
            <div>
              <h2>🏛️ Assembleia Geral CACo</h2>
              <p>Deliberação estudantil com verificação de quórum e voto único anônimo.</p>
            </div>
            <Link to="/caco/assembleia" className="btn-primary">
              Entrar na Assembleia
            </Link>
          </div>
        )}

        {temBotC && (
          <div className="context-card botc">
            <div>
              <h2>🩸 Blood on the Clocktower</h2>
              <p>Roda de votação em tempo real com cronômetro e controle de mão levantada.</p>
            </div>
            <Link to="/botc/partida" className="btn-primary">
              Entrar na Partida
            </Link>
          </div>
        )}

        {isAdmin && (
          <div className="context-card">
            <div>
              <h2>⚙️ Painel de Gestão / Mestre</h2>
              <p>Gerenciar abertura/encerramento de votações e registro de forca.</p>
            </div>
            <a href="/admin" className="btn-secondary">
              Gerenciar Votações
            </a>
          </div>
        )}
      </div>

      <div className="scope-linker-card">
        <h3>➕ Participar de Outro Escopo com este Mesmo Username ({usuario?.username})</h3>
        <form onSubmit={vincularNovoEscopo} className="scope-linker-form">
          <div className="form-group" style={{ marginBottom: 0, minWidth: '260px' }}>
            <label htmlFor="novo_escopo_select">Escolha o contexto adicional</label>
            <select
              id="novo_escopo_select"
              className="form-control"
              value={novoTipo}
              onChange={(e) => setNovoTipo(e.target.value)}
            >
              <option value="AUSTRALIA_ELEITOR">Eleitor (Austrália)</option>
              <option value="CACO_ESTUDANTE">Estudante Unicamp (CACo)</option>
              <option value="CACO_GESTAO">Gestão (CACo)</option>
              <option value="BOTC_JOGADOR">Jogador (BoTC)</option>
              <option value="BOTC_STORYTELLER">Storyteller (BoTC)</option>
            </select>
          </div>

          {novoTipo === 'CACO_ESTUDANTE' && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="ra_extra">RA (Apenas números positivos)</label>
              <input
                id="ra_extra"
                type="text"
                inputMode="numeric"
                className="form-control"
                placeholder="Ex: 288808"
                value={raExtra}
                onChange={(e) => setRaExtra(e.target.value.replace(/\D/g, ''))}
                required
              />
            </div>
          )}

          <button type="submit" className="btn-primary">
            Vincular Escopo à Conta
          </button>
        </form>
      </div>
    </div>
  );
}