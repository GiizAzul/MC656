import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/AuthPage.css';

export default function CadastroPage({ onAuthSuccess }) {
  const navigate = useNavigate();
  const [tipoConta, setTipoConta] = useState('AUSTRALIA_ELEITOR');
  const [nomeReal, setNomeReal] = useState('');
  const [username, setUsername] = useState('');
  const [ra, setRa] = useState('');
  const [senha, setSenha] = useState('');
  const [senhaConfirma, setSenhaConfirma] = useState('');
  const [erro, setErro] = useState('');

  const exigeRa = tipoConta === 'CACO_ESTUDANTE';

  const handleRaChange = (e) => {
    // Permite apenas dígitos inteiros positivos (impede sinal negativo, ponto ou 'e')
    const apenasDigitos = e.target.value.replace(/\D/g, '');
    setRa(apenasDigitos);
  };

  const bloquearTeclasInvalidasNumero = (e) => {
    if (['-', '+', '.', ',', 'e', 'E'].includes(e.key)) {
      e.preventDefault();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro('');

    if (senha !== senhaConfirma) {
      setErro('Senhas não conferem. Tente novamente.');
      return;
    }

    if (exigeRa && (!ra || Number(ra) <= 0)) {
      setErro('Informe um RA numérico positivo válido.');
      return;
    }

    const formData = new URLSearchParams();
    formData.append('tipo_conta', tipoConta);
    formData.append('nome_real', nomeReal);
    formData.append('username', username);
    formData.append('senha', senha);
    formData.append('senha_confirma', senhaConfirma);
    if (exigeRa) {
      formData.append('ra', ra);
    }

    const response = await fetch('/cadastro', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
      redirect: 'manual',
    });

    if (response.status === 302 || response.type === 'opaqueredirect' || response.redirected) {
      if (onAuthSuccess) await onAuthSuccess();
      navigate('/dashboard');
    } else {
      const html = await response.text();
      const match = html.match(/Erro:[^<]+|Senhas não conferem[^<]+|RA inválido[^<]+/);
      setErro(match ? match[0] : 'Não foi possível concluir o cadastro. Verifique os dados.');
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Criar Conta ou Vincular Escopo</h1>
          <p>Dica: Use seu username e senha atuais para adicionar um novo contexto à sua conta.</p>
        </div>

        {erro && <div className="alert-banner alert-error">{erro}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="tipo_conta">Contexto / Tipo de Conta</label>
            <select
              id="tipo_conta"
              className="form-control"
              value={tipoConta}
              onChange={(e) => {
                setTipoConta(e.target.value);
                if (e.target.value !== 'CACO_ESTUDANTE') setRa('');
              }}
              required
            >
              <option value="AUSTRALIA_ELEITOR">Eleitor (Austrália)</option>
              <option value="AUSTRALIA_CANDIDATO">Candidato Federal (Austrália)</option>
              <option value="CACO_ESTUDANTE">Estudante Unicamp (CACo)</option>
              <option value="CACO_GESTAO">Membro da Gestão (CACo)</option>
              <option value="BOTC_JOGADOR">Jogador (Blood on the Clocktower)</option>
              <option value="BOTC_STORYTELLER">Storyteller / Mestre (BoTC)</option>
            </select>
          </div>

          {exigeRa && (
            <div className="ra-collapse-box">
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="ra">RA (Registro Acadêmico Unicamp)</label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]+"
                  id="ra"
                  className="form-control"
                  placeholder="Ex: 288808"
                  value={ra}
                  onKeyDown={bloquearTeclasInvalidasNumero}
                  onChange={handleRaChange}
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="nome_real">Nome Completo</label>
            <input
              type="text"
              id="nome_real"
              className="form-control"
              value={nomeReal}
              onChange={(e) => setNomeReal(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="username">Username (Login)</label>
            <input
              type="text"
              id="username"
              className="form-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="senha">Senha</label>
            <input
              type="password"
              id="senha"
              className="form-control"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="senha_confirma">Confirme a Senha</label>
            <input
              type="password"
              id="senha_confirma"
              className="form-control"
              value={senhaConfirma}
              onChange={(e) => setSenhaConfirma(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" style={{ width: '100%' }}>
            Finalizar Cadastro
          </button>
        </form>

        <div className="auth-footer">
          Já possui conta? <Link to="/">Voltar para o Login</Link>
        </div>
      </div>
    </div>
  );
}